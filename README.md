# RecipeCards - Recipe Management for Home Assistant

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Version](https://img.shields.io/badge/version-1.0.22-green.svg)](https://github.com/ClermontDigital/RecipeCards)

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

### Configuration
1. **Add RecipeCards Integration:**
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Recipe Cards"
   - Complete the setup

2. **Add Lovelace Card:**
   - Edit your dashboard
   - Add card → Manual
   - Add the RecipeCards card

## Usage

### Entities Created
- `sensor.recipecards_recipe_count` - Total number of stored recipes
- `sensor.recipecards_last_updated` - Last recipe modification time

### Recipe Management Services

RecipeCards provides several services for recipe management:

**Add Recipe:**
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

**Get Recipe:**
```yaml
service: recipecards.get_recipe
data:
  recipe_id: "your-recipe-id"
```

**List All Recipes:**
```yaml
service: recipecards.list_recipes
```

### Using Services

**Developer Tools - Actions:**
1. Go to Developer Tools → Actions
2. Choose any `recipecards.*` service
3. Fill in the form with your recipe details

**In Automations:**
```yaml
# Add recipe from template
- service: recipecards.add_recipe
  data:
    title: "Quick Breakfast"
    description: "Simple morning meal"
    ingredients:
      - "2 eggs"
      - "1 slice bread"
      - "Butter"
    notes: "Cook eggs sunny side up"
    instructions:
      - "Toast bread until golden"
      - "Fry eggs sunny side up"
      - "Serve together while hot"
    color: "#4CAF50"
```

### Lovelace Card Configuration

**Show All Recipes (with Tab Bar):**
```yaml
type: custom:recipecards-card
# No recipe_id specified - shows all recipes in tabs
```

**Show Specific Recipe:**
```yaml
type: custom:recipecards-card
recipe_id: "chocolate-chip-cookies"
```

**Card Features:**
- **Tab Navigation**: Click recipe titles in the tab bar to switch between recipes
- **Flip Animation**: Click the card or "Flip for Instructions" button to see cooking instructions
- **Responsive Design**: Works on desktop and mobile devices
- **Loading States**: Shows loading indicators while fetching recipe data

### Advanced Service Examples

**Update Multiple Fields:**
```yaml
service: recipecards.update_recipe
data:
  recipe_id: "chocolate-chip-cookies"
  title: "Updated Chocolate Chip Cookies"
  description: "Improved recipe with better ingredients"
  ingredients:
    - "2.5 cups flour"
    - "1.25 cups butter"
    - "1.5 cups chocolate chips"
  notes: "Bake at 375°F for 10-12 minutes"
  instructions:
    - "Cream butter and sugar until fluffy"
    - "Add eggs one at a time"
    - "Mix in dry ingredients gradually"
    - "Fold in chocolate chips"
    - "Bake until edges are golden"
  color: "#E91E63"
```

## API Documentation

The integration provides a WebSocket API for recipe management:

- **Add Recipe**: `recipecards/add_recipe`
- **Update Recipe**: `recipecards/update_recipe`
- **Delete Recipe**: `recipecards/delete_recipe`
- **Get Recipe**: `recipecards/get_recipe`
- **List Recipes**: `recipecards/list_recipes`

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