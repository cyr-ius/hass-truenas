"""Binary Sensors for TrueNAS integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from homeassistant.components import persistent_notification
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from packaging import version

from . import TruenasConfigEntry
from .const import (
    CONF_NOTIFY,
    EXTRA_ATTRS_NETWORK,
    EXTRA_ATTRS_POOL,
    EXTRA_ATTRS_SMARTDISK,
)
from .entity import TruenasEntity, TruenasEntityDescription
from .helpers import finditem


class BinarySensor(TruenasEntity, BinarySensorEntity):
    """Define an Truenas Binary Sensor."""

    entity_description: TruenasBinarySensorEntityDescription

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        value = finditem(self.device_data, self.entity_description.attribute)
        if self.entity_description.value_fn:
            return bool(self.entity_description.value_fn(value))
        return bool(value)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.is_on:
            return self.entity_description.icon_enabled
        return self.entity_description.icon_disabled


class AlertBinarySensor(BinarySensor):
    """Define a Truenas Alert Binary Sensor."""

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        alerts = finditem(self.device_data, self.entity_description.attribute, [])
        if self.coordinator.config_entry.options.get(CONF_NOTIFY):
            for alert in alerts:
                if (level := alert["level"]) != "INFO":
                    persistent_notification.create(
                        self.hass,
                        alert["formatted"],
                        title=f"{level} {alert['klass']}",
                        notification_id=alert["uuid"],
                    )

        return len(alerts) != 0


@dataclass(frozen=True, kw_only=True)
class TruenasBinarySensorEntityDescription(
    BinarySensorEntityDescription, TruenasEntityDescription
):
    """Class describing entities."""

    icon_disabled: str
    icon_enabled: str
    value_fn: Callable | None = None
    cls: Callable[..., BinarySensor] = BinarySensor


RESOURCE_LIST: Final[tuple[TruenasBinarySensorEntityDescription, ...]] = (
    TruenasBinarySensorEntityDescription(
        key="pools",
        icon_enabled="mdi:database",
        icon_disabled="mdi:database-off",
        device="Pool",
        api="pools",
        attribute="status",
        id="name",
        extra_attributes=EXTRA_ATTRS_POOL,
        value_fn=lambda x: x == "ONLINE",
    ),
    TruenasBinarySensorEntityDescription(
        key="network_card",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        device="System",
        api="interfaces",
        id="id",
        attribute="state.link_state",
        extra_attributes=EXTRA_ATTRS_NETWORK,
        value_fn=lambda x: x == "LINK_STATE_UP",
        icon_enabled="",
        icon_disabled="",
    ),
    TruenasBinarySensorEntityDescription(
        key="alerts",
        name="Alert",
        icon_enabled="mdi:bell",
        icon_disabled="mdi:bell-off",
        device="System",
        api="events",
        attribute="alert_list",
        cls=AlertBinarySensor,
    ),
)

RESOURCE_LIST_LEGACY: Final[tuple[TruenasBinarySensorEntityDescription, ...]] = (
    TruenasBinarySensorEntityDescription(
        key="smartdisks",
        icon_enabled="mdi:bell",
        icon_disabled="mdi:bell-off",
        name="Smartdisk alert",
        device="Disk",
        api="smartdisks",
        attribute="tests.0.status",
        id="name",
        extra_attributes=EXTRA_ATTRS_SMARTDISK,
        value_fn=lambda x: x != "SUCCESS",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TruenasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform."""
    coordinator = entry.runtime_data
    system_version = coordinator.data.get("system_infos", {}).get("version", "0")

    resources = RESOURCE_LIST
    if version.parse(system_version) <= version.parse("25.10.0"):
        resources = resources + RESOURCE_LIST_LEGACY

    entities = []
    for description in resources:
        for value in coordinator.data.get(description.api, {}):
            uid = value[description.id] if description.id else None
            entities.extend([description.cls(coordinator, description, uid)])
    async_add_entities(entities)
