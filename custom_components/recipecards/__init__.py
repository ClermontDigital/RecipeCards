"""The Recipe Cards integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components import frontend
from pathlib import Path

from .const import DOMAIN
from .storage import RecipeStorage
from .services import async_register_services, async_remove_services

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recipe Cards from a config entry."""
    # Initialize domain data structure
    hass.data.setdefault(DOMAIN, {})
    # Ensure WebSocket API is registered even if async_setup wasn't called
    if not hass.data[DOMAIN].get("api_registered"):
        # Lazy import to avoid import-time side effects during config flow discovery
        from .api import register_api  # noqa: WPS433 (local import by design)
        register_api(hass)
        hass.data[DOMAIN]["api_registered"] = True
    
    # Initialize storage
    storage = RecipeStorage(hass, entry.entry_id)
    
    async def async_update_data():
        """Fetch data from storage."""
        return await storage.async_load_recipes()

    coordinator = DataUpdateCoordinator(
        hass,
        logger=__import__("logging").getLogger(__name__),
        name=f"recipecards_sensor_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=None,
    )
    
    # Set up entry data structure
    hass.data[DOMAIN][entry.entry_id] = {
        "storage": storage,
        "coordinator": coordinator,
    }

    # Let storage trigger coordinator refreshes on any write
    storage.set_update_callback(coordinator.async_request_refresh)
    
    await coordinator.async_config_entry_first_refresh()
    
    # Register services
    await async_register_services(hass)
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Serve and auto-load the bundled Lovelace card (no build step required)
    try:
        card_path = Path(__file__).parent / "www" / "recipecards-card.js"
        if card_path.exists():
            url_path = "/recipecards/recipecards-card.js"
            hass.http.register_static_path(url_path, str(card_path))
            frontend.add_extra_js_url(hass, url_path)
    except Exception:  # noqa: BLE001 - best-effort frontend helper
        # Card auto-loading is best-effort; backend still functions without it
        pass
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Remove services if this is the last entry
        if not hass.data[DOMAIN]:
            await async_remove_services(hass)
    return unload_ok


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Recipe Cards domain.

    Registers the WebSocket API and prepares the domain storage.
    """
    hass.data.setdefault(DOMAIN, {})
    if not hass.data[DOMAIN].get("api_registered"):
        # Lazy import to avoid import-time side effects during config flow discovery
        from .api import register_api  # noqa: WPS433 (local import by design)
        # Register WebSocket API commands (idempotent via our flag)
        register_api(hass)
        hass.data[DOMAIN]["api_registered"] = True
    return True
