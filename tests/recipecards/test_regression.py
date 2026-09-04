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


async def _storage_recipes(hass: HomeAssistant, entry) -> list[dict]:
    """Read the full recipes straight from the entry's storage."""
    storage = hass.data[DOMAIN][entry.entry_id]["storage"]
    return [r.to_dict() for r in await storage.async_load_recipes()]


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
    # the sensor carries only a lightweight index now
    entry_index = state.attributes["recipes"][0]
    assert entry_index["ingredient_count"] == 2
    assert entry_index["step_count"] == 2
    assert entry_index["prep_time"] == 10
    assert entry_index["cook_time"] == 25
    assert entry_index["total_time"] == 35

    # the full recipe lives behind the WebSocket API
    stored = await _storage_recipes(hass, entry)
    assert stored[0]["ingredients"] == ["1 cup flour", "2 eggs"]


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

    index = hass.states.get(SENSOR).attributes["recipes"][0]
    assert index["title"] == "Anzacs"
    assert index["cook_time"] == 20, "cook_time was wiped by a title-only update"
    stored = await _storage_recipes(hass, entry)
    assert stored[0]["instructions"] == ["Bake for 20 minutes."]


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


async def test_card_is_registered_once_when_entries_race(hass: HomeAssistant) -> None:
    """The card must be loaded from exactly one URL, however many sections exist.

    Regression: the `frontend_registered` guard was set *after* several awaits, so
    entries setting up concurrently all passed it. The loser of the static-path
    race hit "path already registered", fell back to /local, and the browser
    imported the card twice from two different URLs.

    The static-path stub sleeps before raising on the second call, which is what
    forces the coroutines to interleave the way they do on a real startup.
    """
    import asyncio
    from unittest.mock import patch

    from custom_components.recipecards import _async_setup_frontend

    await _setup(hass)
    hass.data[DOMAIN]["frontend_registered"] = False  # re-arm

    calls = []

    async def _register(self, paths):  # unbound method: takes self
        calls.append(paths)
        n = len(calls)
        await asyncio.sleep(0)  # yield, so a racing coroutine gets its turn
        if n > 1:
            raise RuntimeError("Static path already registered")

    with (
        patch(
            "homeassistant.components.http.HomeAssistantHTTP.async_register_static_paths",
            new=_register,
        ),
        patch("homeassistant.components.frontend.add_extra_js_url") as add_js,
    ):
        await asyncio.gather(*(_async_setup_frontend(hass) for _ in range(3)))

    urls = [c.args[1] for c in add_js.call_args_list]
    assert len(calls) == 1, f"static path registered {len(calls)} times"
    assert len(urls) == 1, f"card registered {len(urls)} times: {urls}"
    assert urls[0].startswith("/recipecards/"), urls


async def test_non_admin_cannot_add_recipe_via_service(
    hass: HomeAssistant, hass_read_only_user
) -> None:
    """Read-only household members must not be able to change recipes."""
    import pytest as _pytest
    from homeassistant.core import Context
    from homeassistant.exceptions import Unauthorized

    entry = await _setup(hass)
    with _pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN, "add_recipe",
            {"config_entry_id": entry.entry_id, "title": "Sneaky"},
            blocking=True,
            context=Context(user_id=hass_read_only_user.id),
        )
    await hass.async_block_till_done()
    assert hass.states.get(SENSOR).state == "0"


async def test_non_admin_cannot_delete_recipe_via_service(
    hass: HomeAssistant, hass_read_only_user
) -> None:
    import pytest as _pytest
    from homeassistant.core import Context
    from homeassistant.exceptions import Unauthorized

    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe", {"config_entry_id": entry.entry_id, "title": "Keep me"},
        blocking=True,
    )
    await hass.async_block_till_done()
    recipe_id = hass.states.get(SENSOR).attributes["recipes"][0]["id"]

    with _pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN, "delete_recipe",
            {"config_entry_id": entry.entry_id, "recipe_id": recipe_id},
            blocking=True,
            context=Context(user_id=hass_read_only_user.id),
        )
    await hass.async_block_till_done()
    assert hass.states.get(SENSOR).state == "1", "recipe was deleted by a non-admin"


