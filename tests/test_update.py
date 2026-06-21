"""Tests for TrueNAS update entities."""

import asyncio
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from truenaspy import TruenasException

from custom_components.truenas.coordinator import TruenasDataUpdateCoordinator
from custom_components.truenas.update import (
    RESOURCE_LIST,
    RESOURCE_LIST_25_10,
    UpdateAppSensor,
    UpdateSensor,
)

SYSTEM_EID = "update.truenas_test_system_firmware"
APP_EID = "update.truenas_test_apps_transmission"


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def test_update_setup_creates_system_and_app_entities(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """async_setup_entry creates the System entity as well as the Apps entities."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(SYSTEM_EID) is not None
    assert hass.states.get(APP_EID) is not None


# ---------------------------------------------------------------------------
# System update — versions and state
# ---------------------------------------------------------------------------


async def test_system_update_versions(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """The System entity exposes the installed version and the available version."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(SYSTEM_EID)
    assert state.attributes["installed_version"] == "25.10.3.1"
    assert state.attributes["latest_version"] == "25.10.4"
    # An update is available → state 'on'.
    assert state.state == "on"


async def test_system_in_progress_reflects_download_percent(
    hass: HomeAssistant,
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """in_progress reflects the download percent from the update.status event."""
    entity = UpdateSensor(coordinator, RESOURCE_LIST_25_10[0])
    # The fixture's update.status event carries a percent of 0.
    assert entity.in_progress == 0


async def test_system_update_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """The System update entity's unique_id is built correctly."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get(SYSTEM_EID)
    assert entry is not None
    assert entry.unique_id == "Truenas_test-system_update"


# ---------------------------------------------------------------------------
# System update — installation
# ---------------------------------------------------------------------------


async def test_system_update_install_calls_websocket(
    hass: HomeAssistant,
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """The System install calls websocket with method='update.run'."""
    entity = UpdateSensor(coordinator, RESOURCE_LIST_25_10[0])
    coordinator.websocket.async_call.reset_mock()

    with patch.object(coordinator, "async_refresh", new=AsyncMock()):
        await entity.async_install(None, False)

    methods = [
        c.kwargs.get("method") for c in coordinator.websocket.async_call.call_args_list
    ]
    assert "update.run" in methods


async def test_system_update_install_truenas_exception_is_caught(
    hass: HomeAssistant,
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """A TruenasException during the System install is caught (no refresh)."""
    entity = UpdateSensor(coordinator, RESOURCE_LIST_25_10[0])
    coordinator.websocket.async_call = AsyncMock(
        side_effect=TruenasException("update failed")
    )

    with patch.object(coordinator, "async_refresh", new=AsyncMock()) as refresh:
        # Must not raise an exception.
        await entity.async_install(None, False)

    refresh.assert_not_called()


# ---------------------------------------------------------------------------
# App update — state and versions
# ---------------------------------------------------------------------------


async def test_app_update_off_when_no_upgrade(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """An app with no available update is in the 'off' state."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(APP_EID)
    assert state.state == "off"
    assert state.attributes["installed_version"] == "1.3.8"


async def test_app_update_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """The App update entity's unique_id includes the app uid."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get(APP_EID)
    assert entry is not None
    assert entry.unique_id == "Truenas_test-app_update-transmission"


# ---------------------------------------------------------------------------
# App update — latest_version / release_summary logic (unit tests)
# ---------------------------------------------------------------------------


def _make_app_entity(
    coordinator: TruenasDataUpdateCoordinator, device_data: dict[str, Any]
) -> UpdateAppSensor:
    """Build an UpdateAppSensor with a controlled device_data."""
    entity = UpdateAppSensor(coordinator, RESOURCE_LIST[0], device_data["id"])
    entity.device_data = device_data
    return entity


async def test_app_latest_version_upgrade_available(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """upgrade_available → latest_version returns latest_version."""
    entity = _make_app_entity(
        coordinator,
        {"id": "foo", "version": "1.0", "upgrade_available": True, "latest_version": "2.0"},
    )
    assert entity.latest_version == "2.0"


async def test_app_latest_version_image_update(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """image_updates_available → latest_version returns 'New image available'."""
    entity = _make_app_entity(
        coordinator,
        {
            "id": "foo",
            "version": "1.0",
            "upgrade_available": False,
            "image_updates_available": True,
        },
    )
    assert entity.latest_version == "New image available"


async def test_app_latest_version_no_update(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """No update → latest_version == installed version."""
    entity = _make_app_entity(
        coordinator,
        {
            "id": "foo",
            "version": "1.0",
            "upgrade_available": False,
            "image_updates_available": False,
        },
    )
    assert entity.latest_version == "1.0"


async def test_app_release_summary_changelog(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """release_summary prefers the version_details changelog."""
    entity = _make_app_entity(
        coordinator,
        {
            "id": "foo",
            "version": "1.0",
            "version_details": {"changelog": "notes ici"},
            "metadata": {"description": "desc"},
        },
    )
    assert entity.release_summary == "notes ici"


async def test_app_release_summary_fallback_description(
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """release_summary falls back to metadata.description without a changelog."""
    entity = _make_app_entity(
        coordinator,
        {"id": "foo", "version": "1.0", "metadata": {"description": "desc"}},
    )
    assert entity.release_summary == "desc"


# ---------------------------------------------------------------------------
# App update — installation (job flow)
# ---------------------------------------------------------------------------


async def _run_app_install(
    hass: HomeAssistant,
    coordinator: TruenasDataUpdateCoordinator,
    device_data: dict[str, Any],
) -> list[str]:
    """Run async_install driving the job/deploy flow and return the called methods."""
    entity = _make_app_entity(coordinator, device_data)
    entity.hass = hass

    captured: dict[str, Any] = {}
    methods: list[str] = []

    async def fake_subscribe(collection: str, cb: Any) -> None:
        captured[collection] = cb

    async def fake_unsubscribe(collection: str) -> None:
        return None

    async def fake_call(method: str | None = None, params: Any = None) -> Any:
        methods.append(method)
        if method in ("app.upgrade", "app.pull_images"):

            async def _fire() -> None:
                # Let async_call return and assign job_id before firing the
                # event (HA tasks start eagerly).
                await asyncio.sleep(0)
                await captured["core.get_jobs"](
                    {"fields": {"id": 99, "state": "SUCCESS", "progress": {"percent": 50}}}
                )

            hass.async_create_task(_fire())
            return 99
        return []

    coordinator.websocket.async_subscribe = AsyncMock(side_effect=fake_subscribe)
    coordinator.websocket.async_unsubscribe = AsyncMock(side_effect=fake_unsubscribe)
    coordinator.websocket.async_call = AsyncMock(side_effect=fake_call)

    with patch.object(UpdateAppSensor, "async_write_ha_state"), patch.object(
        coordinator, "async_refresh", new=AsyncMock()
    ):
        await entity.async_install(None, False)

    return methods


async def test_app_install_upgrade_calls_app_upgrade(
    hass: HomeAssistant,
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """upgrade_available → the install calls 'app.upgrade'."""
    methods = await _run_app_install(
        hass,
        coordinator,
        {
            "id": "foo",
            "version": "1.0",
            "state": "RUNNING",
            "upgrade_available": True,
            "image_updates_available": False,
        },
    )
    assert "app.upgrade" in methods


async def test_app_install_image_update_calls_pull_images(
    hass: HomeAssistant,
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """image_updates_available → the install calls 'app.pull_images'."""
    methods = await _run_app_install(
        hass,
        coordinator,
        {
            "id": "foo",
            "version": "1.0",
            "state": "RUNNING",
            "upgrade_available": False,
            "image_updates_available": True,
        },
    )
    assert "app.pull_images" in methods


async def test_app_install_no_update_does_nothing(
    hass: HomeAssistant,
    coordinator: TruenasDataUpdateCoordinator,
) -> None:
    """No update → the install triggers no upgrade call."""
    methods = await _run_app_install(
        hass,
        coordinator,
        {
            "id": "foo",
            "version": "1.0",
            "state": "RUNNING",
            "upgrade_available": False,
            "image_updates_available": False,
        },
    )
    assert "app.upgrade" not in methods
    assert "app.pull_images" not in methods
