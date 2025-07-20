"""Service calls for Recipe Cards integration."""
import logging
from typing import Any
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
SERVICE_GET_RECIPE = "get_recipe"
SERVICE_LIST_RECIPES = "list_recipes"

ATTR_TITLE = "title"
ATTR_DESCRIPTION = "description"
ATTR_INGREDIENTS = "ingredients"
ATTR_NOTES = "notes"
ATTR_INSTRUCTIONS = "instructions"
ATTR_COLOR = "color"
ATTR_RECIPE_ID = "recipe_id"

ADD_RECIPE_SCHEMA = vol.Schema({
    vol.Required(ATTR_TITLE): cv.string,
    vol.Optional(ATTR_DESCRIPTION, default=""): cv.string,
    vol.Optional(ATTR_INGREDIENTS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_NOTES, default=""): cv.string,
    vol.Optional(ATTR_INSTRUCTIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_COLOR, default="#FFD700"): cv.string,
})

UPDATE_RECIPE_SCHEMA = vol.Schema({
    vol.Required(ATTR_RECIPE_ID): cv.string,
    vol.Optional(ATTR_TITLE): cv.string,
    vol.Optional(ATTR_DESCRIPTION): cv.string,
    vol.Optional(ATTR_INGREDIENTS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_NOTES): cv.string,
    vol.Optional(ATTR_INSTRUCTIONS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_COLOR): cv.string,
})

DELETE_RECIPE_SCHEMA = vol.Schema({
    vol.Required(ATTR_RECIPE_ID): cv.string,
})

GET_RECIPE_SCHEMA = vol.Schema({
    vol.Required(ATTR_RECIPE_ID): cv.string,
})

LIST_RECIPES_SCHEMA = vol.Schema({})


def _get_storage(hass: HomeAssistant):
    """Get the first available storage instance."""
    if DOMAIN not in hass.data:
        return None
    
    # Get the first available storage instance
    for storage in hass.data[DOMAIN].values():
        return storage
    return None


async def async_add_recipe(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle add recipe service call."""
    storage = _get_storage(hass)
    if not storage:
        _LOGGER.error("Recipe Cards integration not configured")
        return
    
    # Generate unique recipe ID
    recipe_id = str(uuid.uuid4())
    
    # Handle instructions - convert string to list if needed
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
    _LOGGER.info("Added recipe: %s", recipe.title)


async def async_update_recipe(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle update recipe service call."""
    storage = _get_storage(hass)
    if not storage:
        _LOGGER.error("Recipe Cards integration not configured")
        return
    
    recipe_id = call.data[ATTR_RECIPE_ID]
    
    # Load existing recipes to find the one to update
    recipes = await storage.async_load_recipes()
    existing_recipe = None
    for recipe in recipes:
        if recipe.id == recipe_id:
            existing_recipe = recipe
            break
    
    if not existing_recipe:
        _LOGGER.error("Recipe not found: %s", recipe_id)
        return
    
    # Update only provided fields
    update_data = {}
    for attr in [ATTR_TITLE, ATTR_DESCRIPTION, ATTR_INGREDIENTS, ATTR_NOTES, ATTR_INSTRUCTIONS, ATTR_COLOR]:
        if attr in call.data:
            update_data[attr] = call.data[attr]
    
    # Handle instructions - convert string to list if needed
    if ATTR_INSTRUCTIONS in update_data:
        instructions = update_data[ATTR_INSTRUCTIONS]
        if isinstance(instructions, str):
            instructions = [instructions]
        update_data[ATTR_INSTRUCTIONS] = instructions
    
    # Create updated recipe with merged data
    updated_recipe = Recipe(
        id=recipe_id,
        title=update_data.get(ATTR_TITLE, existing_recipe.title),
        description=update_data.get(ATTR_DESCRIPTION, existing_recipe.description),
        ingredients=update_data.get(ATTR_INGREDIENTS, existing_recipe.ingredients),
        notes=update_data.get(ATTR_NOTES, existing_recipe.notes),
        instructions=update_data.get(ATTR_INSTRUCTIONS, existing_recipe.instructions),
        color=update_data.get(ATTR_COLOR, existing_recipe.color)
    )
    
    await storage.async_update_recipe(recipe_id, updated_recipe)
    _LOGGER.info("Updated recipe: %s", recipe_id)


async def async_delete_recipe(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle delete recipe service call."""
    storage = _get_storage(hass)
    if not storage:
        _LOGGER.error("Recipe Cards integration not configured")
        return
    
    recipe_id = call.data[ATTR_RECIPE_ID]
    await storage.async_delete_recipe(recipe_id)
    _LOGGER.info("Deleted recipe: %s", recipe_id)


async def async_get_recipe(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle get recipe service call."""
    storage = _get_storage(hass)
    if not storage:
        _LOGGER.error("Recipe Cards integration not configured")
        return
    
    recipe_id = call.data[ATTR_RECIPE_ID]
    recipes = await storage.async_load_recipes()
    
    for recipe in recipes:
        if recipe.id == recipe_id:
            _LOGGER.info("Found recipe: %s", recipe.title)
            return
    
    _LOGGER.warning("Recipe not found: %s", recipe_id)


async def async_list_recipes(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle list recipes service call."""
    storage = _get_storage(hass)
    if not storage:
        _LOGGER.error("Recipe Cards integration not configured")
        return
    
    recipes = await storage.async_load_recipes()
    _LOGGER.info("Listed %d recipes", len(recipes))


async def register_services(hass: HomeAssistant) -> None:
    """Register Recipe Cards services."""
    _LOGGER.info("Registering Recipe Cards services")
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_RECIPE,
        async_add_recipe,
        schema=ADD_RECIPE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_RECIPE,
        async_update_recipe,
        schema=UPDATE_RECIPE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_RECIPE,
        async_delete_recipe,
        schema=DELETE_RECIPE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_RECIPE,
        async_get_recipe,
        schema=GET_RECIPE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_RECIPES,
        async_list_recipes,
        schema=LIST_RECIPES_SCHEMA,
    )