"""Tests for TrueNAS sensor entities."""

from datetime import UTC, datetime
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


# ---------------------------------------------------------------------------
# Sensors système
# ---------------------------------------------------------------------------


async def test_system_cpu_temperature(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_cpu_temperature retourne la température CPU depuis events."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_temperature_cpu_mean")
    assert state is not None
    assert state.state == "74.0"


async def test_system_cpu_usage(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_cpu_usage retourne l'utilisation CPU depuis events."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_cpu_usage")
    assert state is not None
    assert state.state == "14.0"


async def test_system_load_shortterm(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_load_shortterm retourne loadavg[0] depuis system_infos."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_cpu_load_shortterm")
    assert state is not None
    assert state.state == "0.5595703125"


async def test_system_load_midterm(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_load_midterm retourne loadavg[1] depuis system_infos."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_cpu_load_midterm")
    assert state is not None
    assert state.state == "0.72509765625"


async def test_system_load_longterm(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_load_longterm retourne loadavg[2] depuis system_infos."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_cpu_load_longterm")
    assert state is not None
    assert state.state == "0.72900390625"


async def test_system_memory_available(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_memory_available retourne la mémoire disponible en GiB."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_memory_available")
    assert state is not None
    assert state.state == "1.76"


async def test_system_memory_usage(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_memory_usage retourne le pourcentage d'utilisation mémoire."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_memory_usage")
    assert state is not None
    assert state.state == "88.56"


async def test_system_arc_size(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_arc_size retourne la taille ARC en GiB."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_arc_size")
    assert state is not None
    assert state.state == "7.56"


async def test_system_arc_ratio(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_arc_ratio retourne le ratio ARC en %."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_arc_ratio")
    assert state is not None
    assert state.state == "49.09"


async def test_system_uptime_returns_datetime(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """system_uptime retourne un datetime UTC dans le passé."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_uptime")
    assert state is not None

    value = datetime.fromisoformat(state.state)
    assert value.tzinfo is not None
    assert value < datetime.now(UTC)


# ---------------------------------------------------------------------------
# Unique IDs — sensors système
# ---------------------------------------------------------------------------


async def test_system_sensor_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """unique_id d'un sensor système est formé correctement."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get("sensor.truenas_test_system_temperature_cpu_mean")
    assert entry is not None
    assert entry.unique_id == "Truenas_test-system_cpu_temperature"


# ---------------------------------------------------------------------------
# Pool sensor (uid = name)
# ---------------------------------------------------------------------------


async def test_pool_free_value(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """pool_free retourne l'espace libre en GiB pour volume1."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_pool_volume1_free")
    assert state is not None
    assert state.state == "592.52"


async def test_pool_free_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """unique_id du sensor pool_free est formé correctement."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get("sensor.truenas_test_pool_volume1_free")
    assert entry is not None
    assert entry.unique_id == "Truenas_test-pool_free-volume1"


async def test_pool_free_extra_attributes(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """pool_free expose les attributes extra attendus."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_pool_volume1_free")
    assert state is not None
    attrs = state.attributes
    assert attrs["status"] == "ONLINE"
    assert attrs["healthy"] is True
    assert "size" in attrs


# ---------------------------------------------------------------------------
# Sensors réseau (uid = name)
# ---------------------------------------------------------------------------


async def test_traffic_rx_value(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """traffic_rx retourne le débit entrant en KiB/s pour enp2s0."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_enp2s0_rx")
    assert state is not None
    assert state.state == "31.05"


async def test_traffic_tx_value(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """traffic_tx retourne le débit sortant en KiB/s pour enp2s0."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_system_enp2s0_tx")
    assert state is not None
    assert state.state == "161.8"


async def test_traffic_rx_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """unique_id de traffic_rx est formé correctement."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get("sensor.truenas_test_system_enp2s0_rx")
    assert entry is not None
    assert entry.unique_id == "Truenas_test-traffic_rx-enp2s0"


# ---------------------------------------------------------------------------
# Disk sensors (uid = name)
# ---------------------------------------------------------------------------


async def test_disk_used_value(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """disk_used retourne la taille en GiB pour nvme0n1."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_disk_nvme0n1")
    assert state is not None
    assert state.state == "232.89"


async def test_disk_used_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """unique_id de disk_used est formé correctement."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get("sensor.truenas_test_disk_nvme0n1")
    assert entry is not None
    assert entry.unique_id == "Truenas_test-disk_used-nvme0n1"


async def test_disk_temperature_value(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """disk_temperature retourne la température en °C pour sdb."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_disk_sdb_2")
    assert state is not None
    assert state.state == "35.0"


async def test_disk_temperature_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """unique_id de disk_temperature est formé correctement."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get("sensor.truenas_test_disk_sdb_2")
    assert entry is not None
    assert entry.unique_id == "Truenas_test-disk_temperature-sdb"


# ---------------------------------------------------------------------------
# Dataset sensors (uid = id)
# ---------------------------------------------------------------------------


async def test_dataset_value(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """dataset retourne l'espace utilisé en GiB pour volume1."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_datasets_volume1")
    assert state is not None
    assert state.state == "1674.21"


async def test_dataset_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """unique_id de dataset est formé correctement."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get("sensor.truenas_test_datasets_volume1")
    assert entry is not None
    assert entry.unique_id == "Truenas_test-dataset-volume1"


async def test_dataset_snapshot_value(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """dataset_snapshot retourne le nombre de snapshots pour volume1."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.truenas_test_datasets_volume1_snapshots")
    assert state is not None
    assert state.state == "15"


async def test_dataset_snapshot_unique_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """unique_id de dataset_snapshot est formé correctement."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entry = registry.async_get("sensor.truenas_test_datasets_volume1_snapshots")
    assert entry is not None
    assert entry.unique_id == "Truenas_test-dataset_snapshot-volume1"
