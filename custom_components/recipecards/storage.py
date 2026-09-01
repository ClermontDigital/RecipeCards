import asyncio
import logging
from typing import Awaitable, Callable, Optional
from homeassistant.helpers.storage import Store
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .models import Recipe

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1

class RecipeStorage:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        # New preferred filename
        self._store = Store(hass, STORAGE_VERSION, f"recipecards_{entry_id}.json")
        # Legacy filename for migration support
        self._legacy_store = Store(hass, STORAGE_VERSION, f".{DOMAIN}.{entry_id}.json")
        self._recipes: list[Recipe] = []
        self._update_cb: Optional[Callable[[], Awaitable[None]]] = None
        # Serialises read-change-write. Without it two overlapping adds both read
        # the same starting list and the second write drops the first one's recipe.
        self._lock = asyncio.Lock()

    def set_update_callback(self, cb: Callable[[], Awaitable[None]]) -> None:
        """Set a callback to be awaited whenever recipes change."""
        self._update_cb = cb

    async def _read_from_disk(self) -> list[Recipe]:
        """Read the store. Does not touch self._recipes, so a concurrent refresh
        can never clobber a mutation that is midway through."""
        data = await self._store.async_load()
        # Migrate from legacy storage if needed
        if data is None:
            legacy = await self._legacy_store.async_load()
            data = legacy if legacy is not None else []
            # Persist to new store if we loaded legacy data
            if legacy:
                await self._store.async_save(legacy)
        if not isinstance(data, list):
            _LOGGER.warning("Recipe Cards: store for this section was not a list, ignoring it")
            return []
        return [Recipe.from_dict(d) for d in data if isinstance(d, dict)]

    async def async_load_recipes(self) -> list[Recipe]:
        """Return the recipes on disk.

        Serialised against writes. Every mutation below does read, change, write
        while holding the same lock, so two overlapping writes cannot each read the
        same starting list and have the second silently drop the first one's recipe.
        """
        async with self._lock:
            self._recipes = await self._read_from_disk()
            return list(self._recipes)

    async def _save_locked(self) -> None:
        """Write the current list. Callers must already hold self._lock."""
        await self._store.async_save([r.to_dict() for r in (self._recipes or [])])

    async def async_save_recipes(self) -> None:
        async with self._lock:
            await self._save_locked()

    @staticmethod
    def _apply_parsed_times(recipe: Recipe) -> None:
        """Fill in any time fields the caller did not supply, from the recipe text."""
        text = "\n".join(recipe.instructions or []) + "\n" + (recipe.notes or "")
        parsed = Recipe.parse_times(text)
        for key in ("prep_time", "cook_time", "total_time"):
            if getattr(recipe, key, None) is None:
                setattr(recipe, key, parsed[key])

    async def async_add_recipe(self, recipe: Recipe) -> None:
        # Parse times BEFORE persisting, so a parse failure can never leave a
        # half-written record on disk with no coordinator refresh behind it.
        self._apply_parsed_times(recipe)

        async with self._lock:
            self._recipes = await self._read_from_disk()
            self._recipes.append(recipe)
            await self._save_locked()

        # Outside the lock: this refreshes the coordinator, which reads back in.
        await self._notify_update()

    async def async_update_recipe(self, recipe_id: str, updated_recipe: Recipe) -> bool:
        self._apply_parsed_times(updated_recipe)
        found = False
        async with self._lock:
            self._recipes = await self._read_from_disk()
            for idx, recipe in enumerate(self._recipes):
                if recipe.id == recipe_id:
                    self._recipes[idx] = updated_recipe
                    await self._save_locked()
                    found = True
                    break
        if found:
            await self._notify_update()
        return found

    async def async_delete_recipe(self, recipe_id: str) -> None:
        async with self._lock:
            current = await self._read_from_disk()
            self._recipes = [r for r in current if r.id != recipe_id]
            await self._save_locked()
        await self._notify_update()

    async def async_remove(self) -> None:
        """Delete this entry's store files. Used when the config entry is removed."""
        for store in (self._store, self._legacy_store):
            try:
                await store.async_remove()
            except Exception:  # noqa: BLE001
                pass
        self._recipes = []

    async def _notify_update(self) -> None:
        """Notify Home Assistant of recipe updates."""
        if self._update_cb is not None:
            await self._update_cb()
