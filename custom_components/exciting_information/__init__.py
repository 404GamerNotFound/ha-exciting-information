"""The PV Exciting Information integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]
CARD_URL_PATH = "/pv-exciting-information-card.js"
CARD_RESOURCE_PATH = Path(__file__).parent / "www" / "pv-exciting-information-card.js"

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up PV Exciting Information from configuration.yaml."""
    if not CARD_RESOURCE_PATH.exists():
        _LOGGER.warning(
            "Card resource file missing at %s, skipping static path registration",
            CARD_RESOURCE_PATH,
        )
        return True
    if hass.http is None:
        _LOGGER.warning(
            "HTTP component unavailable, skipping static path registration for %s",
            CARD_URL_PATH,
        )
        return True

    hass.http.register_static_path(
        StaticPathConfig(CARD_URL_PATH, str(CARD_RESOURCE_PATH), True)
    )
    return True


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
