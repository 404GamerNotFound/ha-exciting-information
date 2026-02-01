# Exciting Information

A Home Assistant custom integration (HACS) that estimates how far an EV could drive based on your current PV power or energy and your vehicle's consumption.

## README in supported languages
- **Deutsch (DE)**: Eine Home-Assistant-Integration, die anhand deiner aktuellen PV-Leistung oder -Energie und deines Fahrzeugverbrauchs berechnet, wie weit dein E-Auto fahren kann.
- **English (EN)**: A Home Assistant integration that estimates how far an EV could drive based on your current PV power or energy and your vehicle consumption.
- **Français (FR)** : Une intégration Home Assistant qui estime la distance qu’un VE pourrait parcourir à partir de votre puissance ou énergie PV actuelle et de la consommation du véhicule.
- **Italiano (IT)**: Un’integrazione Home Assistant che stima la distanza percorribile da un’auto elettrica in base alla potenza o energia FV attuale e al consumo del veicolo.
- **Español (ES)**: Una integración de Home Assistant que estima cuánta distancia podría recorrer un VE según tu potencia o energía FV actual y el consumo del vehículo.

## Features
- Select a PV power (kW) or energy (kWh) sensor as the basis for calculations.
- Enter your EV consumption in kWh/100 km.
- Creates a sensor with the calculated distance in km and a localized message.

## Installation (HACS)
1. Add this repository as a custom repository in HACS.
2. Install **Exciting Information**.
3. Restart Home Assistant.
4. Add the integration via **Settings → Devices & Services**.

## Configuration
During setup you will be asked for:
- **PV power/energy entity**: a sensor that reports PV power in kW or energy in kWh.
- **EV consumption**: your vehicle's consumption in kWh/100 km.

The sensor computes distance as:

```
Distance (km) = (PV energy in kWh / consumption in kWh/100 km) * 100
```

If a power sensor is selected, the integration assumes the current PV power is available for one hour.

## Sensors (power vs. energy)
This integration accepts either:
- **Power sensors** in **kW** (instantaneous power). The integration assumes the current PV power is available for one hour.
- **Energy sensors** in **kWh** (accumulated energy). The integration uses the current energy value directly.

If your PV sensor is in **W**, convert it to **kW** with a `template` or `utility_meter` sensor before setup. Likewise, choose a sensor that represents PV-only generation (not net grid import/export) for best results.

## Entities & stats (all sensors)
The integration creates the following sensors (stats). The names are localized in the UI, but the list below matches the English default strings:

| Sensor | Unit | Notes |
| --- | --- | --- |
| Solar driving range | km | Main distance estimate; includes attributes listed below. |
| Solar driving message | text | Short localized message for cards. |
| Solar trips around Earth | trips | Distance vs. Earth circumference. |
| Solar coffee cups | cups | Energy converted to coffee cups. |
| Solar fuel savings | L | Gasoline saved. |
| Solar Lisbon–Berlin trips | trips | Route equivalents. |
| Solar New York–Mexico City trips | trips | Route equivalents. |
| Solar marathon equivalents | marathons | Distance equivalents. |
| Solar Berlin–Hamburg trips | trips | Route equivalents. |
| Solar Munich–Hamburg trips | trips | Route equivalents. |
| Solar Paris–Lyon trips | trips | Route equivalents. |
| Solar London–Edinburgh trips | trips | Route equivalents. |
| Solar Rome–Milan trips | trips | Route equivalents. |
| Solar Madrid–Barcelona trips | trips | Route equivalents. |
| Solar Vienna–Prague trips | trips | Route equivalents. |
| Solar Los Angeles–San Francisco trips | trips | Route equivalents. |
| Solar Tokyo–Osaka trips | trips | Route equivalents. |
| Solar phone charges | charges | Phone charge equivalents. |
| Solar laptop charges | charges | Laptop charge equivalents. |
| Solar LED bulb hours | hours | LED bulb runtime. |
| Solar TV hours | hours | TV runtime. |
| Solar fridge days | days | Fridge runtime. |
| Solar washing cycles | cycles | Washing machine cycles. |
| Solar dishwasher cycles | cycles | Dishwasher cycles. |
| Solar hot showers | showers | Hot shower equivalents. |
| Solar microwave meals | meals | Microwave meal equivalents. |
| Solar kettle boils | boils | Kettle boil equivalents. |

The main **Solar driving range** sensor also exposes attributes useful for cards:
- `message`: localized text suitable for cards.
- `consumption_kwh_per_100km`
- `pv_entity_id`
- `pv_energy_kwh` and `pv_source`

## Localization
The UI strings are available in:
- German (de)
- English (en)
- French (fr)
- Italian (it)
- Spanish (es)

## Example Lovelace cards
### Mushroom card (pretty and compact)
```yaml
type: custom:mushroom-template-card
primary: Solar driving range
secondary: "{{ state_attr('sensor.solar_driving_range', 'message') }}"
icon: mdi:car-electric
icon_color: green
```

### Grid of tiles (compact overview)
```yaml
type: grid
columns: 3
square: false
cards:
  - type: tile
    entity: sensor.solar_driving_range
    name: Range
    icon: mdi:car-electric
  - type: tile
    entity: sensor.solar_fuel_savings
    name: Fuel saved
    icon: mdi:gas-station
  - type: tile
    entity: sensor.solar_coffee_cups
    name: Coffee
    icon: mdi:coffee
  - type: tile
    entity: sensor.solar_berlin_hamburg_trips
    name: Berlin–Hamburg
    icon: mdi:car
  - type: tile
    entity: sensor.solar_phone_charges
    name: Phone charges
    icon: mdi:cellphone
  - type: tile
    entity: sensor.solar_led_bulb_hours
    name: LED hours
    icon: mdi:lightbulb-outline
```

### Entities card (full list + message)
```yaml
type: entities
title: Solar stats
entities:
  - entity: sensor.solar_driving_range
    name: Range (km)
  - entity: sensor.solar_driving_message
    name: Message
  - entity: sensor.solar_trips_around_earth
    name: Trips around Earth
  - entity: sensor.solar_coffee_cups
    name: Coffee cups
  - entity: sensor.solar_fuel_savings
    name: Fuel savings (L)
  - entity: sensor.solar_lisbon_berlin_trips
    name: Lisbon–Berlin trips
  - entity: sensor.solar_new_york_mexico_city_trips
    name: New York–Mexico City trips
  - entity: sensor.solar_marathon_equivalents
    name: Marathon equivalents
  - entity: sensor.solar_berlin_hamburg_trips
    name: Berlin–Hamburg trips
  - entity: sensor.solar_munich_hamburg_trips
    name: Munich–Hamburg trips
  - entity: sensor.solar_paris_lyon_trips
    name: Paris–Lyon trips
  - entity: sensor.solar_london_edinburgh_trips
    name: London–Edinburgh trips
  - entity: sensor.solar_rome_milan_trips
    name: Rome–Milan trips
  - entity: sensor.solar_madrid_barcelona_trips
    name: Madrid–Barcelona trips
  - entity: sensor.solar_vienna_prague_trips
    name: Vienna–Prague trips
  - entity: sensor.solar_los_angeles_san_francisco_trips
    name: Los Angeles–San Francisco trips
  - entity: sensor.solar_tokyo_osaka_trips
    name: Tokyo–Osaka trips
  - entity: sensor.solar_phone_charges
    name: Phone charges
  - entity: sensor.solar_laptop_charges
    name: Laptop charges
  - entity: sensor.solar_led_bulb_hours
    name: LED bulb hours
  - entity: sensor.solar_tv_hours
    name: TV hours
  - entity: sensor.solar_fridge_days
    name: Fridge days
  - entity: sensor.solar_washing_cycles
    name: Washing cycles
  - entity: sensor.solar_dishwasher_cycles
    name: Dishwasher cycles
  - entity: sensor.solar_hot_showers
    name: Hot showers
  - entity: sensor.solar_microwave_meals
    name: Microwave meals
  - entity: sensor.solar_kettle_boils
    name: Kettle boils
```
