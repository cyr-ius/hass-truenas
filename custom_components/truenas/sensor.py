"""Sensors for TrueNAS integration."""

from __future__ import annotations

from collections.abc import Callable
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
    EXTRA_ATTRS_CPU,
    EXTRA_ATTRS_DATASET,
    EXTRA_ATTRS_DISK,
    EXTRA_ATTRS_MEMORY,
    EXTRA_ATTRS_NETWORK,
    EXTRA_ATTRS_POOL,
    EXTRA_ATTRS_REPLICATION,
    EXTRA_ATTRS_SNAPSHOTTASK,
)
from .entity import TruenasEntity

_LOGGER = getLogger(__name__)


@dataclass
class TruenasSensorEntityDescription(SensorEntityDescription):
    """Class describing entities."""

    device: str | None = None
    api: str | None = None
    attr: str | None = None
    extra_attributes: list[str] = field(default_factory=list)
    id: str | None = None
    value_fn: Callable | None = None


RESOURCE_LIST: Final[tuple[TruenasSensorEntityDescription, ...]] = (
    TruenasSensorEntityDescription(
        key="system_uptime",
        name="Uptime",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attr="uptimeEpoch",
        value_fn=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S%z"),
    ),
    TruenasSensorEntityDescription(
        key="system_cpu_temperature",
        name="Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attr="cpu_temperature",
    ),
    TruenasSensorEntityDescription(
        key="system_load_shortterm",
        name="CPU load shortterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attr="load_shortterm",
    ),
    TruenasSensorEntityDescription(
        key="system_load_midterm",
        name="CPU load midterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attr="load_midterm",
    ),
    TruenasSensorEntityDescription(
        key="system_load_longterm",
        name="CPU load longterm",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attr="load_longterm",
    ),
    TruenasSensorEntityDescription(
        key="system_cpu_usage",
        name="CPU usage",
        icon="mdi:cpu-64-bit",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
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
        device="System",
        api="system_infos",
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
        device="System",
        api="system_infos",
        attr="memory_arc_size",
    ),
    TruenasSensorEntityDescription(
        key="system_cache_size-L2_value",
        name="L2ARC size",
        icon="mdi:memory",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attr="memory_arc_size",
    ),
    TruenasSensorEntityDescription(
        key="system_cache_ratio-arc_value",
        name="ARC ratio",
        icon="mdi:aspect-ratio",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attr="arc_size_ratio",
    ),
    TruenasSensorEntityDescription(
        key="system_cache_ratio-L2_value",
        name="L2ARC ratio",
        icon="mdi:aspect-ratio",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device="System",
        api="system_infos",
        attr="cache_ratio-L2_value",
    ),
    TruenasSensorEntityDescription(
        key="pool_free",
        name="free",
        icon="mdi:database-settings",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device="Pool",
        api="pools",
        attr="available_gib",
        extra_attributes=EXTRA_ATTRS_POOL,
        id="name",
    ),
    TruenasSensorEntityDescription(
        key="traffic_rx",
        name="RX",
        icon="mdi:download-network-outline",
        native_unit_of_measurement=UnitOfDataRate.KIBIBYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="interfaces",
        attr="received",
        extra_attributes=EXTRA_ATTRS_NETWORK,
        id="id",
    ),
    TruenasSensorEntityDescription(
        key="traffic_tx",
        name="TX",
        icon="mdi:upload-network-outline",
        native_unit_of_measurement=UnitOfDataRate.KIBIBYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        device="System",
        api="interfaces",
        attr="sent",
        extra_attributes=EXTRA_ATTRS_NETWORK,
        id="id",
    ),
    TruenasSensorEntityDescription(
        key="dataset",
        icon="mdi:database",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        device="Datasets",
        api="datasets",
        attr="used_gb",
        extra_attributes=EXTRA_ATTRS_DATASET,
        id="id",
        device_class="datasets",
    ),
    TruenasSensorEntityDescription(
        key="disk",
        icon="mdi:harddisk",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        device="Disk",
        api="disks",
        attr="temperature",
        extra_attributes=EXTRA_ATTRS_DISK,
        id="devname",
    ),
    TruenasSensorEntityDescription(
        key="cloudsync",
        icon="mdi:cloud-upload",
        device="CloudSync",
        api="cloudsync",
        attr="state",
        extra_attributes=EXTRA_ATTRS_CLOUDSYNC,
        id="id",
        device_class="cloudsync",
    ),
    TruenasSensorEntityDescription(
        key="replication",
        icon="mdi:transfer",
        device="Replication",
        api="replications",
        attr="state",
        extra_attributes=EXTRA_ATTRS_REPLICATION,
        id="id",
    ),
    TruenasSensorEntityDescription(
        key="snapshottask",
        icon="mdi:checkbox-marked-circle-plus-outline",
        device="SnapshotTask",
        api="snapshottasks",
        attr="state",
        extra_attributes=EXTRA_ATTRS_SNAPSHOTTASK,
        id="id",
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
    for description in RESOURCE_LIST:
        if description.id:
            for value in getattr(coordinator.data, description.api, {}):
                entities.extend(
                    [Sensor(coordinator, description, value[description.id])]
                )
        else:
            entities.append(Sensor(coordinator, description))

    async_add_entities(entities, update_before_add=True)


class Sensor(TruenasEntity, SensorEntity):
    """Define an Truenas Sensor."""

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        value = self.device_data.get(self.entity_description.attr)
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(value)
        return value
