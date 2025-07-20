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
    
    async_add_entities([RecipeCardsSensor(coordinator, config_entry)])


class RecipeCardsSensor(CoordinatorEntity, SensorEntity):
    """Recipe Cards sensor entity."""

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = f"Recipes: {config_entry.data.get('name', 'Unnamed List')}"
        self._attr_unique_id = f"{config_entry.entry_id}_recipe_count"
        self._attr_icon = "mdi:notebook"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=f"Recipe List: {self._config_entry.data.get('name', 'Unnamed List')}",
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