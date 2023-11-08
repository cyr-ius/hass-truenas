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
    CONF_VERIFY_SSL
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DOMAIN, CONF_NOTIFY

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Truenas", description="Unique Name"): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_SSL): bool,
        vol.Required(CONF_VERIFY_SSL): bool,
    }
)

_LOGGER = logging.getLogger(__name__)


class TruenasFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Truenas config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get option flow."""
        return TruenasOptionsFlowHandler(config_entry)

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

                api = TruenasClient(
                    user_input[CONF_HOST],
                    user_input[CONF_API_KEY],
                    async_create_clientsession(self.hass),
                    user_input[CONF_SSL],
                    user_input[CONF_VERIFY_SSL],
                )
                connected = await api.async_is_alive()
                if connected is False:
                    raise TruenasConnectionError("Truenas not response")
            except TruenasAuthenticationError:
                errors["base"] = "invalid_auth"
            except TruenasConnectionError:
                errors["base"] = "cannot_connect"
            except TruenasError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"{DOMAIN} ({name})", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class TruenasOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle option."""

    def __init__(self, config_entry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry
        self._notify = self.config_entry.options.get(CONF_NOTIFY, False)

    async def async_step_init(self, user_input=None):
        """Handle a flow initialized by the user."""
        options_schema = vol.Schema(
            {vol.Required(CONF_NOTIFY, default=False): bool},
        )
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=options_schema)
