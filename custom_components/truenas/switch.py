"""Switch for TrueNAS integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from truenaspy import TruenasException

from . import TruenasConfigEntry, TruenasDataUpdateCoordinator
from .const import (
    EXTRA_ATTRS_CHART,
    EXTRA_ATTRS_JAIL,
    EXTRA_ATTRS_SERVICE,
    EXTRA_ATTRS_VM,
)
from .entity import TruenasEntity


@dataclass
class TruenasSwitchEntityDescription(SwitchEntityDescription):
    """Class describing mikrotik entities."""

    device: str | None = None
    api: str | None = None
    attr: str | None = None
    extra_attributes: list[str] = field(default_factory=list)
    id: str | None = None
    turn_on: Callable | None = None
    turn_off: Callable | None = None
    value_fn: Callable | None = None


SWITCH_LIST: Final[tuple[TruenasSwitchEntityDescription, ...]] = (
    TruenasSwitchEntityDescription(
        key="container",
        device="Apps",
        api="apps",
        attr="state",
        id="id",
        turn_on="async_start_app",
        turn_off="async_stop_app",
    ),
    TruenasSwitchEntityDescription(
        key="vm",
        device="VMs",
        api="virtualmachines",
        attr="running",
        id="name",
        extra_attributes=EXTRA_ATTRS_VM,
        turn_on="async_start_virtualmachine",
        turn_off="async_stop_virtualmachine",
        value_fn=lambda x: x == "RUNNING",
    ),
    TruenasSwitchEntityDescription(
        key="app",
        device="Charts",
        api="charts",
        attr="running",
        id="charts",
        extra_attributes=EXTRA_ATTRS_CHART,
        turn_on="async_start_chart",
        turn_off="async_stop_chart",
        value_fn=lambda x: x == "RUNNING",
    ),
    TruenasSwitchEntityDescription(
        key="jail",
        device="Jails",
        api="jails",
        attr="state",
        id="id",
        extra_attributes=EXTRA_ATTRS_JAIL,
        turn_on="async_start_jail",
        turn_off="async_stop_jail",
        value_fn=lambda x: x == "up",
    ),
    TruenasSwitchEntityDescription(
        key="service",
        device="Services",
        api="services",
        attr="enable",
        id="service",
        extra_attributes=EXTRA_ATTRS_SERVICE,
        turn_on="async_start_jail",
        turn_off="async_stop_jail",
        value_fn=lambda x: x != "STOPPED",
        device_class="services",
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TruenasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set the sensor platform."""
    coordinator = entry.runtime_data
    entities = []
    for description in SWITCH_LIST:
        if description.id:
            for value in getattr(coordinator.data, description.api, {}):
                obj = SwitchEntity(coordinator, description, value[description.id])
                entities.append(obj)
        else:
            entities.append(SwitchEntity(coordinator, description))

    async_add_entities(entities)


class SwitchEntity(TruenasEntity, SwitchEntity):
    """Switch."""

    def __init__(
        self, coordinator: TruenasDataUpdateCoordinator, description, id: str
    ) -> None:
        """Initialize switch."""
        super().__init__(coordinator, description, id)

    @property
    def is_on(self) -> bool:
        """Return state."""
        value = self.device_data.get(self.entity_description.attr)
        if self.entity_description.value_fn:
            return bool(self.entity_description.value_fn(value))
        return bool(value)

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        try:
            await getattr(self.coordinator.api, self.entity_description.turn_on)(
                self.uid
            )
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        try:
            await getattr(self.coordinator.api, self.entity_description.turn_off)(
                self.uid
            )
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_request_refresh()
