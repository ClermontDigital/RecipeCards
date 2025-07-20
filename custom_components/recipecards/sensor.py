"""Sensor platform for Recipe Cards integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity import DeviceInfo
from datetime import timedelta

from .const import DOMAIN
from .storage import RecipeStorage
from .models import Recipe

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "recipe_count": SensorEntityDescription(
        key="recipe_count",
        name="Recipe Count",
        icon="mdi:counter",
        native_unit_of_measurement="recipes",
    ),
    "last_updated": SensorEntityDescription(
        key="last_updated",
        name="Last Recipe Update",
        icon="mdi:clock-time-eight",
        device_class="timestamp",
    ),
}


class RecipeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching recipe data."""

    def __init__(self, hass: HomeAssistant, storage: RecipeStorage) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.storage = storage

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the storage."""
        recipes = await self.storage.async_load_recipes()
        
        # Find the most recent update time
        last_updated = None
        if recipes:
            # For simplicity, we'll use the current time
            # In a real implementation, you'd store timestamps with recipes
            from datetime import datetime
            last_updated = datetime.now()
        
        return {
            "recipe_count": len(recipes),
            "last_updated": last_updated,
            "recipes": recipes,
        }


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recipe Cards sensor entities."""
    storage = hass.data[DOMAIN][config_entry.entry_id]
    
    # Create coordinator
    coordinator = RecipeDataUpdateCoordinator(hass, storage)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator for other components to use
    hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"] = coordinator
    
    # Create sensor entities
    entities = []
    for sensor_type, description in SENSOR_TYPES.items():
        entities.append(RecipeCardsSensor(coordinator, description, config_entry))
    
    async_add_entities(entities)


class RecipeCardsSensor(CoordinatorEntity[RecipeDataUpdateCoordinator], SensorEntity):
    """Recipe Cards sensor entity."""

    def __init__(
        self,
        coordinator: RecipeDataUpdateCoordinator,
        description: SensorEntityDescription,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="Recipe Cards",
            manufacturer="ClermontDigital",
            model="Recipe Storage",
            sw_version="1.0.13",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.entity_description.key == "recipe_count":
            return self.coordinator.data.get("recipe_count", 0)
        elif self.entity_description.key == "last_updated":
            return self.coordinator.data.get("last_updated")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if self.entity_description.key == "recipe_count":
            recipes = self.coordinator.data.get("recipes", [])
            return {
                "recipe_list": [recipe.title for recipe in recipes],
                "recipe_ids": [recipe.id for recipe in recipes],
            }
        return {}

    async def async_update_recipes(self) -> None:
        """Trigger an update of recipe data."""
        await self.coordinator.async_request_refresh()