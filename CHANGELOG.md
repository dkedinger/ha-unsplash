# Changelog

All notable changes to this project are documented here. This project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-09-06

### Fixed
- **UI showed raw translation keys** — the options menu, form labels, and abort
  messages rendered as `collection_id`, `no_collections`, and blank menu rows.
  Home Assistant only reads `translations/en.json` at runtime; `strings.json` is
  a build-time source for core integrations and is never loaded for custom ones.
  `strings.json` remains the source of truth and is mirrored to
  `translations/en.json`.
- **Photos never actually changed** — `ImageEntity` caches fetched bytes in
  `_cached_image` and never invalidates them itself, so the entity kept serving
  the first photo forever even as the coordinator rotated the URL. The cache is
  now cleared whenever a new photo URL arrives.
- **Broken reauthentication** — a revoked or rotated access key raised
  `ConfigEntryAuthFailed` with no `async_step_reauth` to handle it, leaving the
  entry unusable. Added a reauth flow that validates and stores a new key.
- **Entry setup was all-or-nothing** — one unreachable collection (deleted,
  private, or with no photo matching the orientation) failed the whole entry and
  put every collection on Home Assistant's retry backoff. Collections now refresh
  concurrently and a failing one leaves only its own entity unavailable.
- **Doubled entity names** — with `has_entity_name` set, the entity also carried
  the collection name, producing names like "Unsplash: Morning Blue Morning Blue".
- **`unsplash.refresh` could refresh the wrong entry** — entities were matched by
  collection ID suffix, so two entries (two access keys) sharing a collection both
  refreshed, costing an extra rate-limited request. Matching is now exact.
- **Crash in the options flow** — the "edit collection" step could dereference a
  missing submission; it now falls back to the collection picker.
- Hitting the Unsplash rate limit while adding a collection reported "that
  collection couldn't be found"; it now reports the rate limit.
- `async_unload_entry` no longer assumes `hass.data[DOMAIN]` exists.

### Changed
- Minimum Home Assistant version raised to **2024.11.0**. The options flow relies
  on `self.config_entry` being injected by Home Assistant, which only happens from
  2024.11 — on older releases opening options raised a 500.
- Removed the access-key validation call from entry setup. It cost one
  rate-limited request per setup and per options change (every change reloads the
  entry); the first coordinator refresh exercises the key instead and maps an auth
  failure to a reauth flow.
- Added a GitHub Actions workflow running hassfest and HACS validation, and an
  MIT `LICENSE` file that `README.md` already referenced.

## [0.2.0] - 2026-05-16

### Added
- **Per-collection refresh intervals** — each collection can now have its own refresh schedule independent of the integration default. Useful for mixing slow-rotating art (hourly) with fast-rotating photo streams (every 5 minutes) under one integration.
- **Per-collection orientation override** — pick a different orientation per collection
- **`unsplash.refresh` service** — force an immediate fetch on a specific entity or every Unsplash image entity
- **"Edit a collection" options flow step** — change display name, refresh interval, or orientation after a collection is added (previously required remove + re-add)
- **Diagnostics support** — Download Diagnostics from the integration card dumps config entry data, options, last coordinator state, and last photo payload (with the access key and any photo geolocation EXIF redacted)
- GitHub issue templates for bug reports and feature requests

### Changed
- Options menu split: the previous "Refresh settings" is now "Default refresh settings" — these defaults apply to any collection that doesn't have its own override
- Collection entries in stored options may now include optional `update_interval` and `orientation` keys

### Migration
- Existing installs continue to work without changes. Collections without per-collection overrides inherit the integration defaults exactly as before.

## [0.1.0] - 2026-05-16

Initial release.

### Added
- Config flow for entering and validating an Unsplash API Access Key
- Options flow with menu-driven management:
  - **Add a collection** — register a new public Unsplash collection
  - **Edit a collection** — change display name, refresh interval, or orientation
  - **Remove a collection** — drop a collection (its entity is removed on reload)
  - **Default refresh settings** — per-integration defaults inherited by new collections
- One `image` entity per configured Unsplash collection
- Per-collection refresh interval overrides (e.g. one collection every 5 minutes, another hourly)
- Per-collection orientation overrides (`landscape`, `portrait`, `squarish`)
- `unsplash.refresh` service that forces an immediate fetch on one or all entities
- Automatic per-photo download tracking (Unsplash API terms compliance)
- Photographer name + profile URL exposed as state attributes for attribution
- Diagnostics support — `Download Diagnostics` button on the integration card
- HACS validation + Home Assistant `hassfest` CI on every push and weekly
