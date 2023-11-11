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
SCAN_INTERVAL = 300


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
            datas = ExtendedDict(
                {
                    "system": await self.api.async_get_system(),
                    "alerts": await self.api.async_get_alerts(),
                    "charts": await self.api.async_get_charts(),
                    "cloudsync": await self.api.async_get_cloudsync(),
                    "datasets": await self.api.async_get_datasets(),
                    "disks": await self.api.async_get_disks(),
                    "interfaces": await self.api.async_get_interfaces(),
                    "jails": await self.api.async_get_jails(),
                    "pools": await self.api.async_get_pools(),
                    "replications": await self.api.async_get_replications(),
                    "rsynctasks": await self.api.async_get_rsynctasks(),
                    "services": await self.api.async_get_services(),
                    "smartdisks": await self.api.async_get_smartdisks(),
                    "snapshottasks": await self.api.async_get_snapshottasks(),
                    "virtualmachines": await self.api.async_get_virtualmachines(),
                }
            )
            return datas
        except TruenasAuthenticationError as error:
            raise ConfigEntryAuthFailed from error
        except TruenasError as error:
            raise UpdateFailed(error) from error
