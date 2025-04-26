"""Update for TrueNAS integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Final

from truenaspy import TruenasException

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TruenasConfigEntry
from .coordinator import TruenasDataUpdateCoordinator
from .entity import TruenasEntity, TruenasEntityDescription
from .helpers import finditem

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class TruenasUpdateEntityDescription(UpdateEntityDescription, TruenasEntityDescription):
    """Class describing entities."""

    title: str | None = None
    cls: str = lambda *args: UpdateSensor(*args)  # pylint: disable=W0108


RESOURCE_LIST: Final[tuple[TruenasUpdateEntityDescription, ...]] = (
    TruenasUpdateEntityDescription(
        key="system_update",
        device="System",
        api="update_infos",
        attribute="available",
    ),
    TruenasUpdateEntityDescription(
        key="app_update",
        device="Apps",
        api="apps",
        attribute="upgrade_available",
        id="id",
        cls=lambda *args: UpdateAppSensor(*args),  # pylint: disable=W0108
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
            specs_entities = [
                description.cls(coordinator, description, value[description.id])
                for value in coordinator.data.get(description.api, {})
            ]
            entities.extend(specs_entities)
        else:
            entities.append(description.cls(coordinator, description))

    async_add_entities(entities)


class UpdateSensor(TruenasEntity, UpdateEntity):
    """Define an TrueNAS Update Sensor."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )

    def __init__(
        self,
        coordinator: TruenasDataUpdateCoordinator,
        entity_description,
        uid: str | None = None,
    ) -> None:
        """Set up device update entity."""
        super().__init__(coordinator, entity_description, uid)
        self._attr_title = self.entity_description.device

    @property
    def installed_version(self) -> str:
        """Version installed and in use."""
        return finditem(self.coordinator.data, "system_infos.version")

    @property
    def latest_version(self) -> str:
        """Latest version available for install."""
        return (
            version
            if (version := finditem(self.device_data, "0.new.version"))
            else self.installed_version
        )

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        try:
            await self.coordinator.ws.async_call(
                method="update.install", params=[{"reboot": True}]
            )
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_refresh()

    @property
    def in_progress(self) -> int:
        """Update installation progress."""
        return finditem(self.device_data, "update_available.state") == "RUNNING"


class UpdateAppSensor(TruenasEntity, UpdateEntity):
    """Define an TrueNAS Update Sensor."""

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )

    def __init__(
        self,
        coordinator: TruenasDataUpdateCoordinator,
        entity_description,
        uid: str | None = None,
    ) -> None:
        """Set up device update entity."""
        super().__init__(coordinator, entity_description, uid)
        self._attr_title = uid.capitalize()
        self._installing = False

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        return self.device_data.get("version")

    @property
    def latest_version(self) -> str:
        """Latest version available for install."""
        if self.device_data.get("upgrade_available"):
            return self.device_data.get("lastest_version")
        if self.device_data.get("image_updates_available"):
            return "New image available"
        return self.device_data.get("version")

    @property
    def release_summary(self) -> str | None:
        """Return the release notes."""
        return finditem(self.device_data, "metadata.description")

    @property
    def in_progress(self) -> bool:
        """Update installation progress."""
        if self.latest_version == self.installed_version:
            self._installing = False
        return self._installing

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        self._installing = True
        id_app = self.device_data.get("id")
        try:
            if self.device_data.get("upgrade_available"):
                await self.coordinator.ws.async_call(
                    method="app.upgrade", params=[id_app]
                )
            if self.device_data.get("image_updates_available"):
                await self.coordinator.ws.async_call(
                    method="app.pull_images", params=[id_app, {"redeploy": True}]
                )
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_refresh()
