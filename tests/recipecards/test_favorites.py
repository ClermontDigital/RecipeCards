"""Per-user favourites over the WebSocket API."""
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.recipecards.const import DOMAIN


async def _setup(hass: HomeAssistant, titles=("Pavlova", "Lamingtons")) -> dict[str, str]:
    entry = MockConfigEntry(domain=DOMAIN, title="Desserts", data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for title in titles:
        await hass.services.async_call(
            DOMAIN, "add_recipe", {"config_entry_id": entry.entry_id, "title": title}, blocking=True
        )
    await hass.async_block_till_done()
    return {r["title"]: r["id"] for r in hass.states.get("sensor.recipe_cards").attributes["recipes"]}


async def _call(client, msg_id, **msg):
    await client.send_json({"id": msg_id, **msg})
    return await client.receive_json()


async def _starred(client, msg_id) -> set[str]:
    res = await _call(client, msg_id, type="recipecards/recipe_list")
    assert res["success"]
    return {r["title"] for r in res["result"] if r["_favorite"]}


async def test_star_and_unstar(hass: HomeAssistant, hass_ws_client):
    ids = await _setup(hass)
    client = await hass_ws_client(hass)
    assert await _starred(client, 1) == set()

    res = await _call(client, 2, type="recipecards/favorite_set", recipe_id=ids["Pavlova"], favorite=True)
    assert res["success"] and res["result"] == {"recipe_id": ids["Pavlova"], "favorite": True}
    assert await _starred(client, 3) == {"Pavlova"}

    got = await _call(client, 4, type="recipecards/recipe_get", recipe_id=ids["Pavlova"])
    assert got["result"]["_favorite"] is True

    res = await _call(client, 5, type="recipecards/favorite_set", recipe_id=ids["Pavlova"], favorite=False)
    assert res["result"]["favorite"] is False
    assert await _starred(client, 6) == set()


async def test_favourites_are_per_user_and_not_admin_only(
    hass: HomeAssistant, hass_ws_client, hass_read_only_access_token
):
    ids = await _setup(hass)
    admin = await hass_ws_client(hass)
    other = await hass_ws_client(hass, hass_read_only_access_token)  # a non-admin user

    await _call(admin, 1, type="recipecards/favorite_set", recipe_id=ids["Pavlova"], favorite=True)
    res = await _call(other, 1, type="recipecards/favorite_set", recipe_id=ids["Lamingtons"], favorite=True)
    assert res["success"], res  # starring is allowed for non-admins

    assert await _starred(admin, 2) == {"Pavlova"}
    assert await _starred(other, 2) == {"Lamingtons"}


async def test_unknown_recipe(hass: HomeAssistant, hass_ws_client):
    await _setup(hass)
    client = await hass_ws_client(hass)
    res = await _call(client, 1, type="recipecards/favorite_set", recipe_id="nope", favorite=True)
    assert not res["success"] and res["error"]["code"] == "not_found"
    # unstarring something that no longer exists is harmless
    res = await _call(client, 2, type="recipecards/favorite_set", recipe_id="nope", favorite=False)
    assert res["success"] and res["result"]["favorite"] is False


async def test_favourites_are_saved_and_deleted_recipes_drop_out(
    hass: HomeAssistant, hass_ws_client, hass_storage
):
    ids = await _setup(hass)
    client = await hass_ws_client(hass)
    await _call(client, 1, type="recipecards/favorite_set", recipe_id=ids["Pavlova"], favorite=True)
    await _call(client, 2, type="recipecards/favorite_set", recipe_id=ids["Lamingtons"], favorite=True)
    saved = hass_storage["recipecards_favorites.json"]["data"]["users"]
    assert [set(v) for v in saved.values()] == [{ids["Pavlova"], ids["Lamingtons"]}]

    res = await _call(client, 3, type="recipecards/recipe_delete", recipe_id=ids["Lamingtons"])
    assert res["success"]
    assert await _starred(client, 4) == {"Pavlova"}  # a deleted recipe is never listed

    # the next change prunes the deleted id from the file
    await _call(client, 5, type="recipecards/favorite_set", recipe_id=ids["Pavlova"], favorite=True)
    saved = hass_storage["recipecards_favorites.json"]["data"]["users"]
    assert [v for v in saved.values()] == [[ids["Pavlova"]]]


async def test_search_carries_the_flag(hass: HomeAssistant, hass_ws_client):
    ids = await _setup(hass)
    client = await hass_ws_client(hass)
    await _call(client, 1, type="recipecards/favorite_set", recipe_id=ids["Pavlova"], favorite=True)
    res = await _call(client, 2, type="recipecards/recipe_search", query="pav")
    assert [(r["title"], r["_favorite"]) for r in res["result"]] == [("Pavlova", True)]
