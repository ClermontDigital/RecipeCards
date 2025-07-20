"""The Recipe Cards integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .storage import RecipeStorage
from .services import async_register_services, async_remove_services
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import logging

_LOGGER = logging.getLogger(__name__)

# Import config flow to register it
from . import config_flow

PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Recipe Cards component."""
    hass.data.setdefault(DOMAIN, {})
    await async_register_services(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recipe Cards from a config entry."""
    storage = RecipeStorage(hass, entry.entry_id)
    
    async def async_update_data():
        """Fetch data from storage."""
        return await storage.async_load_recipes()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"recipecards_sensor_{entry.data.get('name', entry.entry_id)}",
        update_method=async_update_data,
        update_interval=None,
    )
    
    hass.data[DOMAIN][entry.entry_id] = {
        "storage": storage,
        "coordinator": coordinator,
    }
    
    await coordinator.async_config_entry_first_refresh()
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # If this is the last entry, remove the service definitions
        if not hass.data[DOMAIN]:
            await async_remove_services(hass)

    return unload_ok
