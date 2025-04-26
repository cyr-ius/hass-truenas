"""Button for TrueNAS integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Final

from truenaspy import TruenasException

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TruenasConfigEntry
from .entity import TruenasEntity, TruenasEntityDescription


@dataclass(frozen=True, kw_only=True)
class TruenasButtonEntityDescription(ButtonEntityDescription, TruenasEntityDescription):
    """Class describing entities."""

    fn: str | None = None


BUTTON_LIST: Final[tuple[TruenasButtonEntityDescription, ...]] = (
    TruenasButtonEntityDescription(
        key="restart",
        name="Restart",
        icon="mdi:restart-alert",
        fn="system.reboot.info",
        device="System",
        api="system_infos",
    ),
    TruenasButtonEntityDescription(
        key="stop",
        name="Stop",
        icon="mdi:stop",
        fn="system.shutdown",
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
    entities = [ButtonSensor(coordinator, description) for description in BUTTON_LIST]
    async_add_entities(entities)


class ButtonSensor(TruenasEntity, ButtonEntity):
    """Representation of a button for TrueNAS."""

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.coordinator.ws.async_call(method=self.entity_description.fn)
        except TruenasException as error:
            _LOGGER.error(error)
        else:
            await self.coordinator.async_refresh()
