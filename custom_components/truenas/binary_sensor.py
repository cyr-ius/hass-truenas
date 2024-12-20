"""Truenas binary sensor platform."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, Final

from homeassistant.components import persistent_notification
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TruenasConfigEntry
from .const import (
    CONF_NOTIFY,
    EXTRA_ATTRS_ALERT,
    EXTRA_ATTRS_APP,
    EXTRA_ATTRS_CHART,
    EXTRA_ATTRS_JAIL,
    EXTRA_ATTRS_POOL,
    EXTRA_ATTRS_SERVICE,
    EXTRA_ATTRS_SMARTDISK,
    EXTRA_ATTRS_VM,
    SCHEMA_SERVICE_APP_START,
    SCHEMA_SERVICE_APP_STOP,
    SCHEMA_SERVICE_APP_UPDATE,
    SCHEMA_SERVICE_CHART_START,
    SCHEMA_SERVICE_CHART_STOP,
    SCHEMA_SERVICE_CHART_UPDATE,
    SCHEMA_SERVICE_JAIL_RESTART,
    SCHEMA_SERVICE_JAIL_START,
    SCHEMA_SERVICE_JAIL_STOP,
    SCHEMA_SERVICE_SERVICE_RELOAD,
    SCHEMA_SERVICE_SERVICE_RESTART,
    SCHEMA_SERVICE_SERVICE_START,
    SCHEMA_SERVICE_SERVICE_STOP,
    SCHEMA_SERVICE_VM_START,
    SCHEMA_SERVICE_VM_STOP,
    SERVICE_APP_START,
    SERVICE_APP_STOP,
    SERVICE_APP_UPDATE,
    SERVICE_CHART_START,
    SERVICE_CHART_STOP,
    SERVICE_CHART_UPDATE,
    SERVICE_JAIL_RESTART,
    SERVICE_JAIL_START,
    SERVICE_JAIL_STOP,
    SERVICE_SERVICE_RELOAD,
    SERVICE_SERVICE_RESTART,
    SERVICE_SERVICE_START,
    SERVICE_SERVICE_STOP,
    SERVICE_VM_START,
    SERVICE_VM_STOP,
)
from .entity import TruenasEntity

_LOGGER = getLogger(__name__)


@dataclass
class TruenasBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing mikrotik entities."""

    icon_disabled: str | None = None
    icon_enabled: str | None = None
    category: str | None = None
    refer: str | None = None
    attr: str | None = None
    extra_attributes: list[str] = field(default_factory=list)
    reference: str | None = None
    func: str = lambda *args: BinarySensor(*args)  # noqa: E731


RESOURCE_LIST: Final[tuple[TruenasBinarySensorEntityDescription, ...]] = (
    TruenasBinarySensorEntityDescription(
        key="pool_healthy",
        icon_enabled="mdi:database",
        icon_disabled="mdi:database-off",
        category="Pool",
        refer="pools",
        attr="healthy",
        reference="name",
        extra_attributes=EXTRA_ATTRS_POOL,
    ),
    TruenasBinarySensorEntityDescription(
        key="jail",
        icon_enabled="mdi:layers",
        icon_disabled="mdi:layers-off",
        category="Jails",
        refer="jails",
        attr="state",
        reference="id",
        extra_attributes=EXTRA_ATTRS_JAIL,
        func=lambda *args: JailBinarySensor(  # pylint: disable=unnecessary-lambda
            *args
        ),
    ),
    TruenasBinarySensorEntityDescription(
        key="vm",
        icon_enabled="mdi:server",
        icon_disabled="mdi:server-off",
        category="VMs",
        refer="virtualmachines",
        attr="running",
        reference="name",
        extra_attributes=EXTRA_ATTRS_VM,
        func=lambda *args: VMBinarySensor(*args),  # pylint: disable=unnecessary-lambda
    ),
    TruenasBinarySensorEntityDescription(
        key="service",
        icon_enabled="mdi:cog",
        icon_disabled="mdi:cog-off",
        category="Services",
        refer="services",
        attr="enable",
        reference="service",
        extra_attributes=EXTRA_ATTRS_SERVICE,
        func=lambda *args: ServiceBinarySensor(  # pylint: disable=unnecessary-lambda
            *args
        ),
    ),
    TruenasBinarySensorEntityDescription(
        key="app",
        icon_enabled="mdi:server",
        icon_disabled="mdi:server-off",
        category="Charts",
        refer="charts",
        attr="running",
        reference="id",
        extra_attributes=EXTRA_ATTRS_CHART,
        func=lambda *args: ChartBinarySensor(  # pylint: disable=unnecessary-lambda
            *args
        ),
    ),
    TruenasBinarySensorEntityDescription(
        key="container",
        icon_enabled="mdi:server",
        icon_disabled="mdi:server-off",
        category="Apps",
        refer="apps",
        attr="state",
        reference="id",
        extra_attributes=EXTRA_ATTRS_APP,
        func=lambda *args: AppBinarySensor(  # pylint: disable=unnecessary-lambda
            *args
        ),
    ),
    TruenasBinarySensorEntityDescription(
        key="alert",
        icon_enabled="mdi:bell",
        icon_disabled="mdi:bell-off",
        category="System",
        refer="alerts",
        attr="level",
        extra_attributes=EXTRA_ATTRS_ALERT,
        func=lambda *args: AlertBinarySensor(  # pylint: disable=unnecessary-lambda
            *args
        ),
    ),
    TruenasBinarySensorEntityDescription(
        key="smart",
        icon_enabled="mdi:bell",
        icon_disabled="mdi:bell-off",
        name="Smartdisk alert",
        category="Disk",
        refer="smartdisks",
        attr="tests",
        reference="name",
        extra_attributes=EXTRA_ATTRS_SMARTDISK,
        func=lambda *args: BinarySensor(*args),  # pylint: disable=unnecessary-lambda
    ),
)

