"""The Recipe Cards integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components import frontend
from pathlib import Path
import json

from .const import DOMAIN
from .storage import RecipeStorage
from .services import async_register_services, async_remove_services
from .models import Recipe
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

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

    # No default recipe creation; entries represent empty sections
    
    # Register services
    await async_register_services(hass)
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Best-effort: migrate existing per-recipe entity_ids to prefix 'recipe_'
    async def _migrate_entity_ids() -> None:
        try:
            registry = er.async_get(hass)
            recipes = await storage.async_load_recipes()
            for r in recipes:
                unique_id = f"{entry.entry_id}_{r.id}"
                expected = f"sensor.recipe_{slugify.slugify(r.title)}"
                current = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
                if current and current != expected and not registry.async_get(expected):
                    registry.async_update_entity(current, new_entity_id=expected)
        except Exception:
            pass

    hass.async_create_task(_migrate_entity_ids())

    # Serve and auto-load the bundled Lovelace card (no build step required)
    try:
        pkg_dir = Path(__file__).parent
        card_path = pkg_dir / "www" / "recipecards-card.js"
        if card_path.exists():
            url_base = "/recipecards/recipecards-card.js"

            # Read the integration version for cache-busting
            version = None
            try:
                manifest_path = pkg_dir / "manifest.json"
                version = json.loads(manifest_path.read_text(encoding="utf-8")).get("version")
            except Exception:  # noqa: BLE001
                version = None
            versioned_url = f"{url_base}?v={version}" if version else url_base

            # Serve static file
            try:
                hass.http.register_static_path(url_base, str(card_path))
            except Exception:  # noqa: BLE001 - path might already be registered
                pass

            # Load for all frontends (best-effort) and also register as Lovelace resource
            try:
                frontend.add_extra_js_url(hass, versioned_url)
            except Exception:  # noqa: BLE001
                pass

            # Also register as a Lovelace resource so the card shows up in the editor
            # and survives cached page loads. This mirrors what HACS does for plugins.
            try:
                from homeassistant.components.lovelace.resources import async_get_registry

                async def _ensure_lovelace_resource() -> None:
                    registry = await async_get_registry(hass)
                    # registry.async_items() returns ResourceEntry objects
                    existing = None
                    for item in registry.async_items():
                        url = getattr(item, "url", None) if not isinstance(item, dict) else item.get("url")
                        if not url:
                            continue
                        # Match either bare or versioned url for upgrades
                        if url.split("?")[0] == url_base:
                            existing = item
                            break
                    if existing:
                        # Try to update URL to include the current version (cache-bust)
                        try:
                            await registry.async_update_item(getattr(existing, "id", existing["id"]), {  # type: ignore[index]
                                "url": versioned_url,
                            })
                        except Exception:  # noqa: BLE001 - API differences across cores
                            # If update not available, create alongside; frontend will de-dupe
                            await registry.async_create_item({"res_type": "js", "url": versioned_url})
                    else:
                        await registry.async_create_item({
                            "res_type": "js",
                            "url": versioned_url,
                        })

                # Fire and forget; we don't want setup to fail on older cores
                hass.async_create_task(_ensure_lovelace_resource())
            except Exception:  # noqa: BLE001 - best-effort; older cores may lack API
                pass
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
