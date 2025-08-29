"""The Recipe Cards integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components import frontend
from pathlib import Path
import json
import shutil

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

            # Serve static file at a fixed URL
            try:
                hass.http.register_static_path(url_base, str(card_path))
            except Exception:  # noqa: BLE001 - path might already be registered
                pass

            # Also expose the containing directory so '/recipecards/recipecards-card.js' resolves
            try:
                hass.http.register_static_path("/recipecards", str(card_path.parent))
            except Exception:  # noqa: BLE001 - path might already be registered
                pass

            # Do not proactively load the '/recipecards' URL to avoid 404s in some setups.
            # We rely on the '/local' fallback resource for loading in the UI.

            # Fallback: also copy to /config/www and register under /local
            try:
                cfg_www = Path(hass.config.path("www"))
                if not cfg_www.exists():
                    cfg_www.mkdir(parents=True, exist_ok=True)
                local_path = cfg_www / "recipecards-card.js"
                # Copy if missing or different size
                try:
                    need_copy = (not local_path.exists()) or (local_path.stat().st_size != card_path.stat().st_size)
                except Exception:  # noqa: BLE001
                    need_copy = True
                if need_copy:
                    try:
                        shutil.copyfile(str(card_path), str(local_path))
                    except Exception:  # noqa: BLE001
                        pass
                local_url_base = "/local/recipecards-card.js"
                local_versioned = f"{local_url_base}?v={version}" if version else local_url_base
                try:
                    frontend.add_extra_js_url(hass, local_versioned)
                except Exception:  # noqa: BLE001
                    pass
            except Exception:  # noqa: BLE001
                pass

            # Register only the '/local' resource in the Lovelace registry to avoid 404s.
            try:
                from homeassistant.components.lovelace.resources import async_get_registry

                async def _ensure_lovelace_resource_local_only() -> None:
                    registry = await async_get_registry(hass)
                    local_url_base = "/local/recipecards-card.js"
                    local_versioned = f"{local_url_base}?v={version}" if version else local_url_base
                    # Remove any stale '/recipecards' resources if present to prevent 404s
                    try:
                        for item in list(registry.async_items()):
                            url = getattr(item, "url", None) if not isinstance(item, dict) else item.get("url")
                            if url and url.split("?")[0] == url_base:
                                try:
                                    await registry.async_delete_item(getattr(item, "id", item["id"]))  # type: ignore[index]
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    # Ensure the '/local' resource exists (or create it)
                    for item in registry.async_items():
                        url = getattr(item, "url", None) if not isinstance(item, dict) else item.get("url")
                        if url and url.split("?")[0] == local_url_base:
                            try:
                                await registry.async_update_item(getattr(item, "id", item["id"]), {  # type: ignore[index]
                                    "url": local_versioned,
                                })
                            except Exception:
                                pass
                            break
                    else:
                        await registry.async_create_item({"res_type": "js", "url": local_versioned})

                hass.async_create_task(_ensure_lovelace_resource_local_only())
            except Exception:  # noqa: BLE001
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
