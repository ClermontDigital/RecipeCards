"""Config flow for Recipe Cards integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class RecipeCardsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Recipe Cards."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({}),
            )

        return self.async_create_entry(
            title="Recipe Cards",
            data={}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "RecipeCardsOptionsFlow":
        """Create the options flow."""
        return RecipeCardsOptionsFlow(config_entry)


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
