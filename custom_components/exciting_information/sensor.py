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

METRIC_TEXTS = {
    "de": {
        "earth_rounds": (
            "Das entspricht etwa {value:.3f} Erdumrundungen (≈ {distance_km:.0f} km)."
        ),
        "coffee_cups": (
            "Das entspricht etwa {value:.0f} Kaffee(n) bei {coffee_kwh:.2f} kWh pro Kaffee."
        ),
        "fuel_saved_liters": (
            "Das entspricht einer Benzinersparnis von {value:.1f} l bei "
            "{fuel_l_per_100km:.1f} l/100 km."
        ),
        "lisbon_berlin_trips": (
            "Das entspricht {value:.2f} Fahrten Lissabon–Berlin (≈ {distance_km:.0f} km)."
        ),
        "nyc_mexico_trips": (
            "Das entspricht {value:.2f} Fahrten New York–Mexiko-Stadt (≈ {distance_km:.0f} km)."
        ),
    },
    "en": {
        "earth_rounds": (
            "That equals about {value:.3f} trips around Earth (≈ {distance_km:.0f} km)."
        ),
        "coffee_cups": (
            "That equals about {value:.0f} coffees at {coffee_kwh:.2f} kWh per coffee."
        ),
        "fuel_saved_liters": (
            "That equals fuel savings of {value:.1f} L at {fuel_l_per_100km:.1f} L/100 km."
        ),
        "lisbon_berlin_trips": (
            "That equals {value:.2f} Lisbon–Berlin trips (≈ {distance_km:.0f} km)."
        ),
        "nyc_mexico_trips": (
            "That equals {value:.2f} New York–Mexico City trips (≈ {distance_km:.0f} km)."
        ),
    },
    "fr": {
        "earth_rounds": (
            "Cela correspond à environ {value:.3f} tours de la Terre (≈ {distance_km:.0f} km)."
        ),
        "coffee_cups": (
            "Cela correspond à environ {value:.0f} cafés à {coffee_kwh:.2f} kWh par café."
        ),
        "fuel_saved_liters": (
            "Cela correspond à une économie d’essence de {value:.1f} L à "
            "{fuel_l_per_100km:.1f} L/100 km."
        ),
        "lisbon_berlin_trips": (
            "Cela correspond à {value:.2f} trajets Lisbonne–Berlin (≈ {distance_km:.0f} km)."
        ),
        "nyc_mexico_trips": (
            "Cela correspond à {value:.2f} trajets New York–Mexico (≈ {distance_km:.0f} km)."
        ),
    },
    "it": {
        "earth_rounds": (
            "Equivale a circa {value:.3f} giri della Terra (≈ {distance_km:.0f} km)."
        ),
        "coffee_cups": (
            "Equivale a circa {value:.0f} caffè a {coffee_kwh:.2f} kWh per caffè."
        ),
        "fuel_saved_liters": (
            "Equivale a un risparmio di benzina di {value:.1f} L a "
            "{fuel_l_per_100km:.1f} L/100 km."
        ),
        "lisbon_berlin_trips": (
            "Equivale a {value:.2f} viaggi Lisbona–Berlino (≈ {distance_km:.0f} km)."
        ),
        "nyc_mexico_trips": (
            "Equivale a {value:.2f} viaggi New York–Città del Messico (≈ {distance_km:.0f} km)."
        ),
    },
    "es": {
        "earth_rounds": (
            "Eso equivale a unas {value:.3f} vueltas a la Tierra (≈ {distance_km:.0f} km)."
        ),
        "coffee_cups": (
            "Eso equivale a unos {value:.0f} cafés a {coffee_kwh:.2f} kWh por café."
        ),
        "fuel_saved_liters": (
            "Eso equivale a un ahorro de gasolina de {value:.1f} L a "
            "{fuel_l_per_100km:.1f} L/100 km."
        ),
        "lisbon_berlin_trips": (
            "Eso equivale a {value:.2f} viajes Lisboa–Berlín (≈ {distance_km:.0f} km)."
        ),
        "nyc_mexico_trips": (
            "Eso equivale a {value:.2f} viajes Nueva York–Ciudad de México (≈ {distance_km:.0f} km)."
        ),
    },
}

SOURCE_LABELS = {
    "de": {"energy": "Solarenergie", "power": "Solarleistung (1 h)"},
    "en": {"energy": "solar energy", "power": "solar power (1 h)"},
    "fr": {"energy": "énergie solaire", "power": "puissance solaire (1 h)"},
    "it": {"energy": "energia solare", "power": "potenza solare (1 h)"},
    "es": {"energy": "energía solar", "power": "potencia solar (1 h)"},
}

