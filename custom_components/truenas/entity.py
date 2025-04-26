"""Truenas entity model."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.typing import UNDEFINED
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TruenasDataUpdateCoordinator
from .helpers import finditem

_LOGGER = logging.getLogger(__name__)


class TruenasEntity(CoordinatorEntity[TruenasDataUpdateCoordinator], Entity):
    """Define entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TruenasDataUpdateCoordinator,
        entity_description,
        uid: str | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.uid = uid

        if entity_description.name != UNDEFINED:
            self._attr_name = entity_description.name.capitalize()
        if uid:
            self._attr_name = (
                f"{uid} {self.name}".capitalize()
                if self.name not in {UNDEFINED, None}
                else uid.capitalize()
            )

        # Device info
        system_info = coordinator.data.get("system_infos", {})
        device_name = coordinator.config_entry.data[CONF_NAME].capitalize()
        identifier = f"{device_name} {entity_description.device}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            manufacturer=system_info.get("system_manufacturer"),
            model=system_info.get("system_product"),
            via_device=(DOMAIN, system_info["hostname"]),
            name=identifier,
        )
        if entity_description.device == "System":
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, system_info["hostname"])},
                manufacturer=system_info.get("system_manufacturer"),
                sw_version=system_info.get("version"),
                model=system_info.get("system_product"),
                configuration_url=f"http://{system_info['hostname']}",
                name=identifier,
            )

        # Unique id
        self._attr_unique_id = (
            f"{device_name}-{entity_description.key}-{self.uid}"
            if uid
            else f"{device_name}-{entity_description.key}"
        )

        # Data for device
        self.device_data = self._handle_data_finder()

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        try:
            if self.entity_description.extra_attributes is None:
                return {}
            return {
                key: finditem(self.device_data, key)
                for key in self.entity_description.extra_attributes
            }
        except AttributeError as error:
            _LOGGER.error(error)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.device_data = self._handle_data_finder()
        super()._handle_coordinator_update()

    def _handle_data_finder(self, default: Any | None = None) -> Any:
        """Find data."""
        data = finditem(self.coordinator.data, self.entity_description.api, default)
        if self.uid and isinstance(data, list):
            data = next(
                (d for d in data if d.get(self.entity_description.id) == self.uid),
                default,
            )
        return data


@dataclass(frozen=True, kw_only=True)
class TruenasEntityDescription:
    """Base class for entity description."""

    id: str | None = None
    device: str | None = None
    api: str | None = None
    attribute: str | None = None
    extra_attributes: list[str] | None = None
    value_fn: Callable | None = None
