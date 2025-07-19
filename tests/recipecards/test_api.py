import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.recipecards.api import (
    async_list_recipes, async_get_recipe, async_add_recipe,
    async_update_recipe, async_delete_recipe
)
from custom_components.recipecards.models import Recipe

@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {}
    return hass

@pytest.fixture
def mock_connection():
    connection = MagicMock()
    connection.send_result = AsyncMock()
    connection.send_error = AsyncMock()
    return connection

@pytest.fixture
def sample_recipe():
    return Recipe(
        id="test-123",
        title="Test Recipe",
        description="A test recipe",
        ingredients=["ingredient 1", "ingredient 2"],
        notes="Test notes",
        instructions=["step 1", "step 2"],
        color="#FF0000"
    )

@pytest.mark.asyncio
async def test_async_list_recipes(mock_hass, mock_connection, sample_recipe):
    # Setup storage with sample recipe
    storage_mock = MagicMock()
    storage_mock.async_load_recipes = AsyncMock(return_value=[sample_recipe])
    mock_hass.data["recipecards"] = storage_mock
    
    msg = {"id": 1}
    await async_list_recipes(mock_hass, mock_connection, msg)
    
    mock_connection.send_result.assert_called_once_with(1, [sample_recipe.to_dict()])

@pytest.mark.asyncio
async def test_async_get_recipe_found(mock_hass, mock_connection, sample_recipe):
    storage_mock = MagicMock()
    storage_mock.async_load_recipes = AsyncMock(return_value=[sample_recipe])
    mock_hass.data["recipecards"] = storage_mock
    
    msg = {"id": 1, "recipe_id": "test-123"}
    await async_get_recipe(mock_hass, mock_connection, msg)
    
    mock_connection.send_result.assert_called_once_with(1, sample_recipe.to_dict())

@pytest.mark.asyncio
async def test_async_get_recipe_not_found(mock_hass, mock_connection, sample_recipe):
    storage_mock = MagicMock()
    storage_mock.async_load_recipes = AsyncMock(return_value=[sample_recipe])
    mock_hass.data["recipecards"] = storage_mock
    
    msg = {"id": 1, "recipe_id": "nonexistent"}
    await async_get_recipe(mock_hass, mock_connection, msg)
    
    mock_connection.send_error.assert_called_once_with(1, "not_found", "Recipe not found")

@pytest.mark.asyncio
async def test_async_add_recipe(mock_hass, mock_connection):
    storage_mock = MagicMock()
    storage_mock.async_add_recipe = AsyncMock()
    mock_hass.data["recipecards"] = storage_mock
    
    recipe_data = {
        "id": "new-recipe",
        "title": "New Recipe",
        "description": "A new recipe",
        "ingredients": ["item 1"],
        "notes": "New notes",
        "instructions": ["new step"],
        "color": "#00FF00"
    }
    
    msg = {"id": 1, "recipe": recipe_data}
    await async_add_recipe(mock_hass, mock_connection, msg)
    
    storage_mock.async_add_recipe.assert_called_once()
    mock_connection.send_result.assert_called_once()

@pytest.mark.asyncio
async def test_async_update_recipe_success(mock_hass, mock_connection):
    storage_mock = MagicMock()
    storage_mock.async_update_recipe = AsyncMock(return_value=True)
    mock_hass.data["recipecards"] = storage_mock
    
    recipe_data = {
        "id": "test-123",
        "title": "Updated Recipe",
        "color": "#0000FF"
    }
    
    msg = {"id": 1, "recipe_id": "test-123", "recipe": recipe_data}
    await async_update_recipe(mock_hass, mock_connection, msg)
    
    storage_mock.async_update_recipe.assert_called_once_with("test-123", pytest.approx(Recipe.from_dict(recipe_data)))
    mock_connection.send_result.assert_called_once()

@pytest.mark.asyncio
async def test_async_update_recipe_not_found(mock_hass, mock_connection):
    storage_mock = MagicMock()
    storage_mock.async_update_recipe = AsyncMock(return_value=False)
    mock_hass.data["recipecards"] = storage_mock
    
    recipe_data = {"id": "nonexistent", "title": "Updated"}
    msg = {"id": 1, "recipe_id": "nonexistent", "recipe": recipe_data}
    await async_update_recipe(mock_hass, mock_connection, msg)
    
    mock_connection.send_error.assert_called_once_with(1, "not_found", "Recipe not found")

@pytest.mark.asyncio
async def test_async_delete_recipe(mock_hass, mock_connection):
    storage_mock = MagicMock()
    storage_mock.async_delete_recipe = AsyncMock()
    mock_hass.data["recipecards"] = storage_mock
    
    msg = {"id": 1, "recipe_id": "test-123"}
    await async_delete_recipe(mock_hass, mock_connection, msg)
    
    storage_mock.async_delete_recipe.assert_called_once_with("test-123")
    mock_connection.send_result.assert_called_once_with(1, True) 