from homeassistant.components import websocket_api
from .const import DOMAIN
from .models import Recipe

RECIPE_LIST_TYPE = "recipecards/recipe_list"
RECIPE_GET_TYPE = "recipecards/recipe_get"
RECIPE_ADD_TYPE = "recipecards/recipe_add"
RECIPE_UPDATE_TYPE = "recipecards/recipe_update"
RECIPE_DELETE_TYPE = "recipecards/recipe_delete"

async def async_list_recipes(hass, connection, msg):
    # Get the first (and only) entry
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        connection.send_result(msg["id"], [])
        return
    
    storage = list(entries.values())[0]  # Get the first storage instance
    recipes = await storage.async_load_recipes()
    connection.send_result(msg["id"], [r.to_dict() for r in recipes])

async def async_get_recipe(hass, connection, msg):
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    
    storage = list(entries.values())[0]
    recipe_id = msg["recipe_id"]
    recipes = await storage.async_load_recipes()
    for recipe in recipes:
        if recipe.id == recipe_id:
            connection.send_result(msg["id"], recipe.to_dict())
            return
    connection.send_error(msg["id"], "not_found", "Recipe not found")

async def async_add_recipe(hass, connection, msg):
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    
    storage = list(entries.values())[0]
    data = msg["recipe"]
    recipe = Recipe.from_dict(data)
    await storage.async_add_recipe(recipe)
    connection.send_result(msg["id"], recipe.to_dict())

async def async_update_recipe(hass, connection, msg):
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    
    storage = list(entries.values())[0]
    recipe_id = msg["recipe_id"]
    data = msg["recipe"]
    updated_recipe = Recipe.from_dict(data)
    ok = await storage.async_update_recipe(recipe_id, updated_recipe)
    if ok:
        connection.send_result(msg["id"], updated_recipe.to_dict())
    else:
        connection.send_error(msg["id"], "not_found", "Recipe not found")

async def async_delete_recipe(hass, connection, msg):
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        connection.send_error(msg["id"], "not_found", "Integration not configured")
        return
    
    storage = list(entries.values())[0]
    recipe_id = msg["recipe_id"]
    await storage.async_delete_recipe(recipe_id)
    connection.send_result(msg["id"], True)

def register_api(hass):
    websocket_api.async_register_command(
        hass,
        websocket_api.async_response(RECIPE_LIST_TYPE)(async_list_recipes),
        schema=websocket_api.BASE_COMMAND_MESSAGE_SCHEMA,
    )
    websocket_api.async_register_command(
        hass,
        websocket_api.async_response(RECIPE_GET_TYPE)(async_get_recipe),
        schema=websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({"recipe_id": str}),
    )
    websocket_api.async_register_command(
        hass,
        websocket_api.async_response(RECIPE_ADD_TYPE)(async_add_recipe),
        schema=websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({"recipe": dict}),
    )
    websocket_api.async_register_command(
        hass,
        websocket_api.async_response(RECIPE_UPDATE_TYPE)(async_update_recipe),
        schema=websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({"recipe_id": str, "recipe": dict}),
    )
    websocket_api.async_register_command(
        hass,
        websocket_api.async_response(RECIPE_DELETE_TYPE)(async_delete_recipe),
        schema=websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({"recipe_id": str}),
    ) 