EARTH_CIRCUMFERENCE_KM = 40075.0
LISBON_BERLIN_KM = 2310.0
NEW_YORK_MEXICO_CITY_KM = 3360.0
COFFEE_KWH = 0.07
FUEL_L_PER_100KM = 7.0


@dataclass(frozen=True)
class SolarDistanceSensorDescription(SensorEntityDescription):
    """Describes the solar distance sensor."""


@dataclass(frozen=True)
class SolarMetrics:
    """Calculated solar metrics."""

    pv_kwh: float
    source_key: str
    distance_value: float
    message: str
    earth_rounds: float
    coffee_cups: float
    fuel_saved_liters: float
    lisbon_berlin_trips: float
    nyc_mexico_trips: float
    texts: dict[str, str]


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
    message_description = SolarDistanceSensorDescription(
        key="message",
        translation_key="message",
        icon="mdi:message-text",
    )
    earth_rounds_description = SolarDistanceSensorDescription(
        key="earth_rounds",
        translation_key="earth_rounds",
        icon="mdi:earth",
    )
    coffee_description = SolarDistanceSensorDescription(
        key="coffee_cups",
        translation_key="coffee_cups",
        icon="mdi:coffee",
        native_unit_of_measurement="cups",
    )
    fuel_description = SolarDistanceSensorDescription(
        key="fuel_saved_liters",
        translation_key="fuel_saved_liters",
        icon="mdi:gas-station",
        native_unit_of_measurement="L",
    )
    lisbon_berlin_description = SolarDistanceSensorDescription(
        key="lisbon_berlin_trips",
        translation_key="lisbon_berlin_trips",
        icon="mdi:car",
        native_unit_of_measurement="trips",
    )
    nyc_mexico_description = SolarDistanceSensorDescription(
        key="nyc_mexico_trips",
        translation_key="nyc_mexico_trips",
        icon="mdi:car",
        native_unit_of_measurement="trips",
    )
    async_add_entities(
        [
            SolarDistanceSensor(hass, entry, description),
            SolarMessageSensor(hass, entry, message_description),
            SolarEarthRoundsSensor(hass, entry, earth_rounds_description),
            SolarCoffeeSensor(hass, entry, coffee_description),
            SolarFuelSavedSensor(hass, entry, fuel_description),
            SolarLisbonBerlinTripsSensor(hass, entry, lisbon_berlin_description),
            SolarNycMexicoTripsSensor(hass, entry, nyc_mexico_description),
        ]
    )


class SolarInfoSensor(SensorEntity):
    """Base class for solar information sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        self.entity_description = description
        self._entry = entry
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
        if state is None or state.state in ("unknown", "unavailable"):
            self._set_unavailable()
            return

        try:
            pv_value = float(state.state)
        except ValueError:
            self._set_unavailable()
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

        template = MESSAGE_TEMPLATES.get(self._language, MESSAGE_TEMPLATES["en"])
        metric_texts = METRIC_TEXTS.get(self._language, METRIC_TEXTS["en"])
        source_label = SOURCE_LABELS.get(self._language, SOURCE_LABELS["en"])[source_key]
        distance = (pv_kwh / self._consumption) * 100
        distance_value = round(distance, 2)
        message = template.format(
            consumption=self._consumption,
            distance=distance_value,
            source=source_label,
        )
        earth_rounds = round(distance_value / EARTH_CIRCUMFERENCE_KM, 3)
        coffee_cups = round(pv_kwh / COFFEE_KWH, 1)
        fuel_saved_liters = round(distance_value * FUEL_L_PER_100KM / 100, 1)
        lisbon_berlin_trips = round(distance_value / LISBON_BERLIN_KM, 2)
        nyc_mexico_trips = round(distance_value / NEW_YORK_MEXICO_CITY_KM, 2)
        texts = {
            "earth_rounds": metric_texts["earth_rounds"].format(
                value=earth_rounds,
                distance_km=EARTH_CIRCUMFERENCE_KM,
            ),
            "coffee_cups": metric_texts["coffee_cups"].format(
                value=coffee_cups,
                coffee_kwh=COFFEE_KWH,
            ),
            "fuel_saved_liters": metric_texts["fuel_saved_liters"].format(
                value=fuel_saved_liters,
                fuel_l_per_100km=FUEL_L_PER_100KM,
            ),
            "lisbon_berlin_trips": metric_texts["lisbon_berlin_trips"].format(
                value=lisbon_berlin_trips,
                distance_km=LISBON_BERLIN_KM,
            ),
            "nyc_mexico_trips": metric_texts["nyc_mexico_trips"].format(
                value=nyc_mexico_trips,
                distance_km=NEW_YORK_MEXICO_CITY_KM,
            ),
        }
        metrics = SolarMetrics(
            pv_kwh=pv_kwh,
            source_key=source_key,
            distance_value=distance_value,
            message=message,
            earth_rounds=earth_rounds,
            coffee_cups=coffee_cups,
            fuel_saved_liters=fuel_saved_liters,
            lisbon_berlin_trips=lisbon_berlin_trips,
            nyc_mexico_trips=nyc_mexico_trips,
            texts=texts,
        )
        self._set_from_metrics(metrics)

    def _set_unavailable(self) -> None:
        self._attr_available = False
        self._attr_native_value = None
        self._attr_extra_state_attributes = {
            "pv_entity_id": self._pv_entity_id,
            "consumption_kwh_per_100km": self._consumption,
        }

    def _build_base_attributes(self, metrics: SolarMetrics) -> dict[str, Any]:
        return {
            "pv_entity_id": self._pv_entity_id,
            "consumption_kwh_per_100km": self._consumption,
            "calculated_at": dt_util.utcnow().isoformat(),
            "pv_energy_kwh": round(metrics.pv_kwh, 3),
            "pv_source": metrics.source_key,
        }

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        raise NotImplementedError


class SolarDistanceSensor(SolarInfoSensor):
    """Calculate how far an EV could drive from solar energy."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(hass, entry, description)
        self._attr_unique_id = f"{entry.entry_id}_distance"

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        self._attr_native_value = metrics.distance_value
        self._attr_available = True
        self._attr_extra_state_attributes = {
            **self._build_base_attributes(metrics),
            "earth_rounds": metrics.earth_rounds,
            "coffee_cups": metrics.coffee_cups,
            "fuel_saved_liters": metrics.fuel_saved_liters,
            "lisbon_berlin_trips": metrics.lisbon_berlin_trips,
            "nyc_mexico_trips": metrics.nyc_mexico_trips,
            "assumptions": {
                "earth_circumference_km": EARTH_CIRCUMFERENCE_KM,
                "lisbon_berlin_km": LISBON_BERLIN_KM,
                "new_york_mexico_city_km": NEW_YORK_MEXICO_CITY_KM,
                "coffee_kwh": COFFEE_KWH,
                "fuel_l_per_100km": FUEL_L_PER_100KM,
            },
        }


