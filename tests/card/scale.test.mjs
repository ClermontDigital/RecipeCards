// Tests for the ingredient multiplier in the shipped (buildless) card.
// Run: node --test tests/card/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const src = fs.readFileSync(new URL('../../custom_components/recipecards/www/recipecards-card.js', import.meta.url), 'utf8');
const defined = {};
const ctx = {
  HTMLElement: class {},
  customElements: { get: (n) => defined[n], define: (n, c) => { defined[n] = c; } },
  window: {},
  console,
};
vm.runInNewContext(src, ctx);
const scaleParts = defined['recipecards-card'].scaleParts;
const scale = (line, f) => scaleParts(line, f).map((p) => p.text).join('');
const marked = (line, f) => scaleParts(line, f).map((p) => (p.scaled ? `[${p.text}]` : p.text)).join('');

test('x1 leaves every line untouched', () => {
  for (const l of ['2 cups flour', '400 g can tomatoes', 'Salt to taste']) {
    // compare as JSON: objects from the vm sandbox have a different prototype
    assert.equal(JSON.stringify(scaleParts(l, 1)), JSON.stringify([{ text: l, scaled: false }]));
  }
});

test('whole numbers, fractions, mixed numbers, unicode and decimals', () => {
  assert.equal(scale('2 cups flour', 4), '8 cups flour');
  assert.equal(scale('1/3 cup cacao', 2), '2/3 cup cacao');
  assert.equal(scale('3/4 cup almond flour', 4), '3 cup almond flour');
  assert.equal(scale('1 1/2 cups milk', 3), '4 1/2 cups milk');
  assert.equal(scale('1-1/2 cups milk', 2), '3 cups milk');
  assert.equal(scale('½ tsp salt', 0.5), '¼ tsp salt');
  assert.equal(scale('1½ cups milk', 3), '4½ cups milk');
  assert.equal(scale('0.5 kg flour', 3), '1.5 kg flour');
  assert.equal(scale('1 tsp vanilla', 0.5), '1/2 tsp vanilla');
  assert.equal(scale('3 large eggs', 0.5), '1 1/2 large eggs');
});

test('metric amounts stay decimal', () => {
  assert.equal(scale('125 g butter', 0.5), '62.5 g butter');
  assert.equal(scale('200g sugar', 3), '600g sugar');
});

test('every amount on the line scales, including equivalents in brackets', () => {
  assert.equal(scale('1 1/2 tablespoons (22 g) cream cheese', 2), '3 tablespoons (44 g) cream cheese');
  assert.equal(scale('1 cup + 2 tablespoons (270 ml) heavy cream', 2), '2 cup + 4 tablespoons (540 ml) heavy cream');
  assert.equal(scale('1 tbsp orange zest or 4 drops orange oil', 2), '2 tbsp orange zest or 8 drops orange oil');
  assert.equal(scale('PUDDING: 4 large eggs', 4), 'PUDDING: 16 large eggs');
});

test('ranges scale at both ends', () => {
  assert.equal(scale('2-3 cloves garlic', 2), '4-6 cloves garlic');
  assert.equal(scale('Optional: 1 to 2 tsp honey', 2), 'Optional: 2 to 4 tsp honey');
  assert.equal(scale('1 tbsp lemon zest (from 2 to 3 lemons)', 2), '2 tbsp lemon zest (from 4 to 6 lemons)');
  assert.equal(scale('1/2-1 1/2 teaspoon kosher salt', 2), '1-3 teaspoon kosher salt');
});

test('package sizes are not scaled; the count is', () => {
  assert.equal(scale('1 (400 g) can tomatoes', 2), '2 (400 g) can tomatoes');
  assert.equal(scale('1 (32 ounce) carton chicken broth', 2), '2 (32 ounce) carton chicken broth');
  assert.equal(scale('1 can (8 ounces) tomato sauce', 2), '2 can (8 ounces) tomato sauce');
  assert.equal(scale('1 (28-ounce can) whole peeled tomatoes', 2), '2 (28-ounce can) whole peeled tomatoes');
  assert.equal(scale('1 13.5 ounce can coconut milk', 2), '2 13.5 ounce can coconut milk');
  assert.equal(scale('2 x 400g tins chickpeas', 2), '4 x 400g tins chickpeas');
  assert.equal(scale('1 x 3kg pork leg', 2), '2 x 3kg pork leg');
});

test('a line that is only a package size gets a count', () => {
  assert.equal(marked('400 g can chopped tomatoes', 2), '[2 × ]400 g can chopped tomatoes');
  assert.equal(marked('395 gram Can Sweetened Condensed Milk', 3), '[3 × ]395 gram Can Sweetened Condensed Milk');
  assert.equal(marked('FILLING: 400 g tin peaches', 2), 'FILLING: [2 × ]400 g tin peaches');
  assert.equal(marked('1 inch piece of ginger, peeled', 2), '[2 × ]1 inch piece of ginger, peeled');
});

test('temperatures, times, percentages, sizes and codes are left alone', () => {
  assert.equal(scale('1 cup vinegar (5% acidity)', 2), '2 cup vinegar (5% acidity)');
  assert.equal(scale('Bamboo sticks (soak for 5 minutes)', 2), 'Bamboo sticks (soak for 5 minutes)');
  assert.equal(scale('2 lb beef, cut into 1 inch pieces', 2), '4 lb beef, cut into 1 inch pieces');
  assert.equal(scale('1 cup mushrooms, sliced 3 mm thick', 2), '2 cup mushrooms, sliced 3 mm thick');
  assert.equal(scale('1 kg pork, cut into 2–3 cm (¾–1¼ inch) cubes', 2), '2 kg pork, cut into 2–3 cm (¾–1¼ inch) cubes');
  assert.equal(scale('100 g butter, softened (oven at 180°C)', 2), '200 g butter, softened (oven at 180°C)');
  assert.equal(scale('12 wings (12-wing bags)', 2), '24 wings (12-wing bags)');
  assert.equal(scale('1 tsp vitamin B12 powder', 2), '2 tsp vitamin B12 powder');
});

test('lines without amounts are unchanged', () => {
  for (const l of ['Salt to taste', 'Pinch of salt and pepper', 'Blueberries, to top', '']) {
    assert.equal(scale(l, 4), l);
  }
});

test('only the numbers are marked as scaled (so the card can highlight them)', () => {
  assert.equal(marked('2 cups flour', 2), '[4] cups flour');
  assert.equal(marked('1 cup + 2 tbsp', 2), '[2] cup + [4] tbsp');
});
