"""Update for TrueNAS integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TruenasConfigEntry
from .const import UPDATE_IMG
from .coordinator import TruenasDataUpdateCoordinator
from .entity import TruenasEntity


@dataclass
class TruenasUpdateEntityDescription(UpdateEntityDescription):
    """Class describing entities."""

    title: str | None = None
    device: str | None = None
    api: str | None = None
    attr: str | None = "available"
    extra_attributes: list[str] = field(default_factory=list)
    id: str | None = None
    cls: str = lambda *args: UpdateSensor(*args)


RESOURCE_LIST: Final[tuple[TruenasUpdateEntityDescription, ...]] = (
    TruenasUpdateEntityDescription(
        key="system_update",
        device="System",
        api="update_infos",
        attr="available",
    ),
    TruenasUpdateEntityDescription(
        key="chart_update",
        device="Charts",
        api="charts",
        attr="available",
        id="id",
        cls=lambda *args: UpdateChart(*args),
    ),
    TruenasUpdateEntityDescription(
        key="app_update",
        device="Apps",
        api="apps",
        attr="upgrade_available",
        id="id",
        cls=lambda *args: UpdateApp(*args),
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
                for value in getattr(coordinator.data, description.api, {})
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
        return self.coordinator.data.system_infos["version"]

    @property
    def latest_version(self) -> str:
        """Latest version available for install."""
        return (
            version
            if (version := self.device_data["version"])
            else self.installed_version
        )

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        await self.coordinator.api.async_update_system(reboot=True)
        await self.coordinator.async_refresh()

    @property
    def in_progress(self) -> int:
        """Update installation progress."""
        if self.device_data.get("state") != "RUNNING":
            return False

        if self.device_data("progress") == 0:
            self.device_data["progress"] = 1

        return self.device_data("progress")


class UpdateChart(TruenasEntity, UpdateEntity):
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
        return self.device_data.get("human_version")

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if self.device_data.get(UPDATE_IMG) is True:
            return "Update image"
        return self.device_data.get("human_latest_version")

    @property
    def release_summary(self) -> str | None:
        """Return the release notes."""
        return self.device_data.get("description")

    @property
    def in_progress(self) -> int:
        """Update installation progress."""
        if self.latest_version == self.installed_version:
            self._installing = False
        return self._installing

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        self._installing = True
        await self.coordinator.api.async_update_chart(id=self.device_data["id"])
        await self.coordinator.async_refresh()


class UpdateApp(TruenasEntity, UpdateEntity):
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
        return self.device_data.get("human_version")

    @property
    def latest_version(self) -> str:
        """Latest version available for install."""
        if self.device_data.get("upgrade_available"):
            return "New version"
        if self.device_data.get("image_updates_available"):
            return "New image available"
        return self.device_data.get("human_version")

    @property
    def release_summary(self) -> str | None:
        """Return the release notes."""
        return self.device_data.get("description")

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
        if self.device_data.get("upgrade_available"):
            await self.coordinator.api.async_update_app(app_name=id_app)
        if self.device_data.get("image_updates_available"):
            await self.coordinator.api.async_pull_images(app_name=id_app)
        await self.coordinator.async_refresh()
