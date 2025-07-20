"""Config flow for Recipe Cards integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RecipeCardsConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Recipe Cards."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> RecipeCardsOptionsFlow:
        """Create the options flow."""
        return RecipeCardsOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Create the config entry
                return self.async_create_entry(
                    title="Recipe Cards",
                    data={}
                )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors=errors,
            description="Recipe Cards integration for storing and displaying recipes in a retro card interface. Click Submit to complete setup."
        )


class RecipeCardsOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Recipe Cards."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description="Recipe Cards integration is configured. No additional options are available."
        ) 