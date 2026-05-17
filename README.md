# Unsplash for Home Assistant

A Home Assistant custom integration that turns any public [Unsplash](https://unsplash.com) collection into a rotating `image` entity. Use the entity as a dashboard background, a [WallPanel](https://github.com/j-a-n/lovelace-wallpanel) slideshow source, a [View Assist](https://dinki.github.io/View-Assist/) background, or anywhere else an `image` entity is supported.

> Unsplash deprecated `source.unsplash.com` in late 2021 and it's been intermittent since 2024. This integration uses the official Unsplash API instead — stable, supported, and rate-limit aware.

## Features

- Configure once with your free Unsplash Access Key
- Add as many collections as you want — each becomes its own `image` entity
- Rotates to a new random photo on a configurable interval (default: every 15 minutes)
- Exposes photographer name and profile URL as state attributes (required for Unsplash attribution)
- Fires Unsplash's per-photo download-tracking endpoint automatically — keeps you compliant with the [API Guidelines](https://help.unsplash.com/en/articles/2511258)
- Filter by orientation (landscape, portrait, squarish)

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Click the **⋮** menu → **Custom repositories**
3. Add `https://github.com/dkedinger/ha-unsplash` as an **Integration**
4. Find "Unsplash" in the HACS list and install
5. Restart Home Assistant

### Manual

1. Download this repo and copy `custom_components/unsplash/` into your HA `config/custom_components/` directory
2. Restart Home Assistant

## Setup

### 1. Get an Unsplash Access Key

1. Go to [unsplash.com/developers](https://unsplash.com/developers) and create a free account
2. Click **New Application**, accept the API terms, and give it a name (e.g. "Home Assistant")
3. Copy the **Access Key** (not the Secret Key)

> Demo applications are rate-limited to **50 requests/hour**. With the default 15-minute refresh interval, you can run ~10 collections comfortably. Apply for production access in your Unsplash dashboard to raise this to 5000/hour.

### 2. Add the integration

1. **Settings → Devices & Services → Add Integration → Unsplash**
2. Paste your Access Key. The integration validates it against the API and rejects bad keys immediately.

### 3. Add collections

1. On the integration card, click **Configure**
2. Choose **Add a collection**
3. Enter a Collection ID. This is the number at the end of the collection URL — e.g. for `https://unsplash.com/collections/8975107`, the ID is `8975107`
4. Optionally provide a display name (otherwise the collection's title from Unsplash is used)

Each collection creates a single image entity, e.g. `image.unsplash_morning_blue`.

### 4. Tune refresh settings (optional)

From the same Configure menu, choose **Refresh settings** to change:

- **Refresh interval** — how often each entity swaps to a new photo (minimum 60 seconds)
- **Orientation** — landscape, portrait, or squarish

## Using the image entity

### As a Lovelace dashboard background

```yaml
type: vertical-stack
cards:
  - type: custom:button-card
    template: my_dashboard_template
    styles:
      card:
        - background: >-
            [[[ const e = hass.states['image.unsplash_my_collection'];
                return `center / cover no-repeat url(${e.attributes.entity_picture})`; ]]]
```

The `entity_picture` attribute is a Home Assistant-proxied URL that updates whenever the photo rotates. This is the recommended approach — it works without exposing your Unsplash key or the photographer's CDN URL to clients.

### As a direct URL (e.g. for an external display)

If you need the raw Unsplash CDN URL instead of HA's proxy:

```yaml
{{ state_attr('image.unsplash_my_collection', 'image_url') }}
```

### In a picture card

```yaml
type: picture-entity
entity: image.unsplash_my_collection
show_state: false
show_name: false
```

### Wired into a View Assist satellite background

This integration pairs nicely with View Assist. Use an automation to write the current image into your satellite's `background` attribute whenever it rotates:

```yaml
automation:
  - alias: "Sync Unsplash to View Assist satellite background"
    triggers:
      - trigger: state
        entity_id: image.unsplash_my_collection
    actions:
      - action: view_assist.set_attribute
        data:
          device: sensor.viewassist_living_room
          attribute: background
          value: "{{ state_attr('image.unsplash_my_collection', 'image_url') }}"
```

## State attributes

Each image entity exposes:

| Attribute            | Description                                                  |
| -------------------- | ------------------------------------------------------------ |
| `collection_id`      | The Unsplash collection ID                                   |
| `collection_name`    | The configured display name                                  |
| `photographer`       | Name of the photographer (use for attribution)               |
| `photographer_url`   | Link to the photographer's Unsplash profile                  |
| `description`        | Photo description from Unsplash, falls back to alt-text      |
| `photo_page_url`     | Link to the photo's Unsplash page                            |
| `image_url`          | Direct CDN URL — `regular` size (~1080px wide)               |
| `image_url_full`     | Direct CDN URL — `full` size (original upload, often large)  |

## Attribution requirements

Unsplash's API terms require that you attribute the photographer wherever a photo is displayed. A simple way to surface this in a dashboard:

```yaml
type: markdown
content: >
  Photo by [{{ state_attr('image.unsplash_my_collection', 'photographer') }}]({{ state_attr('image.unsplash_my_collection', 'photographer_url') }})
  on [Unsplash](https://unsplash.com)
```

## Rate limits and best practices

- **Demo apps: 50 requests/hour.** Each collection refresh = 1 request. The download-tracking ping is _not_ counted against your hourly limit (it's a separate endpoint).
- **Production apps: 5000 requests/hour.** Apply via your Unsplash app dashboard once your integration is functional.
- The integration uses one `DataUpdateCoordinator` per collection, so each collection updates on its own schedule. They share the access key but make independent API calls.
- If you hit the rate limit, individual coordinator updates will fail with an `UpdateFailed`. The entity keeps showing its last image until the next successful refresh. No need to restart anything.

## Troubleshooting

**"Invalid access key"** — Make sure you copied the **Access Key**, not the **Secret Key**. The Secret is longer and not used here.

**Entity shows no image** — Check the integration's diagnostics. Common causes: collection is private (must be public), collection has zero photos matching the orientation filter, or rate limit hit (wait an hour).

**Image doesn't update on the dashboard** — Make sure your dashboard card references `attributes.entity_picture` (which includes a cache-busting token), not a static URL.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgments

Photos powered by [Unsplash](https://unsplash.com). This integration is not affiliated with or endorsed by Unsplash, Inc.
