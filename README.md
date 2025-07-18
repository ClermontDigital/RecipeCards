# RecipeCards Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

A Home Assistant custom integration for managing and displaying recipe cards, by [@ClermontDigital](https://github.com/ClermontDigital).

## Features
- Persistent recipe storage (title, description, ingredients, notes, instructions, color)
- Lovelace card with retro UI and color customization
- WebSocket API for CRUD operations
- HACS-ready structure

## Installation
1. Copy the `custom_components/recipecards` directory to your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Add the integration via the UI ("Recipe Cards").

## Usage
- Use the Lovelace card to view and manage recipes.
- Change the color of the card title area with the built-in color picker.
- Recipes are stored persistently and can be managed via the UI or API.

## Development
- Python 3.10+
- Follows [semantic versioning](https://semver.org/)
- See `tests/` for backend unit tests

## HACS
- Add this repository as a custom repository in HACS to install and update easily.

## License
[Apache 2.0](LICENSE)

---

Repository: https://github.com/ClermontDigital/RecipeCards
Author: [@ClermontDigital](https://github.com/ClermontDigital) 