"""The Recipe Cards integration."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.loader import async_get_integration
from homeassistant.util import slugify

from .const import DOMAIN
from .services import async_register_services, async_remove_services
from .storage import RecipeStorage

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CARD_URL = "/recipecards/recipecards-card.js"
CARD_FILENAME = "recipecards-card.js"


def _register_api(hass: HomeAssistant) -> None:
    """Register the WebSocket API exactly once per HA run."""
    hass.data.setdefault(DOMAIN, {})
    if hass.data[DOMAIN].get("api_registered"):
        return
    from .api import register_api  # local import: avoids import-time side effects

    register_api(hass)
    hass.data[DOMAIN]["api_registered"] = True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Recipe Cards domain."""
    _register_api(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recipe Cards from a config entry."""
    _register_api(hass)

    storage = RecipeStorage(hass, entry.entry_id)

    async def async_update_data():
        """Fetch data from storage."""
        return await storage.async_load_recipes()

    coordinator = DataUpdateCoordinator(
        hass,
        logger=_LOGGER,
        name=f"recipecards_sensor_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=None,
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "storage": storage,
        "coordinator": coordinator,
    }

    # Let storage trigger coordinator refreshes on any write. Use async_refresh,
    # not async_request_refresh: the latter is debounced with a 10s cooldown, so a
    # delete straight after an add would leave the sensor stale for ten seconds.
    # Writes here are user-initiated and rare, so there is nothing to coalesce.
    storage.set_update_callback(coordinator.async_refresh)

    await coordinator.async_config_entry_first_refresh()

    await async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await _async_migrate_entity_ids(hass, entry, storage)
    await _async_setup_frontend(hass)

    return True


async def _async_migrate_entity_ids(
    hass: HomeAssistant, entry: ConfigEntry, storage: RecipeStorage
) -> None:
    """Best-effort: move per-recipe entity_ids onto the 'recipe_' prefix."""
    try:
        registry = er.async_get(hass)
        for recipe in await storage.async_load_recipes():
            unique_id = f"{entry.entry_id}_{recipe.id}"
            expected = f"sensor.recipe_{slugify(recipe.title)}"
            current = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
            if current and current != expected and not registry.async_get(expected):
                registry.async_update_entity(current, new_entity_id=expected)
    except Exception:  # noqa: BLE001 - migration must never block setup
        _LOGGER.exception("Recipe Cards: entity_id migration failed")


async def _async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the bundled Lovelace card and load it into the frontend.

    Preferred route is a registered static path. If that fails for any reason we
    fall back to copying the card into <config>/www and loading it from /local.
    Exactly one URL is ever loaded, so the custom element is defined only once.
    """
    # Claim the registration synchronously, before the first await. Entries are set
    # up concurrently, and every await below is a point where another entry could
    # otherwise pass this guard too - which registered the card twice, from two
    # different URLs, because the loser of the static-path race fell back to /local.
    if hass.data[DOMAIN].get("frontend_registered"):
        return
    hass.data[DOMAIN]["frontend_registered"] = True

    card_path = Path(__file__).parent / "www" / CARD_FILENAME
    if not await hass.async_add_executor_job(card_path.is_file):
        _LOGGER.error("Recipe Cards: bundled card missing at %s", card_path)
        hass.data[DOMAIN]["frontend_registered"] = False
        return

    try:
        integration = await async_get_integration(hass, DOMAIN)
        version = integration.version
    except Exception:  # noqa: BLE001
        version = None

    def _versioned(url: str) -> str:
        return f"{url}?v={version}" if version else url

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(card_path), False)]
        )
        url = CARD_URL
    except Exception:  # noqa: BLE001 - fall back to /local below
        _LOGGER.warning(
            "Recipe Cards: static path registration failed, falling back to /local",
            exc_info=True,
        )
        url = await hass.async_add_executor_job(_copy_card_to_www, hass, card_path)
        if url is None:
            hass.data[DOMAIN]["frontend_registered"] = False
            return

    # Prefer a real Lovelace resource. That is how HACS-installed cards load, it is
    # what the dashboard editor understands, and it survives frontend restarts.
    # add_extra_js_url is only a fallback: it injects a bare import() into the page,
    # which is easy to miss and gives no diagnostics when it does not fire.
    if await _async_register_lovelace_resource(hass, _versioned(url)):
        _LOGGER.debug("Recipe Cards: registered Lovelace resource %s", url)
    else:
        try:
            frontend.add_extra_js_url(hass, _versioned(url))
        except Exception:  # noqa: BLE001 - the backend works without the card
            _LOGGER.warning("Recipe Cards: could not auto-load the card", exc_info=True)
            hass.data[DOMAIN]["frontend_registered"] = False
            return

    _LOGGER.debug("Recipe Cards: card served from %s", url)


async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> bool:
    """Add (or refresh) the card in the Lovelace resource registry.

    Returns True when the resource is present afterwards. Storage-mode dashboards
    only load custom cards that are in this registry, which is why relying on
    frontend.add_extra_js_url alone left the card undefined and the dashboard
    showing "Configuration error".
    """
    try:
        from homeassistant.components.lovelace import LOVELACE_DATA

        lovelace_data = hass.data.get(LOVELACE_DATA)
        if lovelace_data is None:
            _LOGGER.debug("Recipe Cards: lovelace not set up yet")
            return False

        resources = lovelace_data.resources
        if resources is None or not hasattr(resources, "async_create_item"):
            # YAML-mode resources are read-only; the user adds the URL themselves.
            _LOGGER.debug("Recipe Cards: lovelace is in YAML mode, add the resource manually")
            return False

        if hasattr(resources, "async_load") and not resources.loaded:
            await resources.async_load()

        base = url.split("?")[0]
        for item in resources.async_items():
            existing = item.get("url", "") if isinstance(item, dict) else getattr(item, "url", "")
            if existing.split("?")[0] == base:
                if existing != url:  # version bump, refresh the cache buster
                    item_id = item["id"] if isinstance(item, dict) else getattr(item, "id")
                    await resources.async_update_item(item_id, {"url": url})
                return True

        await resources.async_create_item({"res_type": "module", "url": url})
        return True
    except Exception:  # noqa: BLE001 - never let this stop setup
        _LOGGER.warning("Recipe Cards: could not register the Lovelace resource", exc_info=True)
        return False


def _copy_card_to_www(hass: HomeAssistant, card_path: Path) -> str | None:
    """Copy the card into <config>/www. Runs in the executor - blocking I/O."""
    try:
        www_dir = Path(hass.config.path("www"))
        www_dir.mkdir(parents=True, exist_ok=True)
        target = www_dir / CARD_FILENAME
        if not target.exists() or target.stat().st_size != card_path.stat().st_size:
            shutil.copyfile(card_path, target)
        return f"/local/{CARD_FILENAME}"
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Recipe Cards: could not copy card into <config>/www")
        return None


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # Remove services once the last *entry* is gone. Bookkeeping keys such as
        # "api_registered" are not entries, so check for entry dicts specifically.
        if not any(isinstance(v, dict) for v in hass.data[DOMAIN].values()):
            await async_remove_services(hass)
    return unload_ok


# NOTE: deliberately no async_remove_entry.
#
# Deleting a section's store on entry removal leaves no way back if the callback
# ever fires when it should not, and recipes are typed in by hand. Two unexplained
# losses on this instance were enough to decide that an orphaned few-KB JSON file
# in .storage is a far cheaper failure than silently destroying someone's recipes.
# If you remove a section and want its file gone, delete
# .storage/recipecards_<entry_id>.json by hand.
