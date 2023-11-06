"""Config flow to configure Truenas."""
from __future__ import annotations

import logging

import voluptuous as vol
from truenaspy import (
    TruenasAuthenticationError,
    TruenasClient,
    TruenasConnectionError,
    TruenasError,
)

from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_SSL): bool,
        vol.Required(CONF_VERIFY_SSL): bool,
    }
)

_LOGGER = logging.getLogger(__name__)


class HeatzyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Heatzy config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input:
            try:
                api = TruenasClient(
                    config_entry.data[CONF_HOST],
                    config_entry.data[CONF_API_KEY],
                    async_create_clientsession(hass),
                    config_entry.data[CONF_SSL],
                    config_entry.data[CONF_VERIFY_SSL],
                )
                if await api.async_is_alive():
                    raise TruenasConnectionError("Truenas not response")
            except TruenasAuthenticationError:
                errors["base"] = "invalid_auth"
            except TruenasConnectionError:
                errors["base"] = "cannot_connect"
            except TruenasError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"{DOMAIN} ({username})", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
