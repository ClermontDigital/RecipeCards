"""WebSocket API for Recipe Cards integration."""
import logging
from typing import Any
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api
from .const import DOMAIN
from .models import Recipe
from .services import cleanup_recipe_entities

_LOGGER = logging.getLogger(__name__)

RECIPE_LIST_TYPE = "recipecards/recipe_list"
RECIPE_GET_TYPE = "recipecards/recipe_get"
RECIPE_ADD_TYPE = "recipecards/recipe_add"
RECIPE_UPDATE_TYPE = "recipecards/recipe_update"
RECIPE_DELETE_TYPE = "recipecards/recipe_delete"
RECIPE_SEARCH_TYPE = "recipecards/recipe_search"


async def _update_coordinator(hass: HomeAssistant) -> None:
    """Update the data coordinator to refresh sensors."""
    for entry_id, entry_data in hass.data[DOMAIN].items():
        if isinstance(entry_data, dict) and "coordinator" in entry_data:
            await entry_data["coordinator"].async_request_refresh()

def _all_storages(hass: HomeAssistant):
    """Yield all RecipeStorage instances for this domain."""
    if DOMAIN not in hass.data:
        return []
    storages = []
    for entry_id, entry_data in hass.data[DOMAIN].items():
        if isinstance(entry_data, dict) and "storage" in entry_data:
            storages.append((entry_id, entry_data["storage"]))
    return storages


