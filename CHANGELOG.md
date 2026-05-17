# Changelog

All notable changes to this project are documented here. This project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
