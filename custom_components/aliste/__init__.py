"""The Aliste integration."""
from __future__ import annotations

from aliste import AlisteHub

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.FAN]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aliste from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    hub = AlisteHub()

    try:
        await hub.connect(entry.data["username"], entry.data["password"])
    except Exception as err:  # noqa: BLE001 - surface any setup failure as retryable
        await hub.close()
        raise ConfigEntryNotReady(f"Unable to connect to Aliste: {err}") from err

    hass.data[DOMAIN][entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hub: AlisteHub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.close()

    return unload_ok
