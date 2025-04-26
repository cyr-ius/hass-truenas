"""Coordinator platform."""

from __future__ import annotations

from asyncio import Task
from collections import Counter
from datetime import timedelta
import logging

from aiohttp import WebSocketError
from truenaspy import AuthenticationFailed, TruenasException, TruenasWebsocket

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .helpers import finditem

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = 60


class TruenasDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to fetch data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Class to manage fetching Truenas data API."""
        self.unsub: CALLBACK_TYPE | None = None
        self._task: Task | None = None
        self._events = {}
        self.ws: TruenasWebsocket | None = None
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=SCAN_INTERVAL)
        )

    async def _async_setup(self) -> None:
        """Start Truenas connection."""
        try:
            self.ws = TruenasWebsocket(
                self.config_entry.data[CONF_HOST],
                self.config_entry.data[CONF_PORT],
                use_tls=self.config_entry.data[CONF_SSL],
                session=async_create_clientsession(self.hass),
            )
            self._task = await self.ws.async_connect(
                self.config_entry.data[CONF_USERNAME],
                self.config_entry.data[CONF_PASSWORD],
            )
        except AuthenticationFailed as error:
            raise ConfigEntryError(error) from error

        if self.ws.is_connected and self.unsub is None:
            self._handle_websocket()

            await self.ws.async_subscribe("reporting.realtime", self.on_reporting)
            await self.ws.async_subscribe("alert.list", self.on_events)

    async def on_reporting(self, data) -> None:
        """Calbback for websocket."""
        self._events.update({data["collection"].replace(".", "_"): data["fields"]})
        # self.async_set_updated_data(self._events)

    async def on_events(self, data) -> None:
        """Calbback for websocket."""
        name = data["collection"].replace(".", "_")
        if data["msg"].upper() == "ADDED":
            self._events[name].append(data["fields"])
        if data["msg"].upper() == "REMOVED":
            id_to_remove = data["id"]
            self._events[name] = [
                event for event in self._events[name] if event["id"] != id_to_remove
            ]
        # self.async_set_updated_data(self._events)

    @callback
    def _handle_websocket(self, event: Event | None = None) -> None:
        """Handle websocket connection."""

        async def async_listen() -> None:
            """Create the connection and listen to the websocket."""
            try:
                await self._task
            except WebSocketError as error:
                self.logger.error(error)

            # Ensure we are disconnected
            if self.unsub:
                self.unsub()

        async def async_close(_: Event) -> None:
            """Close WebSocket connection."""
            self.unsub = None
            await self.ws.async_close()

        # Clean disconnect WebSocket on Home Assistant shutdown
        self.unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, async_close
        )

        # Start listening
        self.config_entry.async_create_background_task(
            self.hass, async_listen(), "truenas-websocket-listen"
        )

    async def _call(self, method: str, params: list | None = None) -> dict:
        """Call a method on the websocket."""
        if self.ws.is_connected and self.ws.is_logged:
            try:
                return await self.ws.async_call(method=method, params=params)
            except TruenasException as error:
                _LOGGER.error("Error calling {%s}: {%s}", method, error)
        return {}

    async def _async_update_data(self) -> dict:
        """Update data."""
        try:
            # Fetch snaspshots
            snapshots = (
                await self._call(
                    method="zfs.snapshot.query",
                    params=[
                        [
                            ["pool", "!=", "boot-pool"],
                            ["pool", "!=", "freenas-boot"],
                        ],
                        {"select": ["dataset", "snapshot_name", "pool"]},
                    ],
                ),
            )

            # Fetch disk temperatures
            disktemps = []
            disks = await self._call("disk.details")
            all_disks = {
                disk.get("identifier"): disk
                for disk in disks.get("used", []) + disks.get("unused", [])
            }
            netdata = await self._call("reporting.netdata_graph", ["disktemp"])
            for disktemp in netdata:
                identifier = disktemp.get("identifier", "")
                ids = identifier.split("|")
                if len(ids) == 3:
                    disk_id = ids[2].strip()
                    disk = all_disks.get(disk_id)
                    if disk:
                        temp = round(
                            finditem(
                                disktemp, "aggregations.mean.temperature_value", 0
                            ),
                            2,
                        )
                        disktemps.append({"name": disk["name"], "temperature": temp})

            # Fetch network data
            interfaces = await self._call("interface.query")
            interfaces = list(filter(lambda x: "mac" not in x["name"], interfaces))
            net_stats = finditem(self._events, "reporting_realtime.interfaces", {})
            netstats = [
                {
                    "name": iface.get("name"),
                    "statistics": net_stats.get(iface.get("name"), {}),
                }
                for iface in interfaces
            ]

            # Fetch snapshots
            snapshots = [
                {"name": k, "count": v}
                for k, v in Counter(
                    s["pool"] for s in snapshots[0] if len(snapshots) > 0
                ).items()
            ]

            data = {
                "system_infos": await self._call("system.info"),
                "update_available": await self._call("update.check_available"),
                "update_infos": await self._call("update.get_pending"),
                "disks": disks,
                "disktemps": disktemps,
                "apps": await self._call("app.query"),
                "datasets": await self._call("pool.dataset.details"),
                "pools": await self._call("pool.query"),
                "services": await self._call("service.query"),
                "virtualmachines": await self._call("virt.instance.query"),
                "smartdisks": await self._call("smart.test.results"),
                "replications": await self._call("replication.query"),
                "cloudsync": await self._call("cloudsync.query"),
                "snapshottasks": await self._call("pool.snapshottask.query"),
                "rsynctasks": await self._call("rsynctask.query"),
                "interfaces": interfaces,
                "snapshots": snapshots,
                "netstats": netstats,
                "events": self._events,
            }
            _LOGGER.debug("Data: %s", data)

        except TruenasException as error:
            raise UpdateFailed(error) from error
        else:
            return data
