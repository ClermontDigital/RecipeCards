"""Config flow for Recipe Cards integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
def _validate_color(value) -> str:
    """Local color validator to avoid cross-module import during config flow.

    Accepts '#RRGGBB' string, an RGB list [r,g,b], or a dict {r,g,b}.
    """
    import re
    if isinstance(value, (list, tuple)) and len(value) == 3:
        try:
            r, g, b = (int(value[0]), int(value[1]), int(value[2]))
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:  # noqa: BLE001
            return "#FFD700"
    if isinstance(value, dict) and all(k in value for k in ("r", "g", "b")):
        try:
            r, g, b = int(value["r"]), int(value["g"]), int(value["b"])
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:  # noqa: BLE001
            return "#FFD700"
    if isinstance(value, str) and re.match(r"^#[0-9A-Fa-f]{6}$", value):
        return value
    return "#FFD700"


class RecipeCardsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Recipe Cards."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Allow multiple entries. If the user provides a title we treat it as
        # a request to create an initial recipe for this entry.
        schema = vol.Schema(
            {
                vol.Optional("recipe_title", default=""): str,
                vol.Optional("recipe_description", default=""): str,
                vol.Optional("recipe_ingredients", default=""): str,  # one per line
                vol.Optional("recipe_notes", default=""): str,
                vol.Optional("recipe_instructions", default=""): str,  # one per line
                vol.Optional("recipe_color", default="#FFD700"): _validate_color,
            }
        )

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)

        # Store optional initial recipe payload in the entry data so setup can
        # create it in storage. Keeping it small avoids large config entries.
        initial_recipe = None
        title = (user_input.get("recipe_title") or "").strip()
        if title:
            # Parse newline-separated lists
            def _split_lines(value: str) -> list[str]:
                return [line.strip() for line in (value or "").splitlines() if line.strip()]

            initial_recipe = {
                "title": title,
                "description": (user_input.get("recipe_description") or "").strip(),
                "ingredients": _split_lines(user_input.get("recipe_ingredients") or ""),
                "notes": (user_input.get("recipe_notes") or "").strip(),
                "instructions": _split_lines(user_input.get("recipe_instructions") or ""),
                "color": user_input.get("recipe_color") or "#FFD700",
            }

        return self.async_create_entry(
            title=title or "Recipe Cards",
            data={"initial_recipe": initial_recipe} if initial_recipe else {},
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

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Options: allow adding recipes from the options flow."""
        schema = vol.Schema({
            vol.Optional("action", default="add_recipe"): vol.In({
                "add_recipe": "Add recipe",
                "finish": "Finish",
            })
        })

        if user_input is None:
            return self.async_show_form(step_id="init", data_schema=schema, last_step=False)

        action = user_input.get("action")
        if action == "add_recipe":
            return await self.async_step_add_recipe()

        # No persistent options for now; we simply finish.
        return self.async_create_entry(title="", data={})

    async def async_step_add_recipe(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Collect full recipe fields and save to this entry's storage."""
        schema = vol.Schema({
            vol.Required("title"): str,
            vol.Optional("description", default=""): str,
            vol.Optional("ingredients", default=""): str,  # one per line
            vol.Optional("notes", default=""): str,
            vol.Optional("instructions", default=""): str,  # one per line
            vol.Optional("color", default="#FFD700"): _validate_color,
        })

        if user_input is None:
            return self.async_show_form(step_id="add_recipe", data_schema=schema, last_step=False)

        # Save the recipe via storage for this entry
        def _split_lines(value: str) -> list[str]:
            return [line.strip() for line in (value or "").splitlines() if line.strip()]

        recipe_data = {
            "title": user_input.get("title", "").strip(),
            "description": (user_input.get("description") or "").strip(),
            "ingredients": _split_lines(user_input.get("ingredients") or ""),
            "notes": (user_input.get("notes") or "").strip(),
            "instructions": _split_lines(user_input.get("instructions") or ""),
            "color": user_input.get("color") or "#FFD700",
        }

        # Persist asynchronously; ignore errors to keep flow resilient
        try:
            entry_id = self._config_entry.entry_id
            storage = self.hass.data.get(DOMAIN, {}).get(entry_id, {}).get("storage")
            coordinator = self.hass.data.get(DOMAIN, {}).get(entry_id, {}).get("coordinator")
            if storage and coordinator:
                from .models import Recipe
                await storage.async_add_recipe(Recipe.from_dict(recipe_data))
                await coordinator.async_request_refresh()
        except Exception:  # noqa: BLE001
            pass

        # Return to init to allow adding more, not the final screen
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}), last_step=False)
