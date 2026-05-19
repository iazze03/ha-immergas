"""Binary sensor per Immergas Smartech Plus."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
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
        ImmergasHeatingSensor(coordinator, thing_id, device_name)
    ])


class ImmergasHeatingSensor(CoordinatorEntity, BinarySensorEntity):
    """Sensore binario: riscaldamento attivo (fiamma accesa)."""

    _attr_device_class = BinarySensorDeviceClass.HEAT
    _attr_name         = "Riscaldamento Attivo"

    def __init__(
        self,
        coordinator: ImmergasCoordinator,
        thing_id: str,
        device_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"immergas_{thing_id}_heating"
        self._attr_device_info = {
            "identifiers":  {(DOMAIN, thing_id)},
            "name":         f"Immergas {device_name}",
            "manufacturer": "Immergas",
            "model":        "Smartech Plus",
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("fire_icon", False))
