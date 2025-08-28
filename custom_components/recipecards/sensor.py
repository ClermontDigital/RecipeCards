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

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recipe Cards sensor entities."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    
    # Always expose the collection sensor for backward compatibility
    entities: list[SensorEntity] = [RecipeCardsCollectionSensor(coordinator, config_entry)]

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
            manufacturer="ClermontDigital",
        )

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return 0
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return {"recipes": []}
        
        return {
            "recipes": [recipe.to_dict() for recipe in self.coordinator.data]
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
        self._attr_name = title
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
        return recipe.title if recipe else self._attr_name

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
            manufacturer="ClermontDigital",
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
        recipe = self._find()
        return recipe.to_dict() if recipe else {}
