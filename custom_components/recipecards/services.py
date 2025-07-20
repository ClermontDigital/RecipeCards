"""Service calls for Recipe Cards integration."""
import logging
import voluptuous as vol
import uuid
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN
from .models import Recipe

_LOGGER = logging.getLogger(__name__)

SERVICE_ADD_RECIPE = "add_recipe"
SERVICE_UPDATE_RECIPE = "update_recipe"
SERVICE_DELETE_RECIPE = "delete_recipe"

ATTR_TITLE = "title"
ATTR_DESCRIPTION = "description"
ATTR_INGREDIENTS = "ingredients"
ATTR_NOTES = "notes"
ATTR_INSTRUCTIONS = "instructions"
ATTR_COLOR = "color"
ATTR_RECIPE_ID = "recipe_id"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"

ADD_RECIPE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
    vol.Required(ATTR_TITLE): cv.string,
    vol.Optional(ATTR_DESCRIPTION, default=""): cv.string,
    vol.Optional(ATTR_INGREDIENTS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_NOTES, default=""): cv.string,
    vol.Optional(ATTR_INSTRUCTIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_COLOR, default="#FFD700"): cv.string,
})

UPDATE_RECIPE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
    vol.Required(ATTR_RECIPE_ID): cv.string,
    vol.Optional(ATTR_TITLE): cv.string,
    vol.Optional(ATTR_DESCRIPTION): cv.string,
    vol.Optional(ATTR_INGREDIENTS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_NOTES): cv.string,
    vol.Optional(ATTR_INSTRUCTIONS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_COLOR): cv.string,
})

DELETE_RECIPE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
    vol.Required(ATTR_RECIPE_ID): cv.string,
})

def _get_storage_and_coordinator(hass: HomeAssistant, config_entry_id: str):
    """Get the storage and coordinator for a specific config entry."""
    if DOMAIN not in hass.data or config_entry_id not in hass.data[DOMAIN]:
        return None, None
    
    entry_data = hass.data[DOMAIN][config_entry_id]
    return entry_data.get("storage"), entry_data.get("coordinator")

async def async_add_recipe(call: ServiceCall) -> None:
    """Handle add recipe service call."""
    config_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
    storage, coordinator = _get_storage_and_coordinator(call.hass, config_entry_id)
    
    if not storage or not coordinator:
        _LOGGER.error(f"Recipe list with ID '{config_entry_id}' not found.")
        return
    
    recipe_id = str(uuid.uuid4())
    instructions = call.data.get(ATTR_INSTRUCTIONS, [])
    if isinstance(instructions, str):
        instructions = [instructions]
    
    recipe = Recipe(
        id=recipe_id,
        title=call.data[ATTR_TITLE],
        description=call.data.get(ATTR_DESCRIPTION, ""),
        ingredients=call.data.get(ATTR_INGREDIENTS, []),
        notes=call.data.get(ATTR_NOTES, ""),
        instructions=instructions,
        color=call.data.get(ATTR_COLOR, "#FFD700")
    )
    
    await storage.async_add_recipe(recipe)
    await coordinator.async_request_refresh()
    _LOGGER.info("Added recipe: %s", recipe.title)

async def async_update_recipe(call: ServiceCall) -> None:
    """Handle update recipe service call."""
    config_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
    storage, coordinator = _get_storage_and_coordinator(call.hass, config_entry_id)

    if not storage or not coordinator:
        _LOGGER.error(f"Recipe list with ID '{config_entry_id}' not found.")
        return

    recipe_id = call.data[ATTR_RECIPE_ID]
    recipes = await storage.async_load_recipes()
    existing_recipe = next((r for r in recipes if r.id == recipe_id), None)
    
    if not existing_recipe:
        _LOGGER.error("Recipe not found: %s", recipe_id)
        return
    
    update_data = {k: v for k, v in call.data.items() if k != ATTR_CONFIG_ENTRY_ID}
    
    instructions = update_data.get(ATTR_INSTRUCTIONS)
    if isinstance(instructions, str):
        update_data[ATTR_INSTRUCTIONS] = [instructions]
    
    updated_recipe_data = {**existing_recipe.to_dict(), **update_data}
    updated_recipe = Recipe.from_dict(updated_recipe_data)
    
    await storage.async_update_recipe(recipe_id, updated_recipe)
    await coordinator.async_request_refresh()
    _LOGGER.info("Updated recipe: %s", recipe_id)

async def async_delete_recipe(call: ServiceCall) -> None:
    """Handle delete recipe service call."""
    config_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
    storage, coordinator = _get_storage_and_coordinator(call.hass, config_entry_id)

    if not storage or not coordinator:
        _LOGGER.error(f"Recipe list with ID '{config_entry_id}' not found.")
        return
    
    recipe_id = call.data[ATTR_RECIPE_ID]
    await storage.async_delete_recipe(recipe_id)
    await coordinator.async_request_refresh()
    _LOGGER.info("Deleted recipe: %s", recipe_id)

async def async_register_services(hass: HomeAssistant) -> None:
    """Register Recipe Cards services."""
    if hass.services.has_service(DOMAIN, SERVICE_ADD_RECIPE):
        return  # Services already registered

    _LOGGER.info("Registering Recipe Cards services")
    
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_RECIPE, async_add_recipe, schema=ADD_RECIPE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_RECIPE, async_update_recipe, schema=UPDATE_RECIPE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_RECIPE, async_delete_recipe, schema=DELETE_RECIPE_SCHEMA
    )

async def async_remove_services(hass: HomeAssistant) -> None:
    """Remove Recipe Cards services."""
    if not hass.services.has_service(DOMAIN, SERVICE_ADD_RECIPE):
        return

    _LOGGER.info("Removing Recipe Cards services")
    hass.services.async_remove(DOMAIN, SERVICE_ADD_RECIPE)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_RECIPE)
    hass.services.async_remove(DOMAIN, SERVICE_DELETE_RECIPE)
