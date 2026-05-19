"""Entità Climate per Immergas Smartech Plus."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ImmergasCoordinator

PRESET_INVERNO       = "Inverno"
PRESET_ESTATE        = "Estate"
PRESET_RAFFRESCAMENTO = "Raffrescamento"
PRESET_SPENTO        = "Spento"

PRESET_TO_BOILER = {
    PRESET_INVERNO:        "3",
    PRESET_ESTATE:         "2",
    PRESET_RAFFRESCAMENTO: "4",
    PRESET_SPENTO:         "0",
}
BOILER_TO_PRESET = {v: k for k, v in PRESET_TO_BOILER.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura l'entità climate."""
    data        = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client      = data["client"]
    device_name = data["device_name"]
    thing_id    = data["thing_id"]

    async_add_entities([
        ImmergasClimate(coordinator, client, device_name, thing_id)
    ])


class ImmergasClimate(CoordinatorEntity, ClimateEntity):
    """Termostato Immergas Smartech Plus."""

    _attr_has_entity_name          = True
    _attr_name                     = None  # usa il device name
    _attr_temperature_unit         = UnitOfTemperature.CELSIUS
    _attr_hvac_modes               = [HVACMode.HEAT, HVACMode.AUTO]
    _attr_supported_features       = (
        ClimateEntityFeature.TARGET_TEMPERATURE |
        ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes             = [
        PRESET_INVERNO,
        PRESET_ESTATE,
        PRESET_RAFFRESCAMENTO,
        PRESET_SPENTO,
    ]
    _attr_min_temp                 = 5.0
    _attr_max_temp                 = 30.0
    _attr_target_temperature_step  = 0.5

    def __init__(
        self,
        coordinator: ImmergasCoordinator,
        client,
        device_name: str,
        thing_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._client      = client
        self._device_name = device_name
        self._thing_id    = thing_id
        self._attr_unique_id = f"immergas_{thing_id}_climate"
        self._attr_device_info = {
            "identifiers":  {(DOMAIN, thing_id)},
            "name":         f"Immergas {device_name}",
            "manufacturer": "Immergas",
            "model":        "Smartech Plus",
        }

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("current_temp")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.get("setpoint")

    @property
    def hvac_mode(self) -> HVACMode:
        mode = self.coordinator.data.get("mode", 0)
        return HVACMode.AUTO if mode == 1 else HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        if self.coordinator.data.get("fire_icon"):
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        """Preset corrente non tracciato dal polling — None di default."""
        return None

    async def async_set_temperature(self, **kwargs) -> None:
        """Imposta la temperatura target."""
        temp = kwargs.get("temperature")
        if temp is None:
            return
        temp = round(float(temp) * 2) / 2  # arrotonda a 0.5
        await self.hass.async_add_executor_job(
            self._client.set_temperature,
            self._device_name,
            self._thing_id,
            temp,
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Imposta la modalità (heat=manuale, auto=automatico)."""
        mode_int = 1 if hvac_mode == HVACMode.AUTO else 0
        await self.hass.async_add_executor_job(
            self._client.set_mode,
            self._device_name,
            self._thing_id,
            mode_int,
        )
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Imposta la modalità caldaia (Inverno/Estate/Spento/Raffrescamento)."""
        boiler_mode = PRESET_TO_BOILER.get(preset_mode)
        if boiler_mode is None:
            return
        await self.hass.async_add_executor_job(
            self._client.set_boiler_mode,
            self._thing_id,
            boiler_mode,
        )
        await self.coordinator.async_request_refresh()
