## 1.5.0

- Multi-entry support: add multiple Recipe Cards entries (recipe sets)
- Full recipe fields in config and options flows
- One device per recipe; collection sensor kept for compatibility
- WebSocket API aggregates across entries; optional entry targeting
- Lovelace card: entry filter, entry_id/recipe_id config, correct service targeting
- Cleanup recipe entities on delete

## 1.4.1

- Fix: Register Lovelace resource as classic `js` (instead of `module`) to match the buildless IIFE card and avoid loader errors on some HA versions/setups.

## 1.4.0

- Automatically registers the bundled Lovelace card as a resource using the Lovelace resources registry, so the card type `custom:recipecards-card` is available without manual resource setup in storage dashboards.
- Keeps serving the buildless card at `/recipecards/recipecards-card.js` and continues to add it via `frontend.add_extra_js_url` for broad compatibility.
- Updates `iot_class` to `local_push` to reflect coordinator-driven refreshes.

## 1.3.0

- Initial public release of the simplified RecipeCards integration and card UI.
