"""Update for TrueNAS integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any, Final

from packaging import version
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

    cls: Callable[..., UpdateSensor | UpdateAppSensor] = lambda *args: UpdateSensor(
        *args
    )


RESOURCE_LIST: Final[list[TruenasUpdateEntityDescription]] = [
    TruenasUpdateEntityDescription(
        key="app_update",
        device="Apps",
        api="apps",
        attribute="upgrade_available",
        id="id",
        cls=lambda *args: UpdateAppSensor(*args),
    ),
]

RESOURCE_LIST_25_04: Final[list[TruenasUpdateEntityDescription]] = [
    TruenasUpdateEntityDescription(
        key="system_update",
        device="System",
        api="update_infos",
        attribute="available",
    )
]

RESOURCE_LIST_25_10: Final[list[TruenasUpdateEntityDescription]] = [
    TruenasUpdateEntityDescription(
        key="system_update",
        device="System",
        api="update_infos",
        attribute="status.new_version",
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TruenasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform."""
    coordinator = entry.runtime_data
    entities = []
    system_infos = coordinator.data.get("system_infos", {})

    resources = (
        RESOURCE_LIST + RESOURCE_LIST_25_10
        if version.parse(system_infos["version"]) >= version.parse("25.10.0")
        else RESOURCE_LIST + RESOURCE_LIST_25_04
    )

    for description in resources:
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
    """Define an TrueNAS System Update Sensor."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )

    entity_description: TruenasUpdateEntityDescription

    def __init__(
        self,
        coordinator: TruenasDataUpdateCoordinator,
        entity_description: TruenasUpdateEntityDescription,
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
        if version.parse(self.installed_version) <= version.parse("25.10.0"):
            # For versions <= 25.10.0
            return (
                ver
                if (ver := finditem(self.device_data, "0.new.version"))
                else self.installed_version
            )
        return finditem(
            self.device_data, "status.new_version.version", self.installed_version
        )

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        try:
            await self.coordinator.websocket.async_call(
                method="update.run", params=[{"reboot": True}]
            )
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_refresh()

    @property
    def in_progress(self) -> int:
        """Update installation progress."""
        if version.parse(self.installed_version) <= version.parse("25.10.0"):
            # Update installation progress for versions <= 25.10.0
            return finditem(self.device_data, "update_available.state") == "RUNNING"
        return (
            int(finditem(self.device_data, "update_download_progress.percent")) != 100
        )


class UpdateAppSensor(TruenasEntity, UpdateEntity):
    """Define an TrueNAS Apps Update Sensor."""

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )

    def __init__(
        self,
        coordinator: TruenasDataUpdateCoordinator,
        entity_description: TruenasUpdateEntityDescription,
        uid: str,
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
            return self.device_data.get("latest_version")
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
                await self.coordinator.websocket.async_call(
                    method="app.upgrade", params=[id_app]
                )
            if self.device_data.get("image_updates_available"):
                await self.coordinator.websocket.async_call(
                    method="app.pull_images", params=[id_app, {"redeploy": True}]
                )
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_refresh()
