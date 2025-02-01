"""Service for TrueNAS integration."""

from __future__ import annotations

from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import TruenasDataUpdateCoordinator

SERVICE_CLOUDSYNC_RUN = "cloudsync_run"
SCHEMA_SERVICE_CLOUDSYNC_RUN = {}

SERVICE_DATASET_SNAPSHOT = "dataset_snapshot"
SCHEMA_SERVICE_DATASET_SNAPSHOT = {}

SERVICE_SERVICE_RELOAD = "service_reload"
SCHEMA_SERVICE_SERVICE_RELOAD = {}

ATTR_NAME = "name"
ATTR_ID = "id"


async def async_setup_services(
    hass: HomeAssistant, coordinator: TruenasDataUpdateCoordinator
):
    """Register services."""

    async def take_snapshot(call: ServiceCall) -> None:
        """Create dataset snapshot."""
        entity_id = call.data.get(CONF_ENTITY_ID)
        entity = er.async_get(hass).async_get(entity_id)
        await coordinator.api.async_take_snapshot(
            name=entity.extended_dict.get("original_name").lower()
        )

    async def start_cloudsync(call: ServiceCall) -> None:
        """Create dataset snapshot."""
        entity_id = call.data.get(CONF_ENTITY_ID)
        entity = er.async_get(hass).async_get(entity_id)
        await coordinator.api.async_sync_cloudsync(
            id=entity.extended_dict.get("original_name").lower()
        )

    async def service_reload(call: ServiceCall) -> None:
        """Create dataset snapshot."""
        entity_id = call.data.get(CONF_ENTITY_ID)
        entity = er.async_get(hass).async_get(entity_id)
        await coordinator.api.async_reload_service(
            service=entity.extended_dict.get("original_name").lower()
        )

    hass.services.async_register(
        DOMAIN, SERVICE_DATASET_SNAPSHOT, take_snapshot, SCHEMA_SERVICE_DATASET_SNAPSHOT
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLOUDSYNC_RUN, start_cloudsync, SCHEMA_SERVICE_DATASET_SNAPSHOT
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SERVICE_RELOAD, service_reload, SCHEMA_SERVICE_SERVICE_RELOAD
    )
