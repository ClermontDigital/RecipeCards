import pytest
from unittest.mock import MagicMock
from custom_components.recipecards import async_setup
from custom_components.recipecards.config_flow import RecipeCardsConfigFlow
from custom_components.recipecards.const import DOMAIN

@pytest.mark.asyncio
async def test_async_setup_registers_ws_flag():
    hass = MagicMock()
    hass.data = {}
    config = {}

    result = await async_setup(hass, config)

    assert result is True
    assert DOMAIN in hass.data
    assert hass.data[DOMAIN]["api_registered"] is True

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
async def test_config_flow_single_instance():
    flow = RecipeCardsConfigFlow()
    flow.hass = MagicMock()
    # Mock an existing entry via underlying helper
    flow._async_current_entries = MagicMock(return_value=[MagicMock(domain=DOMAIN)])

    result = await flow.async_step_user()

    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"
