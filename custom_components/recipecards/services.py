"""Service calls for Recipe Cards integration."""
import logging
import voluptuous as vol
import uuid
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
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

def validate_color(value) -> str:
    """Validate/normalize color to hex string.

    Accepts '#RRGGBB' string, an RGB list [r,g,b], or a dict {r,g,b}.
    Falls back to default gold if invalid.
    """
    import re

    # If list/tuple of 3 ints
    if isinstance(value, (list, tuple)) and len(value) == 3:
        try:
            r, g, b = (int(value[0]), int(value[1]), int(value[2]))
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:  # noqa: BLE001
            return "#FFD700"

    # If dict with r,g,b
    if isinstance(value, dict) and all(k in value for k in ("r", "g", "b")):
        try:
            r, g, b = int(value["r"]), int(value["g"]), int(value["b"])
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:  # noqa: BLE001
            return "#FFD700"

    # If string '#RRGGBB'
    if isinstance(value, str) and re.match(r"^#[0-9A-Fa-f]{6}$", value):
        return value

    return "#FFD700"  # Default color

def validate_text_length(max_length: int):
    """Validate text length."""
    def validator(value):
        if len(str(value)) > max_length:
            raise vol.Invalid(f"Text too long (max {max_length} characters)")
        return str(value)
    return validator

ADD_RECIPE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,  # Made optional for auto-detection
    vol.Required(ATTR_TITLE): vol.All(cv.string, vol.Length(min=1, max=100)),
    vol.Optional(ATTR_DESCRIPTION, default=""): vol.All(cv.string, vol.Length(max=500)),
    vol.Optional(ATTR_INGREDIENTS, default=[]): vol.All(cv.ensure_list, [vol.All(cv.string, vol.Length(max=200))]),
    vol.Optional(ATTR_NOTES, default=""): vol.All(cv.string, vol.Length(max=1000)),
    vol.Optional(ATTR_INSTRUCTIONS, default=[]): vol.All(cv.ensure_list, [vol.All(cv.string, vol.Length(max=500))]),
    vol.Optional(ATTR_COLOR, default="#FFD700"): validate_color,
})

UPDATE_RECIPE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,  # Made optional for auto-detection
    vol.Required(ATTR_RECIPE_ID): cv.string,
    vol.Optional(ATTR_TITLE): vol.All(cv.string, vol.Length(min=1, max=100)),
    vol.Optional(ATTR_DESCRIPTION): vol.All(cv.string, vol.Length(max=500)),
    vol.Optional(ATTR_INGREDIENTS): vol.All(cv.ensure_list, [vol.All(cv.string, vol.Length(max=200))]),
    vol.Optional(ATTR_NOTES): vol.All(cv.string, vol.Length(max=1000)),
    vol.Optional(ATTR_INSTRUCTIONS): vol.All(cv.ensure_list, [vol.All(cv.string, vol.Length(max=500))]),
    vol.Optional(ATTR_COLOR): validate_color,
})

DELETE_RECIPE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,  # Made optional for auto-detection
    vol.Required(ATTR_RECIPE_ID): cv.string,
})

def _get_storage_and_coordinator(hass: HomeAssistant, config_entry_id: str = None):
    """Get the storage and coordinator for a specific config entry or auto-detect.

    Returns a tuple (storage, coordinator, entry_id) where entry_id is the
    selected config entry id or None if not found.
    """
    if DOMAIN not in hass.data:
        return None, None, None
    
    # If config_entry_id is provided, use it directly
    if config_entry_id and config_entry_id in hass.data[DOMAIN]:
        entry_data = hass.data[DOMAIN][config_entry_id]
        return entry_data.get("storage"), entry_data.get("coordinator"), config_entry_id
    
    # Auto-detect: find the first available config entry
    for entry_id, entry_data in hass.data[DOMAIN].items():
        if not isinstance(entry_data, dict):
            continue  # Skip non-dict entries like "api_registered"
        storage = entry_data.get("storage")
        coordinator = entry_data.get("coordinator")
        if storage and coordinator:
            return storage, coordinator, entry_id
    
    return None, None, None


def cleanup_recipe_entities(hass: HomeAssistant, entry_id: str, recipe_id: str) -> None:
    """Remove entity registry entries for a deleted recipe.

    We match entities with unique_id pattern f"{entry_id}_{recipe_id}" under the
    recipecards sensor platform and remove them.
    """
    try:
        registry = er.async_get(hass)
        target_unique_id = f"{entry_id}_{recipe_id}"
        to_remove = [
            e.entity_id
            for e in registry.entities.values()
            if e.platform == "sensor"
            and e.config_entry_id == entry_id
            and e.unique_id == target_unique_id
        ]
        for entity_id in to_remove:
            registry.async_remove(entity_id)
    except Exception:  # noqa: BLE001
        # Best-effort cleanup
        pass

async def async_add_recipe(call: ServiceCall) -> None:
    """Handle add recipe service call."""
    config_entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
    storage, coordinator, entry_id = _get_storage_and_coordinator(call.hass, config_entry_id)
    
    if not storage or not coordinator:
        if config_entry_id:
            _LOGGER.error(f"Recipe list with ID '{config_entry_id}' not found.")
        else:
            _LOGGER.error("No RecipeCards integration found. Please add the integration first.")
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
    config_entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
    storage, coordinator, entry_id = _get_storage_and_coordinator(call.hass, config_entry_id)

    if not storage or not coordinator:
        if config_entry_id:
            _LOGGER.error(f"Recipe list with ID '{config_entry_id}' not found.")
        else:
            _LOGGER.error("No RecipeCards integration found. Please add the integration first.")
        return

    recipe_id = call.data[ATTR_RECIPE_ID]
    recipes = await storage.async_load_recipes()
    existing_recipe = next((r for r in recipes if r.id == recipe_id), None)
    
    if not existing_recipe:
        _LOGGER.error("Recipe not found: %s", recipe_id)
        return
    
    update_data = {
        k: v
        for k, v in call.data.items()
        if k not in (ATTR_CONFIG_ENTRY_ID, ATTR_RECIPE_ID)
    }
    
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
    config_entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
    storage, coordinator, entry_id = _get_storage_and_coordinator(call.hass, config_entry_id)

    if not storage or not coordinator:
        if config_entry_id:
            _LOGGER.error(f"Recipe list with ID '{config_entry_id}' not found.")
        else:
            _LOGGER.error("No RecipeCards integration found. Please add the integration first.")
        return
    
    recipe_id = call.data[ATTR_RECIPE_ID]
    await storage.async_delete_recipe(recipe_id)
    # Remove the per-recipe entity if present
    if entry_id:
        cleanup_recipe_entities(call.hass, entry_id, recipe_id)
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
