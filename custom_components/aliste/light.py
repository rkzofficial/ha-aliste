"""The MirAIe climate platform."""

from __future__ import annotations
from typing import Any
from aliste import Device as AlisteDevice, AlisteHub, DeviceType as AlisteDeviceType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the MirAIe Climate Hub."""
    hub: AlisteHub = hass.data[DOMAIN][entry.entry_id]

    lights = list(filter(lambda d: d.type == AlisteDeviceType.LIGHT, hub.home.devices))

    entities = list(map(AlisteLight, lights))

    async_add_entities(entities)


class AlisteLight(LightEntity):
    """Representation of a Aliste Light."""

    def __init__(self, light: AlisteDevice) -> None:
        """Initialize an Aliste Light."""
        self._device = light

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
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return float(self._device.switchState) > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self._device.turn_off()

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:lightbulb"

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)
