"""Coordinator platform."""

from __future__ import annotations

from datetime import timedelta
import logging

from truenaspy import AuthenticationFailed, TruenasClient, TruenasException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_SSL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = 120


class TruenasDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to fetch data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Class to manage fetching Truenas data API."""
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=SCAN_INTERVAL)
        )

    async def _async_setup(self) -> None:
        """Start Truenas connection."""
        self.api = TruenasClient(
            self.config_entry.data[CONF_HOST],
            self.config_entry.data[CONF_API_KEY],
            async_create_clientsession(self.hass),
            self.config_entry.data[CONF_SSL],
            self.config_entry.data[CONF_VERIFY_SSL],
        )

    async def _async_update_data(self) -> dict:
        """Update data."""
        try:
            await self.api.async_update()
            if self.api.is_connected is False:
                raise UpdateFailed("Error occurred while communicating with Truenas")
        except AuthenticationFailed as error:
            raise ConfigEntryAuthFailed from error
        except TruenasException as error:
            raise UpdateFailed(error) from error
        else:
            return self.api
