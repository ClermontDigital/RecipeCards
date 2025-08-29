# RecipeCards - Recipe Management for Home Assistant

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Version](https://img.shields.io/badge/version-1.7.1-green.svg)](https://github.com/ClermontDigital/RecipeCards)

Retro-style recipe card management for Home Assistant. Store, browse, and display recipes in a classic 80s-inspired card interface with flip animations and persistent storage.

## Features

- 📝 **Recipe Storage** - Persistent storage for recipes with title, description, ingredients, notes, and instructions
- 🎨 **Retro UI** - 80s-inspired card design with flip animations and color customization
- 🔄 **WebSocket API** - Real-time CRUD operations for recipe management
- 📱 **Lovelace Card** - Custom card component for displaying recipes with tab navigation
- 🏷️ **Recipe Index** - Tab bar interface to browse and switch between multiple recipes
- 🎯 **Color Customization** - Change card title area colors to match your theme
- 🚀 **HACS Ready** - Easy installation and updates via HACS

## Quick Setup

### Requirements
- Home Assistant 2024.1+
- HACS (Home Assistant Community Store)

### Installation
1. **HACS**: Add custom repository `https://github.com/ClermontDigital/RecipeCards`
2. **Manual**: Download and extract to `/config/custom_components/recipecards/`
3. Restart Home Assistant
4. Add integration via Settings → Devices & Services

### Lovelace Card Auto-Loading
The bundled buildless card is automatically served and registered as a Lovelace resource. No manual resource configuration is needed in storage dashboards. The integration also adds a version parameter to the resource URL (e.g., `/recipecards/recipecards-card.js?v=1.7.1`) to bust browser caches after upgrades.

### Configuration
1. **Add RecipeCards Integration (Multiple Sections Supported):**
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Recipe Cards"
   - Enter a Section name (e.g., Desserts)
   - Submit to create an empty section (no recipe is created automatically)

   After the first entry, you can use the blue "Add entry" button on the
   Recipe Cards integration page to add more entries. Each entry creates:
   - A collection device called "Recipe Cards" for that entry, and
   - One device per recipe (exposed as a sensor with recipe attributes)

2. **Add Lovelace Card:**
   - No build step required. The card is auto-loaded and auto-registered as a Lovelace resource by the integration on storage dashboards.
   - Edit your dashboard → Add card → Manual
   - YAML:
     - `type: custom:recipecards-card`
     - `entity: sensor.recipe_cards` (optional; the card uses the WS API by default)

If you use YAML‑mode dashboards, add a resource manually:
```yaml
lovelace:
  resources:
    - url: /recipecards/recipecards-card.js
      type: js
```

## Usage

### Entities Created
- `sensor.recipe_cards` (per entry) – Shows total number of stored recipes with recipe data in attributes
- `sensor.recipe_<title>` (per recipe) – A sensor entity representing a single recipe (prefix `recipe_`). Attributes include `title`, `description`, `ingredients`, `instructions`, `notes`, and `color`.

### Easy Recipe Management

RecipeCards now provides **simplified** recipe management - no config entry IDs needed! If you have multiple entries, the built‑in UI and API aggregate recipes from all entries. You can still target a specific entry by passing `config_entry_id` (services) or `entry_id` (WebSocket API).

**Add Recipe (Simple):**
```yaml
service: recipecards.add_recipe
data:
  title: "Chocolate Chip Cookies"
  description: "Classic homemade cookies"
  ingredients:
    - "2 cups flour"
    - "1 cup butter"
    - "1 cup chocolate chips"
  notes: "Bake at 350°F for 12 minutes"
  instructions:
    - "Mix dry ingredients in a bowl"
    - "Cream butter and add to mixture"
    - "Form cookies and bake until golden"
  color: "#FF6B35"
```

**Update Recipe:**
```yaml
service: recipecards.update_recipe
data:
  recipe_id: "your-recipe-id"
  title: "Updated Chocolate Chip Cookies"
  description: "Improved recipe with better ingredients"
  color: "#E91E63"
```

**Delete Recipe:**
```yaml
service: recipecards.delete_recipe
data:
  recipe_id: "your-recipe-id"
```

> **Note:** Config entry IDs are now auto-detected! You only need to specify `config_entry_id` if you have multiple RecipeCards integrations.

### Sections (Groups)

Each integration entry is a “section” (e.g., Desserts, Mains). Add multiple entries to create multiple sections. The Lovelace card groups recipes by section and shows an Add button for each section.

### New Recipe Collection View

The RecipeCards card now features two modes:

1. **Collection View (Default)**: Browse all recipes as colored tiles with built-in add/edit/delete functionality
2. **Detail View**: Classic single-recipe card with flip animation

**Basic Setup (all sections):**
```yaml
type: custom:recipecards-card
title: "My Recipe Collection"
```

**Group by section explicitly:**
```yaml
type: custom:recipecards-card
group_by: entry
```

**Force Detail View:**
```yaml
type: custom:recipecards-card
entity: sensor.recipe_cards
view: detail
```

**Single recipe via its entity:**
```yaml
type: custom:recipecards-card
entity: sensor.recipe_chocolate_cake  # per-recipe sensor
view: detail
```

**Single recipe via recipe_id:**
```yaml
type: custom:recipecards-card
recipe_id: 01234567-89ab-cdef-0123-456789abcdef
view: detail
```

**Tray Box View (flick through cards):**
```yaml
type: custom:recipecards-card
view: tray
# optional
entry_id: <SECTION_ENTRY_ID>  # limit to a section
title: "Recipe Box"
```
This renders a horizontal tray of mini cards (“dividers”). Click a card to view its full details below, or use Left/Right arrows to move between cards. The + button adds a recipe.

### Recipe Management Features

- **➕ Add Recipes**: Click the + button in collection view
- **✏️ Edit Recipes**: Click "Edit" on any recipe tile  
- **🗑️ Delete Recipes**: Click "Delete" on any recipe tile
- **🎨 Color Coding**: Each recipe has a customizable color header
- **📊 Recipe Info**: See ingredient count and step count at a glance
- **⌨️ Keyboard Navigation**: Full keyboard accessibility support
- **📱 Responsive**: Works on desktop and mobile

### Using Developer Tools (Optional)

For automation or advanced usage:
1. Go to Developer Tools → Actions
2. Choose any `recipecards.*` service
3. Fill in the form (config entry ID is now optional)

### Card Configuration Options

**Collection View (Default):**
```yaml
type: custom:recipecards-card
entity: sensor.recipe_cards  # optional; uses WS API by default
title: "My Recipes"  # Optional custom title
```

**Detail View (Classic):**
```yaml
type: custom:recipecards-card
entity: sensor.recipe_cards
view: detail
```

**Card Features:**
- **Collection View**: Grid of colored recipe tiles, built-in add/edit/delete
- **Detail View**: Tab navigation and flip animation for instructions  
- **Responsive Design**: Works on desktop and mobile devices
- **Loading States**: Shows loading indicators while fetching recipe data
- **Color Coding**: Each recipe has a customizable header color
 - **Sections**: When multiple entries exist, the card groups recipes by section title
 - **Entry Filter**: When multiple entries exist, a dropdown filter appears. You can also target a specific entry with `entry_id: <ENTRY_ID>`.

## Quick Start Guide

1. **Install & Setup:**
   - Install via HACS or manually
   - Add the Recipe Cards integration (no configuration needed)

2. **Add the Lovelace Card:**
   ```yaml
   type: custom:recipecards-card
   entity: sensor.recipe_cards
   ```

3. **Start Adding Recipes:**
   - Click the **+** button in the collection view
   - Fill in the recipe form and save
   - Your recipes appear as colored tiles

4. **Manage Recipes:**
   - **View**: Click any recipe tile to see full details
   - **Edit**: Click "Edit" on any recipe tile
   - **Delete**: Click "Delete" on any recipe tile

## Recipe Management Methods

### Method 1: Built-in UI (Recommended)
The easiest way to manage recipes:
- **Add**: Click the + button in collection view
- **Edit**: Click "Edit" on any recipe tile
- **Delete**: Click "Delete" on any recipe tile
- **View**: Click any recipe tile or switch to detail view

### Method 2: Developer Tools (For Automation)
For creating automations or scripts:
1. Go to Developer Tools → Actions
2. Choose `recipecards.add_recipe`
3. Fill the form (no config entry ID needed)

### Method 3: Service Calls (Advanced)
Use in automations or scripts:
```yaml
service: recipecards.add_recipe
data:
  title: "My Recipe"
  description: "A delicious recipe"
  ingredients:
    - "Ingredient 1"
    - "Ingredient 2"
  instructions:
    - "Step 1"
    - "Step 2"
  color: "#FF6B35"
```

### Method 4: Options Flow (Add via Settings)
From the integration entry row, click Configure. You’ll see a menu:
- Add new recipe — opens a full recipe form and saves to this section
- Edit existing recipe — select a recipe, then update it
- Delete recipe — select a recipe to remove it
- Rename this section — change the section title
Repeat Add to create multiple recipes under the same section.

## Troubleshooting

- **Card not displaying**: Check that recipes exist and the Lovelace card is properly configured
- **Tab bar not showing**: Ensure you have multiple recipes added to see the tab navigation
- **Integration not loading**: Restart Home Assistant after installation
- **Recipes not saving**: Verify the integration is properly configured

Enable debug logging:
```yaml
logger:
  logs:
    custom_components.recipecards: debug
```

## Development

- Python 3.10+
- TypeScript/LitElement for frontend
- Follows [semantic versioning](https://semver.org/)
- See `tests/` for backend unit tests

## Contributing

Bug reports and feature requests welcome via [GitHub Issues](https://github.com/ClermontDigital/RecipeCards/issues).

## License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.

---

Repository: https://github.com/ClermontDigital/RecipeCards
Author: [@ClermontDigital](https://github.com/ClermontDigital) 
