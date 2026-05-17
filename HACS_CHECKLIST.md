# HACS Publishing Checklist

This file is for the maintainer (not end users). It documents what needs to be done outside the codebase before this integration is publishable as a HACS custom repository — and then later, as a HACS default repository.

The code in this repo already satisfies all the code-side HACS requirements (`custom_components/unsplash/` structure, `manifest.json` with required keys, `hacs.json`, validation workflow). Everything in this checklist is the **GitHub-side** and **HA-brands-side** work.

## Before pushing to GitHub

- [ ] Replace `kedinger` placeholder in `custom_components/unsplash/manifest.json` with your actual GitHub username if different — three references (`codeowners`, `documentation`, `issue_tracker`)
- [ ] Update the same in `README.md` install section, `LICENSE` copyright line, and any other `kedinger` references
- [ ] Verify `manifest.json` `version` matches `CHANGELOG.md` (currently `0.1.0`)

## On GitHub

### Repository setup
- [ ] Create a **public** repository (HACS only sees public repos)
- [ ] Set the repository **description**: e.g. _"Home Assistant integration that exposes Unsplash collections as rotating image entities"_ — this is shown in the HACS UI
- [ ] Add **topics**: `home-assistant`, `hacs`, `hacs-integration`, `homeassistant-integration`, `home-assistant-custom-component`, `unsplash`, `image-entity`
- [ ] Verify the default branch is `main`

### Initial release
- [ ] Push everything to `main`
- [ ] Verify the GitHub Actions `Validate` workflow runs green (HACS validation + hassfest)
- [ ] Create a **GitHub Release** with tag `v0.1.0` — HACS reads version from release tags, not commit shas
- [ ] Paste the `CHANGELOG.md` `[0.1.0]` section into the release notes

### Discoverability
- [ ] Generate a [My Home Assistant link](https://my.home-assistant.io/create-link/?redirect=hacs_repository) for the repo and add the badge to README
- [ ] Optionally add the repo to one of the [Home Assistant community lists](https://github.com/home-assistant/awesome) once stable

## Brand assets

HACS requires brand assets. The canonical home is the [`home-assistant/brands`](https://github.com/home-assistant/brands) repository.

- [ ] Design a 256×256 px **`icon.png`** for the integration
  - Standard approach: a simple wordmark or symbol on transparent background
  - Avoid using Unsplash's actual logo unless you have permission — a generic camera/photo icon is safer
- [ ] Optional: 512×512 px `icon@2x.png` for HiDPI
- [ ] Optional: `dark_icon.png` and `dark_icon@2x.png` for dark-mode users
- [ ] Optional: `logo.png` / `logo@2x.png` (landscape format, used on integration setup pages)
- [ ] Fork [`home-assistant/brands`](https://github.com/home-assistant/brands) and PR the icon files into `custom_integrations/unsplash/`
- [ ] Once merged, icons resolve from `https://brands.home-assistant.io/unsplash/...` automatically

The integration works without the brands PR — it just shows a generic icon in the HA UI. The brands PR can land any time after launch.

## After initial release — Custom Repository test

This is what you ask early users to do before the integration is in HACS default:

1. HACS → ⋮ menu → **Custom repositories**
2. Repository URL: `https://github.com/YOUR_USERNAME/ha-unsplash`
3. Category: **Integration**
4. Click **Add**, then find "Unsplash" in HACS, install, restart HA
5. **Settings → Devices & Services → Add Integration → Unsplash**

## Submitting to HACS default (when ready)

Once the integration has been used by a handful of people, has a few releases, and seems stable:

- [ ] Open a PR to [`hacs/default`](https://github.com/hacs/default)
- [ ] Add a single line to `integration` file: `YOUR_USERNAME/ha-unsplash`
- [ ] Lines must be alphabetically sorted
- [ ] PR template asks you to confirm the validate.yaml workflow passes (it does)
- [ ] Expect 1–4 week review turnaround

## Ongoing maintenance expectations

- Bump `manifest.json` version + add CHANGELOG entry + tag a release for every functional change
- Respond to issues — code owners are publicly visible
- Keep the CI workflow green — HACS will eventually de-list repos that fail validation for extended periods
- Watch [Home Assistant breaking changes](https://www.home-assistant.io/blog/categories/release-notes/) for API changes affecting `ImageEntity` or `DataUpdateCoordinator`
