"""Binary Sensors for TrueNAS integration."""

from __future__ import annotations

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

from . import TruenasConfigEntry
from .const import (
    CONF_NOTIFY,
    EXTRA_ATTRS_NETWORK,
    EXTRA_ATTRS_POOL,
    EXTRA_ATTRS_SMARTDISK,
)
from .entity import TruenasEntity, TruenasEntityDescription
from .helpers import finditem


@dataclass(frozen=True, kw_only=True)
class TruenasBinarySensorEntityDescription(
    BinarySensorEntityDescription, TruenasEntityDescription
):
    """Class describing entities."""

    icon_disabled: str | None = None
    icon_enabled: str | None = None
    cls: str = lambda *args: BinarySensor(*args)  # pylint: disable=W0108


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
    TruenasBinarySensorEntityDescription(
        key="network_card",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        device="System",
        api="interfaces",
        id="id",
        attribute="state.link_state",
        extra_attributes=EXTRA_ATTRS_NETWORK,
        value_fn=lambda x: x == "LINK_STATE_UP",
    ),
    TruenasBinarySensorEntityDescription(
        key="alerts",
        name="Alert",
        icon_enabled="mdi:bell",
        icon_disabled="mdi:bell-off",
        device="System",
        api="events",
        attribute="alert_list",
        cls=lambda *args: AlertBinarySensor(*args),  # pylint: disable=W0108
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
        for value in coordinator.data.get(description.api, {}):
            uid = value[description.id] if description.id else None
            entities.extend([description.cls(coordinator, description, uid)])
    async_add_entities(entities)


class BinarySensor(TruenasEntity, BinarySensorEntity):
    """Define an Truenas Binary Sensor."""

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
