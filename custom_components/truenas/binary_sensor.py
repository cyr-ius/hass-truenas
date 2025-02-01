"""Binary Sensors for TrueNAS integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from homeassistant.components import persistent_notification
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TruenasConfigEntry
from .const import CONF_NOTIFY, EXTRA_ATTRS_POOL, EXTRA_ATTRS_SMARTDISK
from .entity import TruenasDataUpdateCoordinator, TruenasEntity


@dataclass
class TruenasBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing entities."""

    icon_disabled: str | None = None
    icon_enabled: str | None = None
    device: str | None = None
    api: str | None = None
    attr: str | None = None
    extra_attributes: list[str] = field(default_factory=list)
    id: str | None = None


RESOURCE_LIST: Final[tuple[TruenasBinarySensorEntityDescription, ...]] = (
    TruenasBinarySensorEntityDescription(
        key="pools",
        icon_enabled="mdi:database",
        icon_disabled="mdi:database-off",
        device="Pool",
        api="pools",
        attr="healthy",
        id="name",
        extra_attributes=EXTRA_ATTRS_POOL,
    ),
    TruenasBinarySensorEntityDescription(
        key="smartdisks",
        icon_enabled="mdi:bell",
        icon_disabled="mdi:bell-off",
        name="Smartdisk alert",
        device="Disk",
        api="smartdisks",
        attr="tests",
        id="name",
        extra_attributes=EXTRA_ATTRS_SMARTDISK,
    ),
)

ALERT = TruenasBinarySensorEntityDescription(
    key="alerts",
    name="Alert",
    icon_enabled="mdi:bell",
    icon_disabled="mdi:bell-off",
    device="System",
    api="alerts",
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
        for value in getattr(coordinator.data, description.api, {}):
            entities.extend(
                [BinarySensor(coordinator, description, value[description.id])]
            )

    entities.append(AlertBinarySensor(coordinator, ALERT))

    async_add_entities(entities, update_before_add=True)


class BinarySensor(TruenasEntity, BinarySensorEntity):
    """Define an Truenas Binary Sensor."""

    def __init__(
        self,
        coordinator: TruenasDataUpdateCoordinator,
        description,
        id: str | None = None,
    ) -> None:
        """Initialize switch."""
        super().__init__(coordinator, description, id)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return bool(self.device_data.get(self.entity_description.attr))

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.is_on:
            return self.entity_description.icon_enabled
        return self.entity_description.icon_disabled


class AlertBinarySensor(BinarySensor):
    """Define a Truenas Alert Binary Sensor."""

    def __init__(self, coordinator: TruenasDataUpdateCoordinator, description) -> None:
        """Initialize switch."""
        super().__init__(coordinator, description)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        if self.coordinator.config_entry.options.get(CONF_NOTIFY):
            for alert in self.device_data:
                if (level := alert["level"]) != "INFO":
                    persistent_notification.create(
                        self.hass,
                        alert["formatted"],
                        title=f"{level} {alert['klass']}",
                        notification_id=alert["uuid"],
                    )

        return len(self.device_data) != 0
