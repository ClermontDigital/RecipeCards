"""Tests for the Recipe Cards WebSocket API.

Skips if Home Assistant isn't available in the environment.
"""
import pytest

ha = pytest.importorskip("homeassistant")
from unittest.mock import AsyncMock  # noqa: E402
from homeassistant.core import HomeAssistant  # type: ignore # noqa: E402
from homeassistant.setup import async_setup_component  # type: ignore # noqa: E402
from custom_components.recipecards.const import DOMAIN  # noqa: E402
from custom_components.recipecards.api import async_list_recipes  # noqa: E402
from custom_components.recipecards.models import Recipe  # noqa: E402


@pytest.fixture
async def setup_integration(hass: HomeAssistant):
    """Set up the Recipe Cards integration."""
    assert await async_setup_component(hass, DOMAIN, {"recipecards": {}})
    await hass.async_block_till_done()


async def test_async_list_recipes_no_entry(hass: HomeAssistant, setup_integration):
    """Test listing recipes with no config entry."""
    connection = AsyncMock()
    msg = {"id": 1}

    await async_list_recipes(hass, connection, msg)

    connection.send_result.assert_called_once_with(1, [])


async def test_async_list_recipes_with_entry(hass: HomeAssistant, setup_integration):
    """Test listing recipes with a config entry."""
    entry_id = "test_entry"
    hass.data[DOMAIN] = {
        entry_id: AsyncMock()
    }
    hass.data[DOMAIN][entry_id].async_load_recipes.return_value = [
        Recipe(id="1", title="Test Recipe", ingredients=[], instructions=[])
    ]

    connection = AsyncMock()
    connection.config_entry.entry_id = entry_id
    msg = {"id": 1}

    await async_list_recipes(hass, connection, msg)

    connection.send_result.assert_called_once_with(
        1,
        [
            {
                "id": "1",
                "title": "Test Recipe",
                "description": None,
                "ingredients": [],
                "notes": None,
                "instructions": [],
                "color": None,
                "created_at": None,
                "updated_at": None,
            }
        ],
    )
