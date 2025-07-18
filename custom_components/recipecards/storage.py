from homeassistant.helpers.storage import Store
from .const import DOMAIN
from .models import Recipe

STORAGE_VERSION = 1
STORAGE_KEY = f".{DOMAIN}.json"

class RecipeStorage:
    def __init__(self, hass):
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._recipes = None  # type: list[Recipe] | None

    async def async_load_recipes(self):
        data = await self._store.async_load()
        self._recipes = [Recipe.from_dict(d) for d in (data or [])]
        return self._recipes

    async def async_save_recipes(self):
        await self._store.async_save([r.to_dict() for r in (self._recipes or [])])

    async def async_add_recipe(self, recipe: Recipe):
        if self._recipes is None:
            await self.async_load_recipes()
        self._recipes.append(recipe)
        await self.async_save_recipes()

    async def async_update_recipe(self, recipe_id, updated_recipe: Recipe):
        if self._recipes is None:
            await self.async_load_recipes()
        for idx, recipe in enumerate(self._recipes):
            if recipe.id == recipe_id:
                self._recipes[idx] = updated_recipe
                await self.async_save_recipes()
                return True
        return False

    async def async_delete_recipe(self, recipe_id):
        if self._recipes is None:
            await self.async_load_recipes()
        self._recipes = [r for r in self._recipes if r.id != recipe_id]
        await self.async_save_recipes() 