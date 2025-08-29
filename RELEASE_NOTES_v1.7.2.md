# RecipeCards 1.7.2

Resolves reports of 404s when loading the card in some environments.

## Fixes

- Add a robust fallback to copy the bundled card to `/config/www/recipecards-card.js` and register `/local/recipecards-card.js?v=…` as an additional resource.
- Ensure both `/recipecards/recipecards-card.js?v=…` and `/local/recipecards-card.js?v=…` are registered with cache-busting.
- Extra guards around HTTP/static path registration so setup never fails.

## After Updating

1. Restart Home Assistant.
2. Hard-refresh the browser (Shift+Reload) or clear the mobile app’s frontend cache.
3. Verify either URL loads in the browser:
   - `/recipecards/recipecards-card.js?v=1.7.2`
   - `/local/recipecards-card.js?v=1.7.2`

If you use YAML-mode dashboards, ensure the resource is declared as:
```yaml
lovelace:
  resources:
    - url: /recipecards/recipecards-card.js
      type: js
    # or fallback
    - url: /local/recipecards-card.js
      type: js
```
