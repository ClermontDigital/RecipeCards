# RecipeCards 1.7.1

This release restores automatic loading of the bundled Lovelace card and adds cache-busting to ensure browsers fetch the latest version after upgrades. It also updates documentation and examples for clarity.

## Highlights

- Auto-serve and auto-register the bundled Lovelace card (`custom:recipecards-card`) — no manual resource setup needed on storage dashboards.
- Cache-busting by appending the integration version to the card URL (e.g., `/recipecards/recipecards-card.js?v=1.7.1`).
- Ensure a Lovelace resource entry exists (or is updated) via the resources registry.
- Documentation updates: corrected examples, clarified `entry_id` (config entry id) vs. sensor entity ids, YAML-mode resource type `js`.

## Upgrade Notes

1. Restart Home Assistant after updating.
2. Hard-refresh the browser (Shift+Reload) to clear cached frontend resources.
3. In YAML-mode dashboards only, ensure your resource is:

```yaml
lovelace:
  resources:
    - url: /recipecards/recipecards-card.js
      type: js
```

## Changes

- feat: restore auto-load of Lovelace card and add `frontend.add_extra_js_url` safety net
- feat: register (or update) Lovelace resource with a versioned URL
- docs: update README, examples, and changelog
- chore: bump integration version to 1.7.1

