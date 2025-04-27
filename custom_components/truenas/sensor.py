"""Sensors for TrueNAS integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import logging
from typing import Final

from homeassistant.components.sensor import (
    EntityCategory,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import TruenasConfigEntry
from .const import (
    EXTRA_ATTRS_CLOUDSYNC,
    EXTRA_ATTRS_DATASET,
    EXTRA_ATTRS_DISK,
    EXTRA_ATTRS_POOL,
    EXTRA_ATTRS_REPLICATION,
    EXTRA_ATTRS_RSYNCTASK,
    EXTRA_ATTRS_SNAPSHOTTASK,
)
from .entity import TruenasEntity, TruenasEntityDescription
from .helpers import finditem

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class TruenasSensorEntityDescription(SensorEntityDescription, TruenasEntityDescription):
    """Class describing entities."""


RESOURCE_LIST: Final[tuple[TruenasSensorEntityDescription, ...]] = (
    TruenasSensorEntityDescription(
        key="system_uptime",
        name="Uptime",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attribute="uptime_seconds",
        value_fn=lambda x: datetime.now(UTC) - timedelta(seconds=x),
    ),
    TruenasSensorEntityDescription(
        key="system_cpu_temperature",
        name="Temperature (Cpu mean)",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="events",
        attribute="reporting_realtime.cpu.cpu.temp",
    ),
    TruenasSensorEntityDescription(
        key="system_cpu_usage",
        name="CPU usage",
        icon="mdi:cpu-64-bit",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="events",
        attribute="reporting_realtime.cpu.cpu.usage",
    ),
    TruenasSensorEntityDescription(
        key="system_load_shortterm",
        name="CPU load shortterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="system_infos",
        attribute="loadavg.0",
    ),
    TruenasSensorEntityDescription(
        key="system_load_midterm",
        name="CPU load midterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="system_infos",
        attribute="loadavg.1",
    ),
    TruenasSensorEntityDescription(
        key="system_load_longterm",
        name="CPU load longterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="system_infos",
        attribute="loadavg.2",
    ),
    TruenasSensorEntityDescription(
        key="system_memory_available",
        name="Memory available",
        icon="mdi:memory",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="events",
        attribute="reporting_realtime.memory.physical_memory_available",
        value_fn=lambda x: round(x / 1024 / 1024 / 1024, 2) if x is not None else 0,
    ),
    TruenasSensorEntityDescription(
        key="system_memory_usage",
        name="Memory usage",
        icon="mdi:memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="events",
        attribute="reporting_realtime.memory",
        value_fn=lambda x: (
            100
            - round(
                x["physical_memory_available"] / x["physical_memory_total"] * 100, 2
            )
        )
        if x is not None
        else 0,
    ),
    TruenasSensorEntityDescription(
        key="system_cache_size-arc_value",
        name="ARC size",
        icon="mdi:memory",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="events",
        attribute="reporting_realtime.memory.arc_size",
        value_fn=lambda x: round(x / 1024 / 1024 / 1024, 2) if x is not None else 0,
    ),
    TruenasSensorEntityDescription(
        key="system_cache_ratio-arc_value",
        name="ARC ratio",
        icon="mdi:aspect-ratio",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="events",
        attribute="reporting_realtime.memory",
        value_fn=lambda x: (
            round(x.get("arc_size", 0) / x.get("physical_memory_total", 1) * 100, 2)
            if x is not None
            else 0
        ),
    ),
    TruenasSensorEntityDescription(
        key="pool_free",
        name="free",
        icon="mdi:database-settings",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device="Pool",
        api="pools",
        attribute="free",
        extra_attributes=EXTRA_ATTRS_POOL,
        value_fn=lambda x: round(x / 1024 / 1024 / 1024, 2),
        id="name",
    ),
    TruenasSensorEntityDescription(
        key="traffic_rx",
        name="RX",
        icon="mdi:download-network-outline",
        native_unit_of_measurement=UnitOfDataRate.KIBIBYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="netstats",
        id="name",
        attribute="statistics.received_bytes_rate",
        value_fn=lambda x: round(x / 1024, 2) if x is not None else 0,
    ),
    TruenasSensorEntityDescription(
        key="traffic_tx",
        name="TX",
        icon="mdi:upload-network-outline",
        native_unit_of_measurement=UnitOfDataRate.KIBIBYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="netstats",
        id="name",
        attribute="statistics.sent_bytes_rate",
        value_fn=lambda x: round(x / 1024, 2) if x is not None else 0,
    ),
    TruenasSensorEntityDescription(
        key="dataset",
        icon="mdi:database",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device="Datasets",
        api="datasets",
        attribute="used.parsed",
        extra_attributes=EXTRA_ATTRS_DATASET,
        id="id",
        device_class="datasets",
        value_fn=lambda x: round(x / 1024 / 1024 / 1024, 2) if x is not None else 0,
    ),
    TruenasSensorEntityDescription(
        key="dataset_snapshot",
        name="Snapshots",
        icon="mdi:database",
        state_class=SensorStateClass.MEASUREMENT,
        device="Datasets",
        api="snapshots",
        attribute="count",
        device_class="datasets",
        id="name",
    ),
    TruenasSensorEntityDescription(
        key="disk_used",
        icon="mdi:harddisk",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device="Disk",
        api="disks.used",
        attribute="size",
        extra_attributes=EXTRA_ATTRS_DISK,
        id="name",
        value_fn=lambda x: round(x / 1024 / 1024 / 1024, 2) if x is not None else 0,
    ),
    TruenasSensorEntityDescription(
        key="disk_temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device="Disk",
        api="disktemps",
        attribute="temperature",
        id="name",
    ),
    TruenasSensorEntityDescription(
        key="disk_unused",
        icon="mdi:harddisk",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device="Disk",
        api="disks.unused",
        attribute="size",
        extra_attributes=EXTRA_ATTRS_DISK,
        id="name",
        value_fn=lambda x: round(x / 1024 / 1024 / 1024, 2) if x is not None else 0,
    ),
    TruenasSensorEntityDescription(
        key="cloudsync",
        icon="mdi:cloud-upload",
        device="CloudSync",
        api="cloudsync",
        attribute="state",
        extra_attributes=EXTRA_ATTRS_CLOUDSYNC,
        id="id",
        device_class="cloudsync",
    ),
    TruenasSensorEntityDescription(
        key="replication",
        icon="mdi:transfer",
        device="Replication",
        api="replications",
        attribute="state",
        extra_attributes=EXTRA_ATTRS_REPLICATION,
        id="id",
    ),
    TruenasSensorEntityDescription(
        key="snapshottask",
        icon="mdi:checkbox-marked-circle-plus-outline",
        device="SnapshotTask",
        api="snapshottasks",
        attribute="state.state",
        extra_attributes=EXTRA_ATTRS_SNAPSHOTTASK,
        id="dataset",
    ),
    TruenasSensorEntityDescription(
        key="rsynctasks",
        icon="mdi:checkbox-marked-circle-plus-outline",
        device="RsyncTask",
        api="rsynctasks",
        attribute="job",
        extra_attributes=EXTRA_ATTRS_RSYNCTASK,
        id="path",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TruenasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform."""
    coordinator = entry.runtime_data
    entities = []
    try:
        for description in RESOURCE_LIST:
            if description.id:
                for value in finditem(coordinator.data, description.api, {}):
                    entities.extend(
                        [Sensor(coordinator, description, value[description.id])]
                    )
            else:
                entities.append(Sensor(coordinator, description))
    except (KeyError, TypeError):
        _LOGGER.error(description.id)

    async_add_entities(entities)


class Sensor(TruenasEntity, SensorEntity):
    """Define an Truenas Sensor."""

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        value = finditem(self.device_data, self.entity_description.attribute)
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(value)
        return value
