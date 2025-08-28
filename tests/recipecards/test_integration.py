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
async def test_config_flow_user_step_shows_form():
    flow = RecipeCardsConfigFlow()
    flow.hass = MagicMock()
    
    result = await flow.async_step_user()
    assert result["type"] == "form"
    assert result["step_id"] == "user"

@pytest.mark.asyncio
async def test_config_flow_user_submit_creates_entry_with_initial_recipe():
    flow = RecipeCardsConfigFlow()
    flow.hass = MagicMock()
    user_input = {
        "recipe_title": "My First",
        "recipe_description": "desc",
        "recipe_ingredients": "a\nb",
        "recipe_notes": "n",
        "recipe_instructions": "s1\ns2",
        "recipe_color": "#112233",
    }

    result = await flow.async_step_user(user_input)
    assert result["type"] == "create_entry"
    assert result["title"] == "My First"
    assert "initial_recipe" in result["data"]
