"""Tests for TrueNAS button entities."""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from truenaspy import TruenasException

# ---------------------------------------------------------------------------
# Setup de la plateforme
# ---------------------------------------------------------------------------


async def test_button_setup_creates_both_buttons(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """async_setup_entry crée exactement deux entités button (restart + stop)."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("button.truenas_test_system_restart")
    assert state is not None


# ---------------------------------------------------------------------------
# Appui sur les boutons
# ---------------------------------------------------------------------------


async def test_restart_button_press_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """Appuyer sur Restart appelle websocket avec method='system.reboot.info'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    data = {ATTR_ENTITY_ID: "button.truenas_test_system_restart"}

    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, service_data=data, blocking=True
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1


async def test_button_press_truenas_exception_is_caught(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """Une TruenasException lors de l'appui est attrapée sans lever d'exception."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    data = {ATTR_ENTITY_ID: "button.truenas_test_system_restart"}

    with patch(
        "custom_components.truenas.coordinator.TruenasWebsocket.async_call",
        side_effect=TruenasException("ws error"),
    ):
        await hass.services.async_call(
            BUTTON_DOMAIN, SERVICE_PRESS, service_data=data, blocking=True
        )
        await hass.async_block_till_done()
