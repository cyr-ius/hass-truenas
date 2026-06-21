"""Tests for TrueNAS services."""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.truenas.const import DOMAIN
from custom_components.truenas.coordinator import TruenasDataUpdateCoordinator
from custom_components.truenas.service import (
    SERVICE_CLOUDSYNC_RUN,
    SERVICE_DATASET_SNAPSHOT,
    SERVICE_SERVICE_RELOAD,
)


def _last_call_kwargs(coordinator: TruenasDataUpdateCoordinator) -> dict:
    """Return the kwargs of the last websocket async_call."""
    return coordinator.websocket.async_call.call_args.kwargs


# ---------------------------------------------------------------------------
# Service registration
# ---------------------------------------------------------------------------


async def test_services_are_registered(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """The three services are registered during setup."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_DATASET_SNAPSHOT)
    assert hass.services.has_service(DOMAIN, SERVICE_CLOUDSYNC_RUN)
    assert hass.services.has_service(DOMAIN, SERVICE_SERVICE_RELOAD)


# ---------------------------------------------------------------------------
# service_reload
# ---------------------------------------------------------------------------


async def test_service_reload_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """service_reload extracts the service name and calls 'service.reload'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: TruenasDataUpdateCoordinator = config_entry.runtime_data
    coordinator.websocket.async_call.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SERVICE_RELOAD,
        {CONF_ENTITY_ID: "switch.truenas_test_services_cifs"},
        blocking=True,
    )

    kwargs = _last_call_kwargs(coordinator)
    assert kwargs["method"] == "service.reload"
    assert kwargs["params"] == ["cifs"]


# ---------------------------------------------------------------------------
# dataset_snapshot
# ---------------------------------------------------------------------------


async def test_dataset_snapshot_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """dataset_snapshot extracts the dataset uid and calls 'zfs.snapshot.create'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # No snapshottask entity exists in the fixtures: register one manually so the
    # uid extraction can resolve it.
    registry = er.async_get(hass)
    entry = registry.async_get_or_create(
        domain="sensor",
        platform=DOMAIN,
        unique_id="Truenas_test-snapshottask-tank/data",
        config_entry=config_entry,
        suggested_object_id="truenas_test_snapshottask",
    )

    coordinator: TruenasDataUpdateCoordinator = config_entry.runtime_data
    coordinator.websocket.async_call.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_DATASET_SNAPSHOT,
        {CONF_ENTITY_ID: entry.entity_id},
        blocking=True,
    )

    kwargs = _last_call_kwargs(coordinator)
    assert kwargs["method"] == "zfs.snapshot.create"
    assert kwargs["params"] == [{"dataset": "tank/data", "name": "manual"}]


# ---------------------------------------------------------------------------
# cloudsync_run
# ---------------------------------------------------------------------------


async def test_cloudsync_run_calls_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """cloudsync_run extracts the numeric task id and calls 'cloudsync.sync'."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get_or_create(
        domain="sensor",
        platform=DOMAIN,
        unique_id="Truenas_test-cloudsync-42",
        config_entry=config_entry,
        suggested_object_id="truenas_test_cloudsync",
    )

    coordinator: TruenasDataUpdateCoordinator = config_entry.runtime_data
    coordinator.websocket.async_call.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOUDSYNC_RUN,
        {CONF_ENTITY_ID: entry.entity_id},
        blocking=True,
    )

    kwargs = _last_call_kwargs(coordinator)
    assert kwargs["method"] == "cloudsync.sync"
    assert kwargs["params"] == [42]
