## 1.9.3

Fixes found by actually looking at the rendered card.

- **The add/edit form had no Save button.** Buttons passed to `ha-dialog` via
  `slot="primaryAction"` did not render in HA 2026.8, so the form could be opened and
  filled in but never submitted, and the dialog showed no heading either. Dialogs are now
  self-contained: own scrim, heading, scrollable body and footer, with Escape,
  click-outside and a close button all working. Ctrl/Cmd+Enter saves.
- **The section label collided with the overflow menu.** `.rc-section` and `.rc-more` were
  both absolutely positioned top-right, so "DESSERTS" rendered underneath the menu button.
  The section is now a chip in the tile's meta row.
- **The "Add recipe" button escaped the card** and floated at the bottom-right of the
  viewport. `ha-button` is no longer used; buttons are plain elements styled from HA theme
  variables, so their placement is deterministic.
- No dependency on `ha-dialog`, `ha-button` or `mwc-button` remains. The only Home
  Assistant element the card still relies on is `ha-icon`.

## 1.9.2

Card redesign. The backend was working from 1.9.0; this is about it being usable.

### Changed

- **Opening a recipe no longer replaces the card.** It opens in a dialog, so there is
  nothing to navigate "back" from - close it, press Escape, or click outside and the
  grid is exactly where you left it. The old inline detail view with its "Back" button
  is kept only for cards deliberately pinned to one recipe (`view: detail` or `recipe_id`),
  where the back button is now hidden because there is nowhere to go back to.
- **Wrapped in a real `ha-card`.** The card previously rendered loose `div`s straight into
  the dashboard, so it never picked up card background, elevation, radius or theming.
- **Whole tile is clickable**, keyboard focusable, and has a hover state. The three
  competing Open / Edit / Delete buttons on every tile are replaced by a single overflow
  menu, so Delete is no longer one misclick from Open.
- **Tiles show what you need to choose a recipe**: total time, ingredient count and step
  count, all of which the integration already knew and never displayed.
- **Section tabs use section names**, not `Set 01ab23`. The old filter dropdown showed
  truncated config entry IDs.
- **Search box** appears once you have more than three recipes.
- **Ingredients and method steps tick off as you cook**, and the ticks persist in browser
  storage so a re-render or a page reload does not lose your place.
- Recipe colour is used as a real accent (tile band, notes rule) rather than a thin strip
  in one view.
- Add/edit form has proper labels, hints, placeholders and a colour swatch picker instead
  of bare inputs.
- `mwc-button` replaced with `ha-button` throughout; `mwc-*` is deprecated in the HA frontend.
- Card picker entry renamed to "Recipe Cards" with a clearer description.

## 1.9.1

- **Fixed: the Lovelace card was loaded twice when more than one section exists.**
  Config entries are set up concurrently, and the `frontend_registered` guard was
  claimed only after several `await`s — so every entry passed it. The loser of the
  static-path race hit "path already registered", fell back to copying the card into
  `/config/www`, and the browser ended up importing the card from two different URLs:

  ```
  import("/recipecards/recipecards-card.js?v=1.9.0");
  import("/local/recipecards-card.js?v=1.9.0");
  ```

  The guard is now claimed synchronously, before the first `await`, and released again
  only if setup genuinely fails. Single-section installs were unaffected.

## 1.9.0

Repair release. Recipe creation could not succeed at all in 1.8.x — five independent defects sat on
the same code path, and each failure was swallowed before it reached the log.

### Fixed — each of these alone prevented the integration from working

- **Services rejected every call.** `prep_time`, `cook_time`, `total_time` and `max_time` were
  declared as `vol.Optional(..., default=None)` piped through `vol.Coerce(int)`. Voluptuous validates
  defaults, so `int(None)` raised and `add_recipe`/`update_recipe`/`recipe_search` returned a bare
  400 no matter what was passed. The defaults are gone and the fields now accept `None`.