class SolarMessageSensor(SolarInfoSensor):
    """Expose the driving range message as its own entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(hass, entry, description)
        self._attr_unique_id = f"{entry.entry_id}_message"

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        self._attr_native_value = metrics.message
        self._attr_available = True
        self._attr_extra_state_attributes = self._build_base_attributes(metrics)


class SolarEarthRoundsSensor(SolarInfoSensor):
    """Expose the earth-rounds metric as its own entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(hass, entry, description)
        self._attr_unique_id = f"{entry.entry_id}_earth_rounds"

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        self._attr_native_value = metrics.earth_rounds
        self._attr_available = True
        self._attr_extra_state_attributes = {
            **self._build_base_attributes(metrics),
            "text": metrics.texts["earth_rounds"],
        }


class SolarCoffeeSensor(SolarInfoSensor):
    """Expose the coffee cups metric as its own entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(hass, entry, description)
        self._attr_unique_id = f"{entry.entry_id}_coffee_cups"

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        self._attr_native_value = metrics.coffee_cups
        self._attr_available = True
        self._attr_extra_state_attributes = {
            **self._build_base_attributes(metrics),
            "text": metrics.texts["coffee_cups"],
        }


class SolarFuelSavedSensor(SolarInfoSensor):
    """Expose the fuel saved metric as its own entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(hass, entry, description)
        self._attr_unique_id = f"{entry.entry_id}_fuel_saved_liters"

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        self._attr_native_value = metrics.fuel_saved_liters
        self._attr_available = True
        self._attr_extra_state_attributes = {
            **self._build_base_attributes(metrics),
            "text": metrics.texts["fuel_saved_liters"],
        }


class SolarLisbonBerlinTripsSensor(SolarInfoSensor):
    """Expose the Lisbon–Berlin trips metric as its own entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(hass, entry, description)
        self._attr_unique_id = f"{entry.entry_id}_lisbon_berlin_trips"

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        self._attr_native_value = metrics.lisbon_berlin_trips
        self._attr_available = True
        self._attr_extra_state_attributes = {
            **self._build_base_attributes(metrics),
            "text": metrics.texts["lisbon_berlin_trips"],
        }


class SolarNycMexicoTripsSensor(SolarInfoSensor):
    """Expose the New York–Mexico City trips metric as its own entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(hass, entry, description)
        self._attr_unique_id = f"{entry.entry_id}_nyc_mexico_trips"

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        self._attr_native_value = metrics.nyc_mexico_trips
        self._attr_available = True
        self._attr_extra_state_attributes = {
            **self._build_base_attributes(metrics),
            "text": metrics.texts["nyc_mexico_trips"],
        }
