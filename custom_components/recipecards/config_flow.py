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

def _validate_image(value) -> Optional[str]:
    """Local image validator."""
    if not value:
        return None
    if isinstance(value, str):
        import re
        # Basic base64 or URL check
        if value.startswith('data:image/') or re.match(r'^https?://.*\.(png|jpg|jpeg|gif)$', value):
            if len(value) > 1000000:  # ~1MB
                raise vol.Invalid("Image too large (max 1MB)")
            return value
    raise vol.Invalid("Invalid image format (base64 or URL expected)")
    return value


class RecipeCardsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Recipe Cards."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Allow multiple entries. Each entry represents a "section" (e.g., Desserts).
        schema = vol.Schema({vol.Required("section_name"): str})

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)

        # Store optional initial recipe payload in the entry data so setup can
        # create it in storage. Keeping it small avoids large config entries.
        section_name = (user_input.get("section_name") or "Recipe Cards").strip() or "Recipe Cards"
        return self.async_create_entry(title=section_name, data={})

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
        """Main options menu, using HA's menu UI to avoid schema validation issues."""
        return self.async_show_menu(
            step_id="init",
            menu_options={
                "add_recipe": "Add new recipe",
                "select_recipe": "Edit existing recipe",
                "select_recipe_delete": "Delete recipe",
                "rename_section": "Rename this section",
                "finish": "Finish",
            },
        )

    def _get_storage_and_coordinator(self):
        domain_data = self.hass.data.get(DOMAIN, {})
        entry_id = self._config_entry.entry_id
        entry_data = domain_data.get(entry_id, {})
        return entry_data.get("storage"), entry_data.get("coordinator")

    async def async_step_add_recipe(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Collect full recipe fields and save to this entry's storage."""
        schema = vol.Schema({
            vol.Required("title"): str,
            vol.Optional("description", default=""): cv.text,
            vol.Optional("ingredients", default=""): cv.text,  # one per line
            vol.Optional("notes", default=""): cv.text,
            vol.Optional("instructions", default=""): cv.text,  # one per line
            vol.Optional("color", default="#FFD700"): str,
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
            "color": _validate_color(user_input.get("color") or "#FFD700"),
        }

        # Persist asynchronously; ignore errors to keep flow resilient
        try:
            storage, coordinator = self._get_storage_and_coordinator()
            if storage and coordinator:
                from .models import Recipe
                await storage.async_add_recipe(Recipe.from_dict(recipe_data))
                await coordinator.async_request_refresh()
        except Exception:  # noqa: BLE001
            pass

        # Back to menu
        return await self.async_step_init()

    async def async_step_select_recipe(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Select a recipe to edit/delete."""
        next_action = "edit"
        storage, _ = self._get_storage_and_coordinator()
        titles: dict[str, str] = {}
        if storage:
            try:
                recipes = await storage.async_load_recipes()
                titles = {r.id: (r.title or r.id) for r in recipes}
            except Exception:  # noqa: BLE001
                titles = {}
        if not titles:
            # Nothing to select; return to menu
            return await self.async_step_init()

        schema = vol.Schema({vol.Required("recipe_id"): vol.In(titles)})
        if user_input and user_input.get("recipe_id"):
            rid = user_input["recipe_id"]
            return await self.async_step_edit_recipe({"recipe_id": rid})
        return self.async_show_form(step_id="select_recipe", data_schema=schema)

    async def async_step_select_recipe_delete(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Select a recipe to delete."""
        storage, _ = self._get_storage_and_coordinator()
        titles: dict[str, str] = {}
        if storage:
            try:
                recipes = await storage.async_load_recipes()
                titles = {r.id: (r.title or r.id) for r in recipes}
            except Exception:  # noqa: BLE001
                titles = {}
        if not titles:
            return await self.async_step_init()

        schema = vol.Schema({vol.Required("recipe_id"): vol.In(titles)})
        if user_input and user_input.get("recipe_id"):
            rid = user_input["recipe_id"]
            return await self.async_step_delete_recipe({"recipe_id": rid})
        return self.async_show_form(step_id="select_recipe_delete", data_schema=schema)

    async def async_step_edit_recipe(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Edit selected recipe."""
        if user_input is None or "recipe_id" not in user_input:
            return await self.async_step_select_recipe({"next": "edit"})

        rid = user_input["recipe_id"]
        storage, coordinator = self._get_storage_and_coordinator()
        if not storage:
            return await self.async_step_init()

        recipes = await storage.async_load_recipes()
        recipe = next((r for r in recipes if r.id == rid), None)
        if not recipe:
            return await self.async_step_init()

        schema = vol.Schema({
            vol.Required("title", default=recipe.title): str,
            vol.Optional("description", default=recipe.description or ""): cv.text,
            vol.Optional("ingredients", default="\n".join(recipe.ingredients or [])): cv.text,
            vol.Optional("notes", default=recipe.notes or ""): cv.text,
            vol.Optional("instructions", default="\n".join(recipe.instructions or [])): cv.text,
            vol.Optional("color", default=recipe.color or "#FFD700"): str,
        })

        if user_input and set(user_input.keys()) - {"recipe_id"}:
            def _split_lines(value: str) -> list[str]:
                return [line.strip() for line in (value or "").splitlines() if line.strip()]

            updated = {
                "id": rid,
                "title": user_input.get("title", recipe.title),
                "description": user_input.get("description", recipe.description or ""),
                "ingredients": _split_lines(user_input.get("ingredients") or "\n".join(recipe.ingredients or [])),
                "notes": user_input.get("notes", recipe.notes or ""),
                "instructions": _split_lines(user_input.get("instructions") or "\n".join(recipe.instructions or [])),
                "color": _validate_color(user_input.get("color") or recipe.color or "#FFD700"),
            }
            try:
                from .models import Recipe
                await storage.async_update_recipe(rid, Recipe.from_dict(updated))
                if coordinator:
                    await coordinator.async_request_refresh()
            except Exception:  # noqa: BLE001
                pass
            return await self.async_step_init()

        return self.async_show_form(step_id="edit_recipe", data_schema=schema)

    async def async_step_delete_recipe(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is None or "recipe_id" not in user_input:
            return await self.async_step_select_recipe_delete()
        rid = user_input["recipe_id"]
        storage, coordinator = self._get_storage_and_coordinator()
        if storage:
            try:
                await storage.async_delete_recipe(rid)
                if coordinator:
                    await coordinator.async_request_refresh()
            except Exception:  # noqa: BLE001
                pass
        return await self.async_step_init()

    async def async_step_rename_section(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        default = getattr(self._config_entry, "title", "Recipe Cards")
        schema = vol.Schema({vol.Required("section_name", default=default): str})
        if user_input is None:
            return self.async_show_form(step_id="rename_section", data_schema=schema)
        try:
            new_title = (user_input.get("section_name") or default).strip() or default
            self.hass.config_entries.async_update_entry(self._config_entry, title=new_title)
        except Exception:  # noqa: BLE001
            pass
        return await self.async_step_init()

    async def async_step_finish(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_create_entry(title="", data={})