async def test_automations_may_still_write(hass: HomeAssistant) -> None:
    """A call with no user in its context is an automation, not a person."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe", {"config_entry_id": entry.entry_id, "title": "From automation"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(SENSOR).state == "1"


async def test_websocket_write_requires_admin(
    hass: HomeAssistant, hass_ws_client, hass_read_only_access_token
) -> None:
    """The WebSocket write commands must refuse non-admins too."""
    await _setup(hass)
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json({
        "id": 1, "type": "recipecards/recipe_add", "recipe": {"title": "Sneaky"},
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "unauthorized"

    await client.send_json({"id": 2, "type": "recipecards/recipe_delete", "recipe_id": "x"})
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "unauthorized"


async def test_non_admin_can_still_read_recipes(
    hass: HomeAssistant, hass_ws_client, hass_read_only_access_token
) -> None:
    """Read-only users keep full read access, which is the whole point."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe", {"config_entry_id": entry.entry_id, "title": "Pavlova"},
        blocking=True,
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json({"id": 1, "type": "recipecards/recipe_list"})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert [r["title"] for r in msg["result"]] == ["Pavlova"]


async def test_concurrent_adds_do_not_lose_recipes(hass: HomeAssistant) -> None:
    """Overlapping writes must all survive.

    Regression: every mutator did read -> change -> write with awaits in between
    and no lock, so two adds could both read the same starting list and the second
    write would silently drop the first one's recipe. A recipe went missing from a
    live instance exactly this way.
    """
    import asyncio

    entry = await _setup(hass)
    titles = [f"Recipe {n:02d}" for n in range(20)]

    await asyncio.gather(*(
        hass.services.async_call(
            DOMAIN, "add_recipe",
            {"config_entry_id": entry.entry_id, "title": t},
            blocking=True,
        )
        for t in titles
    ))
    await hass.async_block_till_done()

    stored = sorted(r["title"] for r in hass.states.get(SENSOR).attributes["recipes"])
    assert stored == sorted(titles), (
        f"lost {sorted(set(titles) - set(stored))} of {len(titles)} concurrent adds"
    )


async def test_concurrent_add_and_delete_are_serialised(hass: HomeAssistant) -> None:
    """A delete running alongside adds must not resurrect or drop anything else."""
    import asyncio

    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe", {"config_entry_id": entry.entry_id, "title": "Doomed"},
        blocking=True,
    )
    await hass.async_block_till_done()
    doomed = hass.states.get(SENSOR).attributes["recipes"][0]["id"]

    await asyncio.gather(
        hass.services.async_call(
            DOMAIN, "delete_recipe",
            {"config_entry_id": entry.entry_id, "recipe_id": doomed}, blocking=True),
        *(hass.services.async_call(
            DOMAIN, "add_recipe",
            {"config_entry_id": entry.entry_id, "title": f"Keeper {n}"}, blocking=True)
          for n in range(5)),
    )
    await hass.async_block_till_done()

    stored = sorted(r["title"] for r in hass.states.get(SENSOR).attributes["recipes"])
    assert stored == sorted(f"Keeper {n}" for n in range(5)), stored


async def test_image_urls_are_accepted(hass: HomeAssistant) -> None:
    """Real recipe-site image URLs must be accepted.

    Regression: validate_image required the URL to end in .png/.jpg/.jpeg/.gif, so
    .webp images and any URL carrying a resize query string were refused.
    """
    entry = await _setup(hass)
    urls = [
        "https://example.com/photo.webp",
        "https://example.com/photo.jpg?resize=600%2C400&ssl=1",
        "https://example.com/img/1234",
        "data:image/png;base64,iVBORw0KGgo=",
    ]
    for n, url in enumerate(urls):
        await hass.services.async_call(
            DOMAIN, "add_recipe",
            {"config_entry_id": entry.entry_id, "title": f"Photo {n}", "image": url},
            blocking=True,
        )
    await hass.async_block_till_done()

    stored = {r["title"]: r["image"] for r in hass.states.get(SENSOR).attributes["recipes"]}
    for n, url in enumerate(urls):
        assert stored[f"Photo {n}"] == url


