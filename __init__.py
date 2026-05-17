"""The Unsplash integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import UnsplashApi, UnsplashApiError, UnsplashAuthError
from .const import (
    CONF_ACCESS_KEY,
    CONF_COLLECTION_ID,
    CONF_COLLECTION_NAME,
    CONF_COLLECTIONS,
    CONF_ORIENTATION,
    CONF_UPDATE_INTERVAL,
    DEFAULT_ORIENTATION,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .coordinator import UnsplashCollectionCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.IMAGE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Unsplash from a config entry."""
    session = async_get_clientsession(hass)
    api = UnsplashApi(entry.data[CONF_ACCESS_KEY], session)

    # Validate the key up front. If it fails authentication, surface a re-auth flow;
    # if it fails for a transient reason, let HA retry the setup later.
    try:
        await api.async_validate()
    except UnsplashAuthError as err:
        raise ConfigEntryAuthFailed("Invalid Unsplash access key") from err
    except UnsplashApiError as err:
        raise ConfigEntryNotReady(f"Cannot reach Unsplash: {err}") from err

    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
    )
    orientation = entry.options.get(CONF_ORIENTATION, DEFAULT_ORIENTATION)
    collections = entry.options.get(CONF_COLLECTIONS, [])

    coordinators: dict[str, UnsplashCollectionCoordinator] = {}
    for coll in collections:
        coord = UnsplashCollectionCoordinator(
            hass=hass,
            api=api,
            collection_id=coll[CONF_COLLECTION_ID],
            collection_name=coll[CONF_COLLECTION_NAME],
            orientation=orientation,
            update_interval=update_interval,
        )
        # First refresh inline so the entity has data before async_add_entities runs.
        # If it fails we still set up the entry — entity will retry on its own schedule.
        await coord.async_config_entry_first_refresh()
        coordinators[coll[CONF_COLLECTION_ID]] = coord

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry whenever options change (collections added/removed, interval changed, etc.)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry whenever options change."""
    await hass.config_entries.async_reload(entry.entry_id)
