"""Truenas binary sensor platform."""
from __future__ import annotations

from dataclasses import dataclass, field
from logging import getLogger

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    EXTRA_ATTRS_CHART,
    EXTRA_ATTRS_JAIL,
    EXTRA_ATTRS_POOL,
    EXTRA_ATTRS_SERVICE,
    EXTRA_ATTRS_VM,
    SCHEMA_SERVICE_APP_START,
    SCHEMA_SERVICE_APP_STOP,
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
from .coordinator import TruenasDataUpdateCoordinator
from .entity import TruenasEntity


@dataclass
class TruenasBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing mikrotik entities."""

    icon_disabled: str | None = None
    icon_enabled: str | None = None
    category: str | None = None
    refer: str | None = None
    attr: str | None = None
    extra_attributes: list[str] = field(default_factory=lambda: [])
    reference: str | None = None
    func: str = lambda *args: BinarySensor(*args)  # pylint: disable=unnecessary-lambda


RESOURCE_LIST: Final[tuple[TruenasBinarySensorEntityDescription, ...]] = (
    TruenasBinarySensorEntityDescription(
        key="pool_healthy",
        icon_enabled="mdi:database",
        icon_disabled="mdi:database-off",
        category="System",
        refer="pools",
        attr="healthy",
        reference="guid",
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
        func=lambda *args: JailBinarySensor(
            *args
        ),  # pylint: disable=unnecessary-lambda
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
        attr="running",
        reference="service",
        extra_attributes=EXTRA_ATTRS_SERVICE,
        func=lambda *args: ServiceBinarySensor(
            *args
        ),  # pylint: disable=unnecessary-lambda
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
        func=lambda *args: ChartBinarySensor(
            *args
        ),  # pylint: disable=unnecessary-lambda
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
    [SERVICE_APP_START, SCHEMA_SERVICE_APP_START, "start"],
    [SERVICE_APP_STOP, SCHEMA_SERVICE_APP_STOP, "stop"],
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    platform = entity_platform.async_get_current_platform()
    for service in SERVICES:
        platform.async_register_entity_service(*service)

    entities = []
    for description in RESOURCE_LIST:
        if description.reference:
            for key, value in coordinator.data.get(description.refer, {}).items():
                entities.append(
                    description.func(
                        coordinator, description, value[description.reference]
                    )
                )
        else:
            entities.append(description.func(coordinator, description))

    async_add_entities(entities, update_before_add=True)


class BinarySensor(TruenasEntity, BinarySensorEntity):
    """Define an Truenas Binary Sensor."""

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.datas.get(self.entity_description.attr)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.entity_description.icon_enabled:
            if self.datas.get(self.entity_description.attr):
                return self.entity_description.icon_enabled
            else:
                return self.entity_description.icon_disabled


class JailBinarySensor(BinarySensor):
    """Define a Truenas Jail Binary Sensor."""

    async def start(self):
        """Start a Jail."""
        tmp_jail = await self.coordinator.api.query(f"jail/id/{self.datas['id']}")
        if "state" not in tmp_jail:
            _LOGGER.error(
                "Jail %s (%s) invalid", self.datas["comment"], self.datas["id"]
            )
            return

        if tmp_jail["state"] != "down":
            _LOGGER.warning(
                "Jail %s (%s) is not down", self.datas["comment"], self.datas["id"]
            )
            return

        await self.coordinator.api.query(
            "jail/start", method="post", json=self.datas["id"]
        )

    async def stop(self):
        """Stop a Jail."""
        tmp_jail = await self.coordinator.api.query(f"jail/id/{self.datas['id']}")

        if "state" not in tmp_jail:
            _LOGGER.error(
                "Jail %s (%s) invalid", self.datas["comment"], self.datas["id"]
            )
            return

        if tmp_jail["state"] != "up":
            _LOGGER.warning(
                "Jail %s (%s) is not up", self.datas["comment"], self.datas["id"]
            )
            return

        await self.coordinator.api.query(
            "jail/stop", method="post", json={"jail": self.datas["id"]}
        )

    async def restart(self):
        """Restart a Jail."""
        tmp_jail = await self.coordinator.api.query(f"jail/id/{self.datas['id']}")

        if "state" not in tmp_jail:
            _LOGGER.error(
                "Jail %s (%s) invalid", self.datas["comment"], self.datas["id"]
            )
            return

        if tmp_jail["state"] != "up":
            _LOGGER.warning(
                "Jail %s (%s) is not up", self.datas["comment"], self.datas["id"]
            )
            return

        await self.coordinator.api.query(
            "jail/restart", method="post", json=self.datas["id"]
        )


class VMBinarySensor(BinarySensor):
    """Define a Truenas VM Binary Sensor."""

    async def start(self, overcommit: bool = False):
        """Start a VM."""
        tmp_vm = await self.coordinator.api.query(f"vm/id/{self.datas['id']}")

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.datas["name"], self.datas["id"])
            return

        if tmp_vm["status"]["state"] != "STOPPED":
            _LOGGER.warning(
                "VM %s (%s) is not down", self.datas["name"], self.datas["id"]
            )
            return

        await self.coordinator.api.query(
            f"vm/id/{self.datas['id']}/start",
            method="post",
            json={"overcommit": overcommit},
        )

    async def stop(self):
        """Stop a VM."""
        tmp_vm = await self.coordinator.api.query(f"vm/id/{self.datas['id']}")

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.datas["name"], self.datas["id"])
            return

        if tmp_vm["status"]["state"] != "RUNNING":
            _LOGGER.warning(
                "VM %s (%s) is not up", self.datas["name"], self.datas["id"]
            )
            return

        await self.coordinator.api.query(
            f"vm/id/{self.datas['id']}/stop", method="post"
        )


class ServiceBinarySensor(BinarySensor):
    """Define a TrueNAS Service Binary Sensor."""

    async def start(self):
        """Start a Service."""
        tmp_service = self.coordinator.api.query(f"service/id/{self.datas['id']}")

        if "state" not in tmp_service:
            _LOGGER.error(
                "Service %s (%s) invalid", self.datas["service"], self.datas["id"]
            )
            return

        if tmp_service["state"] != "STOPPED":
            _LOGGER.warning(
                "Service %s (%s) is not stopped",
                self.datas["service"],
                self.datas["id"],
            )
            return

        await self.coordinator.api.query(
            "service/start", method="post", json={"service": self.datas["service"]}
        )
        await self.coordinator.async_refresh()

    async def stop(self):
        """Stop a Service."""
        tmp_service = self.coordinator.api.query(f"service/id/{self.datas['id']}")

        if "state" not in tmp_service:
            _LOGGER.error(
                "Service %s (%s) invalid", self.datas["service"], self.datas["id"]
            )
            return

        if tmp_service["state"] == "STOPPED":
            _LOGGER.warning(
                "Service %s (%s) is not running",
                self.datas["service"],
                self.datas["id"],
            )
            return

        await self.coordinator.api.query(
            "service/stop", method="post", json={"service": self.datas["service"]}
        )
        await self.coordinator.async_refresh()

    async def restart(self):
        """Restart a Service."""
        tmp_service = self.coordinator.api.query(f"service/id/{self.datas['id']}")

        if "state" not in tmp_service:
            _LOGGER.error(
                "Service %s (%s) invalid", self.datas["service"], self.datas["id"]
            )
            return

        if tmp_service["state"] == "STOPPED":
            _LOGGER.warning(
                "Service %s (%s) is not running",
                self.datas["service"],
                self.datas["id"],
            )
            return

        await self.coordinator.api.query(
            "service/restart", method="post", json={"service": self.datas["service"]}
        )
        await self.coordinator.async_refresh()

    async def reload(self):
        """Reload a Service."""
        tmp_service = self.coordinator.api.query(f"service/id/{self.datas['id']}")

        if "state" not in tmp_service:
            _LOGGER.error(
                "Service %s (%s) invalid", self.datas["service"], self.datas["id"]
            )
            return

        if tmp_service["state"] == "STOPPED":
            _LOGGER.warning(
                "Service %s (%s) is not running",
                self.datas["service"],
                self.datas["id"],
            )
            return

        await self.coordinator.api.query(
            "service/reload", method="post", json={"service": self.datas["service"]}
        )
        await self.coordinator.async_refresh()


class ChartBinarySensor(BinarySensor):
    """Define a Truenas Applications Binary Sensor."""

    async def start(self):
        """Start a VM."""
        tmp_vm = await self.coordinator.api.query(
            f"/chart/release/id/{self.datas['id']}"
        )

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.datas["name"], self.datas["id"])
            return

        if tmp_vm["status"] == "ACTIVE":
            _LOGGER.warning(
                "VM %s (%s) is not down", self.datas["name"], self.datas["id"]
            )
            return

        await self.coordinator.api.query(
            "/chart/release/scale",
            method="post",
            json={
                "release_name": self.datas["id"],
                "scale_options": {"replica_count": 1},
            },
        )

    async def stop(self):
        """Stop a VM."""
        tmp_vm = self.coordinator.api.query(f"/chart/release/id/{self.datas['id']}")

        if "status" not in tmp_vm:
            _LOGGER.error("VM %s (%s) invalid", self.datas["name"], self.datas["id"])
            return

        if tmp_vm["status"] != "ACTIVE":
            _LOGGER.warning(
                "VM %s (%s) is not up", self.datas["name"], self.datas["id"]
            )
            return

        await self.coordinator.api.query(
            "/chart/release/scale",
            method="post",
            json={
                "release_name": self.datas["id"],
                "scale_options": {"replica_count": 0},
            },
        )
