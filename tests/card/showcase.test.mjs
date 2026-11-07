// Tests for the showcase card's random order: every recipe once per round, no repeat across rounds.
// Run: node --test tests/card/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const src = fs.readFileSync(new URL('../../custom_components/recipecards/www/recipecards-card.js', import.meta.url), 'utf8');
const defined = {};
vm.runInNewContext(src, {
  HTMLElement: class {},
  customElements: { get: (n) => defined[n], define: (n, c) => { defined[n] = c; } },
  window: {},
  document: { addEventListener() {} },
  console,
});
const bag = defined['recipecards-card'].shuffleBag;

test('the showcase card is registered', () => {
  assert.equal(typeof defined['recipecards-showcase-card'], 'function');
});

test('a round holds every recipe exactly once', () => {
  const ids = Array.from({ length: 179 }, (_, i) => `r${i}`);
  for (let k = 0; k < 50; k++) {
    const b = bag(ids, null);
    assert.equal(b.length, ids.length);
    assert.deepEqual([...b].sort(), [...ids].sort());
  }
});

test('a new round never starts with the recipe just shown', () => {
  const ids = ['a', 'b', 'c'];
  for (let k = 0; k < 500; k++) {
    for (const last of ids) assert.notEqual(bag(ids, last)[0], last);
  }
});

test('the order is shuffled, and the input is left alone', () => {
  const ids = Array.from({ length: 20 }, (_, i) => i);
  const before = ids.slice();
  const orders = new Set(Array.from({ length: 30 }, () => bag(ids, null).join(',')));
  assert.ok(orders.size > 25);
  assert.deepEqual(ids, before);
});

test('one recipe, or none, still works', () => {
  assert.deepEqual(bag(['only'], 'only'), ['only']);
  assert.deepEqual(bag([], null), []);
});
