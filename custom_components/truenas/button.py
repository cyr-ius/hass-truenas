"""Button for TrueNAS integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Final

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from truenaspy import TruenasException

from . import TruenasConfigEntry, TruenasDataUpdateCoordinator
from .entity import TruenasEntity


@dataclass(frozen=True)
class TruenasButtonEntityDescription(ButtonEntityDescription):
    """Class describing entities."""

    device: str | None = None
    api: str | None = None
    id: str | None = None
    extra_attributes: list[str] = field(default_factory=list)
    func: Callable | None = None


BUTTON_LIST: Final[tuple[TruenasButtonEntityDescription, ...]] = (
    TruenasButtonEntityDescription(
        key="restart",
        name="Restart",
        icon="mdi:restart-alert",
        func="async_restart_system",
        device="System",
        api="system_infos",
    ),
    TruenasButtonEntityDescription(
        key="stop",
        name="Stop",
        icon="mdi:stop",
        func="async_shutdown_system",
        device="System",
        api="system_infos",
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TruenasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor."""
    coordinator = entry.runtime_data
    entities = [Button(coordinator, description) for description in BUTTON_LIST]
    async_add_entities(entities)


class Button(TruenasEntity, ButtonEntity):
    """Representation of a button for TrueNAS."""

    def __init__(
        self,
        coordinator: TruenasDataUpdateCoordinator,
        description,
        id: str | None = None,
    ) -> None:
        """Initialize switch."""
        super().__init__(coordinator, description)

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await getattr(self.coordinator.api, self.description.func)()
        except TruenasException as error:
            _LOGGER.error(error)
