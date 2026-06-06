"""Tests for the TrueNAS config flow."""

from unittest.mock import AsyncMock, PropertyMock, patch

import pytest
from homeassistant import config_entries, setup
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from truenaspy import AuthenticationFailed, TruenasException
from truenaspy import ConnectionError as TruenasConnectionError

from custom_components.truenas.const import (
    CONF_CHECK_DEV_VERSION,
    CONF_NOTIFY,
    DEFAULT_PORT,
    DOMAIN,
)

MOCK_CONFIG = {
    CONF_NAME: "truenas_test",
    CONF_HOST: "192.168.1.100",
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "secret",
    CONF_PORT: DEFAULT_PORT,
    CONF_SSL: True,
    CONF_VERIFY_SSL: True,
}


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Override async_setup_entry."""
    with patch("custom_components.truenas.async_setup_entry", return_value=True):
        yield


# ---------------------------------------------------------------------------
# User step — succès
# ---------------------------------------------------------------------------


async def test_user_success(hass: HomeAssistant, truenas_ws) -> None:
    """Une entrée est créée quand la connection WebSocket réussit."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    with patch("custom_components.truenas.config_flow.TruenasWebsocket") as mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert not result.get("errors")

        mock.return_value = truenas_ws
        type(mock).is_connected = PropertyMock(return_value=True)
        type(mock).is_logged = PropertyMock(return_value=True)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONFIG
        )
        await hass.async_block_till_done()

        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["data"] == MOCK_CONFIG


# ---------------------------------------------------------------------------
# User step — erreurs de connection (drapeaux is_connected / is_logged)
# ---------------------------------------------------------------------------


async def test_user_cannot_connect_flag(hass: HomeAssistant, truenas_ws) -> None:
    """L'erreur cannot_connect est affichée si is_connected retourne False."""
    with patch("custom_components.truenas.config_flow.TruenasWebsocket") as mock:
        mock.return_value = truenas_ws
        mock.return_value.async_connect = AsyncMock()
        mock.return_value.is_connected = False
        mock.return_value.is_logged = True
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_CONFIG
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


# ---------------------------------------------------------------------------
# User step — erreurs via exceptions
# ---------------------------------------------------------------------------


async def test_user_authentication_failed_exception(
    hass: HomeAssistant, truenas_ws
) -> None:
    """L'erreur invalid_auth est affichée sur AuthenticationFailed."""
    with patch("custom_components.truenas.config_flow.TruenasWebsocket") as mock:
        mock.return_value = truenas_ws
        mock.return_value.async_connect.side_effect = AuthenticationFailed(
            "Login failed"
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_CONFIG
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


async def test_user_connection_error_exception(hass: HomeAssistant, truenas_ws) -> None:
    """L'erreur cannot_connect est affichée sur ConnectionError."""
    with patch("custom_components.truenas.config_flow.TruenasWebsocket") as mock:
        mock.return_value = truenas_ws
        mock.return_value.async_connect.side_effect = TruenasConnectionError(
            "Connection failed"
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_CONFIG
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_user_unknown_exception(hass: HomeAssistant, truenas_ws) -> None:
    """L'erreur unknown est affichée sur TruenasException générique."""
    with patch("custom_components.truenas.config_flow.TruenasWebsocket") as mock:
        mock.return_value = truenas_ws
        mock.return_value.async_connect.side_effect = TruenasException("Unknown error")

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_CONFIG
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "unknown"


# ---------------------------------------------------------------------------
# User step — doublon
# ---------------------------------------------------------------------------


async def test_duplicate_entry_abort(hass: HomeAssistant, truenas_ws) -> None:
    """Une deuxième entrée avec le même CONF_NAME est refusée."""
    MockConfigEntry(
        domain=DOMAIN, unique_id=MOCK_CONFIG[CONF_NAME], data=MOCK_CONFIG
    ).add_to_hass(hass)

    with patch("custom_components.truenas.config_flow.TruenasWebsocket") as mock:
        mock.return_value = truenas_ws
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_CONFIG
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Import step
# ---------------------------------------------------------------------------


async def test_import_step_delegates_to_user(hass: HomeAssistant, truenas_ws) -> None:
    """async_step_import délègue à async_step_user et crée l'entrée."""
    with patch("custom_components.truenas.config_flow.TruenasWebsocket") as mock:
        mock.return_value = truenas_ws

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=MOCK_CONFIG
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == MOCK_CONFIG


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------


async def test_options_flow_show_form(hass: HomeAssistant, config_entry) -> None:
    """Le formulaire d'options est affiché sans erreur."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_save(hass: HomeAssistant, config_entry) -> None:
    """Les options sont sauvegardées correctement."""
    with (
        patch("custom_components.truenas.async_setup_entry", return_value=True),
        patch("custom_components.truenas.async_unload_entry", return_value=True),
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_NOTIFY: True, CONF_CHECK_DEV_VERSION: True},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert config_entry.options == {CONF_NOTIFY: True, CONF_CHECK_DEV_VERSION: True}
