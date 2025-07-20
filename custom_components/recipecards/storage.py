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
        self._recipes = [Recipe.from_dict(d) for d in (data or [])]
        return self._recipes

    async def async_save_recipes(self) -> None:
        await self._store.async_save([r.to_dict() for r in (self._recipes or [])])

    async def async_add_recipe(self, recipe: Recipe) -> None:
        self._recipes.append(recipe)
        await self.async_save_recipes()

    async def async_update_recipe(self, recipe_id: str, updated_recipe: Recipe) -> bool:
        for idx, recipe in enumerate(self._recipes):
            if recipe.id == recipe_id:
                self._recipes[idx] = updated_recipe
                await self.async_save_recipes()
                return True
        return False

    async def async_delete_recipe(self, recipe_id: str) -> None:
        self._recipes = [r for r in self._recipes if r.id != recipe_id]
        await self.async_save_recipes()
