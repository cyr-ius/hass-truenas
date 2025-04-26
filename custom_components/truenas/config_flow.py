"""Config flow to configure Truenas."""

from __future__ import annotations

import logging
from typing import Any

from truenaspy import (
    AuthenticationFailed,
    ConnectionError,
    TruenasException,
    TruenasWebsocket,
)
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import CONF_NOTIFY, DEFAULT_PORT, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Truenas", description="Unique Name"): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        # vol.Optional(CONF_API_KEY): str,
        vol.Required(CONF_SSL, default=True): bool,
        vol.Required(CONF_VERIFY_SSL, default=True): bool,
    }
)

_LOGGER = logging.getLogger(__name__)


class TruenasFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Truenas config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get option flow."""
        return TruenasOptionsFlowHandler()

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Occurs when a previous entry setup fails and is re-initiated."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input:
            try:
                name = user_input[CONF_NAME]
                await self.async_set_unique_id(name)
                self._abort_if_unique_id_configured()
                ws = TruenasWebsocket(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_SSL],
                    user_input[CONF_VERIFY_SSL],
                    async_create_clientsession(self.hass),
                )
                await ws.async_connect(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                if ws.is_connected is False:
                    errors["base"] = "cannot_connect"
                if ws.is_logged is False:
                    errors["base"] = "invalid_auth"
            except AuthenticationFailed:
                errors["base"] = "invalid_auth"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except TruenasException:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"{DOMAIN} ({name})", data=user_input
                )
            finally:
                if ws.is_connected:
                    await ws.async_close()

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class TruenasOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle option."""

    async def async_step_init(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {vol.Required(CONF_NOTIFY, default=False): bool},
                ),
                self.config_entry.options,
            ),
        )
