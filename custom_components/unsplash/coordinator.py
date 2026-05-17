"""DataUpdateCoordinator that pulls a fresh random photo per collection."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import UnsplashApi, UnsplashApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class UnsplashCollectionCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches one random photo per refresh from a single Unsplash collection."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: UnsplashApi,
        collection_id: str,
        collection_name: str,
        orientation: str,
        update_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{collection_id}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.api = api
        self.collection_id = collection_id
        self.collection_name = collection_name
        self.orientation = orientation

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            photo = await self.api.async_get_random_photo(
                collection_id=self.collection_id,
                orientation=self.orientation,
            )
        except UnsplashApiError as err:
            raise UpdateFailed(f"Unsplash API error: {err}") from err

        # Per Unsplash terms, ping the download_location every time we "use" a photo.
        # Fire-and-forget — don't block the coordinator on attribution.
        if (
            isinstance(photo, dict)
            and (links := photo.get("links"))
            and (download_location := links.get("download_location"))
        ):
            self.hass.async_create_background_task(
                self.api.async_track_download(download_location),
                name=f"{DOMAIN}_track_download_{self.collection_id}",
            )

        return photo
