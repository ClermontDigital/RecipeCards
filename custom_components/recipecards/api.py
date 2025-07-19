"""WebSocket API for Recipe Cards integration."""
import logging
from typing import Any
import voluptuous as vol
from homeassistant.core import HomeAssistant  # type: ignore[import-untyped]
from homeassistant.components import websocket_api  # type: ignore[import-untyped]
from .const import DOMAIN
from .models import Recipe

_LOGGER = logging.getLogger(__name__)

RECIPE_LIST_TYPE = "recipecards/recipe_list"
RECIPE_GET_TYPE = "recipecards/recipe_get"
RECIPE_ADD_TYPE = "recipecards/recipe_add"
RECIPE_UPDATE_TYPE = "recipecards/recipe_update"
RECIPE_DELETE_TYPE = "recipecards/recipe_delete"

@websocket_api.websocket_command({
    "type": RECIPE_LIST_TYPE,
    "schema": websocket_api.BASE_COMMAND_MESSAGE_SCHEMA,
})
async def async_list_recipes(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """List all recipes."""
    if not connection.config_entry:
        connection.send_result(msg["id"], [])
        return
    entry_id = connection.config_entry.entry_id
    storage = hass.data[DOMAIN][entry_id]
    recipes = await storage.async_load_recipes()
    connection.send_result(msg["id"], [r.to_dict() for r in recipes])

@websocket_api.websocket_command({
    "type": RECIPE_GET_TYPE,
    "schema": websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({"recipe_id": str}),
})
async def async_get_recipe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Get a specific recipe by ID."""
    if not connection.config_entry:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    entry_id = connection.config_entry.entry_id
    storage = hass.data[DOMAIN][entry_id]
    recipe_id = msg["recipe_id"]
    recipes = await storage.async_load_recipes()
    for recipe in recipes:
        if recipe.id == recipe_id:
            connection.send_result(msg["id"], recipe.to_dict())
            return
    connection.send_error(msg["id"], "not_found", "Recipe not found")

@websocket_api.websocket_command({
    "type": RECIPE_ADD_TYPE,
    "schema": websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({"recipe": dict}),
})
async def async_add_recipe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Add a new recipe."""
    if not connection.config_entry:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    entry_id = connection.config_entry.entry_id
    storage = hass.data[DOMAIN][entry_id]
    data = msg["recipe"]
    recipe = Recipe.from_dict(data)
    await storage.async_add_recipe(recipe)
    connection.send_result(msg["id"], recipe.to_dict())

@websocket_api.websocket_command({
    "type": RECIPE_UPDATE_TYPE,
    "schema": websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({"recipe_id": str, "recipe": dict}),
})
async def async_update_recipe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Update an existing recipe."""
    if not connection.config_entry:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    entry_id = connection.config_entry.entry_id
    storage = hass.data[DOMAIN][entry_id]
    recipe_id = msg["recipe_id"]
    data = msg["recipe"]
    updated_recipe = Recipe.from_dict(data)
    ok = await storage.async_update_recipe(recipe_id, updated_recipe)
    if ok:
        connection.send_result(msg["id"], updated_recipe.to_dict())
    else:
        connection.send_error(msg["id"], "not_found", "Recipe not found")

@websocket_api.websocket_command({
    "type": RECIPE_DELETE_TYPE,
    "schema": websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({"recipe_id": str}),
})
async def async_delete_recipe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Delete a recipe by ID."""
    if not connection.config_entry:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    entry_id = connection.config_entry.entry_id
    storage = hass.data[DOMAIN][entry_id]
    recipe_id = msg["recipe_id"]
    await storage.async_delete_recipe(recipe_id)
    connection.send_result(msg["id"], True)

def register_api(hass: HomeAssistant) -> None:
    """Register the WebSocket API commands."""
    _LOGGER.info("Registering Recipe Cards WebSocket API")
    hass.components.websocket_api.async_register_command(async_list_recipes)
    hass.components.websocket_api.async_register_command(async_get_recipe)
    hass.components.websocket_api.async_register_command(async_add_recipe)
    hass.components.websocket_api.async_register_command(async_update_recipe)
    hass.components.websocket_api.async_register_command(async_delete_recipe)
