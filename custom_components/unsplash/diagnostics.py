"""Diagnostics support for the Unsplash integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ACCESS_KEY, DOMAIN
from .coordinator import UnsplashCollectionCoordinator

# Don't leak the access key or the photographer's geolocation EXIF data
# (Unsplash includes lat/lon on some photos via the `location` block).
TO_REDACT = {CONF_ACCESS_KEY, "location", "exif"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinators: dict[str, UnsplashCollectionCoordinator] = entry_data.get(
        "coordinators", {}
    )

    coordinator_diag: dict[str, Any] = {}
    for collection_id, coord in coordinators.items():
        coordinator_diag[collection_id] = {
            "collection_name": coord.collection_name,
            "orientation": coord.orientation,
            "update_interval_seconds": (
                coord.update_interval.total_seconds()
                if coord.update_interval
                else None
            ),
            "last_update_success": coord.last_update_success,
            "last_exception": (
                str(coord.last_exception) if coord.last_exception else None
            ),
            # Latest photo payload (with sensitive fields redacted)
            "last_photo": async_redact_data(coord.data or {}, TO_REDACT),
        }

    return {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinators": coordinator_diag,
    }
