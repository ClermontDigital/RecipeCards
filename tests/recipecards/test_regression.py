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
