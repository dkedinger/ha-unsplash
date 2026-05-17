"""Config and Options flows for the Unsplash integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    UnsplashApi,
    UnsplashApiError,
    UnsplashAuthError,
    UnsplashRateLimitError,
)
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
    MIN_UPDATE_INTERVAL,
    ORIENTATIONS,
)


class UnsplashConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial setup — collects and validates the Unsplash Access Key."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            access_key = user_input[CONF_ACCESS_KEY].strip()
            api = UnsplashApi(access_key, async_get_clientsession(self.hass))
            try:
                await api.async_validate()
            except UnsplashAuthError:
                errors["base"] = "invalid_auth"
            except UnsplashRateLimitError:
                errors["base"] = "rate_limit"
            except UnsplashApiError:
                errors["base"] = "cannot_connect"
            else:
                # Use the first 8 chars of the key as a unique_id so the same key
                # can't be added twice. (Full key in unique_id would be a leak risk.)
                await self.async_set_unique_id(f"unsplash_{access_key[:8]}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Unsplash",
                    data={CONF_ACCESS_KEY: access_key},
                    options={
                        CONF_COLLECTIONS: [],
                        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                        CONF_ORIENTATION: DEFAULT_ORIENTATION,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ACCESS_KEY): str}),
            errors=errors,
            description_placeholders={"url": "https://unsplash.com/developers"},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> UnsplashOptionsFlow:
        return UnsplashOptionsFlow(config_entry)


class UnsplashOptionsFlow(config_entries.OptionsFlow):
    """Options flow.

    Each step that mutates state calls _save() once, which writes a merged copy
    of the options back. The user can re-enter the options flow as many times
    as needed to add/remove/edit.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_collection", "remove_collection", "settings"],
        )

    # ---------- Add a collection ----------
    async def async_step_add_collection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            collection_id = str(user_input[CONF_COLLECTION_ID]).strip()
            api = UnsplashApi(
                self.config_entry.data[CONF_ACCESS_KEY],
                async_get_clientsession(self.hass),
            )
            try:
                collection_data = await api.async_get_collection(collection_id)
            except UnsplashAuthError:
                errors["base"] = "invalid_auth"
            except UnsplashApiError:
                errors[CONF_COLLECTION_ID] = "collection_not_found"
            else:
                current = list(self.config_entry.options.get(CONF_COLLECTIONS, []))
                if any(c[CONF_COLLECTION_ID] == collection_id for c in current):
                    errors[CONF_COLLECTION_ID] = "duplicate"
                else:
                    name = (
                        user_input.get(CONF_COLLECTION_NAME, "").strip()
                        or collection_data.get("title")
                        or f"Collection {collection_id}"
                    )
                    current.append(
                        {
                            CONF_COLLECTION_ID: collection_id,
                            CONF_COLLECTION_NAME: name,
                        }
                    )
                    return self._save({CONF_COLLECTIONS: current})

        return self.async_show_form(
            step_id="add_collection",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COLLECTION_ID): str,
                    vol.Optional(CONF_COLLECTION_NAME, default=""): str,
                }
            ),
            errors=errors,
        )

    # ---------- Remove a collection ----------
    async def async_step_remove_collection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        current = list(self.config_entry.options.get(CONF_COLLECTIONS, []))
        if not current:
            return self.async_abort(reason="no_collections")

        if user_input is not None:
            target = user_input[CONF_COLLECTION_ID]
            updated = [c for c in current if c[CONF_COLLECTION_ID] != target]
            return self._save({CONF_COLLECTIONS: updated})

        return self.async_show_form(
            step_id="remove_collection",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COLLECTION_ID): vol.In(
                        {
                            c[CONF_COLLECTION_ID]: (
                                f"{c[CONF_COLLECTION_NAME]} ({c[CONF_COLLECTION_ID]})"
                            )
                            for c in current
                        }
                    ),
                }
            ),
        )

    # ---------- Update refresh interval / orientation ----------
    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self._save(
                {
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                    CONF_ORIENTATION: user_input[CONF_ORIENTATION],
                }
            )

        opts = self.config_entry.options
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=opts.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    ): vol.All(int, vol.Range(min=MIN_UPDATE_INTERVAL)),
                    vol.Required(
                        CONF_ORIENTATION,
                        default=opts.get(CONF_ORIENTATION, DEFAULT_ORIENTATION),
                    ): vol.In(ORIENTATIONS),
                }
            ),
        )

    # ---------- Helpers ----------
    def _save(self, updates: dict[str, Any]) -> FlowResult:
        """Merge `updates` into current options and persist them."""
        merged = {**self.config_entry.options, **updates}
        return self.async_create_entry(title="", data=merged)
