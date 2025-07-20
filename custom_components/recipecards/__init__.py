"""The Recipe Cards integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .storage import RecipeStorage
from .api import register_api
from .services import register_services

# Import config flow to register it
from . import config_flow

PLATFORMS = []

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Recipe Cards component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recipe Cards from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = RecipeStorage(hass, entry.entry_id)
    
    # Register the API and services
    register_api(hass)
    await register_services(hass)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
