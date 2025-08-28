# RecipeCards Lovelace Card

Custom Lovelace card for the RecipeCards Home Assistant integration.

## Development

- Install dependencies: `npm install`
- Build: `npm run build`
- Watch: `npm run watch`
- Test: `npm run test:simple`

## Testing

The project includes comprehensive frontend tests:

- **Component Structure Tests**: Verify the card component is properly structured
- **Build Process Tests**: Ensure the TypeScript compilation works correctly
- **Source Code Quality Tests**: Check for required elements and patterns
- **Test Coverage**: Comprehensive test cases for all major functionality

Run tests with:
```bash
npm run build && npm run test:simple
```

Test coverage includes:
- ✅ Component rendering and configuration
- ✅ Recipe loading and display
- ✅ Tab navigation functionality
- ✅ Card flip animations
- ✅ Error handling and loading states
- ✅ Accessibility attributes
- ✅ API integration

## Usage

1. Build the card: `npm run build`
2. Copy `dist/recipecards-card.js` to your Home Assistant `www/` directory
3. Add the card as a resource in Lovelace
4. Use `<recipecards-card>` in your dashboard

## Author
@ClermontDigital