SERVICES = [
    [SERVICE_JAIL_START, SCHEMA_SERVICE_JAIL_START, "start"],
    [SERVICE_JAIL_STOP, SCHEMA_SERVICE_JAIL_STOP, "stop"],
    [SERVICE_JAIL_RESTART, SCHEMA_SERVICE_JAIL_RESTART, "restart"],
    [SERVICE_VM_START, SCHEMA_SERVICE_VM_START, "start"],
    [SERVICE_VM_STOP, SCHEMA_SERVICE_VM_STOP, "stop"],
    [SERVICE_SERVICE_START, SCHEMA_SERVICE_SERVICE_START, "start"],
    [SERVICE_SERVICE_STOP, SCHEMA_SERVICE_SERVICE_STOP, "stop"],
    [SERVICE_SERVICE_RESTART, SCHEMA_SERVICE_SERVICE_RESTART, "restart"],
    [SERVICE_SERVICE_RELOAD, SCHEMA_SERVICE_SERVICE_RELOAD, "reload"],
    [SERVICE_CHART_START, SCHEMA_SERVICE_CHART_START, "start"],
    [SERVICE_CHART_STOP, SCHEMA_SERVICE_CHART_STOP, "stop"],
    [SERVICE_CHART_UPDATE, SCHEMA_SERVICE_CHART_UPDATE, "upgrade"],
    [SERVICE_APP_START, SCHEMA_SERVICE_APP_START, "start"],
    [SERVICE_APP_STOP, SCHEMA_SERVICE_APP_STOP, "stop"],
    [SERVICE_APP_UPDATE, SCHEMA_SERVICE_APP_UPDATE, "upgrade"],
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TruenasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform."""
    coordinator = entry.runtime_data
    platform = entity_platform.async_get_current_platform()
    for service in SERVICES:
        platform.async_register_entity_service(*service)

    entities = []
    for description in RESOURCE_LIST:
        if description.reference:
            for value in getattr(coordinator.data, description.refer, {}):
                obj = description.func(
                    coordinator, description, value[description.reference]
                )
                entities.append(obj)
        else:
            entities.append(description.func(coordinator, description))

    async_add_entities(entities, update_before_add=True)


class BinarySensor(TruenasEntity, BinarySensorEntity):
    """Define an Truenas Binary Sensor."""

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.data.get(self.entity_description.attr)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.entity_description.icon_enabled:
            if self.is_on:
                return self.entity_description.icon_enabled
            return self.entity_description.icon_disabled


class JailBinarySensor(BinarySensor):
    """Define a Truenas Jail Binary Sensor."""

    async def start(self):
        """Start a Jail."""
        tmp_jail = await self.coordinator.api.async_get_jail(id=self.data["id"])
        if "state" not in tmp_jail:
            _LOGGER.error("Jail %s (%s) invalid", self.data["comment"], self.data["id"])
            return

        if tmp_jail["state"] != "down":
            _LOGGER.warning(
                "Jail %s (%s) is not down", self.data["comment"], self.data["id"]
            )
            return

        await self.coordinator.api.async_start_jail(id=self.data["id"])

    async def stop(self):
        """Stop a Jail."""
        tmp_jail = await self.coordinator.api.async_get_jail(id=self.data["id"])

        if "state" not in tmp_jail:
            _LOGGER.error("Jail %s (%s) invalid", self.data["comment"], self.data["id"])
            return

        if tmp_jail["state"] != "up":
            _LOGGER.warning(
                "Jail %s (%s) is not up", self.data["comment"], self.data["id"]
            )
            return

        await self.coordinator.api.async_stop_jail(id=self.data["id"])

    async def restart(self):
        """Restart a Jail."""
        tmp_jail = await self.coordinator.api.async_get_jail(id=self.data["id"])

        if "state" not in tmp_jail:
            _LOGGER.error("Jail %s (%s) invalid", self.data["comment"], self.data["id"])
            return

        if tmp_jail["state"] != "up":
            _LOGGER.warning(
                "Jail %s (%s) is not up", self.data["comment"], self.data["id"]
            )
            return

        await self.coordinator.api.async_restart_jail(id=self.data["id"])


class VMBinarySensor(BinarySensor):
    """Define a Truenas VM Binary Sensor."""

    async def start(self, overcommit: bool = False):
        """Start a VM."""
        tmp_vm = await self.coordinator.api.async_get_virtualmachine(id=self.data["id"])

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.data["name"], self.data["id"])
            return

        if tmp_vm["status"]["state"] != "STOPPED":
            _LOGGER.warning(
                "VM %s (%s) is not down", self.data["name"], self.data["id"]
            )
            return

        await self.coordinator.api.async_start_virtualmachine(id=self.data["id"])

    async def stop(self):
        """Stop a VM."""
        tmp_vm = await self.coordinator.api.async_get_virtualmachine(id=self.data["id"])

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.data["name"], self.data["id"])
            return

        if tmp_vm["status"]["state"] != "RUNNING":
            _LOGGER.warning("VM %s (%s) is not up", self.data["name"], self.data["id"])
            return

        await self.coordinator.api.async_stop_virtualmachine(id=self.data["id"])


class ServiceBinarySensor(BinarySensor):
    """Define a TrueNAS Service Binary Sensor."""

    async def start(self):
        """Start a Service."""
        tmp_service = await self.coordinator.api.async_get_service(id=self.data["id"])

        if "state" not in tmp_service:
            _LOGGER.error(
                "Service %s (%s) invalid", self.data["service"], self.data["id"]
            )
            return

        if tmp_service["state"] != "STOPPED":
            _LOGGER.warning(
                "Service %s (%s) is not stopped", self.data["service"], self.data["id"]
            )
            return

        await self.coordinator.api.async_start_service(service=self.data["service"])
        await self.coordinator.async_refresh()

    async def stop(self):
        """Stop a Service."""
        tmp_service = await self.coordinator.api.async_get_service(id=self.data["id"])

        if "state" not in tmp_service:
            _LOGGER.error(
                "Service %s (%s) invalid", self.data["service"], self.data["id"]
            )
            return

        if tmp_service["state"] == "STOPPED":
            _LOGGER.warning(
                "Service %s (%s) is not running", self.data["service"], self.data["id"]
            )
            return

        await self.coordinator.api.async_stop_service(service=self.data["service"])
        await self.coordinator.async_refresh()

    async def restart(self):
        """Restart a Service."""
        tmp_service = await self.coordinator.api.async_get_service(id=self.data["id"])

        if "state" not in tmp_service:
            _LOGGER.error(
                "Service %s (%s) invalid", self.data["service"], self.data["id"]
            )
            return

        if tmp_service["state"] == "STOPPED":
            _LOGGER.warning(
                "Service %s (%s) is not running", self.data["service"], self.data["id"]
            )
            return

        await self.coordinator.api.async_restart_service(service=self.data["service"])
        await self.coordinator.async_refresh()

    async def reload(self):
        """Reload a Service."""
        tmp_service = await self.coordinator.api.async_get_service(id=self.data["id"])

        if "state" not in tmp_service:
            _LOGGER.error(
                "Service %s (%s) invalid", self.data["service"], self.data["id"]
            )
            return

        if tmp_service["state"] == "STOPPED":
            _LOGGER.warning(
                "Service %s (%s) is not running", self.data["service"], self.data["id"]
            )
            return

        await self.coordinator.api.async_reload_service(service=self.data["service"])
        await self.coordinator.async_refresh()


class ChartBinarySensor(BinarySensor):
    """Define a Truenas Applications Binary Sensor."""

    async def start(self):
        """Start a chart."""
        tmp_vm = await self.coordinator.api.async_get_chart(id=self.data["id"])

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.data["name"], self.data["id"])
            return

        if tmp_vm["status"] == "ACTIVE":
            _LOGGER.warning(
                "VM %s (%s) is not down", self.data["name"], self.data["id"]
            )
            return

        await self.coordinator.api.async_start_chart(id=self.data["id"])

    async def stop(self):
        """Stop a chart."""
        tmp_vm = await self.coordinator.api.async_get_chart(id=self.data["id"])

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.data["name"], self.data["id"])
            return

        if tmp_vm["status"] != "ACTIVE":
            _LOGGER.warning("VM %s (%s) is not up", self.data["name"], self.data["id"])
            return

        await self.coordinator.api.async_stop_chart(id=self.data["id"])

    async def upgrade(self):
        """Update a chart."""
        tmp_vm = await self.coordinator.api.async_get_chart(id=self.data["id"])

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.data["name"], self.data["id"])
            return

        if tmp_vm["status"] != "ACTIVE":
            _LOGGER.warning("VM %s (%s) is not up", self.data["name"], self.data["id"])
            return

        if tmp_vm.get("container_images_update_available") is True:
            repo = tmp_vm.get("config", {}).get("image", {}).get("repository")
            tag = tmp_vm.get("config", {}).get("image", {}).get("tag")
            await self.coordinator.api.async_update_chart_image(repo=repo, tag=tag)
        else:
            await self.coordinator.api.async_update_chart(id=self.data["id"])


class AlertBinarySensor(BinarySensor):
    """Define a Truenas Applications Binary Sensor."""

    @property
    def name(self):
        """Return name."""
        return "Alert"

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        status = False
        for alert in self.data:
            if getattr(alert, self.entity_description.attr) != "INFO":
                if self.coordinator.config_entry.options.get(CONF_NOTIFY):
                    persistent_notification.create(
                        self.hass,
                        alert.formatted,
                        title=f"{alert.level} {alert.klass}",
                        notification_id=alert.uuid,
                    )
                status = True

        return status

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return extra attributes."""
        return {
            "msg": {
                alert.uuid: alert.formatted
                for alert in self.data
                if getattr(alert, self.entity_description.attr) != "INFO"
            }
        }


class AppBinarySensor(BinarySensor):
    """Define a Truenas Applications Binary Sensor."""

    async def start(self):
        """Start a chart."""
        tmp_vm = await self.coordinator.api.async_get_apps()[self.data["id"]]

        if "state" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.data["name"], self.data["id"])
            return

        await self.coordinator.api.async_start_app(app_name=self.data["id"])

    async def stop(self):
        """Stop a chart."""
        tmp_vm = await self.coordinator.api.async_get_apps()[self.data["id"]]

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.data["name"], self.data["id"])
            return

        await self.coordinator.api.async_stop_app(app_name=self.data["id"])

    async def upgrade(self):
        """Update a chart."""
        tmp_vm = await self.coordinator.api.async_get_apps()[self.data["id"]]

        if "state" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.data["name"], self.data["id"])
            return

        if tmp_vm.get("images_update_available") is True:
            repo = tmp_vm.get("config", {}).get("image", {}).get("repository")
            tag = tmp_vm.get("config", {}).get("image", {}).get("tag")
            await self.coordinator.api.async_update_chart_image(repo=repo, tag=tag)
        else:
            await self.coordinator.api.async_update_chart(id=self.data["id"])
