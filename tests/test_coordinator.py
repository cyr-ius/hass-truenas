"""Tests for the TrueNAS data update coordinator."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import WebSocketError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from truenaspy import TruenasException

from custom_components.truenas.coordinator import TruenasDataUpdateCoordinator


# ---------------------------------------------------------------------------
# _ensure_connection / connection errors
# ---------------------------------------------------------------------------


async def test_ensure_connection_websocket_error_raises_update_failed(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """A WebSocketError during connection is converted to UpdateFailed."""
    coordinator = TruenasDataUpdateCoordinator(hass, config_entry)
    coordinator.websocket = MagicMock()
    coordinator.websocket.is_connected = False
    coordinator.websocket.async_connect = AsyncMock(
        side_effect=WebSocketError(1006, "boom")
    )

    with pytest.raises(UpdateFailed):
        await coordinator._ensure_connection()


async def test_ensure_connection_skips_when_already_connected(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """When already connected, no connect attempt is made."""
    coordinator = TruenasDataUpdateCoordinator(hass, config_entry)
    coordinator.websocket = MagicMock()
    coordinator.websocket.is_connected = True
    coordinator.websocket.async_connect = AsyncMock()

    await coordinator._ensure_connection()

    coordinator.websocket.async_connect.assert_not_called()


# ---------------------------------------------------------------------------
# _async_call critical / non-critical
# ---------------------------------------------------------------------------


async def test_async_call_critical_raises_update_failed(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """A critical call raising TruenasException becomes UpdateFailed."""
    coordinator = TruenasDataUpdateCoordinator(hass, config_entry)
    coordinator.websocket = MagicMock()
    coordinator.websocket.async_call = AsyncMock(side_effect=TruenasException("nope"))

    with pytest.raises(UpdateFailed):
        await coordinator._async_call("system.info")


async def test_async_call_non_critical_returns_empty(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """A non-critical call raising TruenasException returns an empty dict."""
    coordinator = TruenasDataUpdateCoordinator(hass, config_entry)
    coordinator.websocket = MagicMock()
    coordinator.websocket.async_call = AsyncMock(side_effect=TruenasException("nope"))

    result = await coordinator._async_call("app.query", critical=False)

    assert result == {}


# ---------------------------------------------------------------------------
# _async_update_data error wrapping
# ---------------------------------------------------------------------------


async def test_async_update_data_wraps_truenas_exception(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """A TruenasException raised by _fetch_data is wrapped in UpdateFailed."""
    coordinator = TruenasDataUpdateCoordinator(hass, config_entry)
    coordinator.websocket = MagicMock()
    coordinator.websocket.is_connected = True

    with patch.object(
        coordinator, "_fetch_data", side_effect=TruenasException("kaput")
    ):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


# ---------------------------------------------------------------------------
# _fetch_data — legacy version path (<= 25.10.0)
# ---------------------------------------------------------------------------


async def test_fetch_data_legacy_version_path(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """For versions < 25.10.0, the legacy calls and disk-temperature graph run."""
    coordinator = TruenasDataUpdateCoordinator(hass, config_entry)

    responses: dict[str, Any] = {
        "system.info": {"version": "24.10.0"},
        "interface.query": [{"name": "eth0"}],
        "zfs.snapshot.query": [],
        "disk.details": {
            "used": [{"identifier": "DISK1", "name": "sda"}],
            "unused": [],
        },
        "reporting.netdata_graph": [
            {
                "identifier": "type|bus|DISK1",
                "aggregations": {"mean": {"temperature_value": 41.5}},
            }
        ],
        "update.check_available": {"status": "AVAILABLE"},
        "update.get_pending": [],
        "smart.test.results": [],
        "virt.instance.query": [],
    }

    async def _call(method: str, params: Any = None) -> Any:
        return responses.get(method, [])

    coordinator.websocket = MagicMock()
    coordinator.websocket.async_call = AsyncMock(side_effect=_call)

    data = await coordinator._fetch_data()

    # The legacy branch populated the smart-disk + virtual machine keys.
    assert data["smartdisks"] == []
    assert data["virtualmachines"] == []
    # The disk temperature was resolved from the netdata graph.
    assert data["disks_temperatures"] == [{"name": "sda", "temperature": 41.5}]


# ---------------------------------------------------------------------------
# _make_event_callback — branches
# ---------------------------------------------------------------------------


async def test_event_callback_ignores_message_without_collection(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """A message without a collection name is ignored."""
    cb = coordinator._make_event_callback()
    await cb({"msg": "added", "fields": {"id": 1}})
    assert "None" not in coordinator._events


async def test_event_callback_scalar_added_and_removed(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """Scalar mode stores fields on ADDED/CHANGED and drops them on REMOVED."""
    cb = coordinator._make_event_callback(scalar=True)

    await cb({"collection": "my.scalar", "msg": "added", "fields": {"v": 1}})
    assert coordinator._events["my_scalar"] == {"v": 1}

    await cb({"collection": "my.scalar", "msg": "removed", "fields": {}})
    assert "my_scalar" not in coordinator._events


async def test_event_callback_list_added_removed_changed(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """List mode appends, updates by id and removes by id."""
    cb = coordinator._make_event_callback(scalar=False)
    name = "my_list"
    coordinator._events.pop(name, None)

    await cb({"collection": "my.list", "msg": "added", "fields": {"id": 1, "v": "a"}})
    await cb({"collection": "my.list", "msg": "added", "fields": {"id": 2, "v": "b"}})
    assert len(coordinator._events[name]) == 2

    # CHANGED with id updates the matching entry.
    await cb(
        {"collection": "my.list", "msg": "changed", "id": 1, "fields": {"id": 1, "v": "z"}}
    )
    assert coordinator._events[name][0]["v"] == "z"

    # REMOVED with id drops the matching entry.
    await cb({"collection": "my.list", "msg": "removed", "id": 2})
    assert [e["id"] for e in coordinator._events[name]] == [1]


async def test_event_callback_list_changed_without_id(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """A CHANGED message without id replaces the whole collection with fields."""
    cb = coordinator._make_event_callback(scalar=False)
    await cb({"collection": "whole.list", "msg": "changed", "fields": {"x": 1}})
    assert coordinator._events["whole_list"] == {"x": 1}


async def test_event_callback_notify_pushes_data(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """With notify=True and existing data, the coordinator pushes an update."""
    cb = coordinator._make_event_callback(scalar=True, notify=True)
    with patch.object(coordinator, "async_set_updated_data") as push:
        await cb({"collection": "n.scalar", "msg": "added", "fields": {"v": 1}})
    push.assert_called_once()
