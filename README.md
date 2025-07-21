# RecipeCards - Recipe Management for Home Assistant

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Version](https://img.shields.io/badge/version-1.0.27-green.svg)](https://github.com/ClermontDigital/RecipeCards)

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
- `sensor.recipe_cards` - Shows total number of stored recipes with recipe data in attributes

### Recipe Management Services

RecipeCards provides three main services for recipe management:

**Add Recipe:**
```yaml
service: recipecards.add_recipe
data:
  config_entry_id: "your-config-entry-id"  # See below for how to find this
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
  config_entry_id: "your-config-entry-id"
  recipe_id: "your-recipe-id"
  title: "Updated Chocolate Chip Cookies"
  description: "Improved recipe with better ingredients"
  color: "#E91E63"
```

**Delete Recipe:**
```yaml
service: recipecards.delete_recipe
data:
  config_entry_id: "your-config-entry-id"
  recipe_id: "your-recipe-id"
```

#### Finding Your Config Entry ID
1. Go to Settings → Devices & Services
2. Find "Recipe Cards" integration
3. Click on it to see the entity
4. The config entry ID is in the entity details

### Using Services

**Developer Tools - Actions:**
1. Go to Developer Tools → Actions
2. Choose any `recipecards.*` service
3. Fill in the form with your recipe details
4. Use the UI selectors to pick your config entry and enter recipe data

### Lovelace Dashboard with Buttons

Here's a complete example dashboard with buttons to add recipes and display them:

```yaml
type: vertical-stack
cards:
  # Recipe Display Card
  - type: custom:recipecards-card
    entity: sensor.recipe_cards
    title: "My Recipe Collection"
  
  # Add Recipe Buttons
  - type: horizontal-stack
    cards:
      - type: button
        name: "Add Breakfast Recipe"
        icon: mdi:egg-fried
        tap_action:
          action: call-service
          service: recipecards.add_recipe
          service_data:
            config_entry_id: "your-config-entry-id"  # Replace with your actual ID
            title: "Scrambled Eggs"
            description: "Quick breakfast option"
            ingredients:
              - "3 eggs"
              - "2 tbsp butter"
              - "Salt and pepper"
            instructions:
              - "Beat eggs in a bowl"
              - "Heat butter in pan"
              - "Add eggs and scramble gently"
              - "Season to taste"
            color: "#FFD700"
      
      - type: button
        name: "Add Dessert Recipe"
        icon: mdi:cupcake
        tap_action:
          action: call-service
          service: recipecards.add_recipe
          service_data:
            config_entry_id: "your-config-entry-id"  # Replace with your actual ID
            title: "Chocolate Cake"
            description: "Rich chocolate dessert"
            ingredients:
              - "2 cups flour"
              - "1 cup cocoa powder"
              - "2 cups sugar"
              - "3 eggs"
            instructions:
              - "Mix dry ingredients"
              - "Add eggs and mix well"
              - "Bake at 350°F for 30 minutes"
            color: "#8B4513"
  
  # Recipe Management
  - type: entities
    title: "Recipe Management"
    entities:
      - sensor.recipe_cards
    card_mod:
      style: |
        ha-card {
          --mdc-icon-size: 20px;
        }
```

### Lovelace Card Configuration

**Basic Recipe Display:**
```yaml
type: custom:recipecards-card
entity: sensor.recipe_cards
```

**Card Features:**
- **Tab Navigation**: Click recipe titles in the tab bar to switch between recipes
- **Flip Animation**: Click the card or "Flip for Instructions" button to see cooking instructions
- **Responsive Design**: Works on desktop and mobile devices
- **Loading States**: Shows loading indicators while fetching recipe data

## How to Get Your Config Entry ID

To use the services, you need your config entry ID:

1. **Via UI:**
   - Go to Settings → Devices & Services
   - Find "Recipe Cards" integration
   - Click on the entity name (e.g., "Recipe Cards")
   - Look in the entity details for the config entry ID

2. **Via Developer Tools:**
   - Go to Developer Tools → States
   - Find your `sensor.recipe_cards` entity
   - The config entry ID is visible in the entity attributes

3. **Using the Service UI:**
   - Go to Developer Tools → Actions
   - Select `recipecards.add_recipe`
   - The config entry selector will show available integrations

## Quick Start Guide

1. **Install & Setup:**
   - Install via HACS or manually
   - Add the Recipe Cards integration
   - Note your config entry ID

2. **Add Your First Recipe:**
   - Go to Developer Tools → Actions
   - Choose `recipecards.add_recipe`
   - Fill in the form and submit

3. **Add the Lovelace Card:**
   ```yaml
   type: custom:recipecards-card
   entity: sensor.recipe_cards
   ```

4. **Create Dashboard Buttons:**
   - Use the example configuration above
   - Replace `your-config-entry-id` with your actual ID
   - Customize the recipes in the buttons

## UI Flows for Adding Recipes

### Method 1: Simple Developer Tools (Easiest)
Add this button to navigate to Developer Tools:
```yaml
type: button
name: "Add New Recipe"
icon: mdi:plus-circle
tap_action:
  action: navigate
  navigation_path: "/developer-tools/service"
```

### Method 2: Input Helper Form (Recommended)
**Step 1:** Create input helpers in Settings → Devices & Services → Helpers:
- `input_text.recipe_title` (max: 100)
- `input_text.recipe_description` (max: 200)  
- `input_text.recipe_ingredients` (mode: text)
- `input_text.recipe_instructions` (mode: text)
- `input_text.recipe_notes` (max: 300)

**Step 2:** Add this form to your dashboard:
```yaml
type: vertical-stack
cards:
  # Recipe Form
  - type: entities
    title: "Add New Recipe"
    entities:
      - input_text.recipe_title
      - input_text.recipe_description
      - input_text.recipe_ingredients
      - input_text.recipe_instructions
      - input_text.recipe_notes
  
  # Submit Button
  - type: button
    name: "Save Recipe"
    icon: mdi:content-save
    tap_action:
      action: call-service
      service: recipecards.add_recipe
      service_data:
        config_entry_id: "your-config-entry-id"
        title: "{{ states('input_text.recipe_title') }}"
        description: "{{ states('input_text.recipe_description') }}"
        ingredients: "{{ states('input_text.recipe_ingredients').split('\n') }}"
        instructions: "{{ states('input_text.recipe_instructions').split('\n') }}"
        notes: "{{ states('input_text.recipe_notes') }}"
        color: "#FFD700"
  
  # Clear Form Button
  - type: button
    name: "Clear Form"
    icon: mdi:eraser
    tap_action:
      action: call-service
      service: input_text.set_value
      target:
        entity_id:
          - input_text.recipe_title
          - input_text.recipe_description
          - input_text.recipe_ingredients
          - input_text.recipe_instructions
          - input_text.recipe_notes
      service_data:
        value: ""
```

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