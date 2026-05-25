"""Truenas platform configuration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import PLATFORMS
from .coordinator import TruenasDataUpdateCoordinator

# from .service import async_setup_services

type TruenasConfigEntry = ConfigEntry[TruenasDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TruenasConfigEntry) -> bool:
    """Set up Heatzy as config entry."""
    coordinator = TruenasDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # await async_setup_services(hass, coordinator)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: TruenasConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True
