"""Sensor platform for Exciting Information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, UnitOfEnergy, UnitOfPower
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import EnergyConverter, PowerConverter

from .const import CONF_CONSUMPTION, CONF_PV_ENTITY_ID, DOMAIN

MESSAGE_TEMPLATES = {
    "de": (
        "Mit deiner aktuellen {source} könntest du bei einem Verbrauch von {consumption:.1f} "
        "kWh/100 km etwa {distance:.1f} km fahren."
    ),
    "en": (
        "With your current {source} you could drive about {distance:.1f} km at a "
        "consumption of {consumption:.1f} kWh/100 km."
    ),
    "fr": (
        "Avec votre {source} actuelle, vous pourriez parcourir environ {distance:.1f} km pour "
        "une consommation de {consumption:.1f} kWh/100 km."
    ),
    "it": (
        "Con la tua {source} attuale potresti percorrere circa {distance:.1f} km con un consumo "
        "di {consumption:.1f} kWh/100 km."
    ),
    "es": (
        "Con tu {source} actual podrías recorrer aproximadamente {distance:.1f} km con un "
        "consumo de {consumption:.1f} kWh/100 km."
    ),
}

SOURCE_LABELS = {
    "de": {"energy": "Solarenergie", "power": "Solarleistung (1 h)"},
    "en": {"energy": "solar energy", "power": "solar power (1 h)"},
    "fr": {"energy": "énergie solaire", "power": "puissance solaire (1 h)"},
    "it": {"energy": "energia solare", "power": "potenza solare (1 h)"},
    "es": {"energy": "energía solar", "power": "potencia solar (1 h)"},
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
            pv_value = float(state.state)
        except ValueError:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "pv_entity_id": self._pv_entity_id,
                "consumption_kwh_per_100km": self._consumption,
            }
            return

        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        pv_kwh = None
        source_key = "power"

        if unit in (UnitOfEnergy.KILO_WATT_HOUR, UnitOfEnergy.WATT_HOUR):
            pv_kwh = EnergyConverter.convert(pv_value, unit, UnitOfEnergy.KILO_WATT_HOUR)
            source_key = "energy"
        elif unit in (UnitOfPower.KILO_WATT, UnitOfPower.WATT):
            pv_kw = PowerConverter.convert(pv_value, unit, UnitOfPower.KILO_WATT)
            pv_kwh = pv_kw
            source_key = "power"
        else:
            pv_kwh = pv_value
            source_key = "power"

        distance = (pv_kwh / self._consumption) * 100
        distance_value = round(distance, 2)
        self._attr_native_value = distance_value
        self._attr_available = True
        template = MESSAGE_TEMPLATES.get(self._language, MESSAGE_TEMPLATES["en"])
        source_label = SOURCE_LABELS.get(self._language, SOURCE_LABELS["en"])[source_key]
        message = template.format(
            consumption=self._consumption,
            distance=distance_value,
            source=source_label,
        )
        self._attr_extra_state_attributes = {
            "pv_entity_id": self._pv_entity_id,
            "consumption_kwh_per_100km": self._consumption,
            "message": message,
            "calculated_at": dt_util.utcnow().isoformat(),
            "pv_energy_kwh": round(pv_kwh, 3),
            "pv_source": source_key,
        }
