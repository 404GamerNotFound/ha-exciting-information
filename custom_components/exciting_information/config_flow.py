"""Config flow for PV Exciting Information."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import (
    CONF_CONSUMPTION,
    CONF_GRID_EXPORT_ENTITY_ID,
    CONF_GRID_IMPORT_ENTITY_ID,
    CONF_PV_ENTITY_ID,
    DEFAULT_CONSUMPTION,
    DOMAIN,
)


def _schema(default_consumption: float) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_PV_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(CONF_GRID_IMPORT_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(CONF_GRID_EXPORT_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_CONSUMPTION, default=default_consumption): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    step=0.1,
                    unit_of_measurement="kWh/100 km",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _options_schema(
    default_consumption: float,
    default_pv_entity_id: str,
    default_grid_import_entity_id: str | None,
    default_grid_export_entity_id: str | None,
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(CONF_PV_ENTITY_ID, default=default_pv_entity_id): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(
                CONF_GRID_IMPORT_ENTITY_ID,
                default=default_grid_import_entity_id,
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_GRID_EXPORT_ENTITY_ID,
                default=default_grid_export_entity_id,
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_CONSUMPTION, default=default_consumption): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    step=0.1,
                    unit_of_measurement="kWh/100 km",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _validate_entity_ids(hass: HomeAssistant, user_input: dict) -> dict[str, str]:
    errors: dict[str, str] = {}
    for key in (
        CONF_PV_ENTITY_ID,
        CONF_GRID_IMPORT_ENTITY_ID,
        CONF_GRID_EXPORT_ENTITY_ID,
    ):
        entity_id = user_input.get(key)
        if not entity_id:
            continue
        if hass.states.get(entity_id) is None:
            errors[key] = "entity_not_found"
    return errors


class ExcitingInformationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PV Exciting Information."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        if user_input is not None:
            errors = _validate_entity_ids(self.hass, user_input)
            if errors:
                return self.async_show_form(
                    step_id="user",
                    data_schema=_schema(DEFAULT_CONSUMPTION),
                    errors=errors,
                )
            return self.async_create_entry(
                title="PV Exciting Information",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(DEFAULT_CONSUMPTION),
        )

    async def async_step_reauth(self, user_input: dict | None = None):
        """Handle reauth."""
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        return ExcitingInformationOptionsFlow(config_entry)


class ExcitingInformationOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage options."""
        if user_input is not None:
            if CONF_PV_ENTITY_ID not in user_input:
                user_input[CONF_PV_ENTITY_ID] = self._entry.options.get(
                    CONF_PV_ENTITY_ID, self._entry.data[CONF_PV_ENTITY_ID]
                )
            errors = _validate_entity_ids(self.hass, user_input)
            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=_options_schema(
                        self._entry.options.get(
                            CONF_CONSUMPTION,
                            self._entry.data.get(CONF_CONSUMPTION, DEFAULT_CONSUMPTION),
                        ),
                        self._entry.options.get(
                            CONF_PV_ENTITY_ID, self._entry.data[CONF_PV_ENTITY_ID]
                        ),
                        self._entry.options.get(
                            CONF_GRID_IMPORT_ENTITY_ID,
                            self._entry.data.get(CONF_GRID_IMPORT_ENTITY_ID),
                        ),
                        self._entry.options.get(
                            CONF_GRID_EXPORT_ENTITY_ID,
                            self._entry.data.get(CONF_GRID_EXPORT_ENTITY_ID),
                        ),
                    ),
                    errors=errors,
                )
            return self.async_create_entry(title="", data=user_input)

        default_consumption = self._entry.options.get(
            CONF_CONSUMPTION, self._entry.data.get(CONF_CONSUMPTION, DEFAULT_CONSUMPTION)
        )
        default_pv_entity_id = self._entry.options.get(
            CONF_PV_ENTITY_ID, self._entry.data[CONF_PV_ENTITY_ID]
        )
        default_grid_import_entity_id = self._entry.options.get(
            CONF_GRID_IMPORT_ENTITY_ID,
            self._entry.data.get(CONF_GRID_IMPORT_ENTITY_ID),
        )
        default_grid_export_entity_id = self._entry.options.get(
            CONF_GRID_EXPORT_ENTITY_ID,
            self._entry.data.get(CONF_GRID_EXPORT_ENTITY_ID),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(
                default_consumption,
                default_pv_entity_id,
                default_grid_import_entity_id,
                default_grid_export_entity_id,
            ),
        )
