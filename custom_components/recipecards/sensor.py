"""Sensor platform for Recipe Cards integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import CONF_PER_RECIPE_ENTITIES, DEFAULT_PER_RECIPE_ENTITIES, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recipe Cards sensor entities."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    
    entities: list[SensorEntity] = [RecipeCardsCollectionSensor(coordinator, config_entry)]

    per_recipe = config_entry.options.get(
        CONF_PER_RECIPE_ENTITIES, DEFAULT_PER_RECIPE_ENTITIES
    )
    if not per_recipe:
        async_add_entities(entities)
        return

    # Track and add one sensor per recipe so each appears as its own device
    known_ids: set[str] = set()
    for recipe in (coordinator.data or []):
        entities.append(RecipeSensor(coordinator, config_entry, recipe.id))
        known_ids.add(recipe.id)

    async_add_entities(entities)

    # Dynamically add new recipe sensors when recipes are created
    def _handle_update() -> None:
        if coordinator.data is None:
            return
        new_entities: list[SensorEntity] = []
        for recipe in coordinator.data:
            if recipe.id not in known_ids:
                new_entities.append(RecipeSensor(coordinator, config_entry, recipe.id))
                known_ids.add(recipe.id)
        if new_entities:
            async_add_entities(new_entities)

    coordinator.async_add_listener(_handle_update)


class RecipeCardsCollectionSensor(CoordinatorEntity, SensorEntity):
    """Sensor that represents the collection for this config entry."""

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = "Recipe Cards"
        self._attr_unique_id = f"{config_entry.entry_id}_recipe_count"
        self._attr_icon = "mdi:notebook"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="Recipe Cards",
            manufacturer="recipecards",
        )

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return 0
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return a lightweight index of the collection.

        Deliberately NOT the full text of every recipe. Home Assistant caps a
        single attribute at about 16 KB, every browser downloads all attributes
        on connect, and the recorder writes them on each change. Ingredients,
        method and notes are served over the WebSocket API instead, which is
        what the card uses. This keeps a collection of hundreds of recipes to a
        few KB and still gives automations and templates something to work with.
        """
        recipes = self.coordinator.data or []
        if not recipes:
            return {"recipes": [], "count": 0, "avg_prep_time": 0}

        index = [
            {
                "id": r.id,
                "title": r.title,
                "image": r.image,
                "color": r.color,
                "prep_time": r.prep_time,
                "cook_time": r.cook_time,
                "total_time": r.total_time,
                "ingredient_count": len(r.ingredients or []),
                "step_count": len(r.instructions or []),
                "tags": r.tags or [],
            }
            for r in recipes
        ]
        prep = [r.prep_time for r in recipes if r.prep_time]
        all_tags = sorted({t for r in recipes for t in (r.tags or [])})
        return {
            "recipes": index,
            "count": len(recipes),
            "tags": all_tags,
            "avg_prep_time": round(sum(prep) / len(prep), 1) if prep else 0,
        }


class RecipeSensor(CoordinatorEntity, SensorEntity):
    """One sensor per recipe so each appears as its own device."""

    def __init__(self, coordinator, config_entry: ConfigEntry, recipe_id: str) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._recipe_id = recipe_id

        # Names and IDs fill in from current data at init; will update on refresh
        recipe = self._find()
        title = recipe.title if recipe else "Recipe"
        # Prefix name so new entity IDs are suggested as sensor.recipe_<slug(title)>
        self._attr_name = f"Recipe {title}"
        self._attr_unique_id = f"{config_entry.entry_id}_{recipe_id}"
        self._attr_icon = "mdi:note-text"

    def _find(self):
        if self.coordinator.data is None:
            return None
        for r in self.coordinator.data:
            if r.id == self._recipe_id:
                return r
        return None

    @property
    def name(self) -> str:  # type: ignore[override]
        recipe = self._find()
        if recipe:
            return f"Recipe {recipe.title}".strip()
        return self._attr_name

    @property
    def available(self) -> bool:  # type: ignore[override]
        # Consider the entity unavailable if its backing recipe no longer exists
        return super().available and self._find() is not None

    @property
    def device_info(self) -> DeviceInfo:
        recipe = self._find()
        title = recipe.title if recipe else "Recipe"
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._config_entry.entry_id}:{self._recipe_id}")},
            name=title,
            manufacturer="recipecards",
            via_device=(DOMAIN, self._config_entry.entry_id),
        )

    @property
    def native_value(self) -> int:
        recipe = self._find()
        if not recipe:
            return 0
        # Use instruction count as a sensible numeric state
        try:
            return len(recipe.instructions or [])
        except Exception:  # noqa: BLE001
            return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Summary only. The full recipe is served over the WebSocket API."""
        recipe = self._find()
        if not recipe:
            return {}
        return {
            "id": recipe.id,
            "title": recipe.title,
            "description": recipe.description,
            "image": recipe.image,
            "color": recipe.color,
            "prep_time": recipe.prep_time,
            "cook_time": recipe.cook_time,
            "total_time": recipe.total_time,
            "ingredient_count": len(recipe.ingredients or []),
            "step_count": len(recipe.instructions or []),
            "tags": recipe.tags or [],
        }
