"""The Recipe Cards integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .storage import RecipeStorage
from .api import register_api

# Import config flow to register it
from . import config_flow

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Recipe Cards component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recipe Cards from a config entry."""
    _LOGGER.info("Recipe Cards setup starting: %s", entry.title)
    
    try:
        # Initialize domain data structure
        hass.data.setdefault(DOMAIN, {})
        
        # Initialize storage
        storage = RecipeStorage(hass, entry.entry_id)
        
        async def async_update_data():
            """Fetch data from storage."""
            return await storage.async_load_recipes()

        coordinator = DataUpdateCoordinator(
            hass,
            logger=__name__,
            name=f"recipecards_sensor_{entry.entry_id}",
            update_method=async_update_data,
            update_interval=None,
        )
        
        # Set up entry data structure
        hass.data[DOMAIN][entry.entry_id] = {
            "config": entry.data,
            "storage": storage,
            "coordinator": coordinator,
        }
        
        # Register the API
        register_api(hass)
        
        await coordinator.async_config_entry_first_refresh()
        
        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        _LOGGER.info("Recipe Cards setup complete: %s", entry.title)
        return True
        
    except Exception as err:
        _LOGGER.error("Recipe Cards setup failed: %s", err)
        # Clean up on failure
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN].pop(entry.entry_id)
        raise ConfigEntryNotReady(f"Failed to set up Recipe Cards: {err}") from err


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok