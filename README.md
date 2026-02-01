# Exciting Information

A Home Assistant custom integration (HACS) that estimates how far an EV could drive based on your current PV power and your vehicle's consumption.

## Features
- Select a PV power sensor (kW) as the basis for calculations.
- Enter your EV consumption in kWh/100 km.
- Creates a sensor with the calculated distance in km and a localized message (German, English, French, Italian, Spanish).

## Installation (HACS)
1. Add this repository as a custom repository in HACS.
2. Install **Exciting Information**.
3. Restart Home Assistant.
4. Add the integration via **Settings → Devices & Services**.

## Configuration
During setup you will be asked for:
- **PV power entity**: a sensor that reports PV power in kW.
- **EV consumption**: your vehicle's consumption in kWh/100 km.

The sensor computes distance as:

```
Distance (km) = (PV power in kW / consumption in kWh/100 km) * 100
```

This assumes the current PV power is available for one hour.

## Entities
- **Solar driving range** (`sensor`) with attributes:
  - `message`: localized text suitable for cards.
  - `consumption_kwh_per_100km`
  - `pv_entity_id`

## Localization
Strings are available in German, English, French, Italian, and Spanish.
