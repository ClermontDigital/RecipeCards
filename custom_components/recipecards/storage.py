from homeassistant.helpers.storage import Store
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .models import Recipe

STORAGE_VERSION = 1

class RecipeStorage:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store = Store(hass, STORAGE_VERSION, f".{DOMAIN}.{entry_id}.json")
        self._recipes: list[Recipe] = []

    async def async_load_recipes(self) -> list[Recipe]:
        data = await self._store.async_load()
        if data is None:
            data = []
        self._recipes = [Recipe.from_dict(d) for d in data]
        return self._recipes

    async def async_save_recipes(self) -> None:
        await self._store.async_save([r.to_dict() for r in (self._recipes or [])])

    async def async_add_recipe(self, recipe: Recipe) -> None:
        await self.async_load_recipes()  # Ensure we have latest data
        self._recipes.append(recipe)
        await self.async_save_recipes()
        await self._notify_update()

    async def async_update_recipe(self, recipe_id: str, updated_recipe: Recipe) -> bool:
        await self.async_load_recipes()  # Ensure we have latest data
        for idx, recipe in enumerate(self._recipes):
            if recipe.id == recipe_id:
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

    async def _notify_update(self) -> None:
        """Notify Home Assistant of recipe updates."""
        # This will be used by the coordinator to update sensors
        pass
