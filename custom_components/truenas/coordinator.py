"""Coordinator platform."""
from __future__ import annotations

import logging
from datetime import timedelta

import async_timeout
from truenaspy import TruenasAuthenticationError, TruenasClient, TruenasError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .helpers import ExtendedDict

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = 120


class TruenasDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to fetch datas."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Class to manage fetching Truenas data API."""
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=SCAN_INTERVAL)
        )
        self.api = TruenasClient(
            entry.data[CONF_HOST],
            entry.data[CONF_API_KEY],
            async_create_clientsession(hass),
            entry.data[CONF_SSL],
            entry.data[CONF_VERIFY_SSL],
        )

    async def _async_update_data(self) -> dict:
        """Update data."""
        try:
            await self.api.async_update()
            if self.api.is_connected is False:
                raise UpdateFailed("Error occurred while communicating with Truenas")
            return self.api 
        except TruenasAuthenticationError as error:
            raise ConfigEntryAuthFailed from error
        except TruenasError as error:
            raise UpdateFailed(error) from error
