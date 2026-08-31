"""Tests for the Recipe Cards WebSocket API.

These drive the commands through HA's real dispatch path via hass_ws_client.
Calling the handlers directly (as this file used to) cannot catch a missing
@websocket_api.async_response, because HA invokes handlers synchronously and
discards the returned coroutine.
"""
import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.recipecards.const import DOMAIN


async def _add_entry(hass: HomeAssistant, title: str) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, title=title, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _add_recipe(hass: HomeAssistant, entry, title: str) -> None:
    await hass.services.async_call(
        DOMAIN, "add_recipe",
        {"config_entry_id": entry.entry_id, "title": title},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_recipe_list_empty(hass: HomeAssistant, hass_ws_client):
    await _add_entry(hass, "Desserts")
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "recipecards/recipe_list"})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"] == []


async def test_recipe_list_aggregates_multiple_entries(hass: HomeAssistant, hass_ws_client):
    desserts = await _add_entry(hass, "Desserts")
    mains = await _add_entry(hass, "Mains")
    await _add_recipe(hass, desserts, "Pavlova")
    await _add_recipe(hass, mains, "Roast lamb")

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "recipecards/recipe_list"})
    msg = await client.receive_json()

    assert msg["success"] is True
    assert sorted(r["title"] for r in msg["result"]) == ["Pavlova", "Roast lamb"]
    assert {r["_entry_title"] for r in msg["result"]} == {"Desserts", "Mains"}


async def test_recipe_get_and_delete(hass: HomeAssistant, hass_ws_client):
    entry = await _add_entry(hass, "Desserts")
    await _add_recipe(hass, entry, "Pavlova")
    recipe_id = hass.states.get("sensor.recipe_cards").attributes["recipes"][0]["id"]

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "recipecards/recipe_get", "recipe_id": recipe_id})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["title"] == "Pavlova"

    await client.send_json({"id": 2, "type": "recipecards/recipe_delete", "recipe_id": recipe_id})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert hass.states.get("sensor.recipe_cards").state == "0"


async def test_recipe_get_missing_returns_error(hass: HomeAssistant, hass_ws_client):
    await _add_entry(hass, "Desserts")
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "recipecards/recipe_get", "recipe_id": "nope"})
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "not_found"


async def test_recipe_add_via_websocket(hass: HomeAssistant, hass_ws_client):
    entry = await _add_entry(hass, "Desserts")
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 1,
        "type": "recipecards/recipe_add",
        "recipe": {"title": "Lamingtons", "instructions": ["Bake for 25 minutes."]},
    })
    msg = await client.receive_json()

    assert msg["success"] is True
    assert msg["result"]["title"] == "Lamingtons"
    assert msg["result"]["cook_time"] == 25
    assert hass.states.get("sensor.recipe_cards").state == "1"
