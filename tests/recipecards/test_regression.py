"""Regression tests for the defects that made RecipeCards unusable before 1.9.0.

Each test here maps to a specific bug that shipped in 1.8.0 and was only
observable against a running Home Assistant, which is why the original suite
(which mocked the seams) never caught any of them.
"""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.recipecards.const import DOMAIN
from custom_components.recipecards.models import Recipe

SENSOR = "sensor.recipe_cards"


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, title="Desserts", data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_add_recipe_with_minimal_payload(hass: HomeAssistant) -> None:
    """A title-only call must succeed.

    Regression: `vol.Optional("prep_time", default=None)` piped through
    `vol.Coerce(int)` meant voluptuous validated `int(None)` and rejected
    *every* add_recipe call with a bare 400.
    """
    entry = await _setup(hass)

    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": "Pavlova"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SENSOR)
    assert state.state == "1"
    assert [r["title"] for r in state.attributes["recipes"]] == ["Pavlova"]


async def test_add_recipe_full_payload_persists_and_refreshes(hass: HomeAssistant) -> None:
    """The write must land AND the coordinator must refresh.

    Regression: the double `@classmethod` on parse_times raised TypeError after
    the save but before _notify_update(), so recipes persisted invisibly and
    only appeared after a restart.
    """
    entry = await _setup(hass)

    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {
            "config_entry_id": entry.entry_id,
            "title": "Lamingtons",
            "ingredients": ["1 cup flour", "2 eggs"],
            "instructions": ["Prep for 10 minutes.", "Bake for 25 minutes."],
            "notes": "A classic.",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SENSOR)
    assert state.state == "1", "sensor did not refresh after the write"
    recipe = state.attributes["recipes"][0]
    assert recipe["ingredients"] == ["1 cup flour", "2 eggs"]
    # times parsed out of the instruction text
    assert recipe["prep_time"] == 10
    assert recipe["cook_time"] == 25
    assert recipe["total_time"] == 35


async def test_parse_times_is_callable_and_correct() -> None:
    """Regression: `@classmethod` was applied twice, which Python 3.13 removed."""
    assert Recipe.parse_times("Prep: 15 min. Cook: 1 hour.") == {
        "prep_time": 15, "cook_time": 60, "total_time": 75,
    }
    assert Recipe.parse_times("no times here") == {
        "prep_time": None, "cook_time": None, "total_time": None,
    }


async def test_explicit_times_are_not_overwritten_by_parsing(hass: HomeAssistant) -> None:
    """Caller-supplied times must win over text parsing."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {
            "config_entry_id": entry.entry_id,
            "title": "Slow roast",
            "instructions": ["Bake for 25 minutes."],
            "cook_time": 240,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(SENSOR).attributes["recipes"][0]["cook_time"] == 240


async def test_update_recipe_does_not_wipe_untouched_fields(hass: HomeAssistant) -> None:
    """Regression: injected `None` defaults were merged over the stored record,
    clearing image and times on every edit - even a title-only change."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {
            "config_entry_id": entry.entry_id,
            "title": "Anzac biscuits",
            "instructions": ["Bake for 20 minutes."],
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    recipe_id = hass.states.get(SENSOR).attributes["recipes"][0]["id"]

    await hass.services.async_call(
        DOMAIN, "update_recipe",
        {"config_entry_id": entry.entry_id, "recipe_id": recipe_id, "title": "Anzacs"},
        blocking=True,
    )
    await hass.async_block_till_done()

    recipe = hass.states.get(SENSOR).attributes["recipes"][0]
    assert recipe["title"] == "Anzacs"
    assert recipe["cook_time"] == 20, "cook_time was wiped by a title-only update"
    assert recipe["instructions"] == ["Bake for 20 minutes."]


async def test_websocket_recipe_list_responds(hass: HomeAssistant, hass_ws_client) -> None:
    """Regression: all six handlers were async but lacked @async_response, so HA
    called them synchronously, dropped the coroutine, and never sent a result.
    The frontend's callWS promise hung forever."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": "Damper"},
        blocking=True,
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "recipecards/recipe_list"})
    msg = await client.receive_json()

    assert msg["success"] is True
    assert [r["title"] for r in msg["result"]] == ["Damper"]
    assert msg["result"][0]["_entry_title"] == "Desserts"


async def test_websocket_search_without_max_time(hass: HomeAssistant, hass_ws_client) -> None:
    """Regression: `max_time` had the same default=None/Coerce(int) bug, and the
    filter then compared None > int."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": "Scones"},
        blocking=True,
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "recipecards/recipe_search", "query": "sco"})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert len(msg["result"]) == 1


async def test_options_flow_add_recipe_form_renders(hass: HomeAssistant) -> None:
    """Regression: config_flow.py used `cv.text` with `cv` never imported, so the
    Settings UI died with NameError on entry."""
    entry = await _setup(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_recipe"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "add_recipe"


async def test_delete_recipe(hass: HomeAssistant) -> None:
    """delete_recipe was the only working service before; keep it that way."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": "Temporary"},
        blocking=True,
    )
    await hass.async_block_till_done()
    recipe_id = hass.states.get(SENSOR).attributes["recipes"][0]["id"]

    await hass.services.async_call(
        DOMAIN, "delete_recipe",
        {"config_entry_id": entry.entry_id, "recipe_id": recipe_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(SENSOR).state == "0"


async def test_recipes_survive_a_reload(hass: HomeAssistant) -> None:
    """Storage must round-trip through a config entry reload."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": "Sticky date pudding"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(SENSOR)
    assert state.state == "1"
    assert state.attributes["recipes"][0]["title"] == "Sticky date pudding"
