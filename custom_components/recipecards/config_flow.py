"""Config flow for Recipe Cards integration."""
from homeassistant import config_entries  # type: ignore[import-untyped]
from homeassistant.core import callback  # type: ignore[import-untyped]
from homeassistant.data_entry_flow import FlowResult  # type: ignore[import-untyped]
from .const import DOMAIN


class RecipeCardsConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Recipe Cards."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=None,
                description="Recipe Cards integration for storing and displaying recipes in a retro card interface. Click Submit to complete setup."
            )

        return self.async_create_entry(
            title="Recipe Cards",
            data={}
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
            data_schema=None,
            description="Recipe Cards integration is configured. No additional options are available."
        ) 