"""Sensor platform for Exciting Information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import CONF_CONSUMPTION, CONF_PV_ENTITY_ID, DOMAIN

MESSAGE_TEMPLATES = {
    "de": (
        "Mit deiner aktuellen Solarenergie könntest du bei einem Verbrauch von {consumption:.1f} "
        "kWh/100 km etwa {distance:.1f} km fahren (z. B. Berlin–München)."
    ),
    "en": (
        "With your current solar energy you could drive about {distance:.1f} km at a "
        "consumption of {consumption:.1f} kWh/100 km (e.g. Berlin–Munich)."
    ),
    "fr": (
        "Avec votre énergie solaire actuelle, vous pourriez parcourir environ {distance:.1f} km "
        "pour une consommation de {consumption:.1f} kWh/100 km (par ex. Berlin–Munich)."
    ),
    "it": (
        "Con la tua energia solare attuale potresti percorrere circa {distance:.1f} km con un "
        "consumo di {consumption:.1f} kWh/100 km (ad es. Berlino–Monaco)."
    ),
    "es": (
        "Con tu energía solar actual podrías recorrer aproximadamente {distance:.1f} km con un "
        "consumo de {consumption:.1f} kWh/100 km (p. ej., Berlín–Múnich)."
    ),
}


@dataclass(frozen=True)
class SolarDistanceSensorDescription(SensorEntityDescription):
    """Describes the solar distance sensor."""


def _get_language(hass: HomeAssistant) -> str:
    language = hass.config.language or "en"
    return language.split("-")[0]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Exciting Information sensors."""
    description = SolarDistanceSensorDescription(
        key="distance",
        translation_key="distance",
        icon="mdi:car-electric",
        native_unit_of_measurement="km",
    )
    async_add_entities([SolarDistanceSensor(hass, entry, description)])


class SolarDistanceSensor(SensorEntity):
    """Calculate how far an EV could drive from solar energy."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_distance"
        self._attr_extra_state_attributes: dict[str, Any] = {}
        self._attr_available = False
        self._pv_entity_id = entry.options.get(CONF_PV_ENTITY_ID, entry.data[CONF_PV_ENTITY_ID])
        self._consumption = entry.options.get(CONF_CONSUMPTION, entry.data[CONF_CONSUMPTION])
        self._language = _get_language(hass)
        self._unsub = None
        self._hass = hass

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self._unsub = async_track_state_change_event(
            self._hass,
            [self._pv_entity_id],
            self._handle_state_change,
        )
        self._update_from_state()

    async def async_will_remove_from_hass(self) -> None:
        """Remove callbacks."""
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _handle_state_change(self, event: Event) -> None:
        self._update_from_state()
        self.async_write_ha_state()

    def _update_from_state(self) -> None:
        state = self._hass.states.get(self._pv_entity_id)
        self._attr_available = False
        if state is None or state.state in ("unknown", "unavailable"):
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "pv_entity_id": self._pv_entity_id,
                "consumption_kwh_per_100km": self._consumption,
            }
            return

        try:
            pv_kw = float(state.state)
        except ValueError:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "pv_entity_id": self._pv_entity_id,
                "consumption_kwh_per_100km": self._consumption,
            }
            return

        distance = (pv_kw / self._consumption) * 100
        self._attr_native_value = round(distance, 2)
        self._attr_available = True
        template = MESSAGE_TEMPLATES.get(self._language, MESSAGE_TEMPLATES["en"])
        message = template.format(consumption=self._consumption, distance=distance)
        self._attr_extra_state_attributes = {
            "pv_entity_id": self._pv_entity_id,
            "consumption_kwh_per_100km": self._consumption,
            "message": message,
            "calculated_at": dt_util.utcnow().isoformat(),
        }
