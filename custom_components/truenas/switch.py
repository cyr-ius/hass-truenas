"""Switch for TrueNAS integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any, Final

from truenaspy import TruenasException

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TruenasConfigEntry
from .const import EXTRA_ATTRS_SERVICE, EXTRA_ATTRS_VM
from .entity import TruenasEntity, TruenasEntityDescription
from .helpers import finditem


@dataclass(frozen=True, kw_only=True)
class TruenasSwitchEntityDescription(SwitchEntityDescription, TruenasEntityDescription):
    """Class describing mikrotik entities."""

    turn_on: Callable | None = None
    turn_off: Callable | None = None
    params_on: dict[str, Any] | None = None
    params_off: dict[str, Any] | None = None


SWITCH_LIST: Final[tuple[TruenasSwitchEntityDescription, ...]] = (
    TruenasSwitchEntityDescription(
        key="container",
        device="Apps",
        api="apps",
        attribute="state",
        id="id",
        turn_on="app.start",
        turn_off="app.stop",
        value_fn=lambda x: x != "STOPPED",
    ),
    TruenasSwitchEntityDescription(
        key="vm",
        device="VMs",
        api="virtualmachines",
        attribute="status",
        id="name",
        extra_attributes=EXTRA_ATTRS_VM,
        turn_on="virt.instance.start",
        turn_off="virt.instance.stop",
        params_off={"force": True},
        value_fn=lambda x: x == "RUNNING",
    ),
    TruenasSwitchEntityDescription(
        key="service",
        device="Services",
        api="services",
        attribute="state",
        id="service",
        extra_attributes=EXTRA_ATTRS_SERVICE,
        turn_on="service.start",
        turn_off="service.stop",
        params_off={"silent": False},
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
            for value in coordinator.data.get(description.api, {}):
                obj = SwitchSensor(coordinator, description, value[description.id])
                entities.append(obj)
        else:
            entities.append(SwitchSensor(coordinator, description))

    async_add_entities(entities)


class SwitchSensor(TruenasEntity, SwitchEntity):
    """Switch."""

    @property
    def is_on(self) -> bool:
        """Return state."""
        value = finditem(self.device_data, self.entity_description.attribute)
        if self.entity_description.value_fn:
            return bool(self.entity_description.value_fn(value))
        return bool(value)

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        try:
            params = (
                [self.uid]
                if self.entity_description.params_on is None
                else [self.uid, self.entity_description.params_on]
            )
            await self.coordinator.ws.async_call(
                method=self.entity_description.turn_on, params=params
            )
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        try:
            params = (
                [self.uid]
                if self.entity_description.params_off is None
                else [self.uid, self.entity_description.params_off]
            )
            await self.coordinator.ws.async_call(
                method=self.entity_description.turn_off, params=params
            )
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_request_refresh()
