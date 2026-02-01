"""Config flow for Exciting Information."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import CONF_CONSUMPTION, CONF_PV_ENTITY_ID, DEFAULT_CONSUMPTION, DOMAIN


def _schema(default_consumption: float) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_PV_ENTITY_ID): selector.EntitySelector(
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


class ExcitingInformationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Exciting Information."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Exciting Information", data=user_input)

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
            return self.async_create_entry(title="", data=user_input)

        default_consumption = self._entry.options.get(
            CONF_CONSUMPTION, self._entry.data.get(CONF_CONSUMPTION, DEFAULT_CONSUMPTION)
        )
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(default_consumption),
        )
