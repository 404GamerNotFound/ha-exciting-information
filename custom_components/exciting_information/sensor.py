"""Sensor platform for PV Exciting Information."""

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
        "marathon_equivalents": (
            "Das entspricht etwa {value:.2f} Marathons (≈ {distance_km:.1f} km)."
        ),
        "berlin_hamburg_trips": (
            "Das entspricht {value:.2f} Fahrten Berlin–Hamburg (≈ {distance_km:.0f} km)."
        ),
        "munich_hamburg_trips": (
            "Das entspricht {value:.2f} Fahrten München–Hamburg (≈ {distance_km:.0f} km)."
        ),
        "paris_lyon_trips": (
            "Das entspricht {value:.2f} Fahrten Paris–Lyon (≈ {distance_km:.0f} km)."
        ),
        "london_edinburgh_trips": (
            "Das entspricht {value:.2f} Fahrten London–Edinburgh (≈ {distance_km:.0f} km)."
        ),
        "rome_milan_trips": (
            "Das entspricht {value:.2f} Fahrten Rom–Mailand (≈ {distance_km:.0f} km)."
        ),
        "madrid_barcelona_trips": (
            "Das entspricht {value:.2f} Fahrten Madrid–Barcelona (≈ {distance_km:.0f} km)."
        ),
        "vienna_prague_trips": (
            "Das entspricht {value:.2f} Fahrten Wien–Prag (≈ {distance_km:.0f} km)."
        ),
        "la_sf_trips": (
            "Das entspricht {value:.2f} Fahrten Los Angeles–San Francisco (≈ {distance_km:.0f} km)."
        ),
        "tokyo_osaka_trips": (
            "Das entspricht {value:.2f} Fahrten Tokio–Osaka (≈ {distance_km:.0f} km)."
        ),
        "phone_charges": (
            "Das entspricht etwa {value:.0f} Handy-Ladungen bei {energy_kwh:.3f} kWh pro Ladung."
        ),
        "laptop_charges": (
            "Das entspricht etwa {value:.0f} Laptop-Ladungen bei {energy_kwh:.2f} kWh pro Ladung."
        ),
        "led_bulb_hours": (
            "Das entspricht etwa {value:.0f} Stunden LED-Licht bei {energy_kwh:.2f} kWh pro Stunde."
        ),
        "tv_hours": (
            "Das entspricht etwa {value:.0f} TV-Stunden bei {energy_kwh:.2f} kWh pro Stunde."
        ),
        "fridge_days": (
            "Das entspricht etwa {value:.1f} Kühlschrank-Tagen bei {energy_kwh:.1f} kWh pro Tag."
        ),
        "washing_cycles": (
            "Das entspricht etwa {value:.1f} Waschzyklen bei {energy_kwh:.1f} kWh pro Waschgang."
        ),
        "dishwasher_cycles": (
            "Das entspricht etwa {value:.1f} Spülmaschinenzyklen bei {energy_kwh:.1f} kWh pro Lauf."
        ),
        "hot_showers": (
            "Das entspricht etwa {value:.1f} warmen Duschen bei {energy_kwh:.1f} kWh pro Dusche."
        ),
        "microwave_meals": (
            "Das entspricht etwa {value:.0f} Mikrowellen-Mahlzeiten bei {energy_kwh:.2f} kWh pro Mahlzeit."
        ),
        "kettle_boils": (
            "Das entspricht etwa {value:.0f} Wasserkocher-Vorgängen bei {energy_kwh:.2f} kWh pro Vorgang."
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
        "marathon_equivalents": (
            "That equals about {value:.2f} marathons (≈ {distance_km:.1f} km)."
        ),
        "berlin_hamburg_trips": (
            "That equals {value:.2f} Berlin–Hamburg trips (≈ {distance_km:.0f} km)."
        ),
        "munich_hamburg_trips": (
            "That equals {value:.2f} Munich–Hamburg trips (≈ {distance_km:.0f} km)."
        ),
        "paris_lyon_trips": (
            "That equals {value:.2f} Paris–Lyon trips (≈ {distance_km:.0f} km)."
        ),
        "london_edinburgh_trips": (
            "That equals {value:.2f} London–Edinburgh trips (≈ {distance_km:.0f} km)."
        ),
        "rome_milan_trips": (
            "That equals {value:.2f} Rome–Milan trips (≈ {distance_km:.0f} km)."
        ),
        "madrid_barcelona_trips": (
            "That equals {value:.2f} Madrid–Barcelona trips (≈ {distance_km:.0f} km)."
        ),
        "vienna_prague_trips": (
            "That equals {value:.2f} Vienna–Prague trips (≈ {distance_km:.0f} km)."
        ),
        "la_sf_trips": (
            "That equals {value:.2f} Los Angeles–San Francisco trips (≈ {distance_km:.0f} km)."
        ),
        "tokyo_osaka_trips": (
            "That equals {value:.2f} Tokyo–Osaka trips (≈ {distance_km:.0f} km)."
        ),
        "phone_charges": (
            "That equals about {value:.0f} phone charges at {energy_kwh:.3f} kWh per charge."
        ),
        "laptop_charges": (
            "That equals about {value:.0f} laptop charges at {energy_kwh:.2f} kWh per charge."
        ),
        "led_bulb_hours": (
            "That equals about {value:.0f} LED bulb hours at {energy_kwh:.2f} kWh per hour."
        ),
        "tv_hours": (
            "That equals about {value:.0f} TV hours at {energy_kwh:.2f} kWh per hour."
        ),
        "fridge_days": (
            "That equals about {value:.1f} fridge days at {energy_kwh:.1f} kWh per day."
        ),
        "washing_cycles": (
            "That equals about {value:.1f} washing cycles at {energy_kwh:.1f} kWh per cycle."
        ),
        "dishwasher_cycles": (
            "That equals about {value:.1f} dishwasher cycles at {energy_kwh:.1f} kWh per cycle."
        ),
        "hot_showers": (
            "That equals about {value:.1f} hot showers at {energy_kwh:.1f} kWh per shower."
        ),
        "microwave_meals": (
            "That equals about {value:.0f} microwave meals at {energy_kwh:.2f} kWh per meal."
        ),
        "kettle_boils": (
            "That equals about {value:.0f} kettle boils at {energy_kwh:.2f} kWh per boil."
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
        "marathon_equivalents": (
            "Cela correspond à environ {value:.2f} marathons (≈ {distance_km:.1f} km)."
        ),
        "berlin_hamburg_trips": (
            "Cela correspond à {value:.2f} trajets Berlin–Hambourg (≈ {distance_km:.0f} km)."
        ),
        "munich_hamburg_trips": (
            "Cela correspond à {value:.2f} trajets Munich–Hambourg (≈ {distance_km:.0f} km)."
        ),
        "paris_lyon_trips": (
            "Cela correspond à {value:.2f} trajets Paris–Lyon (≈ {distance_km:.0f} km)."
        ),
        "london_edinburgh_trips": (
            "Cela correspond à {value:.2f} trajets Londres–Édimbourg (≈ {distance_km:.0f} km)."
        ),
        "rome_milan_trips": (
            "Cela correspond à {value:.2f} trajets Rome–Milan (≈ {distance_km:.0f} km)."
        ),
        "madrid_barcelona_trips": (
            "Cela correspond à {value:.2f} trajets Madrid–Barcelone (≈ {distance_km:.0f} km)."
        ),
        "vienna_prague_trips": (
            "Cela correspond à {value:.2f} trajets Vienne–Prague (≈ {distance_km:.0f} km)."
        ),
        "la_sf_trips": (
            "Cela correspond à {value:.2f} trajets Los Angeles–San Francisco (≈ {distance_km:.0f} km)."
        ),
        "tokyo_osaka_trips": (
            "Cela correspond à {value:.2f} trajets Tokyo–Osaka (≈ {distance_km:.0f} km)."
        ),
        "phone_charges": (
            "Cela correspond à environ {value:.0f} charges de téléphone à {energy_kwh:.3f} kWh par charge."
        ),
        "laptop_charges": (
            "Cela correspond à environ {value:.0f} charges d’ordinateur portable à {energy_kwh:.2f} kWh par charge."
        ),
        "led_bulb_hours": (
            "Cela correspond à environ {value:.0f} heures de LED à {energy_kwh:.2f} kWh par heure."
        ),
        "tv_hours": (
            "Cela correspond à environ {value:.0f} heures de TV à {energy_kwh:.2f} kWh par heure."
        ),
        "fridge_days": (
            "Cela correspond à environ {value:.1f} jours de réfrigérateur à {energy_kwh:.1f} kWh par jour."
        ),
        "washing_cycles": (
            "Cela correspond à environ {value:.1f} cycles de lavage à {energy_kwh:.1f} kWh par cycle."
        ),
        "dishwasher_cycles": (
            "Cela correspond à environ {value:.1f} cycles de lave-vaisselle à {energy_kwh:.1f} kWh par cycle."
        ),
        "hot_showers": (
            "Cela correspond à environ {value:.1f} douches chaudes à {energy_kwh:.1f} kWh par douche."
        ),
        "microwave_meals": (
            "Cela correspond à environ {value:.0f} repas au micro-ondes à {energy_kwh:.2f} kWh par repas."
        ),
        "kettle_boils": (
            "Cela correspond à environ {value:.0f} bouilloires à {energy_kwh:.2f} kWh par ébullition."
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
        "marathon_equivalents": (
            "Equivale a circa {value:.2f} maratone (≈ {distance_km:.1f} km)."
        ),
        "berlin_hamburg_trips": (
            "Equivale a {value:.2f} viaggi Berlino–Amburgo (≈ {distance_km:.0f} km)."
        ),
        "munich_hamburg_trips": (
            "Equivale a {value:.2f} viaggi Monaco–Amburgo (≈ {distance_km:.0f} km)."
        ),
        "paris_lyon_trips": (
            "Equivale a {value:.2f} viaggi Parigi–Lione (≈ {distance_km:.0f} km)."
        ),
        "london_edinburgh_trips": (
            "Equivale a {value:.2f} viaggi Londra–Edimburgo (≈ {distance_km:.0f} km)."
        ),
        "rome_milan_trips": (
            "Equivale a {value:.2f} viaggi Roma–Milano (≈ {distance_km:.0f} km)."
        ),
        "madrid_barcelona_trips": (
            "Equivale a {value:.2f} viaggi Madrid–Barcellona (≈ {distance_km:.0f} km)."
        ),
        "vienna_prague_trips": (
            "Equivale a {value:.2f} viaggi Vienna–Praga (≈ {distance_km:.0f} km)."
        ),
        "la_sf_trips": (
            "Equivale a {value:.2f} viaggi Los Angeles–San Francisco (≈ {distance_km:.0f} km)."
        ),
        "tokyo_osaka_trips": (
            "Equivale a {value:.2f} viaggi Tokyo–Osaka (≈ {distance_km:.0f} km)."
        ),
        "phone_charges": (
            "Equivale a circa {value:.0f} ricariche del telefono a {energy_kwh:.3f} kWh per ricarica."
        ),
        "laptop_charges": (
            "Equivale a circa {value:.0f} ricariche del portatile a {energy_kwh:.2f} kWh per ricarica."
        ),
        "led_bulb_hours": (
            "Equivale a circa {value:.0f} ore di lampadina LED a {energy_kwh:.2f} kWh per ora."
        ),
        "tv_hours": (
            "Equivale a circa {value:.0f} ore di TV a {energy_kwh:.2f} kWh per ora."
        ),
        "fridge_days": (
            "Equivale a circa {value:.1f} giorni di frigorifero a {energy_kwh:.1f} kWh al giorno."
        ),
        "washing_cycles": (
            "Equivale a circa {value:.1f} cicli di lavaggio a {energy_kwh:.1f} kWh per ciclo."
        ),
        "dishwasher_cycles": (
            "Equivale a circa {value:.1f} cicli di lavastoviglie a {energy_kwh:.1f} kWh per ciclo."
        ),
        "hot_showers": (
            "Equivale a circa {value:.1f} docce calde a {energy_kwh:.1f} kWh per doccia."
        ),
        "microwave_meals": (
            "Equivale a circa {value:.0f} pasti al microonde a {energy_kwh:.2f} kWh per pasto."
        ),
        "kettle_boils": (
            "Equivale a circa {value:.0f} bolliture del bollitore a {energy_kwh:.2f} kWh per bollitura."
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
        "marathon_equivalents": (
            "Eso equivale a unas {value:.2f} maratones (≈ {distance_km:.1f} km)."
        ),
        "berlin_hamburg_trips": (
            "Eso equivale a {value:.2f} viajes Berlín–Hamburgo (≈ {distance_km:.0f} km)."
        ),
        "munich_hamburg_trips": (
            "Eso equivale a {value:.2f} viajes Múnich–Hamburgo (≈ {distance_km:.0f} km)."
        ),
        "paris_lyon_trips": (
            "Eso equivale a {value:.2f} viajes París–Lyon (≈ {distance_km:.0f} km)."
        ),
        "london_edinburgh_trips": (
            "Eso equivale a {value:.2f} viajes Londres–Edimburgo (≈ {distance_km:.0f} km)."
        ),
        "rome_milan_trips": (
            "Eso equivale a {value:.2f} viajes Roma–Milán (≈ {distance_km:.0f} km)."
        ),
        "madrid_barcelona_trips": (
            "Eso equivale a {value:.2f} viajes Madrid–Barcelona (≈ {distance_km:.0f} km)."
        ),
        "vienna_prague_trips": (
            "Eso equivale a {value:.2f} viajes Viena–Praga (≈ {distance_km:.0f} km)."
        ),
        "la_sf_trips": (
            "Eso equivale a {value:.2f} viajes Los Ángeles–San Francisco (≈ {distance_km:.0f} km)."
        ),
        "tokyo_osaka_trips": (
            "Eso equivale a {value:.2f} viajes Tokio–Osaka (≈ {distance_km:.0f} km)."
        ),
        "phone_charges": (
            "Eso equivale a unas {value:.0f} cargas de teléfono a {energy_kwh:.3f} kWh por carga."
        ),
        "laptop_charges": (
            "Eso equivale a unas {value:.0f} cargas de portátil a {energy_kwh:.2f} kWh por carga."
        ),
        "led_bulb_hours": (
            "Eso equivale a unas {value:.0f} horas de bombilla LED a {energy_kwh:.2f} kWh por hora."
        ),
        "tv_hours": (
            "Eso equivale a unas {value:.0f} horas de TV a {energy_kwh:.2f} kWh por hora."
        ),
        "fridge_days": (
            "Eso equivale a unos {value:.1f} días de frigorífico a {energy_kwh:.1f} kWh por día."
        ),
        "washing_cycles": (
            "Eso equivale a unos {value:.1f} ciclos de lavado a {energy_kwh:.1f} kWh por ciclo."
        ),
        "dishwasher_cycles": (
            "Eso equivale a unos {value:.1f} ciclos de lavavajillas a {energy_kwh:.1f} kWh por ciclo."
        ),
        "hot_showers": (
            "Eso equivale a unas {value:.1f} duchas calientes a {energy_kwh:.1f} kWh por ducha."
        ),
        "microwave_meals": (
            "Eso equivale a unas {value:.0f} comidas de microondas a {energy_kwh:.2f} kWh por comida."
        ),
        "kettle_boils": (
            "Eso equivale a unas {value:.0f} hervidas de hervidor a {energy_kwh:.2f} kWh por hervida."
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

EARTH_CIRCUMFERENCE_KM = 39100.0
LISBON_BERLIN_KM = 2310.0
NEW_YORK_MEXICO_CITY_KM = 3360.0
MARATHON_KM = 42.195
BERLIN_HAMBURG_KM = 289.0
MUNICH_HAMBURG_KM = 776.0
PARIS_LYON_KM = 465.0
LONDON_EDINBURGH_KM = 534.0
ROME_MILAN_KM = 571.0
MADRID_BARCELONA_KM = 621.0
VIENNA_PRAGUE_KM = 333.0
LA_SF_KM = 615.0
TOKYO_OSAKA_KM = 515.0
COFFEE_KWH = 0.07
PHONE_CHARGE_KWH = 0.012
LAPTOP_CHARGE_KWH = 0.06
LED_BULB_KWH_PER_HOUR = 0.01
TV_KWH_PER_HOUR = 0.1
FRIDGE_KWH_PER_DAY = 1.5
WASHING_CYCLE_KWH = 1.0
DISHWASHER_CYCLE_KWH = 1.2
HOT_SHOWER_KWH = 4.5
MICROWAVE_MEAL_KWH = 0.1
KETTLE_BOIL_KWH = 0.11
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
    metric_values: dict[str, float]
    texts: dict[str, str]


def _get_language(hass: HomeAssistant) -> str:
    language = hass.config.language or "en"
    return language.split("-")[0]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up PV Exciting Information sensors."""
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
    metric_descriptions = [
        SolarDistanceSensorDescription(
            key="marathon_equivalents",
            translation_key="marathon_equivalents",
            icon="mdi:run",
            native_unit_of_measurement="marathons",
        ),
        SolarDistanceSensorDescription(
            key="berlin_hamburg_trips",
            translation_key="berlin_hamburg_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="munich_hamburg_trips",
            translation_key="munich_hamburg_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="paris_lyon_trips",
            translation_key="paris_lyon_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="london_edinburgh_trips",
            translation_key="london_edinburgh_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="rome_milan_trips",
            translation_key="rome_milan_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="madrid_barcelona_trips",
            translation_key="madrid_barcelona_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="vienna_prague_trips",
            translation_key="vienna_prague_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="la_sf_trips",
            translation_key="la_sf_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="tokyo_osaka_trips",
            translation_key="tokyo_osaka_trips",
            icon="mdi:car",
            native_unit_of_measurement="trips",
        ),
        SolarDistanceSensorDescription(
            key="phone_charges",
            translation_key="phone_charges",
            icon="mdi:cellphone",
            native_unit_of_measurement="charges",
        ),
        SolarDistanceSensorDescription(
            key="laptop_charges",
            translation_key="laptop_charges",
            icon="mdi:laptop",
            native_unit_of_measurement="charges",
        ),
        SolarDistanceSensorDescription(
            key="led_bulb_hours",
            translation_key="led_bulb_hours",
            icon="mdi:lightbulb-outline",
            native_unit_of_measurement="hours",
        ),
        SolarDistanceSensorDescription(
            key="tv_hours",
            translation_key="tv_hours",
            icon="mdi:television",
            native_unit_of_measurement="hours",
        ),
        SolarDistanceSensorDescription(
            key="fridge_days",
            translation_key="fridge_days",
            icon="mdi:fridge",
            native_unit_of_measurement="days",
        ),
        SolarDistanceSensorDescription(
            key="washing_cycles",
            translation_key="washing_cycles",
            icon="mdi:washing-machine",
            native_unit_of_measurement="cycles",
        ),
        SolarDistanceSensorDescription(
            key="dishwasher_cycles",
            translation_key="dishwasher_cycles",
            icon="mdi:dishwasher",
            native_unit_of_measurement="cycles",
        ),
        SolarDistanceSensorDescription(
            key="hot_showers",
            translation_key="hot_showers",
            icon="mdi:shower",
            native_unit_of_measurement="showers",
        ),
        SolarDistanceSensorDescription(
            key="microwave_meals",
            translation_key="microwave_meals",
            icon="mdi:microwave",
            native_unit_of_measurement="meals",
        ),
        SolarDistanceSensorDescription(
            key="kettle_boils",
            translation_key="kettle_boils",
            icon="mdi:kettle",
            native_unit_of_measurement="boils",
        ),
    ]
    async_add_entities(
        [
            SolarDistanceSensor(hass, entry, description),
            SolarMessageSensor(hass, entry, message_description),
            SolarEarthRoundsSensor(hass, entry, earth_rounds_description),
            SolarCoffeeSensor(hass, entry, coffee_description),
            SolarFuelSavedSensor(hass, entry, fuel_description),
            SolarLisbonBerlinTripsSensor(hass, entry, lisbon_berlin_description),
            SolarNycMexicoTripsSensor(hass, entry, nyc_mexico_description),
            *(SolarMetricSensor(hass, entry, metric) for metric in metric_descriptions),
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
        metric_values = {
            "marathon_equivalents": round(distance_value / MARATHON_KM, 2),
            "berlin_hamburg_trips": round(distance_value / BERLIN_HAMBURG_KM, 2),
            "munich_hamburg_trips": round(distance_value / MUNICH_HAMBURG_KM, 2),
            "paris_lyon_trips": round(distance_value / PARIS_LYON_KM, 2),
            "london_edinburgh_trips": round(distance_value / LONDON_EDINBURGH_KM, 2),
            "rome_milan_trips": round(distance_value / ROME_MILAN_KM, 2),
            "madrid_barcelona_trips": round(distance_value / MADRID_BARCELONA_KM, 2),
            "vienna_prague_trips": round(distance_value / VIENNA_PRAGUE_KM, 2),
            "la_sf_trips": round(distance_value / LA_SF_KM, 2),
            "tokyo_osaka_trips": round(distance_value / TOKYO_OSAKA_KM, 2),
            "phone_charges": round(pv_kwh / PHONE_CHARGE_KWH, 0),
            "laptop_charges": round(pv_kwh / LAPTOP_CHARGE_KWH, 0),
            "led_bulb_hours": round(pv_kwh / LED_BULB_KWH_PER_HOUR, 0),
            "tv_hours": round(pv_kwh / TV_KWH_PER_HOUR, 0),
            "fridge_days": round(pv_kwh / FRIDGE_KWH_PER_DAY, 1),
            "washing_cycles": round(pv_kwh / WASHING_CYCLE_KWH, 1),
            "dishwasher_cycles": round(pv_kwh / DISHWASHER_CYCLE_KWH, 1),
            "hot_showers": round(pv_kwh / HOT_SHOWER_KWH, 1),
            "microwave_meals": round(pv_kwh / MICROWAVE_MEAL_KWH, 0),
            "kettle_boils": round(pv_kwh / KETTLE_BOIL_KWH, 0),
        }
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
            "marathon_equivalents": metric_texts["marathon_equivalents"].format(
                value=metric_values["marathon_equivalents"],
                distance_km=MARATHON_KM,
            ),
            "berlin_hamburg_trips": metric_texts["berlin_hamburg_trips"].format(
                value=metric_values["berlin_hamburg_trips"],
                distance_km=BERLIN_HAMBURG_KM,
            ),
            "munich_hamburg_trips": metric_texts["munich_hamburg_trips"].format(
                value=metric_values["munich_hamburg_trips"],
                distance_km=MUNICH_HAMBURG_KM,
            ),
            "paris_lyon_trips": metric_texts["paris_lyon_trips"].format(
                value=metric_values["paris_lyon_trips"],
                distance_km=PARIS_LYON_KM,
            ),
            "london_edinburgh_trips": metric_texts["london_edinburgh_trips"].format(
                value=metric_values["london_edinburgh_trips"],
                distance_km=LONDON_EDINBURGH_KM,
            ),
            "rome_milan_trips": metric_texts["rome_milan_trips"].format(
                value=metric_values["rome_milan_trips"],
                distance_km=ROME_MILAN_KM,
            ),
            "madrid_barcelona_trips": metric_texts["madrid_barcelona_trips"].format(
                value=metric_values["madrid_barcelona_trips"],
                distance_km=MADRID_BARCELONA_KM,
            ),
            "vienna_prague_trips": metric_texts["vienna_prague_trips"].format(
                value=metric_values["vienna_prague_trips"],
                distance_km=VIENNA_PRAGUE_KM,
            ),
            "la_sf_trips": metric_texts["la_sf_trips"].format(
                value=metric_values["la_sf_trips"],
                distance_km=LA_SF_KM,
            ),
            "tokyo_osaka_trips": metric_texts["tokyo_osaka_trips"].format(
                value=metric_values["tokyo_osaka_trips"],
                distance_km=TOKYO_OSAKA_KM,
            ),
            "phone_charges": metric_texts["phone_charges"].format(
                value=metric_values["phone_charges"],
                energy_kwh=PHONE_CHARGE_KWH,
            ),
            "laptop_charges": metric_texts["laptop_charges"].format(
                value=metric_values["laptop_charges"],
                energy_kwh=LAPTOP_CHARGE_KWH,
            ),
            "led_bulb_hours": metric_texts["led_bulb_hours"].format(
                value=metric_values["led_bulb_hours"],
                energy_kwh=LED_BULB_KWH_PER_HOUR,
            ),
            "tv_hours": metric_texts["tv_hours"].format(
                value=metric_values["tv_hours"],
                energy_kwh=TV_KWH_PER_HOUR,
            ),
            "fridge_days": metric_texts["fridge_days"].format(
                value=metric_values["fridge_days"],
                energy_kwh=FRIDGE_KWH_PER_DAY,
            ),
            "washing_cycles": metric_texts["washing_cycles"].format(
                value=metric_values["washing_cycles"],
                energy_kwh=WASHING_CYCLE_KWH,
            ),
            "dishwasher_cycles": metric_texts["dishwasher_cycles"].format(
                value=metric_values["dishwasher_cycles"],
                energy_kwh=DISHWASHER_CYCLE_KWH,
            ),
            "hot_showers": metric_texts["hot_showers"].format(
                value=metric_values["hot_showers"],
                energy_kwh=HOT_SHOWER_KWH,
            ),
            "microwave_meals": metric_texts["microwave_meals"].format(
                value=metric_values["microwave_meals"],
                energy_kwh=MICROWAVE_MEAL_KWH,
            ),
            "kettle_boils": metric_texts["kettle_boils"].format(
                value=metric_values["kettle_boils"],
                energy_kwh=KETTLE_BOIL_KWH,
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
            metric_values=metric_values,
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


class SolarMetricSensor(SolarInfoSensor):
    """Expose a generic solar metric as its own entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(hass, entry, description)
        self._metric_key = description.key
        self._attr_unique_id = f"{entry.entry_id}_{self._metric_key}"

    def _set_from_metrics(self, metrics: SolarMetrics) -> None:
        self._attr_native_value = metrics.metric_values[self._metric_key]
        self._attr_available = True
        self._attr_extra_state_attributes = {
            **self._build_base_attributes(metrics),
            "text": metrics.texts[self._metric_key],
        }


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
                "marathon_km": MARATHON_KM,
                "berlin_hamburg_km": BERLIN_HAMBURG_KM,
                "munich_hamburg_km": MUNICH_HAMBURG_KM,
                "paris_lyon_km": PARIS_LYON_KM,
                "london_edinburgh_km": LONDON_EDINBURGH_KM,
                "rome_milan_km": ROME_MILAN_KM,
                "madrid_barcelona_km": MADRID_BARCELONA_KM,
                "vienna_prague_km": VIENNA_PRAGUE_KM,
                "los_angeles_san_francisco_km": LA_SF_KM,
                "tokyo_osaka_km": TOKYO_OSAKA_KM,
                "coffee_kwh": COFFEE_KWH,
                "phone_charge_kwh": PHONE_CHARGE_KWH,
                "laptop_charge_kwh": LAPTOP_CHARGE_KWH,
                "led_bulb_kwh_per_hour": LED_BULB_KWH_PER_HOUR,
                "tv_kwh_per_hour": TV_KWH_PER_HOUR,
                "fridge_kwh_per_day": FRIDGE_KWH_PER_DAY,
                "washing_cycle_kwh": WASHING_CYCLE_KWH,
                "dishwasher_cycle_kwh": DISHWASHER_CYCLE_KWH,
                "hot_shower_kwh": HOT_SHOWER_KWH,
                "microwave_meal_kwh": MICROWAVE_MEAL_KWH,
                "kettle_boil_kwh": KETTLE_BOIL_KWH,
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
