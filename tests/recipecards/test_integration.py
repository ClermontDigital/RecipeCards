import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.recipecards import async_setup
from custom_components.recipecards.config_flow import RecipeCardsConfigFlow
from custom_components.recipecards.storage import RecipeStorage
from custom_components.recipecards.models import Recipe

@pytest.mark.asyncio
async def test_async_setup():
    hass = MagicMock()
    hass.data = {}
    config = {}
    
    result = await async_setup(hass, config)
    
    assert result is True
    assert "recipecards" in hass.data
    assert isinstance(hass.data["recipecards"], RecipeStorage)

@pytest.mark.asyncio
async def test_config_flow_user_step():
    flow = RecipeCardsConfigFlow()
    flow.hass = MagicMock()
    flow.hass.config_entries = MagicMock()
    flow.hass.config_entries.async_entries = MagicMock(return_value=[])
    
    result = await flow.async_step_user()
    
    assert result["type"] == "create_entry"
    assert result["title"] == "Recipe Cards"
    assert result["data"] == {}

@pytest.mark.asyncio
async def test_config_flow_single_instance():
    flow = RecipeCardsConfigFlow()
    flow.hass = MagicMock()
    
    # Mock existing entry
    mock_entry = MagicMock()
    mock_entry.domain = "recipecards"
    flow.hass.config_entries = MagicMock()
    flow.hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])
    
    result = await flow.async_step_user()
    
    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"

@pytest.mark.asyncio
async def test_storage_integration():
    hass = MagicMock()
    hass.data = {}
    
    # Setup integration
    await async_setup(hass, {})
    
    # Get storage instance
    storage = hass.data["recipecards"]
    assert isinstance(storage, RecipeStorage)
    
    # Test basic storage operations
    recipe = Recipe(
        id="test-integration",
        title="Integration Test Recipe",
        color="#FF0000"
    )
    
    await storage.async_add_recipe(recipe)
    recipes = await storage.async_load_recipes()
    
    assert len(recipes) == 1
    assert recipes[0].id == "test-integration"
    assert recipes[0].title == "Integration Test Recipe"
    assert recipes[0].color == "#FF0000" 