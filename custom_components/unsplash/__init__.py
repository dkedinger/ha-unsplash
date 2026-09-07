"""The Unsplash integration."""
from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import UnsplashApi
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
    SERVICE_REFRESH,
)
from .coordinator import UnsplashCollectionCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.IMAGE]

SERVICE_REFRESH_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Unsplash from a config entry."""
    session = async_get_clientsession(hass)
    api = UnsplashApi(entry.data[CONF_ACCESS_KEY], session)

    # No separate key validation here: it would cost one rate-limited request
    # per setup *and* per options change (every change reloads the entry). The
    # first coordinator refresh exercises the key, and the coordinator maps an
    # auth failure to ConfigEntryAuthFailed, which starts the reauth flow.

    # Per-entry defaults (used when a collection doesn't override).
    default_interval = entry.options.get(
        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
    )
    default_orientation = entry.options.get(CONF_ORIENTATION, DEFAULT_ORIENTATION)
    collections = entry.options.get(CONF_COLLECTIONS, [])

    coordinators: dict[str, UnsplashCollectionCoordinator] = {}
    for coll in collections:
        # Each collection may override the per-entry defaults.
        interval = coll.get(CONF_UPDATE_INTERVAL, default_interval)
        orientation = coll.get(CONF_ORIENTATION, default_orientation)

        coord = UnsplashCollectionCoordinator(
            hass=hass,
            api=api,
            collection_id=coll[CONF_COLLECTION_ID],
            collection_name=coll[CONF_COLLECTION_NAME],
            orientation=orientation,
            update_interval=interval,
        )
        coordinators[coll[CONF_COLLECTION_ID]] = coord

    # Refresh every collection concurrently so setup doesn't serialize N HTTP
    # calls. async_refresh (not async_config_entry_first_refresh) is deliberate:
    # a single bad collection — deleted, private, or with no photo matching the
    # orientation — leaves only its own entity unavailable instead of failing
    # the whole entry and retrying every collection on HA's backoff timer.
    if coordinators:
        await asyncio.gather(
            *(coord.async_refresh() for coord in coordinators.values())
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the refresh service exactly once across all entries.
    _async_register_services(hass)

    # Reload entry whenever options change (collections added/removed/edited).
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)

        # Last entry going away — remove the service so it doesn't linger.
        if not domain_data:
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)

    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry whenever options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_services(hass: HomeAssistant) -> None:
    """Register the unsplash.refresh service (idempotent across entries)."""
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        return

    async def async_handle_refresh(call: ServiceCall) -> None:
        """Force one or more Unsplash image entities to fetch a new photo now."""
        target_entity_ids: list[str] | None = call.data.get(ATTR_ENTITY_ID)
        ent_reg = er.async_get(hass)

        # Collect the matching coordinators first so we don't await inside
        # iteration over hass.data (which can mutate on reloads).
        to_refresh: list[UnsplashCollectionCoordinator] = []

        # Unique IDs are "{entry_id}_{collection_id}", so resolve the requested
        # entity_ids to those exact unique IDs first. Matching on the collection
        # ID alone would also refresh a second account's entry that happens to
        # use the same collection — an extra rate-limited request each time.
        target_unique_ids: set[str] | None = None
        if target_entity_ids is not None:
            target_unique_ids = set()
            for ent_id in target_entity_ids:
                reg_entry = ent_reg.async_get(ent_id)
                if reg_entry and reg_entry.platform == DOMAIN:
                    target_unique_ids.add(reg_entry.unique_id)

        for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
            coordinators: dict[str, UnsplashCollectionCoordinator] = entry_data[
                "coordinators"
            ]
            for collection_id, coord in coordinators.items():
                if (
                    target_unique_ids is None  # No targets supplied — refresh all.
                    or f"{entry_id}_{collection_id}" in target_unique_ids
                ):
                    to_refresh.append(coord)

        for coord in to_refresh:
            await coord.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        async_handle_refresh,
        schema=SERVICE_REFRESH_SCHEMA,
    )
