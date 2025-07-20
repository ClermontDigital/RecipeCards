"""Config flow for Recipe Cards integration."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN


class RecipeCardsConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Recipe Cards."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name"): str,
            }),
            errors=errors,
            description="Enter a name for your new recipe list (e.g., 'Desserts', 'Weeknight Meals')."
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return RecipeCardsOptionsFlow(config_entry)


class RecipeCardsOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description="Recipe Cards integration is configured. No additional options are available."
        )
