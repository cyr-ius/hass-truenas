"""The tests for the component."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

from custom_components.truenas.const import DOMAIN
from custom_components.truenas.coordinator import TruenasDataUpdateCoordinator

from .const import MOCK_USER_INPUT

FIXTURE_DATA: dict = json.loads(
    (Path(__file__).parent / "fixtures" / "truenas.json").read_text()
)
EVENTS_DATA: dict = json.loads(
    (Path(__file__).parent / "fixtures" / "events.json").read_text()
)


# ---------------------------------------------------------------------------
# Fixtures generiques
# ---------------------------------------------------------------------------


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for hass."""
    yield


@pytest.fixture(name="config_entry")
def get_config_entry(hass: HomeAssistant) -> ConfigEntry:
    """Create and register mock config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=MOCK_USER_INPUT,
        unique_id="012345678901234",
        options={"check_dev_version": False, "notify": True},
        title=f"{DOMAIN} ({MOCK_USER_INPUT[CONF_USERNAME]})",
    )
    config_entry.add_to_hass(hass)
    return config_entry


@pytest.fixture(name="truenas_ws")
def fixture_mock_truenas_ws():
    """Mock TruenasWebsocket pour eviter les vraies connexions reseau."""
    with patch("custom_components.truenas.coordinator.TruenasWebsocket") as mock_cls:
        instance = mock_cls.return_value
        instance.is_connected = False
        instance.is_logged = False
        instance.async_close = AsyncMock()

        async def _mock_async_call(**kwargs):
            method = kwargs.get("method", "")
            if method == "system.info":
                return deepcopy(FIXTURE_DATA["system_infos"])
            if method == "interface.query":
                return deepcopy(FIXTURE_DATA["interfaces"])
            if method == "zfs.snapshot.query":
                return deepcopy(FIXTURE_DATA["snapshots"])
            if method == "disk.details":
                return deepcopy(FIXTURE_DATA["disks"])
            if method == "update.check_available":
                return deepcopy(FIXTURE_DATA["update_available"])
            if method == "update.available_versions":
                return deepcopy(FIXTURE_DATA["update_available"])
            if method == "update.get_pending":
                return deepcopy(FIXTURE_DATA["update_infos"])
            if method == "update.status":
                return deepcopy(FIXTURE_DATA["update_infos"])
            if method == "disk.temperatures":
                return {"sdb": 35.0, "sda": 36.0, "sdd": 41.0, "sdc": 36.0, "nvme0n1": 50.85}
            if method == "virt.instance.query":
                return deepcopy(FIXTURE_DATA["virtualmachines"])
            if method == "vm.query":
                return deepcopy(FIXTURE_DATA["virtualmachines"])
            if method == "app.query":
                return deepcopy(FIXTURE_DATA["apps"])
            if method == "pool.dataset.details":
                return deepcopy(FIXTURE_DATA["datasets"])
            if method == "pool.query":
                return deepcopy(FIXTURE_DATA["pools"])
            if method == "service.query":
                return deepcopy(FIXTURE_DATA["services"])
            if method == "replication.query":
                return deepcopy(FIXTURE_DATA["replications"])
            if method == "cloudsync.query":
                return deepcopy(FIXTURE_DATA["cloudsync"])
            if method == "pool.snapshottask.query":
                return deepcopy(FIXTURE_DATA["snapshottasks"])
            if method == "rsynctask.query":
                return deepcopy(FIXTURE_DATA["rsynctasks"])

            return []

        instance.async_call = AsyncMock(side_effect=_mock_async_call)

        async def _mock_async_subscribe(collection, callback):
            if collection == "reporting.realtime":
                return await callback(EVENTS_DATA["events"]["reporting.realtime"][0])
            elif collection == "alert.list":
                return await callback(EVENTS_DATA["events"]["alert.list"][0])
            elif collection == "update.status":
                return await callback(EVENTS_DATA["events"]["update.status"][0])
            elif collection == "app.query":
                for event in EVENTS_DATA["events"]["app.query"]:
                    await callback(event)

        instance.async_subscribe = AsyncMock(side_effect=_mock_async_subscribe)

        async def _mock_async_connect(*args, **kwargs):
            instance.is_connected = True
            instance.is_logged = True

        instance.async_connect = AsyncMock(side_effect=_mock_async_connect)

        yield instance


@pytest.fixture(name="coordinator")
async def fixture_coordinator(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> TruenasDataUpdateCoordinator:
    """Crée un coordinator réel avec WebSocket mocké et données chargées."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry.runtime_data
