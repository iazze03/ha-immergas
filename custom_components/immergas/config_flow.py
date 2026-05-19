"""Config flow per Immergas Smartech Plus."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback

from .api import ImmergasClient, ImmergasAuthError, ImmergasConnectionError
from .const import DOMAIN, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL


class ImmergasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il config flow per Immergas Smartech Plus."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Primo step: chiede email e password."""
        errors = {}

        if user_input is not None:
            email    = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            # Evita configurazioni duplicate
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            # Tenta il login per validare le credenziali
            client = ImmergasClient(email, password)
            try:
                await self.hass.async_add_executor_job(client.login)
                devices = await self.hass.async_add_executor_job(
                    client.get_devices
                )
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    return self.async_create_entry(
                        title=f"Immergas ({email})",
                        data={
                            CONF_EMAIL:    email,
                            CONF_PASSWORD: password,
                        },
                    )
            except ImmergasAuthError:
                errors["base"] = "invalid_auth"
            except ImmergasConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL):    str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Restituisce il flow per le opzioni."""
        return ImmergasOptionsFlow(config_entry)


class ImmergasOptionsFlow(config_entries.OptionsFlow):
    """Gestisce le opzioni dell'integrazione (es. intervallo di polling)."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Mostra il form delle opzioni."""
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
