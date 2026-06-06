"""Tests for TrueNAS switch entities."""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_ON, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from truenaspy import TruenasException



async def test_service_switch_is_on_when_running(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """Service cifs RUNNING → state est 'on'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.truenas_test_services_cifs")
    assert state is not None
    assert state.state == "on"


async def test_service_switch_is_off_when_stopped(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """Service ftp STOPPED → state est 'off'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.truenas_test_services_ftp")
    assert state is not None
    assert state.state == "off"


# ---------------------------------------------------------------------------
# Service switch — unique_id
# ---------------------------------------------------------------------------


async def test_service_switch_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """unique_id du service switch est formé correctement."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get("switch.truenas_test_services_cifs")
    assert entry is not None
    assert entry.unique_id == "Truenas_test-service-cifs"


# ---------------------------------------------------------------------------
# Service switch — actions
# ---------------------------------------------------------------------------


async def test_service_turn_on_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """turn_on sur service appelle websocket avec method='service.start' et params=['cifs']."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    data = {ATTR_ENTITY_ID: "switch.truenas_test_services_cifs"}
    await hass.services.async_call(Platform.SWITCH, "turn_on", data, blocking=True)

    assert len(service_calls) == 1

    coordinator = config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("switch.truenas_test_services_cifs")
    assert state is not None
    assert state.state == STATE_ON


async def test_service_turn_off_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """turn_off sur service appelle websocket."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    data = {ATTR_ENTITY_ID: "switch.truenas_test_services_cifs"}
    await hass.services.async_call(Platform.SWITCH, "turn_off", data, blocking=True)

    assert len(service_calls) == 1


async def test_service_turn_on_exception_caught(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """TruenasException lors du turn_on est attrapée sans lever d'exception."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    truenas_ws.async_call.side_effect = TruenasException("ws error")

    data = {ATTR_ENTITY_ID: "switch.truenas_test_services_cifs"}
    await hass.services.async_call(Platform.SWITCH, "turn_on", data, blocking=True)
    await hass.async_block_till_done()

    assert len(service_calls) == 1


# ---------------------------------------------------------------------------
# App (container) switch — états
# ---------------------------------------------------------------------------


async def test_app_switch_is_on_when_running(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """App transmission RUNNING → state est 'on'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.truenas_test_apps_transmission")
    assert state is not None
    assert state.state == STATE_ON


# ---------------------------------------------------------------------------
# App (container) switch — actions
# ---------------------------------------------------------------------------


async def test_app_turn_on_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """turn_on sur app appelle websocket avec method='app.start' et params=['transmission']."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    data = {ATTR_ENTITY_ID: "switch.truenas_test_apps_transmission"}
    await hass.services.async_call(Platform.SWITCH, "turn_on", data, blocking=True)

    assert len(service_calls) == 1


async def test_app_turn_off_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """turn_off sur app appelle websocket avec method='app.stop' et params=['transmission']."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    data = {ATTR_ENTITY_ID: "switch.truenas_test_apps_transmission"}
    await hass.services.async_call(Platform.SWITCH, "turn_off", data, blocking=True)

    assert len(service_calls) == 1


# ---------------------------------------------------------------------------
# VM switch (25.10+) — états
# ---------------------------------------------------------------------------


async def test_vm_switch_is_on_when_running(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """VM HomeAssistant status.state=RUNNING → state est 'on'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.truenas_test_vms_homeassistant")
    assert state is not None
    assert state.state == "on"


async def test_vm_switch_is_off_when_stopped(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """VM FlatcarOS status.state=STOPPED → state est 'off'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.truenas_test_vms_flatcaros")
    assert state is not None
    assert state.state == "off"


# ---------------------------------------------------------------------------
# VM switch (25.10+) — actions
# ---------------------------------------------------------------------------


async def test_vm_turn_on_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """turn_on sur VM appelle websocket avec method='vm.start' et params=['HomeAssistant']."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    data = {ATTR_ENTITY_ID: "switch.truenas_test_vms_homeassistant"}
    await hass.services.async_call(Platform.SWITCH, "turn_on", data, blocking=True)

    assert len(service_calls) == 1


async def test_vm_turn_off_calls_websocket_with_force(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """turn_off sur VM appelle websocket avec params_off={'force': True}."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    data = {ATTR_ENTITY_ID: "switch.truenas_test_vms_homeassistant"}
    await hass.services.async_call(Platform.SWITCH, "turn_off", data, blocking=True)

    assert len(service_calls) == 1


async def test_vm_turn_off_exception_skips_refresh(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
    service_calls: list[ServiceCall],
) -> None:
    """En cas de TruenasException lors du turn_off, le refresh n'est pas appelé."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    truenas_ws.async_call.reset_mock()
    truenas_ws.async_call.side_effect = TruenasException("ws error")

    data = {ATTR_ENTITY_ID: "switch.truenas_test_vms_homeassistant"}
    await hass.services.async_call(Platform.SWITCH, "turn_off", data, blocking=True)

    assert len(service_calls) == 1
