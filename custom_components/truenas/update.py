"""Truenas update sensor platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from logging import getLogger
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

_LOGGER = getLogger(__name__)


@dataclass
class TruenasUpdateEntityDescription(UpdateEntityDescription):
    """Class describing mikrotik entities."""

    title: str | None = None
    category: str | None = None
    refer: str | None = None
    attr: str | None = "available"
    extra_attributes: list[str] = field(default_factory=list)
    extra_name: str | None = None
    reference: str | None = None
    func: str = lambda *args: UpdateSensor(*args)  # noqa: E731


RESOURCE_LIST: Final[tuple[TruenasUpdateEntityDescription, ...]] = (
    TruenasUpdateEntityDescription(
        key="system_update",
        name="Update",
        category="System",
        refer="update_infos",
        attr="available",
        title="Truenas",
    ),
    TruenasUpdateEntityDescription(
        key="chart_update",
        category="Charts",
        refer="charts",
        attr="available",
        title="Charts",
        reference="id",
        func=lambda *args: UpdateChart(*args),  # noqa: E731
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
        if description.reference:
            for value in getattr(coordinator.data, description.refer, {}):
                entities.append(
                    description.func(
                        coordinator, description, value[description.reference]
                    )
                )
        else:
            entities.append(description.func(coordinator, description))

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
        self._attr_title = self.entity_description.title

    @property
    def installed_version(self) -> str:
        """Version installed and in use."""
        return self.coordinator.data.system_infos["version"]

    @property
    def latest_version(self) -> str:
        """Latest version available for install."""
        return version if (version := self.data["version"]) else self.installed_version

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        self.data["job_id"] = await self.coordinator.api.query(
            "update/update", method="post", json={"reboot": True}
        )
        await self.coordinator.async_refresh()

    @property
    def in_progress(self) -> int:
        """Update installation progress."""
        if self.data.get("state") != "RUNNING":
            return False

        if self.data("progress") == 0:
            self.data["progress"] = 1

        return self.data("progress")


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
        return self.data.get("human_version")

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if self.data.get(UPDATE_IMG) is True:
            return "Update image"
        return self.data.get("human_latest_version")

    @property
    def release_summary(self) -> str | None:
        """Return the release notes."""
        return self.data.get("description")

    @property
    def in_progress(self) -> int:
        """Update installation progress."""
        if self.latest_version == self.installed_version:
            self._installing = False
        return self._installing

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        self._installing = True
        await self.coordinator.api.query(
            "chart/release/upgrade",
            method="post",
            json={"release_name": self.data["id"]},
        )
        await self.coordinator.async_refresh()
