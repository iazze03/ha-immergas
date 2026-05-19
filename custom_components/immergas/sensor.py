"""Sensori per Immergas Smartech Plus."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ImmergasCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data        = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    thing_id    = data["thing_id"]
    device_name = data["device_name"]

    async_add_entities([
        ImmergasTempSensor(coordinator, thing_id, device_name, "ambiente"),
        ImmergasTempSensor(coordinator, thing_id, device_name, "esterna"),
    ])


class ImmergasTempSensor(CoordinatorEntity, SensorEntity):
    """Sensore di temperatura Immergas."""

    _attr_device_class  = SensorDeviceClass.TEMPERATURE
    _attr_state_class   = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: ImmergasCoordinator,
        thing_id: str,
        device_name: str,
        sensor_type: str,  # "ambiente" o "esterna"
    ) -> None:
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"immergas_{thing_id}_temp_{sensor_type}"
        self._attr_name = (
            f"Temperatura {'Ambiente' if sensor_type == 'ambiente' else 'Esterna'}"
        )
        self._attr_device_info = {
            "identifiers":  {(DOMAIN, thing_id)},
            "name":         f"Immergas {device_name}",
            "manufacturer": "Immergas",
            "model":        "Smartech Plus",
        }

    @property
    def native_value(self) -> float | None:
        if self._sensor_type == "ambiente":
            return self.coordinator.data.get("current_temp")
        return self.coordinator.data.get("ext_temp")
