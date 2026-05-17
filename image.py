"""Image entity platform for Unsplash."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_COLLECTION_ID,
    ATTR_COLLECTION_NAME,
    ATTR_DESCRIPTION,
    ATTR_IMAGE_URL,
    ATTR_IMAGE_URL_FULL,
    ATTR_PHOTO_PAGE_URL,
    ATTR_PHOTOGRAPHER,
    ATTR_PHOTOGRAPHER_URL,
    DOMAIN,
)
from .coordinator import UnsplashCollectionCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one image entity per configured collection."""
    coordinators: dict[str, UnsplashCollectionCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ]["coordinators"]

    entities = [
        UnsplashCollectionImage(hass, entry, coordinator)
        for coordinator in coordinators.values()
    ]
    async_add_entities(entities)


class UnsplashCollectionImage(
    CoordinatorEntity[UnsplashCollectionCoordinator], ImageEntity
):
    """An image entity backed by a single Unsplash collection.

    Each refresh of the coordinator swaps in a new random photo from the
    collection. The image_url returns whatever Unsplash served us most recently
    and image_last_updated triggers HA's frontend to refresh the picture.
    """

    _attr_has_entity_name = True
    _attr_content_type = "image/jpeg"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: UnsplashCollectionCoordinator,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_{coordinator.collection_id}"
        self._attr_name = coordinator.collection_name
        self._current_url: str | None = None
        self._update_image_state()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry_id}_{self.coordinator.collection_id}")},
            name=f"Unsplash: {self.coordinator.collection_name}",
            manufacturer="Unsplash",
            model="Collection",
            configuration_url=(
                f"https://unsplash.com/collections/{self.coordinator.collection_id}"
            ),
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Coordinator delivered new data — pick up the new photo URL."""
        self._update_image_state()
        super()._handle_coordinator_update()

    def _update_image_state(self) -> None:
        photo = self.coordinator.data
        if not photo:
            return
        urls = photo.get("urls") or {}
        # `regular` is ~1080px wide — good balance for tablet/desktop dashboards.
        # `full` is the raw uploaded size (often huge); we keep it as an attribute.
        new_url = urls.get("regular") or urls.get("full")
        if new_url and new_url != self._current_url:
            self._current_url = new_url
            self._attr_image_last_updated = dt_util.utcnow()

    @property
    def image_url(self) -> str | None:
        return self._current_url

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        photo = self.coordinator.data or {}
        user = photo.get("user") or {}
        user_links = user.get("links") or {}
        urls = photo.get("urls") or {}
        links = photo.get("links") or {}
        return {
            ATTR_COLLECTION_ID: self.coordinator.collection_id,
            ATTR_COLLECTION_NAME: self.coordinator.collection_name,
            ATTR_PHOTOGRAPHER: user.get("name"),
            ATTR_PHOTOGRAPHER_URL: user_links.get("html"),
            ATTR_DESCRIPTION: (
                photo.get("description") or photo.get("alt_description")
            ),
            ATTR_PHOTO_PAGE_URL: links.get("html"),
            ATTR_IMAGE_URL: urls.get("regular"),
            ATTR_IMAGE_URL_FULL: urls.get("full"),
        }
