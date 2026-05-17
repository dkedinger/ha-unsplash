"""Constants for the Unsplash integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "unsplash"

# Config / options keys
CONF_ACCESS_KEY: Final = "access_key"
CONF_COLLECTIONS: Final = "collections"
CONF_COLLECTION_ID: Final = "collection_id"
CONF_COLLECTION_NAME: Final = "collection_name"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_ORIENTATION: Final = "orientation"

# Defaults
DEFAULT_UPDATE_INTERVAL: Final = 900   # 15 minutes
MIN_UPDATE_INTERVAL: Final = 60        # 1 minute floor — keeps users from blowing rate limits
DEFAULT_ORIENTATION: Final = "landscape"
ORIENTATIONS: Final = ["landscape", "portrait", "squarish"]

# Unsplash API
API_BASE: Final = "https://api.unsplash.com"

# Entity extra_state_attributes
ATTR_PHOTOGRAPHER: Final = "photographer"
ATTR_PHOTOGRAPHER_URL: Final = "photographer_url"
ATTR_DESCRIPTION: Final = "description"
ATTR_PHOTO_PAGE_URL: Final = "photo_page_url"
ATTR_IMAGE_URL: Final = "image_url"
ATTR_IMAGE_URL_FULL: Final = "image_url_full"
ATTR_COLLECTION_ID: Final = "collection_id"
ATTR_COLLECTION_NAME: Final = "collection_name"
