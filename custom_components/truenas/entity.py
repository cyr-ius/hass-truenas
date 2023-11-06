"""Truenas entity model."""
from __future__ import annotations

from logging import getLogger

from .const import DOMAIN
from .coordinator import TruenasDataUpdateCoordinator
from .helpers import format_attribute

_LOGGER = getLogger(__name__)
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify


class TruenasEntity(CoordinatorEntity[TruenasDataUpdateCoordinator], Entity):
    """Define entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrueNASCoordinator,
        entity_description,
        uid: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.uid = uid
        self.datas = coordinator.data.get(entity_description.refer, {})
        if uid:
            self.datas = self.datas.get(uid, {})

        self._attr_name = None
        if isinstance(entity_description.name, str):
            self._attr_name = entity_description.name.capitalize()
        if uid and self.name:
            self._attr_name = f"{uid} {self.name}".capitalize()
        if uid and self.name is None:
            self._attr_name = uid.capitalize()

        # Device info
        system_info = coordinator.data.get("systeminfos", {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entity_description.category)},
            manufacturer=system_info.get("system_manufacturer"),
            model=system_info.get("system_product"),
            via_device=(DOMAIN, system_info["hostname"]),
            name=entity_description.category,
        )
        if entity_description.category == "System":
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entity_description.category)},
                manufacturer=system_info.get("system_manufacturer"),
                sw_version=system_info.get("version"),
                model=system_info.get("system_product"),
                configuration_url=f"http://{system_info['hostname']}",
                name=entity_description.category,
            )

        # Unique id
        self._attr_unique_id = entity_description.key
        if reference := entity_description.reference:
            ref_str = slugify(str(self.datas.get(reference, "")).lower())
            self._attr_unique_id = f"{entity_description.key}-{ref_str}"

    @callback
    def _handle_coordinator_update(self) -> None:
        refer = self.entity_description.refer
        self.datas = (
            self.coordinator.data.getr(refer, {}).get(self.uid)
            if self.uid
            else self.coordinator.data.getr(refer)
        )
        self.async_write_ha_state()
        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        return {
            format_attribute(key): self.datas.get(key)
            for key in self.entity_description.extra_attributes
        }

    async def start(self):
        """Run function."""
        raise NotImplementedError()

    async def stop(self):
        """Stop function."""
        raise NotImplementedError()

    async def restart(self):
        """Restart function."""
        raise NotImplementedError()

    async def reload(self):
        """Reload function."""
        raise NotImplementedError()

    async def snapshot(self):
        """Snapshot function."""
        raise NotImplementedError()
