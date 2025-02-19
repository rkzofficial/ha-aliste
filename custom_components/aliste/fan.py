"""The Aliste Fan platform."""

from __future__ import annotations
from typing import Any, Optional
from aliste import Device as AlisteDevice, AlisteHub, DeviceType as AlisteDeviceType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Aliste Hub."""
    hub: AlisteHub = hass.data[DOMAIN][entry.entry_id]

    fans = list(filter(lambda d: d.type == AlisteDeviceType.FAN, hub.home.devices))

    entities = list(map(AlisteFan, fans))

    async_add_entities(entities)


class AlisteFan(FanEntity):
    """Representation of a Aliste Fan."""

    def __init__(self, device: AlisteDevice) -> None:
        """Initialize an Aliste Fan."""
        self._device = device
        self.last_preset_mode = "Medium"

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        return FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE | FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON

    @property
    def preset_modes(self) -> list[str] | None:
        return ["Low", "Medium", "High", "Max"]

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.deviceId}_{self._device.switchId}"

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return f"{self._device.roomName} {self._device.name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._device.deviceId}_{self._device.switchId}")},
            name=f"{self._device.roomName} {self._device.name}",
            manufacturer="Aliste",
            model="-",
            sw_version="20",
        )

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:fan"

    @property
    def preset_mode(self) -> str | None:
        state = float(self._device.switchState)
        
        if (state) > 0.75:
            return "Max"
        if state > 0.50:
            return "High"
        if state > 0.25:
            return "Medium"
        if state > 0:
            return "Low"
        return self.last_preset_mode

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        if preset_mode == "Low":
            await self._device.dim(0.25)
        if preset_mode == "Medium":
            await self._device.dim(0.5)
        if preset_mode == "High":
            await self._device.dim(0.75)
        if preset_mode == "Max":
            await self._device.dim(1.0)

        self.last_preset_mode = preset_mode

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        return float(self._device.switchState) * 100

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        await self._device.dim(percentage / 100)

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return float(self._device.switchState) > 0

    async def async_turn_on(self, speed: Optional[str] = None, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self._device.dim(percentage / 100)
        else:
            await self.async_set_preset_mode(self.last_preset_mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self._device.turn_off()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)
