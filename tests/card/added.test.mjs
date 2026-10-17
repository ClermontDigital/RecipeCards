// Tests for the "Added" date the card shows on tiles and in the recipe views.
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
const label = defined['recipecards-card'].addedLabel;
const today = new Date(2026, 9, 17);

test('this year shows the day and month; another year adds the year', () => {
  assert.equal(label({ added: '2026-10-17' }, false, today), '17 Oct');
  assert.equal(label({ added: '2025-03-02' }, false, today), '2 Mar 2025');
});

test('the long form always has the year', () => {
  assert.equal(label({ added: '2026-10-17' }, true, today), '17 Oct 2026');
});

test('an approximate date says "before"', () => {
  assert.equal(label({ added: '2026-09-27', added_approx: true }, false, today), 'before 27 Sep');
  assert.equal(label({ added: '2026-09-27', added_approx: true }, true, today), 'before 27 Sep 2026');
});

test('no date, or a malformed one, shows nothing', () => {
  for (const r of [{}, { added: null }, { added: '' }, { added: '17/10/2026' }, { added: '2026-13-01' }, null]) {
    assert.equal(label(r, false, today), '');
  }
});