@websocket_api.websocket_command({vol.Required("type"): RECIPE_LIST_TYPE})
async def async_list_recipes(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """List all recipes."""
    if DOMAIN not in hass.data or not hass.data[DOMAIN]:
        connection.send_result(msg["id"], [])
        return
    
    storages = _all_storages(hass)
    if not storages:
        connection.send_result(msg["id"], [])
        return
    combined = []
    for entry_id, storage in storages:
        entry_title = None
        try:
            ce = hass.config_entries.async_get_entry(entry_id)
            entry_title = getattr(ce, "title", None)
        except Exception:  # noqa: BLE001
            entry_title = None
        recipes = await storage.async_load_recipes()
        # annotate entry_id so UIs can target a specific collection if needed
        for r in recipes:
            data = r.to_dict()
            data["_entry_id"] = entry_id
            if entry_title:
                data["_entry_title"] = entry_title
            combined.append(data)
    connection.send_result(msg["id"], combined)

@websocket_api.websocket_command({
    vol.Required("type"): RECIPE_GET_TYPE,
    vol.Required("recipe_id"): str,
})
async def async_get_recipe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Get a specific recipe by ID."""
    if DOMAIN not in hass.data or not hass.data[DOMAIN]:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    
    # Search across all storages
    recipe_id = msg["recipe_id"]
    for entry_id, storage in _all_storages(hass):
        recipes = await storage.async_load_recipes()
        for recipe in recipes:
            if recipe.id == recipe_id:
                data = recipe.to_dict()
                data["_entry_id"] = entry_id
                try:
                    ce = hass.config_entries.async_get_entry(entry_id)
                    if ce and getattr(ce, "title", None):
                        data["_entry_title"] = ce.title
                except Exception:  # noqa: BLE001
                    pass
                connection.send_result(msg["id"], data)
                return
    connection.send_error(msg["id"], "not_found", "Recipe not found")

@websocket_api.websocket_command({
    vol.Required("type"): RECIPE_ADD_TYPE,
    vol.Required("recipe"): dict,
    vol.Optional("entry_id"): str,
})
async def async_add_recipe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Add a new recipe."""
    if DOMAIN not in hass.data or not hass.data[DOMAIN]:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    
    # Find target storage, prefer provided entry_id if present
    target_entry_id = msg.get("entry_id")
    storage = None
    for entry_id, s in _all_storages(hass):
        if target_entry_id is None or target_entry_id == entry_id:
            storage = s
            target_entry_id = entry_id
            break
    if not storage:
        connection.send_error(msg["id"], "not_found", "No storage instance found")
        return
    data = msg["recipe"]
    recipe = Recipe.from_dict(data)
    await storage.async_add_recipe(recipe)
    
    # Update coordinator
    await _update_coordinator(hass)
    
    data = recipe.to_dict()
    data["_entry_id"] = target_entry_id
    connection.send_result(msg["id"], data)

@websocket_api.websocket_command({
    vol.Required("type"): RECIPE_UPDATE_TYPE,
    vol.Required("recipe_id"): str,
    vol.Required("recipe"): dict,
})
async def async_update_recipe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Update an existing recipe."""
    if DOMAIN not in hass.data or not hass.data[DOMAIN]:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    
    # Update across storages; stop at the first match
    recipe_id = msg["recipe_id"]
    data = msg["recipe"]
    updated_recipe = Recipe.from_dict(data)
    for entry_id, storage in _all_storages(hass):
        ok = await storage.async_update_recipe(recipe_id, updated_recipe)
        if ok:
            await _update_coordinator(hass)
            result = updated_recipe.to_dict()
            result["_entry_id"] = entry_id
            connection.send_result(msg["id"], result)
            return
    connection.send_error(msg["id"], "not_found", "Recipe not found")

@websocket_api.websocket_command({
    vol.Required("type"): RECIPE_DELETE_TYPE,
    vol.Required("recipe_id"): str,
})
async def async_delete_recipe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Delete a recipe by ID."""
    if DOMAIN not in hass.data or not hass.data[DOMAIN]:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    
    # Delete across storages; stop at the first match
    recipe_id = msg["recipe_id"]
    for _entry_id, storage in _all_storages(hass):
        recipes = await storage.async_load_recipes()
        if any(r.id == recipe_id for r in recipes):
            await storage.async_delete_recipe(recipe_id)
            await _update_coordinator(hass)
            # Also remove the entity for this recipe
            cleanup_recipe_entities(hass, _entry_id, recipe_id)
            connection.send_result(msg["id"], True)
            return
    connection.send_error(msg["id"], "not_found", "Recipe not found")

@websocket_api.websocket_command({
    vol.Required("type"): RECIPE_SEARCH_TYPE,
    vol.Optional("query", default=""): str,
    vol.Optional("max_time", default=None): vol.All(vol.Coerce(int), vol.Range(min=0, max=1440)),
})
async def async_search_recipes(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Search recipes by query and optional max total time."""
    if DOMAIN not in hass.data or not hass.data[DOMAIN]:
        connection.send_result(msg["id"], [])
        return
    
    query = msg.get("query", "").lower()
    max_time = msg.get("max_time")
    
    storages = _all_storages(hass)
    if not storages:
        connection.send_result(msg["id"], [])
        return
    
    combined = []
    for entry_id, storage in storages:
        entry_title = None
        try:
            ce = hass.config_entries.async_get_entry(entry_id)
            entry_title = getattr(ce, "title", None)
        except Exception:  # noqa: BLE001
            entry_title = None
        recipes = await storage.async_load_recipes()
        for r in recipes:
            data = r.to_dict()
            data["_entry_id"] = entry_id
            if entry_title:
                data["_entry_title"] = entry_title
            
            # Filter by query
            if query and query not in data["title"].lower() and query not in (data.get("description", "") or "").lower():
                continue
            
            # Filter by max_time
            if max_time is not None and data.get("total_time", 0) > max_time:
                continue
            
            combined.append(data)
    connection.send_result(msg["id"], combined)

def register_api(hass: HomeAssistant) -> None:
    """Register the WebSocket API commands."""
    _LOGGER.info("Registering Recipe Cards WebSocket API")
    websocket_api.async_register_command(hass, async_list_recipes)
    websocket_api.async_register_command(hass, async_get_recipe)
    websocket_api.async_register_command(hass, async_add_recipe)
    websocket_api.async_register_command(hass, async_update_recipe)
    websocket_api.async_register_command(hass, async_delete_recipe)
    websocket_api.async_register_command(hass, async_search_recipes)
