"""Tests for domain setup and the config flow."""
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.recipecards import async_setup
from custom_components.recipecards.const import DOMAIN


async def test_async_setup_registers_ws_api():
    hass = MagicMock()
    hass.data = {}

    assert await async_setup(hass, {}) is True
    assert hass.data[DOMAIN]["api_registered"] is True


async def test_config_flow_shows_form(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_config_flow_creates_named_empty_section(hass: HomeAssistant):
    """Entries are empty named sections - no recipe is created automatically."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"section_name": "Desserts"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Desserts"
    assert result["data"] == {}


async def test_multiple_sections_allowed(hass: HomeAssistant):
    for name in ("Desserts", "Mains"):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"section_name": name}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2
