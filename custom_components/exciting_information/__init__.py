"""The PV Exciting Information integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]


def _get_entry_data(entry: ConfigEntry) -> dict[str, str | float]:
    """Return merged config entry data and options."""
    data = dict(entry.data)
    data.update(entry.options)
    return data


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PV Exciting Information from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _get_entry_data(entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle reloading the config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
