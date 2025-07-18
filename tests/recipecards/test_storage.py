import pytest
from unittest.mock import MagicMock
from custom_components.recipecards.storage import RecipeStorage
from custom_components.recipecards.models import Recipe

class DummyStore:
    def __init__(self):
        self.data = None
    async def async_load(self):
        return self.data
    async def async_save(self, data):
        self.data = data

@pytest.fixture
def storage():
    hass = MagicMock()
    dummy_store = DummyStore()
    hass.data = {}
    # Patch Store to use DummyStore
    import custom_components.recipecards.storage as storage_mod
    storage_mod.Store = lambda *a, **kw: dummy_store
    return RecipeStorage(hass)

@pytest.mark.asyncio
async def test_crud(storage):
    r1 = Recipe(id="1", title="A", color="#123456")
    r2 = Recipe(id="2", title="B", color="#654321")
    # Add
    await storage.async_add_recipe(r1)
    await storage.async_add_recipe(r2)
    recipes = await storage.async_load_recipes()
    assert len(recipes) == 2
    # Update
    r2b = Recipe(id="2", title="B2", color="#000000")
    ok = await storage.async_update_recipe("2", r2b)
    assert ok
    recipes = await storage.async_load_recipes()
    assert any(r.title == "B2" and r.color == "#000000" for r in recipes)
    # Delete
    await storage.async_delete_recipe("1")
    recipes = await storage.async_load_recipes()
    assert len(recipes) == 1
    assert recipes[0].id == "2" 