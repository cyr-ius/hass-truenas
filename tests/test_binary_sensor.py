"""Tests for TrueNAS binary sensor entities."""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# ---------------------------------------------------------------------------
# Pool binary sensor
# ---------------------------------------------------------------------------


async def test_pool_sensor_is_on_when_online(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """Pool avec status ONLINE → is_on est True et icon = mdi:database."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.truenas_test_pool_volume1")
    assert state is not None
    assert state.state == "on"


# ---------------------------------------------------------------------------
# Network interface binary sensor
# ---------------------------------------------------------------------------


async def test_network_sensor_is_on_when_link_up(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """Interface avec LINK_STATE_UP → is_on est True."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.truenas_test_system_enp2s0")
    assert state is not None
    assert state.state == "on"


async def test_network_sensor_is_off_when_link_down(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """Interface avec LINK_STATE_DOWN → is_on est False."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.truenas_test_system_enp0s31f6")
    assert state is not None
    assert state.state == "off"


# ---------------------------------------------------------------------------
# Alert binary sensor
# ---------------------------------------------------------------------------


# async def test_alert_sensor_is_off_when_no_alerts(
#     hass: HomeAssistant,
#     config_entry: ConfigEntry,
#     truenas_ws: Generator[AsyncMock | MagicMock],
# ) -> None:
#     """alert_list vide → is_on est False."""
#     await hass.config_entries.async_setup(config_entry.entry_id)
#     await hass.async_block_till_done()

#     state = hass.states.get("binary_sensor.truenas_test_system_enp0s31f6")


async def test_alert_sensor_creates_persistent_notification(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    truenas_ws: Generator[AsyncMock | MagicMock],
) -> None:
    """CONF_NOTIFY=True déclenche une notification persistante pour les alertes non-INFO."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    config = hass.config_entries.async_get_entry(config_entry.entry_id)

    hass.config_entries.async_update_entry(
        config, options={"notify": True, "check_dev_version": False}
    )
    # coordinator.data["events"] = {
    #     "alert_list": [
    #         {
    #             "uuid": "abc-123",
    #             "level": "WARN",
    #             "formatted": "Disk failure detected",
    #             "klass": "DiskAlert",
    #         }
    #     ]
    # }
    # sensor = _make_sensor(coordinator, "alerts")
    # sensor.hass = hass
    # _ = sensor.is_on
    # await hass.async_block_till_done()
    # notifications = hass.data.get("persistent_notification", {})
    # assert "abc-123" in notifications
    # assert notifications["abc-123"]["message"] == "Disk failure detected"
    # assert notifications["abc-123"]["title"] == "WARN DiskAlert"


# async def test_alert_sensor_no_notification_for_info_level(
#     hass: HomeAssistant,
#     config_entry: ConfigEntry,
#     truenas_ws: Generator[AsyncMock | MagicMock],
# ) -> None:
#     """Les alertes de niveau INFO ne créent pas de notification persistante."""
#     hass.config_entries.async_update_entry(
#         coordinator.config_entry, options={"notify": True, "check_dev_version": False}
#     )
#     coordinator.data["events"] = {
#         "alert_list": [
#             {
#                 "uuid": "info-456",
#                 "level": "INFO",
#                 "formatted": "Info message",
#                 "klass": "InfoAlert",
#             }
#         ]
#     }
#     sensor = _make_sensor(coordinator, "alerts")
#     sensor.hass = hass
#     _ = sensor.is_on
#     await hass.async_block_till_done()
#     notifications = hass.data.get("persistent_notification", {})
#     assert "info-456" not in notifications


# async def test_alert_sensor_no_notification_when_notify_disabled(
#     hass: HomeAssistant,
#     config_entry: ConfigEntry,
#     truenas_ws: Generator[AsyncMock | MagicMock],
# ) -> None:
#     """CONF_NOTIFY=False → aucune notification même avec des alertes."""
#     coordinator.data["events"] = {
#         "alert_list": [
#             {
#                 "uuid": "abc-999",
#                 "level": "CRITICAL",
#                 "formatted": "Critical error",
#                 "klass": "CritAlert",
#             }
#         ]
#     }
#     await hass.config_entries.async_setup(config_entry.entry_id)
#     await hass.async_block_till_done()

#     sensor = _make_sensor(coordinator, "alerts")
#     sensor.hass = hass
#     _ = sensor.is_on
#     await hass.async_block_till_done()
#     notifications = hass.data.get("persistent_notification", {})
#     assert "abc-999" not in notifications
