"""Config flow per Immergas Smartech Plus."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL
from homeassistant.core import callback

from .api import ImmergasClient, ImmergasConnectionError
from .const import DOMAIN, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL

CONF_TOKEN_A   = "token_a"
CONF_TOKEN_B   = "token_b"
CONF_PHPSESSID = "phpsessid"


class ImmergasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            token_a   = user_input[CONF_TOKEN_A].strip()
            token_b   = user_input[CONF_TOKEN_B].strip()
            phpsessid = user_input[CONF_PHPSESSID].strip()
            email     = user_input.get(CONF_EMAIL, "immergas").strip()

            await self.async_set_unique_id(token_a[:16])
            self._abort_if_unique_id_configured()

            client = ImmergasClient(token_a=token_a, token_b=token_b, phpsessid=phpsessid)
            try:
                devices = await self.hass.async_add_executor_job(client.get_devices)
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    return self.async_create_entry(
                        title=f"Immergas ({devices[0]['device_name']})",
                        data={
                            CONF_TOKEN_A:   token_a,
                            CONF_TOKEN_B:   token_b,
                            CONF_PHPSESSID: phpsessid,
                            CONF_EMAIL:     email,
                        },
                    )
            except ImmergasConnectionError as err:
                import logging
                logging.getLogger(__name__).error("Connection error: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                import logging
                logging.getLogger(__name__).exception("Unexpected: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN_A):   str,
                vol.Required(CONF_TOKEN_B):   str,
                vol.Required(CONF_PHPSESSID): str,
                vol.Optional(CONF_EMAIL, default=""): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ImmergasOptionsFlow(config_entry)


class ImmergasOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current_interval = self.config_entry.options.get(
            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_POLL_INTERVAL, default=current_interval
                ): vol.All(int, vol.Range(min=15, max=300)),
            }),
        )
