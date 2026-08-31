from typing import Awaitable, Callable, Optional
from homeassistant.helpers.storage import Store
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .models import Recipe

STORAGE_VERSION = 1

class RecipeStorage:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        # New preferred filename
        self._store = Store(hass, STORAGE_VERSION, f"recipecards_{entry_id}.json")
        # Legacy filename for migration support
        self._legacy_store = Store(hass, STORAGE_VERSION, f".{DOMAIN}.{entry_id}.json")
        self._recipes: list[Recipe] = []
        self._update_cb: Optional[Callable[[], Awaitable[None]]] = None

    def set_update_callback(self, cb: Callable[[], Awaitable[None]]) -> None:
        """Set a callback to be awaited whenever recipes change."""
        self._update_cb = cb

    async def async_load_recipes(self) -> list[Recipe]:
        data = await self._store.async_load()
        # Migrate from legacy storage if needed
        if data is None:
            legacy = await self._legacy_store.async_load()
            data = legacy if legacy is not None else []
            # Persist to new store if we loaded legacy data
            if legacy:
                await self._store.async_save(legacy)
        self._recipes = [Recipe.from_dict(d) for d in data]
        return self._recipes

    async def async_save_recipes(self) -> None:
        await self._store.async_save([r.to_dict() for r in (self._recipes or [])])

    @staticmethod
    def _apply_parsed_times(recipe: Recipe) -> None:
        """Fill in any time fields the caller did not supply, from the recipe text."""
        text = "\n".join(recipe.instructions or []) + "\n" + (recipe.notes or "")
        parsed = Recipe.parse_times(text)
        for key in ("prep_time", "cook_time", "total_time"):
            if getattr(recipe, key, None) is None:
                setattr(recipe, key, parsed[key])

    async def async_add_recipe(self, recipe: Recipe) -> None:
        await self.async_load_recipes()  # Ensure we have latest data

        # Parse times BEFORE persisting, so a parse failure can never leave a
        # half-written record on disk with no coordinator refresh behind it.
        self._apply_parsed_times(recipe)

        self._recipes.append(recipe)
        await self.async_save_recipes()
        await self._notify_update()

    async def async_update_recipe(self, recipe_id: str, updated_recipe: Recipe) -> bool:
        await self.async_load_recipes()  # Ensure we have latest data
        for idx, recipe in enumerate(self._recipes):
            if recipe.id == recipe_id:
                self._apply_parsed_times(updated_recipe)
                self._recipes[idx] = updated_recipe
                await self.async_save_recipes()
                await self._notify_update()
                return True
        return False

    async def async_delete_recipe(self, recipe_id: str) -> None:
        await self.async_load_recipes()  # Ensure we have latest data
        self._recipes = [r for r in self._recipes if r.id != recipe_id]
        await self.async_save_recipes()
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
