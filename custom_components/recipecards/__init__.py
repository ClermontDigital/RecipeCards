"""The Recipe Cards integration."""
import logging
from homeassistant.config_entries import ConfigEntry  # type: ignore[import-untyped]
from homeassistant.core import HomeAssistant  # type: ignore[import-untyped]
from .const import DOMAIN
from .storage import RecipeStorage
from .api import register_api

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = []

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recipe Cards from a config entry."""
    _LOGGER.info("Setting up Recipe Cards integration")
    try:
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
            _LOGGER.info("First time setup, registering API.")
            register_api(hass)
        
        storage = RecipeStorage(hass, entry.entry_id)
        hass.data[DOMAIN][entry.entry_id] = storage
        _LOGGER.info("Successfully set up Recipe Cards for entry %s", entry.entry_id)
        
        return True
    except Exception as e:
        _LOGGER.exception("Failed to set up Recipe Cards integration")
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
