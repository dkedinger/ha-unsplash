"""Minimal async Unsplash API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class UnsplashApiError(Exception):
    """Generic Unsplash API error."""


class UnsplashAuthError(UnsplashApiError):
    """Raised when the access key is rejected."""


class UnsplashRateLimitError(UnsplashApiError):
    """Raised when Unsplash returns 403 due to rate limiting."""


class UnsplashApi:
    """Thin async wrapper around the public Unsplash REST API.

    Only implements the endpoints this integration actually needs:
      - validate the key
      - look up a collection's metadata
      - fetch a random photo from a collection
      - ping the per-photo download_location (required by Unsplash terms)
    """

    def __init__(self, access_key: str, session: aiohttp.ClientSession) -> None:
        self._access_key = access_key
        self._session = session

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Client-ID {self._access_key}",
            "Accept-Version": "v1",
        }

    async def _request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{API_BASE}{path}"
        try:
            async with self._session.get(
                url, headers=self._headers, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 401:
                    raise UnsplashAuthError("Invalid Unsplash access key")
                if resp.status == 403:
                    # Could be rate limit OR auth-scope issue; check header for clarity.
                    remaining = resp.headers.get("X-Ratelimit-Remaining")
                    if remaining == "0":
                        raise UnsplashRateLimitError("Unsplash rate limit exceeded")
                    raise UnsplashAuthError(
                        "Unsplash rejected the request (403 — check the access key)"
                    )
                if resp.status == 404:
                    raise UnsplashApiError(f"Not found: {path}")
                if resp.status >= 400:
                    body = await resp.text()
                    raise UnsplashApiError(
                        f"Unsplash API error {resp.status}: {body[:200]}"
                    )
                return await resp.json()
        except aiohttp.ClientError as err:
            raise UnsplashApiError(f"Network error talking to Unsplash: {err}") from err

    async def async_validate(self) -> bool:
        """Verify the access key works by hitting a public endpoint.

        Uses /photos/random because it's the cheapest call that requires a valid Client-ID.
        """
        await self._request("/photos/random")
        return True

    async def async_get_collection(self, collection_id: str) -> dict[str, Any]:
        """Fetch collection metadata (title, total photos, etc)."""
        return await self._request(f"/collections/{collection_id}")

    async def async_get_random_photo(
        self,
        collection_id: str,
        orientation: str = "landscape",
    ) -> dict[str, Any]:
        """Fetch a single random photo from a specific collection."""
        return await self._request(
            "/photos/random",
            params={
                "collections": collection_id,
                "orientation": orientation,
            },
        )

    async def async_track_download(self, download_location: str) -> None:
        """Ping the photo's download_location per Unsplash API terms.

        Required whenever a photo is "used" (displayed in our case).
        See: https://help.unsplash.com/en/articles/2511258
        """
        try:
            async with self._session.get(
                download_location,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status >= 400:
                    _LOGGER.debug(
                        "Unsplash download tracking returned %s", resp.status
                    )
        except aiohttp.ClientError as err:
            _LOGGER.debug("Unsplash download tracking failed: %s", err)