async def test_image_survives_a_title_only_update(hass: HomeAssistant) -> None:
    """Editing the title must not drop the photo."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": "Pav",
         "image": "https://example.com/pav.webp"},
        blocking=True,
    )
    await hass.async_block_till_done()
    rid = hass.states.get(SENSOR).attributes["recipes"][0]["id"]

    await hass.services.async_call(
        DOMAIN, "update_recipe",
        {"config_entry_id": entry.entry_id, "recipe_id": rid, "title": "Pavlova"},
        blocking=True,
    )
    await hass.async_block_till_done()
    r = hass.states.get(SENSOR).attributes["recipes"][0]
    assert r["title"] == "Pavlova"
    assert r["image"] == "https://example.com/pav.webp"


async def test_collection_attributes_stay_small(hass: HomeAssistant) -> None:
    """The collection sensor must not embed the full text of every recipe.

    Home Assistant caps a single attribute near 16 KB, every browser downloads all
    attributes on connect, and the recorder writes them on change. A 40 recipe
    collection previously blew straight past that.
    """
    import json as _json

    entry = await _setup(hass)
    long_step = "Stir the mixture gently for several minutes until it thickens. " * 6
    for n in range(40):
        await hass.services.async_call(
            DOMAIN, "add_recipe",
            {"config_entry_id": entry.entry_id, "title": f"Recipe {n:02d}",
             "description": "A fairly wordy description of this dish. " * 4,
             "ingredients": [f"{i} cups of something" for i in range(12)],
             "instructions": [long_step for _ in range(8)],
             "notes": "Some notes that go on a bit. " * 8},
            blocking=True,
        )
    await hass.async_block_till_done()

    attrs = hass.states.get(SENSOR).attributes
    size = len(_json.dumps(dict(attrs)))
    assert attrs["count"] == 40
    assert size < 16384, f"attributes are {size} bytes, over the 16 KB cap"
    # the index still carries what a tile needs
    first = attrs["recipes"][0]
    assert {"id", "title", "image", "total_time", "ingredient_count", "step_count"} <= set(first)
    # but not the bulk
    assert "instructions" not in first and "ingredients" not in first


async def test_per_recipe_entities_are_off_by_default(hass: HomeAssistant) -> None:
    """Hundreds of extra entities should not appear just for having recipes."""
    entry = await _setup(hass)
    for n in range(5):
        await hass.services.async_call(
            DOMAIN, "add_recipe",
            {"config_entry_id": entry.entry_id, "title": f"Dish {n}"}, blocking=True)
    await hass.async_block_till_done()

    recipe_entities = [
        e for e in hass.states.async_entity_ids("sensor")
        if e.startswith("sensor.") and "recipe" in e and e != SENSOR
    ]
    assert recipe_entities == [], f"unexpected per-recipe entities: {recipe_entities}"
    assert hass.states.get(SENSOR).state == "5"


async def test_tags_round_trip(hass: HomeAssistant) -> None:
    """A recipe can carry several tags, which is the point of them."""
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": "Brisket",
         "tags": ["Mains", "Slow Cooked", "Keto"]},
        blocking=True,
    )
    await hass.async_block_till_done()

    stored = await _storage_recipes(hass, entry)
    assert stored[0]["tags"] == ["Mains", "Slow Cooked", "Keto"]
    idx = hass.states.get(SENSOR).attributes["recipes"][0]
    assert idx["tags"] == ["Mains", "Slow Cooked", "Keto"]
    assert hass.states.get(SENSOR).attributes["tags"] == ["Keto", "Mains", "Slow Cooked"]


async def test_tags_survive_a_title_only_update(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": "Pav", "tags": ["Desserts"]},
        blocking=True)
    await hass.async_block_till_done()
    rid = hass.states.get(SENSOR).attributes["recipes"][0]["id"]
    await hass.services.async_call(
        DOMAIN, "update_recipe",
        {"config_entry_id": entry.entry_id, "recipe_id": rid, "title": "Pavlova"},
        blocking=True)
    await hass.async_block_till_done()
    stored = await _storage_recipes(hass, entry)
    assert stored[0]["title"] == "Pavlova"
    assert stored[0]["tags"] == ["Desserts"]


async def test_existing_recipes_are_seeded_with_the_section_name(hass: HomeAssistant) -> None:
    """Upgrading should populate tags from the section, without touching anything else."""
    from custom_components.recipecards.models import Recipe
    from custom_components.recipecards.storage import RecipeStorage
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, title="Desserts", data={})
    entry.add_to_hass(hass)
    # a recipe written by an older version: no tags at all
    pre = RecipeStorage(hass, entry.entry_id)
    await pre.async_add_recipe(Recipe(id="old1", title="Anzac Biscuits"))

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    stored = await _storage_recipes(hass, entry)
    assert stored[0]["title"] == "Anzac Biscuits"
    assert stored[0]["tags"] == ["Desserts"]


async def test_seeding_does_not_overwrite_existing_tags(hass: HomeAssistant) -> None:
    from custom_components.recipecards.models import Recipe
    from custom_components.recipecards.storage import RecipeStorage
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, title="Desserts", data={})
    entry.add_to_hass(hass)
    pre = RecipeStorage(hass, entry.entry_id)
    await pre.async_add_recipe(Recipe(id="x", title="Pav", tags=["Summer", "Eggs"]))

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    stored = await _storage_recipes(hass, entry)
    assert stored[0]["tags"] == ["Summer", "Eggs"], "seeding clobbered the user's own tags"


async def test_websocket_search_by_tag(hass: HomeAssistant, hass_ws_client) -> None:
    entry = await _setup(hass)
    for title, tags in (("Brisket", ["Mains", "Slow Cooked"]), ("Pav", ["Desserts"])):
        await hass.services.async_call(
            DOMAIN, "add_recipe",
            {"config_entry_id": entry.entry_id, "title": title, "tags": tags}, blocking=True)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "recipecards/recipe_search", "tag": "slow cooked"})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert [r["title"] for r in msg["result"]] == ["Brisket"]


def test_parse_duration_handles_both_shapes() -> None:
    """Mealie stores times as whatever the user typed, so both turn up."""
    from custom_components.recipecards.importers import parse_duration
    assert parse_duration("PT1H30M") == 90
    assert parse_duration("PT45M") == 45
    assert parse_duration("1 hour 30 minutes") == 90
    assert parse_duration("30 Minutes") == 30
    assert parse_duration("2 hrs") == 120
    assert parse_duration(25) == 25
    assert parse_duration("") is None
    assert parse_duration(None) is None
    assert parse_duration("ages") is None
    assert parse_duration("3 days") is None  # over the 1440 cap


def test_mealie_mapping() -> None:
    """A realistic Mealie payload maps onto the Recipe Cards shape."""
    from custom_components.recipecards.importers import mealie_to_recipe
    payload = {
        "id": "abc-123",
        "name": "Anzac Biscuits",
        "description": "Chewy and golden.",
        "recipeYield": "24 biscuits",
        "prepTime": "15 Minutes",
        "performTime": "20 Minutes",
        "totalTime": "35 Minutes",
        "orgURL": "https://example.com/anzac",
        "recipeIngredient": [
            {"display": "1 cup rolled oats"},
            {"quantity": 125, "unit": {"name": "g"}, "food": {"name": "butter"}, "note": "melted"},
            "2 tbsp golden syrup",
        ],
        "recipeInstructions": [{"text": "Heat the oven to 160C."}, {"text": "Bake for 20 minutes."}],
        "tags": [{"name": "Biscuits"}, {"name": "Baking"}],
        "recipeCategory": [{"name": "Desserts"}],
        "notes": [{"title": "Tip", "text": "Leave on the tray 5 minutes."}],
    }
    r = mealie_to_recipe(payload, "http://mealie.local:9925/")
    assert r["title"] == "Anzac Biscuits"
    assert r["ingredients"] == ["1 cup rolled oats", "125 g butter, melted", "2 tbsp golden syrup"]
    assert r["instructions"] == ["Heat the oven to 160C.", "Bake for 20 minutes."]
    assert r["tags"] == ["Biscuits", "Baking", "Desserts"]
    assert r["prep_time"] == 15 and r["cook_time"] == 20 and r["total_time"] == 35
    assert r["image"] == "http://mealie.local:9925/api/media/recipes/abc-123/images/original.webp"
    assert "24 biscuits" in r["notes"] and "example.com/anzac" in r["notes"]


def test_mealie_mapping_skips_untitled() -> None:
    from custom_components.recipecards.importers import mealie_to_recipe
    assert mealie_to_recipe({"name": ""}, "http://x") is None


async def test_import_recipes_service(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    res = await hass.services.async_call(
        DOMAIN, "import_recipes",
        {"config_entry_id": entry.entry_id, "recipes": [
            {"title": "One", "ingredients": ["a"], "tags": ["Imported"]},
            {"title": "Two", "instructions": ["Bake for 20 minutes."]},
        ]},
        blocking=True, return_response=True,
    )
    await hass.async_block_till_done()
    assert res["imported"] == 2
    assert hass.states.get(SENSOR).state == "2"
    stored = {r["title"]: r for r in await _storage_recipes(hass, entry)}
    assert stored["One"]["tags"] == ["Imported"]
    assert stored["Two"]["cook_time"] == 20  # times still parsed out of the method


async def test_import_skips_titles_already_present(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, "add_recipe", {"config_entry_id": entry.entry_id, "title": "Pavlova"}, blocking=True)
    await hass.async_block_till_done()

    res = await hass.services.async_call(
        DOMAIN, "import_recipes",
        {"config_entry_id": entry.entry_id,
         "recipes": [{"title": "Pavlova"}, {"title": "pavlova"}, {"title": "Lamingtons"}]},
        blocking=True, return_response=True,
    )
    await hass.async_block_till_done()
    assert res["imported"] == 1 and res["skipped"] == 2
    assert hass.states.get(SENSOR).state == "2"


async def test_import_requires_admin(hass: HomeAssistant, hass_read_only_user) -> None:
    import pytest as _pytest
    from homeassistant.core import Context
    from homeassistant.exceptions import Unauthorized

    entry = await _setup(hass)
    with _pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN, "import_recipes",
            {"config_entry_id": entry.entry_id, "recipes": [{"title": "Sneaky"}]},
            blocking=True, context=Context(user_id=hass_read_only_user.id),
        )


async def test_fetch_mealie_paginates_and_maps(hass: HomeAssistant, aioclient_mock) -> None:
    """Walks every page of the recipe list, then reads each recipe in full."""
    from custom_components.recipecards.importers import fetch_mealie

    base = "http://mealie.local:9925"
    page1 = {"items": [{"slug": f"r{n}"} for n in range(100)]}
    page2 = {"items": [{"slug": "r100"}]}
    aioclient_mock.get(f"{base}/api/recipes", json=page1, params={"page": "1", "perPage": "100"})
    aioclient_mock.get(f"{base}/api/recipes", json=page2, params={"page": "2", "perPage": "100"})
    for n in range(101):
        aioclient_mock.get(
            f"{base}/api/recipes/r{n}",
            json={"id": f"id{n}", "name": f"Recipe {n}", "recipeIngredient": ["a"],
                  "recipeInstructions": [{"text": "Bake for 20 minutes."}]},
        )

    out = await fetch_mealie(hass, base, "tok")
    assert len(out) == 101
    assert out[0]["title"] == "Recipe 0"
    assert out[0]["image"].endswith("/api/media/recipes/id0/images/original.webp")


async def test_fetch_mealie_reports_a_bad_token(hass: HomeAssistant, aioclient_mock) -> None:
    import pytest as _pytest
    from custom_components.recipecards.importers import fetch_mealie

    base = "http://mealie.local:9925"
    aioclient_mock.get(f"{base}/api/recipes", status=401)
    with _pytest.raises(ValueError, match="token"):
        await fetch_mealie(hass, base, "wrong")


async def test_fetch_mealie_skips_one_unreadable_recipe(hass: HomeAssistant, aioclient_mock) -> None:
    """One bad recipe must not abandon the whole import."""
    from custom_components.recipecards.importers import fetch_mealie

    base = "http://mealie.local:9925"
    aioclient_mock.get(f"{base}/api/recipes",
                       json={"items": [{"slug": "good"}, {"slug": "bad"}]})
    aioclient_mock.get(f"{base}/api/recipes/good", json={"id": "1", "name": "Good"})
    aioclient_mock.get(f"{base}/api/recipes/bad", status=500)

    out = await fetch_mealie(hass, base, "tok")
    assert [r["title"] for r in out] == ["Good"]


def _mela_doc(title="Anzac Biscuits", **over):
    doc = {
        "id": "example.com/anzac",
        "title": title,
        "text": "Chewy and golden.",
        "yield": "24 biscuits",
        "prepTime": "15 minutes",
        "cookTime": "20 minutes",
        "totalTime": "35 minutes",
        "categories": ["Baking", "Biscuits"],
        "ingredients": "- 1 cup rolled oats\n- **125 g** butter\n\n- 2 tbsp golden syrup",
        "instructions": "1. Heat the oven to 160C.\n2. Bake for 20 minutes.",
        "notes": "Leave on the tray 5 minutes.",
        "nutrition": "120 cal each",
        "link": "https://example.com/anzac",
        "images": [],
    }
    doc.update(over)
    return doc


def test_mela_mapping_strips_markdown_and_splits_lines(tmp_path) -> None:
    from custom_components.recipecards.importers import mela_to_recipe
    r = mela_to_recipe(_mela_doc(), None, "/local/recipecards")
    assert r["title"] == "Anzac Biscuits"
    assert r["description"] == "Chewy and golden."
    # bullets, bold markers and numbering all gone, blank lines dropped
    assert r["ingredients"] == ["1 cup rolled oats", "125 g butter", "2 tbsp golden syrup"]
    assert r["instructions"] == ["Heat the oven to 160C.", "Bake for 20 minutes."]
    assert r["tags"] == ["Baking", "Biscuits"]
    assert r["prep_time"] == 15 and r["cook_time"] == 20 and r["total_time"] == 35
    assert "24 biscuits" in r["notes"] and "example.com/anzac" in r["notes"]
    assert "image" not in r


def test_mela_writes_images_out_to_disk(tmp_path) -> None:
    """Base64 photos go to disk, not into the store."""
    import base64
    from custom_components.recipecards.importers import mela_to_recipe

    png = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 200).decode()
    r = mela_to_recipe(_mela_doc(images=[png]), str(tmp_path), "/local/recipecards")
    assert r["image"].startswith("/local/recipecards/")
    assert r["image"].endswith(".png")
    written = list(tmp_path.iterdir())
    assert len(written) == 1 and written[0].stat().st_size > 200


def test_mela_skips_heic_photos(tmp_path) -> None:
    """iOS HEIC would give a broken image in every browser."""
    import base64
    from custom_components.recipecards.importers import mela_to_recipe

    heic = base64.b64encode(b"\x00\x00\x00\x20ftypheic" + b"0" * 200).decode()
    r = mela_to_recipe(_mela_doc(images=[heic]), str(tmp_path), "/local/recipecards")
    assert "image" not in r
    assert list(tmp_path.iterdir()) == []


def test_parse_mela_single_file(tmp_path) -> None:
    import json as _json
    from custom_components.recipecards.importers import parse_mela

    f = tmp_path / "one.melarecipe"
    f.write_text(_json.dumps(_mela_doc()))
    out = parse_mela(str(f), None, "/local/recipecards")
    assert [r["title"] for r in out] == ["Anzac Biscuits"]


def test_parse_mela_archive_skips_junk(tmp_path) -> None:
    """A .melarecipes is a zip; ignore anything that is not a recipe."""
    import json as _json, zipfile
    from custom_components.recipecards.importers import parse_mela

    archive = tmp_path / "export.melarecipes"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("Anzac.melarecipe", _json.dumps(_mela_doc()))
        z.writestr("Pav.melarecipe", _json.dumps(_mela_doc(title="Pavlova")))
        z.writestr("broken.melarecipe", "{not json")
        z.writestr("__MACOSX/._Anzac.melarecipe", "junk")
        z.writestr("readme.txt", "ignore me")
    out = parse_mela(str(archive), None, "/local/recipecards")
    assert sorted(r["title"] for r in out) == ["Anzac Biscuits", "Pavlova"]


def test_parse_mela_rejects_a_missing_file(tmp_path) -> None:
    import pytest as _pytest
    from custom_components.recipecards.importers import parse_mela
    with _pytest.raises(ValueError, match="No such file"):
        parse_mela(str(tmp_path / "nope.melarecipe"), None, "/local")


async def test_mela_import_refuses_paths_outside_config(hass: HomeAssistant) -> None:
    """The importer must not be a way to read arbitrary files off the host."""
    import pytest as _pytest
    from homeassistant.exceptions import HomeAssistantError

    entry = await _setup(hass)
    with _pytest.raises(HomeAssistantError, match="config directory"):
        await hass.services.async_call(
            DOMAIN, "import_from_mela",
            {"config_entry_id": entry.entry_id, "path": "/etc/passwd"},
            blocking=True, return_response=True,
        )
    with _pytest.raises(HomeAssistantError, match="config directory"):
        await hass.services.async_call(
            DOMAIN, "import_from_mela",
            {"config_entry_id": entry.entry_id, "path": "../../../../etc/hosts"},
            blocking=True, return_response=True,
        )


async def test_mela_import_end_to_end(hass: HomeAssistant) -> None:
    import json as _json, os

    entry = await _setup(hass)
    rel = "mela-export.melarecipe"
    with open(hass.config.path(rel), "w") as handle:
        _json.dump(_mela_doc(), handle)

    res = await hass.services.async_call(
        DOMAIN, "import_from_mela",
        {"config_entry_id": entry.entry_id, "path": rel, "import_images": False},
        blocking=True, return_response=True,
    )
    await hass.async_block_till_done()
    assert res["imported"] == 1
    stored = await _storage_recipes(hass, entry)
    assert stored[0]["title"] == "Anzac Biscuits"
    assert stored[0]["tags"] == ["Baking", "Biscuits"]
    os.remove(hass.config.path(rel))
