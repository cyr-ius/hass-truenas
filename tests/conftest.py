"""The tests for the component."""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    load_json_object_fixture,
)

from custom_components.truenas.const import DOMAIN

from .const import MOCK_USER_INPUT


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for hass."""
    yield


@pytest.fixture(name="HeatzyClient")
def mock_router(request) -> Generator[MagicMock | AsyncMock]:
    """Mock a successful connection."""
    api = load_json_object_fixture("truenas.json")

    with patch("custom_components.truenas.coordinator.TruenasClient") as mock:
        instance = mock.return_value

        type(instance).__devices = PropertyMock(return_value=api)
        yield instance


@pytest.fixture(name="config_entry")
def get_config_entry(hass: HomeAssistant) -> ConfigEntry:
    """Create and register mock config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=MOCK_USER_INPUT,
        unique_id="012345678901234",
        options={"check_dev_version": False, "notify": False},
        title=f"{DOMAIN} ({MOCK_USER_INPUT[CONF_USERNAME]})",
    )
    config_entry.add_to_hass(hass)
    return config_entry
