"""Truenas binary sensor platform."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from logging import getLogger
from typing import Final

from homeassistant.components.sensor import (
    EntityCategory,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    EXTRA_ATTRS_CLOUDSYNC,
    EXTRA_ATTRS_CPU,
    EXTRA_ATTRS_DATASET,
    EXTRA_ATTRS_DISK,
    EXTRA_ATTRS_MEMORY,
    EXTRA_ATTRS_NETWORK,
    EXTRA_ATTRS_POOL,
    EXTRA_ATTRS_REPLICATION,
    EXTRA_ATTRS_SNAPSHOTTASK,
    SCHEMA_SERVICE_CLOUDSYNC_RUN,
    SCHEMA_SERVICE_DATASET_SNAPSHOT,
    SCHEMA_SERVICE_SYSTEM_REBOOT,
    SCHEMA_SERVICE_SYSTEM_SHUTDOWN,
    SERVICE_CLOUDSYNC_RUN,
    SERVICE_DATASET_SNAPSHOT,
    SERVICE_SYSTEM_REBOOT,
    SERVICE_SYSTEM_SHUTDOWN,
)
from .entity import TruenasEntity

_LOGGER = getLogger(__name__)


@dataclass
class TruenasSensorEntityDescription(SensorEntityDescription):
    """Class describing entities."""

    sensor_class: TruenasEntity | None = None
    category: str | None = None
    refer: str | None = None
    attr: str | None = None
    extra_attributes: list[str] = field(default_factory=lambda: [])
    reference: str | None = None
    func: str = lambda *args: Sensor(*args)  # noqa: E731


RESOURCE_LIST: Final[tuple[TruenasSensorEntityDescription, ...]] = (
    TruenasSensorEntityDescription(
        key="system_uptime",
        name="Uptime",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="uptimeEpoch",
        func=lambda *args: UptimeSensor(*args),  # noqa: E731
    ),
    TruenasSensorEntityDescription(
        key="system_cpu_temperature",
        name="Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="cpu_temperature",
    ),
    TruenasSensorEntityDescription(
        key="system_load_shortterm",
        name="CPU load shortterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="load_shortterm",
    ),
    TruenasSensorEntityDescription(
        key="system_load_midterm",
        name="CPU load midterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="load_midterm",
    ),
    TruenasSensorEntityDescription(
        key="system_load_longterm",
        name="CPU load longterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="load_longterm",
    ),
    TruenasSensorEntityDescription(
        key="system_cpu_usage",
        name="CPU usage",
        icon="mdi:cpu-64-bit",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="cpu_usage",
        extra_attributes=EXTRA_ATTRS_CPU,
    ),
    TruenasSensorEntityDescription(
        key="system_memory_usage",
        name="Memory usage",
        icon="mdi:memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="memory_usage_percent",
        extra_attributes=EXTRA_ATTRS_MEMORY,
    ),
    TruenasSensorEntityDescription(
        key="system_cache_size-arc_value",
        name="ARC size",
        icon="mdi:memory",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="memory_arc_size",
    ),
    # TruenasSensorEntityDescription(
    #     key="system_cache_size-L2_value",
    #     name="L2ARC size",
    #     icon="mdi:memory",
    #     native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     entity_category=EntityCategory.DIAGNOSTIC,
    #     category="System",
    #     refer="system_infos",
    #     attr="memory_arc_size",
    # ),
    TruenasSensorEntityDescription(
        key="system_cache_ratio-arc_value",
        name="ARC ratio",
        icon="mdi:aspect-ratio",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        category="System",
        refer="system_infos",
        attr="arc_size_ratio",
    ),
    # TruenasSensorEntityDescription(
    #     key="system_cache_ratio-L2_value",
    #     name="L2ARC ratio",
    #     icon="mdi:aspect-ratio",
    #     state_class=SensorStateClass.MEASUREMENT,
    #     entity_category=EntityCategory.DIAGNOSTIC,
    #     category="System",
    #     refer="system_infos",
    #     attr="cache_ratio-L2_value",
    # ),
    TruenasSensorEntityDescription(
        key="system_swap",
        name="Swap used",
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        category="System",
        refer="system_infos",
        attr="swap_used",
    ),
    TruenasSensorEntityDescription(
        key="pool_free",
        name="free",
        icon="mdi:database-settings",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        category="Pool",
        refer="pools",
        attr="available_gib",
        extra_attributes=EXTRA_ATTRS_POOL,
        reference="name",
    ),
    TruenasSensorEntityDescription(
        key="traffic_rx",
        name="RX",
        icon="mdi:download-network-outline",
        native_unit_of_measurement=UnitOfDataRate.KIBIBYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        category="System",
        refer="interfaces",
        attr="received",
        extra_attributes=EXTRA_ATTRS_NETWORK,
        reference="id",
    ),
    TruenasSensorEntityDescription(
        key="traffic_tx",
        name="TX",
        icon="mdi:upload-network-outline",
        native_unit_of_measurement=UnitOfDataRate.KIBIBYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        category="System",
        refer="interfaces",
        attr="sent",
        extra_attributes=EXTRA_ATTRS_NETWORK,
        reference="id",
    ),
    TruenasSensorEntityDescription(
        key="dataset",
        icon="mdi:database",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        category="Datasets",
        refer="datasets",
        attr="used_gb",
        extra_attributes=EXTRA_ATTRS_DATASET,
        reference="id",
        func=lambda *args: DatasetSensor(*args),  # pylint: disable=unnecessary-lambda
    ),
    TruenasSensorEntityDescription(
        key="disk",
        icon="mdi:harddisk",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        category="Disk",
        refer="disks",
        attr="temperature",
        extra_attributes=EXTRA_ATTRS_DISK,
        reference="devname",
    ),
    TruenasSensorEntityDescription(
        key="cloudsync",
        icon="mdi:cloud-upload",
        category="CloudSync",
        refer="cloudsync",
        attr="state",
        extra_attributes=EXTRA_ATTRS_CLOUDSYNC,
        reference="id",
        func=lambda *args: ClousyncSensor(*args),  # pylint: disable=unnecessary-lambda
    ),
    TruenasSensorEntityDescription(
        key="replication",
        icon="mdi:transfer",
        category="Replication",
        refer="replications",
        attr="state",
        extra_attributes=EXTRA_ATTRS_REPLICATION,
        reference="id",
    ),
    TruenasSensorEntityDescription(
        key="snapshottask",
        icon="mdi:checkbox-marked-circle-plus-outline",
        category="SnapshotTask",
        refer="snapshottasks",
        attr="state",
        extra_attributes=EXTRA_ATTRS_SNAPSHOTTASK,
        reference="id",
    ),
)

SERVICES = [
    [SERVICE_CLOUDSYNC_RUN, SCHEMA_SERVICE_CLOUDSYNC_RUN, "start"],
    [SERVICE_DATASET_SNAPSHOT, SCHEMA_SERVICE_DATASET_SNAPSHOT, "snapshot"],
    [SERVICE_SYSTEM_REBOOT, SCHEMA_SERVICE_SYSTEM_REBOOT, "restart"],
    [SERVICE_SYSTEM_SHUTDOWN, SCHEMA_SERVICE_SYSTEM_SHUTDOWN, "stop"],
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    platform = entity_platform.async_get_current_platform()
    for service in SERVICES:
        platform.async_register_entity_service(*service)

    entities = []
    for description in RESOURCE_LIST:
        if description.reference:
            for value in getattr(coordinator.data, description.refer, {}):
                entities.append(
                    description.func(
                        coordinator, description, value[description.reference]
                    )
                )
        else:
            entities.append(description.func(coordinator, description))

    async_add_entities(entities, update_before_add=True)


class Sensor(TruenasEntity, SensorEntity):
    """Generic sensor."""

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return self.data.get(self.entity_description.attr)


class UptimeSensor(Sensor):
    """Define an Truenas Uptime sensor."""

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return datetime.strptime(
            self.data.get(self.entity_description.attr), "%Y-%m-%dT%H:%M:%S%z"
        )

    async def restart(self) -> None:
        """Restart TrueNAS system."""
        await self.coordinator.api.query("system/reboot", method="post")

    async def stop(self) -> None:
        """Shutdown TrueNAS system."""
        await self.coordinator.api.query("system/shutdown", method="post")


class DatasetSensor(Sensor):
    """Define an Truenas Dataset sensor."""

    async def snapshot(self) -> None:
        """Create dataset snapshot."""
        ts = datetime.now().isoformat(sep="_", timespec="microseconds")
        await self.coordinator.api.query(
            "zfs/snapshot",
            method="post",
            json={"dataset": f"{self.ref['name']}", "name": f"custom-{ts}"},
        )


class ClousyncSensor(Sensor):
    """Define an Truenas Cloudsync sensor."""

    async def start(self) -> None:
        """Run cloudsync job."""
        tmp_job = await self.coordinator.api.query(f"cloudsync/id/{self.ref['id']}")

        if "job" not in tmp_job:
            _LOGGER.error(
                "Clousync job %s (%s) invalid",
                self.ref["description"],
                self.ref["id"],
            )
            return
        if tmp_job["job"]["state"] in ["WAITING", "RUNNING"]:
            _LOGGER.warning(
                "Clousync job %s (%s) is already running",
                self.ref["description"],
                self.ref["id"],
            )
            return

        await self.coordinator.api.query(
            f"cloudsync/id/{self._ref['id']}/sync", method="post"
        )
