"""Coordinator platform."""

from __future__ import annotations

from collections import Counter
from datetime import timedelta
import logging
from typing import Any

from aiohttp import WebSocketError
from packaging import version
from truenaspy import TruenasException, TruenasWebsocket

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
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
        self._events = {}
        self.websocket: TruenasWebsocket
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=SCAN_INTERVAL)
        )

    async def _async_setup(self) -> None:
        """Start Truenas connection."""

        self.websocket = TruenasWebsocket(
            self.config_entry.data[CONF_HOST],
            self.config_entry.data[CONF_PORT],
            use_tls=self.config_entry.data[CONF_SSL],
            verify_ssl=self.config_entry.data[CONF_VERIFY_SSL],
            session=async_create_clientsession(self.hass),
        )

        self._setup_websocket_monitoring()

    async def _ensure_connection(self) -> None:
        """Ensure websocket is connected."""
        if self.websocket.is_connected:
            return

        try:
            await self.websocket.async_connect(
                self.config_entry.data[CONF_USERNAME],
                self.config_entry.data[CONF_PASSWORD],
            )
        except WebSocketError as error:
            self.logger.error("Error connecting to WebSocket: %s", error)
            raise UpdateFailed(f"WebSocket connection failed: {error}") from error
        else:
            await self.websocket.async_subscribe(
                "reporting.realtime", self._callback_reporting
            )
            await self.websocket.async_subscribe("alert.list", self._callback_events)

    @callback
    def _setup_websocket_monitoring(self) -> None:
        """Setup WebSocket monitoring and cleanup."""

        async def close_websocket(_: Event) -> None:
            """Close WebSocket on HA shutdown."""
            if self.unsub:
                self.unsub()
                self.unsub = None
            await self.websocket.async_close()

        # Cleanup sur shutdown
        self.unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, close_websocket
        )

    async def _async_call(
        self, method: str, params: list | None = None, critical: bool = True
    ) -> dict[str, Any]:
        """Call a method on the websocket."""
        try:
            return await self.websocket.async_call(method=method, params=params)
        except TruenasException as error:
            if critical:
                raise UpdateFailed(
                    f"Critical API call {method} failed: {error}"
                ) from error

            self.logger.warning("Non-critical call %s failed, continuing", method)
            return {}

    async def _async_update_data(self) -> dict:
        """Update data."""
        await self._ensure_connection()

        try:
            return await self._fetch_data()
        except TruenasException as error:
            raise UpdateFailed(error) from error

    async def _fetch_data(self) -> dict[str, Any]:
        """Fetch data."""

        # FETCH system infos to check version
        system_infos = await self._async_call("system.info")
        data: dict[str, Any] = {"system_infos": system_infos}

        # Fetch network interfaces
        interfaces = await self._async_call("interface.query")
        data["interfaces"] = list(filter(lambda x: "mac" not in x["name"], interfaces))

        # Fetch network statistics
        net_stats = finditem(self._events, "reporting_realtime.interfaces", {})
        data["netstats"] = [
            {
                "name": iface.get("name"),
                "statistics": net_stats.get(iface.get("name"), {}),
            }
            for iface in data["interfaces"]
        ]

        # Fetch snapshots
        snapshots = (
            await self._async_call(
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
        data["snapshots"] = [
            {"name": k, "count": v}
            for k, v in Counter(
                s["pool"] for s in snapshots[0] if len(snapshots) > 0
            ).items()
        ]

        # Fetch disks data
        data["disks"] = await self._async_call("disk.details")

        if version.parse(system_infos["version"]) <= version.parse("25.10.0"):
            """Fetch additional data for versions < 25.10.0."""

            async def disktemps() -> list[dict[str, Any] | None]:
                """Fetch disks data for versions < 25.10.0."""
                disktemps = []

                all_disks = {
                    disk.get("identifier"): disk
                    for disk in data["disks"].get("used", [])
                    + data["disks"].get("unused", [])
                }

                netdata = await self._async_call(
                    "reporting.netdata_graph", ["disktemp"]
                )
                for disktemp in netdata:
                    identifier = disktemp.get("identifier", "")
                    ids = identifier.split("|")
                    if len(ids) == 3:
                        disk_id = ids[2].strip()
                        disk = all_disks.get(disk_id)
                        if disk:
                            temp = round(
                                finditem(
                                    disktemp,
                                    "aggregations.mean.temperature_value",
                                    0,
                                ),
                                2,
                            )
                            disktemps.append(
                                {"name": disk["name"], "temperature": temp}
                            )
                return disktemps

            data["update_available"] = await self._async_call("update.check_available")
            data["update_infos"] = await self._async_call("update.get_pending")
            data["smartdisks"] = await self._async_call("smart.test.results")
            data["disks_temperatures"] = await disktemps()
            data["virtualmachines"] = await self._async_call("virt.instance.query")

        if version.parse(system_infos["version"]) >= version.parse("25.10.0"):
            """Fetch additional data for versions >= 25.10.0."""
            data["update_available"] = await self._async_call(
                "update.available_versions"
            )
            data["update_infos"] = await self._async_call("update.status")
            data["disks_temperatures"] = [
                {"name": k, "temperature": v}
                for k, v in (await self._async_call("disk.temperatures")).items()
            ]
            data["virtualmachines"] = await self._async_call("vm.query")

        other_data = {
            "apps": await self._async_call("app.query", critical=False),
            "datasets": await self._async_call("pool.dataset.details", critical=False),
            "pools": await self._async_call("pool.query", critical=False),
            "services": await self._async_call("service.query", critical=False),
            "replications": await self._async_call("replication.query", critical=False),
            "cloudsync": await self._async_call("cloudsync.query", critical=False),
            "snapshottasks": await self._async_call(
                "pool.snapshottask.query", critical=False
            ),
            "rsynctasks": await self._async_call("rsynctask.query", critical=False),
            "events": self._events,
        }

        data.update(other_data)
        _LOGGER.debug("Truenas Data: %s", data)

        return data

    async def _callback_reporting(self, data) -> None:
        """Calbback for websocket."""
        self._events.update({data["collection"].replace(".", "_"): data["fields"]})

    async def _callback_events(self, data) -> None:
        """Calbback for websocket."""
        name = data["collection"].replace(".", "_")
        if name not in self._events:
            self._events[name] = []
        if data["msg"].upper() == "ADDED":
            self._events[name].append(data["fields"])
        if data["msg"].upper() == "REMOVED":
            id_to_remove = data["id"]
            self._events[name] = [
                event for event in self._events[name] if event["id"] != id_to_remove
            ]