- **`Recipe.parse_times` was not callable.** `@classmethod` was applied twice. Chained classmethod
  descriptors were deprecated in Python 3.11 and removed in 3.13, so on Home Assistant 2025.12+
  every write raised `TypeError: 'classmethod' object is not callable`.
- **WebSocket API never responded.** All six commands were `async def` but lacked
  `@websocket_api.async_response`. Home Assistant invoked them synchronously and discarded the
  coroutine, so `connection.send_result` was never reached and the card's `callWS` promise hung
  forever instead of rejecting.
- **Options flow crashed on entry.** `config_flow.py` used `cv.text` eight times with `cv` never
  imported — and `cv.text` does not exist. Settings → Configure → Add new recipe raised `NameError`.
  Now imports `config_validation` and uses `cv.string`.
- **Card was served stale.** `www/recipecards-card.js` had not been rebuilt since 1.7.x. The
  `recipecards-card/` TypeScript tree cannot compile (it imports npm packages that do not exist and
  the repo has no bundler) and is now documented as legacy; the shipped JS is the source of truth.

### Fixed — data loss and correctness

- **Half-written records.** `async_add_recipe` saved to disk *before* parsing times and notified the
  coordinator *after*, so a parse failure persisted the recipe while leaving the sensor stale. Times
  are now parsed before the single save.
- **Time parsing never worked.** `extract_time` searched for `min`/`hour` inside a capture group that
  by construction held only the bare number, so every parse returned `None`. Rewritten to read the
  unit from the match: "Prep for 10 minutes", "Bake 25 min", "Roast for 1 hour 30 min" all work.
  Explicitly supplied times are no longer overwritten by parsed ones.
- **`update_recipe` wiped fields.** Injected `None` defaults were merged over the stored record,
  clearing image and times on every edit — including a title-only change.
- **`recipe_search` crashed** comparing `None > int` when a recipe had no total time.
- **Sensor lagged writes by 10 seconds.** Storage used the debounced `async_request_refresh`; a
  delete straight after an add left the sensor stale. Now refreshes immediately.
- **Storage was never removed** with its config entry. Added `async_remove_entry`, so deleting a
  section deletes its store instead of orphaning it.
- **Services were never unregistered** on unload — the `api_registered` bookkeeping key meant
  `hass.data[DOMAIN]` was never empty.

### Fixed — frontend

- Card accepts a bare `type: custom:recipecards-card` (as the docs have always shown) and provides
  `getStubConfig`, so adding it from the card picker works.
- Save and delete failures are surfaced as a Home Assistant notification instead of being logged to
  the browser console with the dialog left open.
- Recipe text is HTML-escaped in the add/edit form; a title containing a quote no longer corrupts it.
- The card no longer refetches and rebuilds its entire DOM on every state change in the instance.

### Changed

- `register_static_path` (removed from HA in 2025.7) replaced with `async_register_static_paths`;
  the dead `lovelace.resources.async_get_registry` import removed. Minimum supported HA is 2024.7.
- Manifest declares `http` as a dependency and `frontend`/`lovelace` as after-dependencies.
- All blocking file I/O moved off the event loop.
- Bare `except: pass` blocks replaced with real logging — five errors were firing on every startup
  with nothing written to the log.
- `services.yaml` now declares the time and image fields the schema has always accepted.
- Test suite rewritten against a real Home Assistant instance (30 tests, all passing). The previous
  suite mocked the exact seams where the bugs lived.

## 1.8.1

- Version bump for release

## 1.7.2

- Fix: add resilient fallback to serve the card under `/local/recipecards-card.js` by copying the bundled file to `/config/www/` if direct static serving is unavailable on some setups
- Ensure both `/recipecards/...` and `/local/...` resources are registered and cache-busted
- Additional hardening for environments initializing HTTP later

## 1.7.1

- Restore automatic loading of the bundled Lovelace card
- Add cache-busting to the served card URL using the integration version
- Ensure Lovelace resource is auto-created/updated (no manual resource needed)
- Documentation updates clarifying `entry_id` vs entity ids and examples

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
