"""Service for TrueNAS integration."""

from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
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

    def _extract_uid(entity_id: str, key: str) -> str:
        """Extract the TrueNAS uid from an entity unique_id."""
        entry = er.async_get(hass).async_get(entity_id)
        device_name = coordinator.config_entry.data[CONF_NAME].capitalize()
        prefix = f"{device_name}-{key}-"
        return entry.unique_id[len(prefix):]

    async def take_snapshot(call: ServiceCall) -> None:
        """Take a snapshot of a dataset."""
        dataset = _extract_uid(call.data.get(CONF_ENTITY_ID), "snapshottask")
        await coordinator.websocket.async_call(
            method="zfs.snapshot.create",
            params=[{"dataset": dataset, "name": "manual"}],
        )

    async def start_cloudsync(call: ServiceCall) -> None:
        """Start cloudsync."""
        task_id = int(_extract_uid(call.data.get(CONF_ENTITY_ID), "cloudsync"))
        await coordinator.websocket.async_call(
            method="cloudsync.sync",
            params=[task_id],
        )

    async def service_reload(call: ServiceCall) -> None:
        """Reload a service."""
        service_name = _extract_uid(call.data.get(CONF_ENTITY_ID), "service")
        await coordinator.websocket.async_call(
            method="service.reload",
            params=[service_name],
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
