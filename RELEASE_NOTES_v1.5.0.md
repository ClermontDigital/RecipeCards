# Release Notes — v1.5.0

Highlights:

- Multiple recipe sets (config entries). Use the “Add entry” button to create additional collections.
- Full recipe capture in setup and options flows (title, description, ingredients, instructions, notes, color).
- One device per recipe plus a collection sensor per entry.
- WebSocket API now aggregates across entries; `entry_id` can target a specific set.
- Lovelace card can filter by entry, and passes `config_entry_id` to services.
- Deleting a recipe removes the corresponding entity from the registry.

Upgrade notes:

- Existing dashboards keep working. The card prefers WebSocket data but falls back to `sensor.recipe_cards` if present.
- The integration auto‑loads the card as `/recipecards/recipecards-card.js`.

