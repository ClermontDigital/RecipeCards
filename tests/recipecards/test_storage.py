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
    return RecipeStorage(hass, "test_entry")

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

@pytest.mark.asyncio
async def test_empty_storage(storage):
    recipes = await storage.async_load_recipes()
    assert recipes == []

@pytest.mark.asyncio
async def test_update_nonexistent_recipe(storage):
    r1 = Recipe(id="1", title="A", color="#123456")
    await storage.async_add_recipe(r1)
    
    r2 = Recipe(id="2", title="B", color="#654321")
    ok = await storage.async_update_recipe("nonexistent", r2)
    assert not ok
    
    recipes = await storage.async_load_recipes()
    assert len(recipes) == 1
    assert recipes[0].id == "1"

@pytest.mark.asyncio
async def test_delete_nonexistent_recipe(storage):
    r1 = Recipe(id="1", title="A", color="#123456")
    await storage.async_add_recipe(r1)
    
    await storage.async_delete_recipe("nonexistent")
    recipes = await storage.async_load_recipes()
    assert len(recipes) == 1
    assert recipes[0].id == "1"

@pytest.mark.asyncio
async def test_color_persistence(storage):
    r1 = Recipe(id="1", title="A", color="#FF0000")
    await storage.async_add_recipe(r1)
    
    recipes = await storage.async_load_recipes()
    assert recipes[0].color == "#FF0000"
    
    # Update color
    r1_updated = Recipe(id="1", title="A", color="#00FF00")
    await storage.async_update_recipe("1", r1_updated)
    
    recipes = await storage.async_load_recipes()
    assert recipes[0].color == "#00FF00"

@pytest.mark.asyncio
async def test_recipe_with_all_fields(storage):
    r1 = Recipe(
        id="complete-recipe",
        title="Complete Recipe",
        description="A complete recipe with all fields",
        ingredients=["ingredient 1", "ingredient 2", "ingredient 3"],
        notes="Important cooking notes",
        instructions=["step 1", "step 2", "step 3"],
        color="#FFD700"
    )
    
    await storage.async_add_recipe(r1)
    recipes = await storage.async_load_recipes()
    
    assert len(recipes) == 1
    recipe = recipes[0]
    assert recipe.id == "complete-recipe"
    assert recipe.title == "Complete Recipe"
    assert recipe.description == "A complete recipe with all fields"
    assert recipe.ingredients == ["ingredient 1", "ingredient 2", "ingredient 3"]
    assert recipe.notes == "Important cooking notes"
    assert recipe.instructions == ["step 1", "step 2", "step 3"]
    assert recipe.color == "#FFD700"

@pytest.mark.asyncio
async def test_multiple_operations_sequence(storage):
    # Add multiple recipes
    recipes = [
        Recipe(id="1", title="Recipe 1", color="#FF0000"),
        Recipe(id="2", title="Recipe 2", color="#00FF00"),
        Recipe(id="3", title="Recipe 3", color="#0000FF"),
    ]
    
    for recipe in recipes:
        await storage.async_add_recipe(recipe)
    
    # Verify all added
    loaded = await storage.async_load_recipes()
    assert len(loaded) == 3
    
    # Update middle recipe
    updated = Recipe(id="2", title="Updated Recipe 2", color="#FFFF00")
    ok = await storage.async_update_recipe("2", updated)
    assert ok
    
    # Delete first recipe
    await storage.async_delete_recipe("1")
    
    # Verify final state
    final = await storage.async_load_recipes()
    assert len(final) == 2
    assert final[0].id == "2" and final[0].title == "Updated Recipe 2"
    assert final[1].id == "3" 
