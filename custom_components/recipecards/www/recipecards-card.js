// RecipeCards Lovelace card - buildless, no NPM step.
// Served and auto-loaded by the integration.
(function () {
  const ICONS = {
    clock: 'mdi:clock-outline',
    basket: 'mdi:basket-outline',
    steps: 'mdi:format-list-numbered',
    back: 'mdi:arrow-left',
    more: 'mdi:dots-vertical',
    add: 'mdi:plus',
    search: 'mdi:magnify',
  };

  const STYLE = `
    <style>
      :host { display: block; }
      .rc-wrap { --rc-radius: var(--ha-card-border-radius, 12px); }

      /* ---------- header ---------- */
      .rc-head {
        display: flex; align-items: center; gap: 12px;
        padding: 12px 16px 8px; flex-wrap: wrap;
      }
      .rc-head h2 {
        margin: 0; flex: 1 1 auto; min-width: 0;
        font-size: 1.25rem; font-weight: 500; line-height: 1.3;
        color: var(--primary-text-color);
      }
      .rc-count {
        font-size: .8rem; color: var(--secondary-text-color);
        font-weight: 400; margin-left: 8px; white-space: nowrap;
      }
      .rc-search {
        display: flex; align-items: center; gap: 6px;
        background: var(--secondary-background-color);
        border-radius: 999px; padding: 4px 12px; flex: 0 1 220px; min-width: 140px;
      }
      .rc-search ha-icon { --mdc-icon-size: 18px; color: var(--secondary-text-color); flex: none; }
      .rc-search input {
        border: 0; background: none; outline: none; width: 100%;
        color: var(--primary-text-color); font: inherit; font-size: .9rem; padding: 4px 0;
      }
      .rc-tabs {
        display: flex; gap: 6px; overflow-x: auto; padding: 0 16px 10px;
        scrollbar-width: none;
      }
      .rc-tabs::-webkit-scrollbar { display: none; }
      .rc-tab {
        border: 1px solid var(--divider-color); background: none; cursor: pointer;
        border-radius: 999px; padding: 5px 14px; font: inherit; font-size: .82rem;
        color: var(--secondary-text-color); white-space: nowrap; transition: all .15s;
      }
      .rc-tab:hover { background: var(--secondary-background-color); }
      .rc-tab[aria-selected="true"] {
        background: var(--primary-color); border-color: var(--primary-color);
        color: var(--text-primary-color, #fff); font-weight: 500;
      }

      /* ---------- grid ---------- */
      .rc-grid {
        display: grid; gap: 12px; padding: 4px 16px 16px;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      }
      .rc-tile {
        position: relative; display: flex; flex-direction: column;
        border-radius: var(--rc-radius); overflow: hidden; cursor: pointer;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        transition: transform .15s ease, box-shadow .15s ease;
      }
      .rc-tile:hover { transform: translateY(-2px); box-shadow: var(--ha-card-box-shadow, 0 4px 12px rgba(0,0,0,.18)); }
      .rc-tile:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
      .rc-band { height: 6px; flex: none; }
      .rc-thumb {
        width: 100%; height: 132px; object-fit: cover; display: block; flex: none;
        background: var(--secondary-background-color);
      }
      .rc-hero {
        width: 100%; max-height: 300px; object-fit: cover; display: block;
        border-radius: 10px; margin-bottom: 14px; background: var(--secondary-background-color);
      }
      .rc-body { padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
      .rc-title {
        font-size: 1rem; font-weight: 500; line-height: 1.3; color: var(--primary-text-color);
        padding-right: 28px;
      }
      .rc-desc {
        font-size: .84rem; color: var(--secondary-text-color); line-height: 1.45;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
      }
      .rc-meta {
        display: flex; flex-wrap: wrap; gap: 4px 12px; margin-top: auto; padding-top: 8px;
        font-size: .76rem; color: var(--secondary-text-color);
      }
      .rc-meta span { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
      .rc-meta ha-icon { --mdc-icon-size: 14px; }
      .rc-section {
        display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px;
        background: var(--secondary-background-color); color: var(--secondary-text-color);
        font-size: .68rem; text-transform: uppercase; letter-spacing: .06em; font-weight: 600;
      }
      .rc-more {
        position: absolute; top: 8px; right: 4px;
        border: 0; background: none; cursor: pointer; border-radius: 50%;
        color: var(--secondary-text-color); padding: 4px; line-height: 0;
      }
      .rc-more:hover { background: var(--secondary-background-color); color: var(--primary-text-color); }
      .rc-fav {
        position: absolute; top: 8px; right: 4px;
        border: 0; background: none; cursor: pointer; border-radius: 50%;
        color: var(--secondary-text-color); padding: 4px; line-height: 0; transition: transform .12s;
      }
      .rc-fav.beside-more { right: 34px; }
      .rc-tile.has-img .rc-fav { background: rgba(0, 0, 0, .42); color: #fff; }
      .rc-fav:hover { transform: scale(1.12); }
      .rc-fav.on, .rc-tile.has-img .rc-fav.on { color: #FFC107; }
      .rc-fav ha-icon { --mdc-icon-size: 18px; }
      .rc-fav.inline { position: static; background: none; padding: 6px; }
      .rc-fav.inline ha-icon { --mdc-icon-size: 22px; }
      .rc-tile.no-img .rc-title { padding-right: 64px; }
      .rc-more ha-icon { --mdc-icon-size: 18px; }

      .rc-btn {
        flex: none; border: 0; cursor: pointer; font: inherit; font-size: .88rem; font-weight: 500;
        border-radius: 999px; padding: 8px 18px; white-space: nowrap;
        background: var(--primary-color); color: var(--text-primary-color, #fff);
        transition: filter .15s;
      }
      .rc-btn:hover { filter: brightness(1.1); }
      .rc-btn:focus-visible { outline: 2px solid var(--primary-text-color); outline-offset: 2px; }
      .rc-btn.ghost {
        background: none; color: var(--primary-color);
        border: 1px solid var(--divider-color);
      }
      .rc-btn.ghost:hover { background: var(--secondary-background-color); }
      .rc-btn.danger { background: none; color: var(--error-color, #c62828); border: 1px solid var(--divider-color); }

      /* ---------- detail ---------- */
      .rc-detail-head { padding: 16px; display: flex; flex-direction: column; gap: 8px; }
      .rc-detail-top { display: flex; align-items: center; gap: 8px; }
      .rc-back {
        border: 0; background: none; cursor: pointer; color: var(--secondary-text-color);
        display: inline-flex; align-items: center; gap: 4px; font: inherit; font-size: .85rem;
        padding: 6px 10px 6px 6px; border-radius: 999px;
      }
      .rc-back:hover { background: var(--secondary-background-color); color: var(--primary-text-color); }
      .rc-back ha-icon { --mdc-icon-size: 18px; }
      .rc-detail-head h2 { margin: 0; font-size: 1.5rem; font-weight: 500; line-height: 1.25; }
      .rc-detail-desc { color: var(--secondary-text-color); font-size: .95rem; line-height: 1.5; }
      .rc-stats { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
      .rc-stat {
        display: inline-flex; align-items: center; gap: 5px;
        background: var(--secondary-background-color); border-radius: 999px;
        padding: 5px 12px; font-size: .8rem; color: var(--primary-text-color);
      }
      .rc-stat ha-icon { --mdc-icon-size: 15px; color: var(--secondary-text-color); }
      .rc-stat b { font-weight: 500; }

      .rc-cols { display: grid; gap: 20px; padding: 4px 16px 16px; grid-template-columns: 1fr; }
      @media (min-width: 620px) { .rc-cols { grid-template-columns: minmax(200px, 0.8fr) 1.2fr; } }

      .rc-col h3 {
        margin: 0 0 10px; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em;
        color: var(--secondary-text-color); font-weight: 600;
      }
      .rc-col-head {
        display: flex; align-items: center; justify-content: space-between;
        gap: 6px 10px; flex-wrap: wrap; margin: 0 0 10px;
      }
      .rc-col-head h3 { margin: 0; }
      .rc-scale { display: flex; align-items: center; gap: 3px; flex-wrap: wrap; }
      .rc-scale-l { font-size: .72rem; color: var(--secondary-text-color); margin-right: 2px; }
      .rc-scale button {
        border: 1px solid var(--divider-color); background: none; cursor: pointer;
        border-radius: 999px; padding: 2px 6px; min-width: 28px; font: inherit; font-size: .76rem;
        color: var(--secondary-text-color); transition: all .15s;
      }
      .rc-scale button:hover { background: var(--secondary-background-color); }
      .rc-scale button[aria-pressed="true"] {
        background: var(--primary-color); border-color: var(--primary-color);
        color: var(--text-primary-color, #fff); font-weight: 500;
      }
      .rc-scale input {
        width: 3em; padding: 2px 6px; font: inherit; font-size: .76rem; border-radius: 999px;
        border: 1px solid var(--divider-color); background: none; color: var(--primary-text-color);
      }
      .rc-scale input.on { border-color: var(--primary-color); }
      .rc-q { font-weight: 600; color: var(--primary-color); }
      .rc-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px; }
      .rc-item {
        display: flex; gap: 10px; align-items: flex-start; cursor: pointer;
        padding: 7px 8px; border-radius: 8px; line-height: 1.5; font-size: .92rem;
        transition: background .12s;
      }
      .rc-item:hover { background: var(--secondary-background-color); }
      .rc-item.done { color: var(--disabled-text-color); text-decoration: line-through; }
      .rc-check {
        flex: none; width: 18px; height: 18px; margin-top: 2px; border-radius: 4px;
        border: 2px solid var(--divider-color); display: inline-flex;
        align-items: center; justify-content: center; font-size: 12px; line-height: 1;
        color: var(--text-primary-color, #fff);
      }
      .rc-item.done .rc-check { background: var(--primary-color); border-color: var(--primary-color); }
      .rc-step-n {
        flex: none; width: 22px; height: 22px; border-radius: 50%; font-size: .75rem;
        display: inline-flex; align-items: center; justify-content: center; margin-top: 1px;
        background: var(--secondary-background-color); color: var(--secondary-text-color); font-weight: 600;
      }
      .rc-item.done .rc-step-n { background: var(--primary-color); color: var(--text-primary-color, #fff); }

      .rc-notes {
        margin: 0 16px 16px; padding: 12px 14px; border-radius: 8px;
        background: var(--secondary-background-color); font-size: .88rem; line-height: 1.55;
        color: var(--primary-text-color); border-left: 3px solid var(--rc-accent, var(--primary-color));
      }
      .rc-notes b {
        display: block; font-size: .72rem; text-transform: uppercase; letter-spacing: .08em;
        color: var(--secondary-text-color); margin-bottom: 4px; font-weight: 600;
      }

      /* ---------- tray ---------- */
      .rc-tray { display: flex; gap: 10px; overflow-x: auto; padding: 4px 16px 14px; }
      .rc-card-mini {
        flex: none; width: 130px; height: 86px; border-radius: 10px; cursor: pointer;
        border: 1px solid var(--divider-color); overflow: hidden; position: relative;
        display: flex; flex-direction: column; background: var(--card-background-color);
        transition: transform .15s, box-shadow .15s;
      }
      .rc-card-mini:hover { transform: translateY(-2px); }
      .rc-card-mini[aria-selected="true"] { border-color: var(--primary-color); box-shadow: 0 0 0 1px var(--primary-color); }
      .rc-card-mini .rc-band { height: 20px; }
      .rc-mini-t {
        padding: 6px 8px; font-size: .8rem; line-height: 1.25; font-weight: 500;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
      }

      /* ---------- empty / form ---------- */
      .rc-empty { padding: 28px 16px 34px; text-align: center; color: var(--secondary-text-color); }
      .rc-empty ha-icon { --mdc-icon-size: 40px; opacity: .35; display: block; margin: 0 auto 10px; }
      .rc-empty p { margin: 0 0 14px; font-size: .92rem; }

      .rc-field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
      .rc-label { font-size: .78rem; font-weight: 600; color: var(--secondary-text-color);
                  text-transform: uppercase; letter-spacing: .05em; }
      .rc-hint { font-size: .75rem; color: var(--secondary-text-color); font-weight: 400;
                 text-transform: none; letter-spacing: 0; }
      .rc-input, .rc-textarea {
        width: 100%; box-sizing: border-box; padding: 9px 11px; font: inherit; font-size: .92rem;
        border: 1px solid var(--divider-color); border-radius: 8px;
        background: var(--card-background-color); color: var(--primary-text-color);
      }
      .rc-input:focus, .rc-textarea:focus { outline: none; border-color: var(--primary-color); }
      .rc-textarea { min-height: 92px; resize: vertical; line-height: 1.5; }
      .rc-swatches { display: flex; gap: 8px; flex-wrap: wrap; }
      .rc-swatch { width: 28px; height: 28px; border-radius: 50%; cursor: pointer; border: 2px solid transparent; }
      .rc-swatch[aria-selected="true"] { border-color: var(--primary-text-color); }
      .rc-dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }

      /* self-contained modal - no dependency on ha-dialog being loaded */
      .rc-scrim {
        position: fixed; inset: 0; z-index: 9998; background: rgba(0,0,0,.55);
        display: flex; align-items: center; justify-content: center; padding: 16px;
      }
      .rc-modal {
        background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121);
        border-radius: 16px; width: min(720px, 100%); max-height: min(86vh, 900px);
        display: flex; flex-direction: column; overflow: hidden;
        box-shadow: 0 12px 40px rgba(0,0,0,.4);
      }
      .rc-modal-head {
        display: flex; align-items: center; gap: 10px; padding: 16px 12px 12px 20px;
        border-bottom: 1px solid var(--divider-color);
      }
      .rc-modal-head h2 { margin: 0; flex: 1; font-size: 1.2rem; font-weight: 500; line-height: 1.3; }
      .rc-close {
        border: 0; background: none; cursor: pointer; border-radius: 50%; padding: 6px; line-height: 0;
        color: var(--secondary-text-color);
      }
      .rc-close:hover { background: var(--secondary-background-color); color: var(--primary-text-color); }
      .rc-close ha-icon { --mdc-icon-size: 22px; }
      .rc-modal-body { overflow-y: auto; padding: 16px 20px 20px; flex: 1; }
      .rc-modal-foot {
        display: flex; justify-content: flex-end; gap: 8px; padding: 12px 16px;
        border-top: 1px solid var(--divider-color); background: var(--secondary-background-color);
      }
    </style>
  `;

  // ---------- batch multiplier: scale the amounts inside free-text ingredient lines ----------
  // Every amount on the line is scaled ("1 cup + 2 tbsp (270 ml)", "2 to 3 lemons");
  // package sizes, temperatures, times, percentages and cut sizes are left alone.
  const UNI = { '½': 1 / 2, '⅓': 1 / 3, '⅔': 2 / 3, '¼': 1 / 4, '¾': 3 / 4, '⅕': 1 / 5, '⅖': 2 / 5,
    '⅗': 3 / 5, '⅘': 4 / 5, '⅙': 1 / 6, '⅚': 5 / 6, '⅛': 1 / 8, '⅜': 3 / 8, '⅝': 5 / 8, '⅞': 7 / 8 };
  const UNI_CHARS = Object.keys(UNI).join('');
  const NUM = `(?:\\d+(?:\\s+|-)\\d+\\/\\d+|\\d+\\/\\d+|\\d*[${UNI_CHARS}]|\\d+(?:\\.\\d+)?)`;
  const QTY_RE = new RegExp(`(${NUM})(?:(\\s*(?:-|–|—|to)\\s*)(${NUM}))?`, 'g');
  const FRACTIONS = [[1, 8, '⅛'], [1, 4, '¼'], [1, 3, '⅓'], [3, 8, '⅜'], [1, 2, '½'],
    [5, 8, '⅝'], [2, 3, '⅔'], [1, 6, '⅙'], [5, 6, '⅚'], [3, 4, '¾'], [7, 8, '⅞']];
  const METRIC_RE = /^\s*(?:mg|g|gm|gms|grams?|kg|kilograms?|ml|mls|millilit(?:er|re)s?|cl|dl|l|lit(?:er|re)s?)\b/i;
  // Numbers that describe the thing rather than how much of it: temperatures,
  // percentages, times, pan sizes.
  const NOT_AMOUNT_RE = /^\s*(?:%|°|º|degrees?\b|(?:hours?|hrs?|minutes?|mins?|seconds?|secs?|days?|weeks?)\b|(?:cm|mm)\b|-?\s*inch|in\b|")/i;
  // "400 g can", "(400 g) tin": a package size, not an amount to multiply.
  const CONTAINER = '(?:cans?|tins?|jars?|packets?|packages?|packs?|pkts?|bags?|box(?:es)?|bottles?|cartons?|blocks?|tubs?|containers?|punnets?)';
  const SIZE_UNIT = '(?:g|gm|grams?|kg|kilograms?|ml|millilit(?:er|re)s?|l|lit(?:er|re)s?|oz|ounces?|lbs?|pounds?|fl\\.?\\s*oz)';
  const PACKAGE_RE = new RegExp(`^\\s*-?\\s*${SIZE_UNIT}\\b\\s*\\)?\\s*${CONTAINER}\\b`, 'i');
  // "1 can (8 ounces)": the size follows the container
  const AFTER_CONTAINER_RE = new RegExp(`\\b${CONTAINER}\\s*\\(\\s*(?:about\\s+)?$`, 'i');

  function parseNum(s) {
    s = s.trim();
    let m = s.match(/^(\d+)(?:\s+|-)(\d+)\/(\d+)$/);
    if (m) return +m[1] + +m[2] / +m[3];
    m = s.match(/^(\d+)\/(\d+)$/);
    if (m) return +m[2] ? +m[1] / +m[2] : NaN;
    m = s.match(new RegExp(`^(\\d*)([${UNI_CHARS}])$`));
    if (m) return (m[1] ? +m[1] : 0) + UNI[m[2]];
    return parseFloat(s);
  }

  function styleOf(s) {
    if (new RegExp(`[${UNI_CHARS}]`).test(s)) return 'unicode';
    if (s.includes('.')) return 'decimal';
    return 'ascii';
  }

  function formatNum(v, style, metric) {
    if (Math.abs(v - Math.round(v)) < 1e-6) return String(Math.round(v));
    if (!metric && style !== 'decimal') {
      const whole = Math.floor(v);
      const frac = v - whole;
      for (const [n, d, u] of FRACTIONS) {
        if (Math.abs(frac - n / d) < 0.01) {
          if (style === 'unicode') return `${whole || ''}${u}`;
          return whole ? `${whole} ${n}/${d}` : `${n}/${d}`;
        }
      }
    }
    const dp = v < 10 ? 2 : v < 100 ? 1 : 0;
    return String(Number(v.toFixed(dp)));
  }

  // Split an ingredient line into plain text and scaled-quantity parts.
  // Returns [{text, scaled: bool}] so callers can highlight what changed.
  function scaleParts(line, factor) {
    const text = String(line ?? '');
    if (!factor || factor === 1) return [{ text, scaled: false }];
    const parts = [];
    let last = 0;
    let packageAt = -1;  // first quantity skipped because it was a package/piece size
    QTY_RE.lastIndex = 0;
    let m;
    while ((m = QTY_RE.exec(text))) {
      const start = m.index;
      const end = start + m[0].length;
      const before = text.slice(0, start);
      const after = text.slice(end);
      const prev = before.slice(-1);
      const skip =
        /[A-Za-z]/.test(prev) ||                 // B12, Type 00 handled below
        /[x×]\s*$/i.test(before) ||              // "2 x 400g tins": the 400g
        /^-[A-Za-z]/.test(after) ||              // "28-ounce can", "12-wing bags"
        AFTER_CONTAINER_RE.test(before) ||
        NOT_AMOUNT_RE.test(after) ||
        PACKAGE_RE.test(after) ||
        /^\s*°?\s*[CF]\b/.test(after) && parseNum(m[1]) >= 100 ||  // 180C, 350 F
        parseNum(m[1]) === 0;
      if (skip) {
        if (packageAt < 0 && !parts.length && (PACKAGE_RE.test(after) || /^\s*-?\s*(?:inch|cm)\b/i.test(after))
            && /^\s*(?:[A-Za-z][A-Za-z ()]*:\s*)?$/.test(before)) packageAt = start;
        continue;
      }
      const metric = METRIC_RE.test(after);
      const a = parseNum(m[1]);
      if (!Number.isFinite(a)) continue;
      let out = formatNum(a * factor, styleOf(m[1]), metric);
      if (m[3] !== undefined) {
        const b = parseNum(m[3]);
        if (!Number.isFinite(b)) continue;
        out += m[2] + formatNum(b * factor, styleOf(m[3]), metric);
      }
      if (start > last) parts.push({ text: text.slice(last, start), scaled: false });
      parts.push({ text: out, scaled: true });
      last = end;
    }
    if (last < text.length) parts.push({ text: text.slice(last), scaled: false });
    if (packageAt >= 0 && !parts.some((p) => p.scaled)) {
      return [
        { text: text.slice(0, packageAt), scaled: false },
        { text: `${formatNum(factor, 'unicode', false)} × `, scaled: true },
        { text: text.slice(packageAt), scaled: false },
      ].filter((p) => p.text);
    }
    return parts;
  }
  const SCALE_PRESETS = [0.5, 1, 2, 3, 4];
  const FAVOURITES = '__favourites__';  // the tab value for the favourites filter

  const PALETTE = ['#D98F3B', '#8C3B2E', '#3E6B8A', '#5C8A3E', '#7B4B2A', '#6A4C93', '#B0455E', '#4A5568'];

  class RecipeCardsCard extends HTMLElement {
    static getStubConfig() {
      return { type: 'custom:recipecards-card' };
    }

    setConfig(config) {
      this._config = config || {};
      this._title = this._config.title || 'Recipes';
      this._view = this._config.view || (this._config.recipe_id ? 'detail' : 'collection');
      this._selected = null;
      this._entryFilter = this._config.entry_id || null;  // set by config only
      // favourites: true opens on the caller's favourites
      this._tagFilter = (this._config.favourites || this._config.favorites) ? FAVOURITES : (this._config.tag || 'all');
      this._query = '';
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._config) return;
      const sig = this._signature(hass);
      if (sig === this._sig) return;
      this._sig = sig;
      this._load();
    }

    _signature(hass) {
      let sig = '';
      for (const id in hass.states) {
        if (id.startsWith('sensor.recipe')) sig += id + hass.states[id].last_updated + '|';
      }
      const watched = this._config && this._config.entity;
      if (watched && hass.states[watched]) sig += watched + hass.states[watched].last_updated;
      return sig;
    }

    getCardSize() { return this._view === 'detail' ? 12 : 6; }

    // Only administrators may add, edit or delete. This hides the controls; the
    // integration refuses the underlying service and WebSocket calls regardless.
    _canEdit() {
      return Boolean(this._hass && this._hass.user && this._hass.user.is_admin);
    }

    // ---------- data ----------
    async _load() {
      const cfg = this._config || {};
      this._error = null;
      try {
        if (cfg.recipe_id) {
          const r = await this._hass.callWS({ type: 'recipecards/recipe_get', recipe_id: cfg.recipe_id });
          this._recipes = r ? [r] : [];
          this._selected = r ? r.id : null;
        } else {
          const list = await this._hass.callWS({ type: 'recipecards/recipe_list' });
          let recipes = Array.isArray(list) ? list : [];
          if (cfg.entry_id) recipes = recipes.filter((x) => x._entry_id === cfg.entry_id);
          this._recipes = recipes;
        }
      } catch (e) {
        try {
          if (cfg.entity) {
            const st = this._hass.states[cfg.entity];
            this._recipes = (st && st.attributes && st.attributes.recipes) || [];
          } else {
            throw e;
          }
        } catch (err) {
          this._recipes = [];
          this._error = (err && err.message) ? `Could not load recipes: ${err.message}` : 'Could not load recipes.';
          console.error('RecipeCards: load failed', err);
        }
      }
      this._render();
    }

    _visible() {
      let list = this._recipes || [];
      if (this._entryFilter) {
        list = list.filter((r) => r._entry_id === this._entryFilter);
      }
      if (this._tagFilter === FAVOURITES) {
        list = list.filter((r) => r._favorite);
      } else if (this._tagFilter && this._tagFilter !== 'all') {
        list = list.filter((r) => (r.tags || []).includes(this._tagFilter));
      }
      const q = (this._query || '').trim().toLowerCase();
      if (q) {
        list = list.filter((r) =>
          (r.title || '').toLowerCase().includes(q) ||
          (r.description || '').toLowerCase().includes(q) ||
          (r.tags || []).some((t) => String(t).toLowerCase().includes(q)) ||
          (r.ingredients || []).some((i) => String(i).toLowerCase().includes(q)));
      }
      return list;
    }

    _allTags() {
      const counts = new Map();
      const pool = this._entryFilter
        ? (this._recipes || []).filter((r) => r._entry_id === this._entryFilter)
        : (this._recipes || []);
      for (const r of pool) {
        for (const t of r.tags || []) counts.set(t, (counts.get(t) || 0) + 1);
      }
      // most used first, then alphabetical, so the useful tags lead
      return [...counts.entries()]
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .map(([tag, n]) => ({ tag, n }));
    }

    // ---------- tick state (survives re-render and reload) ----------
    _ticks(id) {
      try { return new Set(JSON.parse(localStorage.getItem('rc-ticks-' + id) || '[]')); }
      catch (e) { return new Set(); }
    }
    _toggleTick(id, key) {
      const set = this._ticks(id);
      if (set.has(key)) set.delete(key); else set.add(key);
      try { localStorage.setItem('rc-ticks-' + id, JSON.stringify([...set])); } catch (e) { /* private mode */ }
      return set;
    }

    // ---------- batch multiplier (per recipe; survives re-render and reload) ----------
    _scale(id) {
      try {
        const v = parseFloat(localStorage.getItem('rc-scale-' + id));
        return v > 0 ? v : 1;
      } catch (e) { return 1; }
    }
    _setScale(id, v) {
      try {
        if (v === 1) localStorage.removeItem('rc-scale-' + id);
        else localStorage.setItem('rc-scale-' + id, String(v));
      } catch (e) { /* private mode */ }
    }
    _ingHtml(item, factor) {
      return scaleParts(item, factor)
        .map((p) => (p.scaled ? `<b class="rc-q">${this._esc(p.text)}</b>` : this._esc(p.text)))
        .join('');
    }
    _scaleHtml(factor) {
      const custom = SCALE_PRESETS.includes(factor) ? '' : String(factor);
      return `<div class="rc-scale" role="group" aria-label="Batch size">
          <span class="rc-scale-l">Make</span>
          ${SCALE_PRESETS.map((v) => `<button type="button" data-scale="${v}" aria-pressed="${v === factor}">${v === 0.5 ? '½' : v}×</button>`).join('')}
          <input type="number" min="0.1" max="50" step="any" inputmode="decimal" placeholder="×"
                 aria-label="Custom multiplier" class="${custom ? 'on' : ''}" value="${custom}">
        </div>`;
    }

    // ---------- favourites (per HA user, stored by the integration) ----------
    _starHtml(r, extra) {
      const on = Boolean(r._favorite);
      const label = on ? 'Remove from favourites' : 'Add to favourites';
      return `<button type="button" class="rc-fav ${extra || ''} ${on ? 'on' : ''}" data-id="${this._esc(r.id)}"
          aria-pressed="${on}" aria-label="${label}" title="${label}">
          <ha-icon icon="${on ? 'mdi:star' : 'mdi:star-outline'}"></ha-icon></button>`;
    }
    _paintStar(btn, on) {
      const label = on ? 'Remove from favourites' : 'Add to favourites';
      btn.classList.toggle('on', on);
      btn.setAttribute('aria-pressed', String(on));
      btn.setAttribute('aria-label', label);
      btn.setAttribute('title', label);
      const icon = btn.querySelector('ha-icon');
      if (icon) icon.setAttribute('icon', on ? 'mdi:star' : 'mdi:star-outline');
    }
    _wireFavs(scope) {
      (scope || this).querySelectorAll('.rc-fav').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const r = (this._recipes || []).find((x) => x.id === btn.getAttribute('data-id'));
          if (r) this._toggleFavorite(r);
        });
        btn.addEventListener('keydown', (e) => e.stopPropagation());  // don't open the tile
      });
    }
    async _toggleFavorite(r) {
      const want = !r._favorite;
      r._favorite = want;  // show it straight away; put it back if the save fails
      this._favoriteChanged(r);
      try {
        const res = await this._hass.callWS({ type: 'recipecards/favorite_set', recipe_id: r.id, favorite: want });
        r._favorite = Boolean(res && res.favorite);
      } catch (err) {
        r._favorite = !want;
        this._toast(`Couldn't update favourites: ${(err && err.message) || err}`);
      }
      this._favoriteChanged(r);
    }
    _favoriteChanged(r) {
      // An open recipe dialog lives outside the card; repaint its star directly.
      document.querySelectorAll('.rc-scrim .rc-fav').forEach((btn) => {
        if (btn.getAttribute('data-id') === r.id) this._paintStar(btn, Boolean(r._favorite));
      });
      this._render();  // tab count, the favourites filter, every star in the card
    }

    // ---------- helpers ----------
    _esc(t) {
      return String(t ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    _fmtTime(mins) {
      if (!mins && mins !== 0) return null;
      if (mins < 60) return `${mins} min`;
      const h = Math.floor(mins / 60);
      const m = mins % 60;
      return m ? `${h} hr ${m} min` : `${h} hr`;
    }

    _toast(message) {
      this.dispatchEvent(new CustomEvent('hass-notification', {
        detail: { message: String(message) }, bubbles: true, composed: true,
      }));
    }

    _target(recipe) {
      if (recipe && recipe._entry_id) return recipe._entry_id;
      if (this._entryFilter && this._entryFilter !== 'all') return this._entryFilter;
      return this._config.entry_id || null;
    }

    _metaHtml(r) {
      const bits = [];
      const t = this._fmtTime(r.total_time) || this._fmtTime(r.cook_time);
      if (t) bits.push(`<span><ha-icon icon="${ICONS.clock}"></ha-icon>${t}</span>`);
      if (r.ingredients && r.ingredients.length) {
        bits.push(`<span><ha-icon icon="${ICONS.basket}"></ha-icon>${r.ingredients.length}</span>`);
      }
      if (r.instructions && r.instructions.length) {
        bits.push(`<span><ha-icon icon="${ICONS.steps}"></ha-icon>${r.instructions.length} steps</span>`);
      }
      return bits.join('');
    }

    // ---------- render ----------
    // A full re-render replaces the search box. If it had focus (a refresh arriving
    // mid-typing, a tab click, the tray view), put it back once ha-card has drawn.
    _render() {
      const prev = this.querySelector('.rc-search input');
      const root = prev && prev.getRootNode();
      const pos = prev && root && root.activeElement === prev ? prev.selectionStart : null;
      this._renderNow();
      if (pos !== null) this._refocusSearch(pos);
    }

    _refocusSearch(pos) {
      const input = this.querySelector('.rc-search input');
      if (!input) return;
      const go = () => {
        if (!input.isConnected) return;
        input.focus({ preventScroll: true });
        try { input.setSelectionRange(pos, pos); } catch (e) { /* not a text input */ }
      };
      // ha-card is a Lit element: until its first render adds the <slot>, our
      // content isn't rendered, and focus() on anything inside it silently fails.
      const card = this.querySelector('ha-card');
      if (card && card.updateComplete) card.updateComplete.then(go);
      else go();
    }

    // Typing in the search box: swap the count and the grid, never the box itself.
    _updateResults() {
      const old = this.querySelector('.rc-grid, .rc-empty');
      if (!old || this._view === 'tray') { this._render(); return; }
      const list = this._visible();
      const count = this.querySelector('.rc-count');
      if (count) count.textContent = `${list.length} recipe${list.length === 1 ? '' : 's'}`;
      const tmp = document.createElement('div');
      tmp.innerHTML = list.length
        ? `<div class="rc-grid">${list.map((r) => this._tileHtml(r)).join('')}</div>`
        : this._emptyHtml();
      old.replaceWith(...tmp.childNodes);
      this._wireTiles();
      this._wireMore();
      this._wireFavs(this.querySelector('.rc-grid'));
    }

    _renderNow() {
      if (!this._config) return;
      if (this._error) {
        this.innerHTML = `${STYLE}<ha-card><div class="rc-wrap"><ha-alert alert-type="error">${this._esc(this._error)}</ha-alert></div></ha-card>`;
        return;
      }
      if (this._view === 'detail' && this._selected) {
        const r = (this._recipes || []).find((x) => x.id === this._selected);
        if (r) return this._renderDetail(r);
        this._view = 'collection';
      }
      if (this._view === 'tray') return this._renderTray();
      return this._renderCollection();
    }

    _headerHtml(count) {
      const showSearch = (this._recipes || []).length > 3;
      return `
        <div class="rc-head">
          <h2>${this._esc(this._title)}<span class="rc-count">${count} recipe${count === 1 ? '' : 's'}</span></h2>
          ${showSearch ? `
            <label class="rc-search">
              <ha-icon icon="${ICONS.search}"></ha-icon>
              <input type="search" placeholder="Search" value="${this._esc(this._query)}" aria-label="Search recipes">
            </label>` : ''}
          ${this._canEdit() ? '<button class="rc-btn rc-add" type="button">Add recipe</button>' : ''}
        </div>`;
    }

    _tabsHtml() {
      const tags = this._allTags();
      const favs = (this._recipes || []).filter((r) => r._favorite).length;
      const showFavs = favs > 0 || this._tagFilter === FAVOURITES;
      if (tags.length < 2 && !showFavs) return '';
      const tab = (value, label) =>
        `<button class="rc-tab" role="tab" data-tag="${this._esc(value)}" aria-selected="${this._tagFilter === value}">${this._esc(label)}</button>`;
      return `<div class="rc-tabs" role="tablist">
        ${tab('all', 'All')}${showFavs ? tab(FAVOURITES, `★ Favourites ${favs}`) : ''}${
          tags.map((t) => tab(t.tag, `${t.tag} ${t.n}`)).join('')}
      </div>`;
    }

    _tileHtml(r) {
      const colour = r.color || PALETTE[0];
      return `
        <div class="rc-tile ${r.image ? 'has-img' : 'no-img'}" data-id="${this._esc(r.id)}" tabindex="0" role="button"
             aria-label="Open ${this._esc(r.title)}">
          ${r.image
            ? `<img class="rc-thumb" src="${this._esc(r.image)}" alt="" loading="lazy"
                 onerror="this.remove()">
               <div class="rc-band" style="background:${this._esc(colour)}"></div>`
            : `<div class="rc-band" style="background:${this._esc(colour)}"></div>`}
          ${this._canEdit() ? `<button class="rc-more" data-id="${this._esc(r.id)}" aria-label="More actions for ${this._esc(r.title)}">
            <ha-icon icon="${ICONS.more}"></ha-icon>
          </button>` : ''}
          ${this._starHtml(r, this._canEdit() ? 'beside-more' : '')}
          <div class="rc-body">
            <div class="rc-title">${this._esc(r.title)}</div>
            ${r.description ? `<div class="rc-desc">${this._esc(r.description)}</div>` : ''}
            <div class="rc-meta">
              ${(r.tags || []).slice(0, 2).map((t) => `<span class="rc-section">${this._esc(t)}</span>`).join('')}
              ${this._metaHtml(r)}
            </div>
          </div>
        </div>`;
    }

    _emptyHtml() {
      const filtered = (this._recipes || []).length > 0;
      return `<div class="rc-empty">
        <ha-icon icon="mdi:chef-hat"></ha-icon>
        <p>${this._tagFilter === FAVOURITES && !(this._query || '').trim()
          ? 'No favourites yet. Tap the ☆ on a recipe to add it here.'
          : filtered ? 'No recipes match that search.' : 'No recipes yet.'}</p>
        ${filtered || !this._canEdit() ? '' : '<button class="rc-btn rc-add" type="button">Add your first recipe</button>'}
      </div>`;
    }

    _renderCollection() {
      const list = this._visible();
      this.innerHTML = `${STYLE}
        <ha-card><div class="rc-wrap">
          ${this._headerHtml(list.length)}
          ${this._tabsHtml()}
          ${list.length ? `<div class="rc-grid">${list.map((r) => this._tileHtml(r)).join('')}</div>` : this._emptyHtml()}
        </div></ha-card>`;
      this._wireCommon();
      this._wireTiles();
      this._wireFavs();
    }

    _renderTray() {
      const list = this._visible();
      const sel = list.find((x) => x.id === this._selected) || list[0];
      this.innerHTML = `${STYLE}
        <ha-card><div class="rc-wrap">
          ${this._headerHtml(list.length)}
          ${this._tabsHtml()}
          ${list.length ? `<div class="rc-tray">${list.map((r) => `
            <div class="rc-card-mini" data-id="${this._esc(r.id)}" tabindex="0" role="button"
                 aria-selected="${sel && sel.id === r.id}" aria-label="${this._esc(r.title)}">
              <div class="rc-band" style="background:${this._esc(r.color || PALETTE[0])}"></div>
              <div class="rc-mini-t">${this._esc(r.title)}</div>
            </div>`).join('')}</div>` : this._emptyHtml()}
          ${sel ? this._detailBodyHtml(sel) : ''}
        </div></ha-card>`;
      this._wireCommon();
      this.querySelectorAll('.rc-card-mini').forEach((el) => {
        const open = () => { this._selected = el.getAttribute('data-id'); this._render(); };
        el.addEventListener('click', open);
        el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
      });
      if (sel) this._wireDetailBody(sel);
    }

    _detailBodyHtml(r) {
      const ticks = this._ticks(r.id);
      const factor = this._scale(r.id);
      const ing = (r.ingredients || []).map((item, i) => {
        const done = ticks.has('i' + i);
        return `<li class="rc-item ${done ? 'done' : ''}" data-tick="i${i}">
          <span class="rc-check">${done ? '&#10003;' : ''}</span><span class="rc-ing">${this._ingHtml(item, factor)}</span></li>`;
      }).join('');
      const steps = (r.instructions || []).map((item, i) => {
        const done = ticks.has('s' + i);
        return `<li class="rc-item ${done ? 'done' : ''}" data-tick="s${i}">
          <span class="rc-step-n">${i + 1}</span><span>${this._esc(item)}</span></li>`;
      }).join('');
      return `
        <div class="rc-cols">
          ${ing ? `<div class="rc-col"><div class="rc-col-head"><h3>Ingredients</h3>${this._scaleHtml(factor)}</div><ul class="rc-list">${ing}</ul></div>` : ''}
          ${steps ? `<div class="rc-col"><h3>Method</h3><ul class="rc-list">${steps}</ul></div>` : ''}
        </div>
        ${r.notes ? `<div class="rc-notes" style="--rc-accent:${this._esc(r.color || PALETTE[0])}"><b>Notes</b>${this._esc(r.notes)}</div>` : ''}`;
    }

    _renderDetail(r) {
      const stats = this._statsHtml(r);
      const pinned = this._config.view === 'detail' || this._config.recipe_id;

      this.innerHTML = `${STYLE}
        <ha-card><div class="rc-wrap">
          ${r.image
            ? `<img class="rc-thumb" style="height:200px" src="${this._esc(r.image)}" alt="" onerror="this.remove()">`
            : ''}
          <div class="rc-band" style="background:${this._esc(r.color || PALETTE[0])};height:8px"></div>
          <div class="rc-detail-head">
            <div class="rc-detail-top">
              ${pinned ? '' : `<button class="rc-back"><ha-icon icon="${ICONS.back}"></ha-icon>All recipes</button>`}
              <span style="flex:1"></span>
              ${this._starHtml(r, 'inline')}
              <button class="rc-more" style="position:static" data-id="${this._esc(r.id)}" aria-label="More actions">
                <ha-icon icon="${ICONS.more}"></ha-icon>
              </button>
            </div>
            <h2>${this._esc(r.title)}</h2>
            ${r.description ? `<div class="rc-detail-desc">${this._esc(r.description)}</div>` : ''}
            ${stats ? `<div class="rc-stats">${stats}</div>` : ''}
          </div>
          ${this._detailBodyHtml(r)}
        </div></ha-card>`;

      this.querySelector('.rc-back')?.addEventListener('click', () => {
        this._view = this._config.view === 'detail' ? 'detail' : 'collection';
        if (this._config.view === 'detail') return;
        this._selected = null; this._render();
      });
      this._wireMore();
      this._wireFavs();
      this._wireDetailBody(r);
    }

    _wireDetailBody(r, root) {
      const scope = root || this;
      // Re-render only the ingredient text, so an open recipe or modal stays put.
      const apply = (v) => {
        v = Math.round(v * 100) / 100;
        if (!(v > 0)) return;
        this._setScale(r.id, v);
        (r.ingredients || []).forEach((item, i) => {
          const span = scope.querySelector(`.rc-item[data-tick="i${i}"] .rc-ing`);
          if (span) span.innerHTML = this._ingHtml(item, v);
        });
        scope.querySelectorAll('.rc-scale button').forEach((b) => {
          b.setAttribute('aria-pressed', String(parseFloat(b.getAttribute('data-scale')) === v));
        });
        const input = scope.querySelector('.rc-scale input');
        if (input) {
          const custom = !SCALE_PRESETS.includes(v);
          input.classList.toggle('on', custom);
          if (!custom) input.value = '';
        }
      };
      scope.querySelectorAll('.rc-scale button').forEach((b) => {
        b.addEventListener('click', () => apply(parseFloat(b.getAttribute('data-scale'))));
      });
      const custom = scope.querySelector('.rc-scale input');
      if (custom) {
        custom.addEventListener('change', () => {
          const v = parseFloat(custom.value);
          if (v > 0 && v <= 50) apply(v);
          else if (!custom.value) apply(1);
        });
      }
      scope.querySelectorAll('.rc-item').forEach((el) => {
        el.addEventListener('click', () => {
          const key = el.getAttribute('data-tick');
          const set = this._toggleTick(r.id, key);
          const done = set.has(key);
          el.classList.toggle('done', done);
          const box = el.querySelector('.rc-check');
          if (box) box.innerHTML = done ? '&#10003;' : '';
        });
      });
    }

    _wireCommon() {
      this.querySelectorAll('.rc-add').forEach((b) => b.addEventListener('click', () => this._openForm()));
      this.querySelectorAll('.rc-tab').forEach((b) => b.addEventListener('click', () => {
        this._tagFilter = b.getAttribute('data-tag');
        this._render();
      }));
      const search = this.querySelector('.rc-search input');
      if (search) {
        search.addEventListener('input', (e) => {
          this._query = e.target.value;
          this._updateResults();
        });
      }
      this._wireMore();
    }

    _wireTiles() {
      this.querySelectorAll('.rc-tile').forEach((el) => {
        const open = () => {
          const r = (this._recipes || []).find((x) => x.id === el.getAttribute('data-id'));
          if (r) this._openRecipe(r);
        };
        el.addEventListener('click', (e) => { if (!e.target.closest('.rc-more, .rc-fav')) open(); });
        el.addEventListener('keydown', (e) => {
          if (e.target !== el) return;  // Enter on the star or menu button is theirs
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
        });
      });
    }

    _wireMore() {
      this.querySelectorAll('.rc-more').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const r = (this._recipes || []).find((x) => x.id === btn.getAttribute('data-id'));
          if (r) this._openMenu(btn, r);
        });
      });
    }

    _openMenu(anchor, r) {
      const existing = document.querySelector('.rc-menu-sheet');
      if (existing) existing.remove();
      const sheet = document.createElement('div');
      sheet.className = 'rc-menu-sheet';
      const rect = anchor.getBoundingClientRect();
      sheet.setAttribute('style', `position:fixed;z-index:9999;top:${rect.bottom + 4}px;left:${Math.max(8, rect.right - 160)}px;
        min-width:150px;background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ddd);
        border-radius:10px;box-shadow:0 6px 20px rgba(0,0,0,.24);overflow:hidden;`);
      sheet.innerHTML = `
        <button class="rc-menu-edit" style="all:unset;display:block;width:100%;box-sizing:border-box;padding:11px 14px;cursor:pointer;font-size:.9rem;color:var(--primary-text-color,#222);">Edit</button>
        <button class="rc-menu-del" style="all:unset;display:block;width:100%;box-sizing:border-box;padding:11px 14px;cursor:pointer;font-size:.9rem;color:var(--error-color,#c62828);">Delete</button>`;
      document.body.appendChild(sheet);
      const close = () => { sheet.remove(); document.removeEventListener('click', close, true); };
      setTimeout(() => document.addEventListener('click', close, true), 0);
      sheet.querySelector('.rc-menu-edit').addEventListener('click', () => { close(); this._openForm(r); });
      sheet.querySelector('.rc-menu-del').addEventListener('click', () => { close(); this._delete(r); });
    }

    // ---------- modal ----------
    _modal(heading, bodyHtml, buttons) {
      document.querySelectorAll('.rc-scrim').forEach((el) => el.remove());
      const scrim = document.createElement('div');
      scrim.className = 'rc-scrim';
      scrim.innerHTML = `${STYLE}
        <div class="rc-modal" role="dialog" aria-modal="true" aria-label="${this._esc(heading)}">
          <div class="rc-modal-head">
            <h2>${this._esc(heading)}</h2>
            <button class="rc-close" type="button" aria-label="Close"><ha-icon icon="mdi:close"></ha-icon></button>
          </div>
          <div class="rc-modal-body">${bodyHtml}</div>
          <div class="rc-modal-foot"></div>
        </div>`;
      document.body.appendChild(scrim);
      const prevOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';

      const close = () => {
        document.body.style.overflow = prevOverflow;
        document.removeEventListener('keydown', onKey, true);
        scrim.remove();
      };
      const onKey = (e) => { if (e.key === 'Escape') { e.stopPropagation(); close(); } };
      document.addEventListener('keydown', onKey, true);
      scrim.addEventListener('mousedown', (e) => { if (e.target === scrim) close(); });
      scrim.querySelector('.rc-close').addEventListener('click', close);

      const foot = scrim.querySelector('.rc-modal-foot');
      for (const b of buttons || []) {
        const el = document.createElement('button');
        el.type = 'button';
        el.className = 'rc-btn' + (b.style ? ' ' + b.style : '');
        el.textContent = b.label;
        el.addEventListener('click', () => b.onClick(close));
        foot.appendChild(el);
      }
      return { scrim, body: scrim.querySelector('.rc-modal-body'), close };
    }

    // ---------- read a recipe ----------
    _openRecipe(r) {
      const stats = this._statsHtml(r);
      const body = `
        ${r.image
          ? `<img class="rc-hero" src="${this._esc(r.image)}" alt="" onerror="this.remove()">`
          : `<div class="rc-band" style="background:${this._esc(r.color || PALETTE[0])};height:6px;border-radius:3px;margin-bottom:14px"></div>`}
        ${r.description ? `<div class="rc-detail-desc" style="margin-bottom:10px">${this._esc(r.description)}</div>` : ''}
        ${stats ? `<div class="rc-stats" style="margin-bottom:6px">${stats}</div>` : ''}
        ${(r.tags || []).length ? `<div class="rc-meta" style="margin-bottom:10px">${
            (r.tags || []).map((t) => `<span class="rc-section">${this._esc(t)}</span>`).join('')
          }</div>` : ''}
        ${this._detailBodyHtml(r)}`;

      const buttons = [];
      if (this._canEdit()) {
        buttons.push({ label: 'Delete', style: 'danger', onClick: (close) => { close(); this._delete(r); } });
        buttons.push({ label: 'Edit', style: 'ghost', onClick: (close) => { close(); this._openForm(r); } });
      }
      buttons.push({ label: 'Done', onClick: (close) => close() });
      const m = this._modal(r.title, body, buttons);
      const head = m.scrim.querySelector('.rc-modal-head');
      head.insertAdjacentHTML('beforeend', this._starHtml(r, 'inline'));
      head.appendChild(head.querySelector('.rc-close'));  // keep close last
      this._wireFavs(head);
      m.body.querySelectorAll('.rc-cols').forEach((el) => { el.style.padding = '4px 0 0'; });
      m.body.querySelectorAll('.rc-notes').forEach((el) => { el.style.margin = '14px 0 0'; });
      this._wireDetailBody(r, m.body);
    }

    _statsHtml(r) {
      const stats = [];
      if (r.prep_time) stats.push(`<span class="rc-stat"><ha-icon icon="${ICONS.clock}"></ha-icon>Prep <b>${this._fmtTime(r.prep_time)}</b></span>`);
      if (r.cook_time) stats.push(`<span class="rc-stat"><ha-icon icon="mdi:stove"></ha-icon>Cook <b>${this._fmtTime(r.cook_time)}</b></span>`);
      if (r.total_time) stats.push(`<span class="rc-stat"><ha-icon icon="mdi:timer-outline"></ha-icon>Total <b>${this._fmtTime(r.total_time)}</b></span>`);
      if (r.ingredients && r.ingredients.length) stats.push(`<span class="rc-stat"><ha-icon icon="${ICONS.basket}"></ha-icon><b>${r.ingredients.length}</b> ingredients</span>`);
      return stats.join('');
    }

    // ---------- add / edit ----------
    _openForm(r) {
      if (!this._canEdit()) { this._toast('Only an administrator can change recipes.'); return; }
      const colour = (r && r.color) || PALETTE[0];
      const body = `
        <div class="rc-field">
          <label class="rc-label">Title</label>
          <input class="rc-input rc-f-title" value="${this._esc(r?.title)}" placeholder="Anzac Biscuits">
        </div>
        <div class="rc-field">
          <label class="rc-label">Description</label>
          <input class="rc-input rc-f-desc" value="${this._esc(r?.description)}" placeholder="Chewy, golden, keeps for a fortnight">
        </div>
        <div class="rc-field">
          <label class="rc-label">Ingredients <span class="rc-hint">one per line</span></label>
          <textarea class="rc-textarea rc-f-ings" placeholder="1 cup rolled oats&#10;125 g butter">${this._esc((r?.ingredients || []).join('\n'))}</textarea>
        </div>
        <div class="rc-field">
          <label class="rc-label">Method <span class="rc-hint">one step per line &mdash; times are picked up automatically</span></label>
          <textarea class="rc-textarea rc-f-steps" placeholder="Prep for 15 minutes: heat the oven to 160C.&#10;Bake for 20 minutes until golden.">${this._esc((r?.instructions || []).join('\n'))}</textarea>
        </div>
        <div class="rc-field">
          <label class="rc-label">Notes</label>
          <textarea class="rc-textarea rc-f-notes" style="min-height:60px" placeholder="Leave on the tray 5 minutes or they break.">${this._esc(r?.notes)}</textarea>
        </div>
        <div class="rc-field">
          <label class="rc-label">Tags <span class="rc-hint">comma separated, a recipe can have several</span></label>
          <input class="rc-input rc-f-tags" value="${this._esc((r?.tags || []).join(', '))}" placeholder="Mains, Slow Cooked, Keto">
        </div>
        <div class="rc-field">
          <label class="rc-label">Image <span class="rc-hint">a link to a photo, optional</span></label>
          <input class="rc-input rc-f-image" value="${this._esc(r?.image)}" placeholder="https://example.com/photo.jpg">
        </div>
        <div class="rc-field">
          <label class="rc-label">Colour</label>
          <div class="rc-swatches">
            ${PALETTE.map((c) => `<span class="rc-swatch" data-colour="${c}" style="background:${c}" aria-selected="${c === colour}" role="button" tabindex="0"></span>`).join('')}
          </div>
        </div>`;

      let chosen = colour;
      let saving = false;

      const save = async (close) => {
        if (saving) return;
        const q = (sel) => m.body.querySelector(sel);
        const lines = (sel) => q(sel).value.split('\n').map((x) => x.trim()).filter(Boolean);
        const title = q('.rc-f-title').value.trim();
        if (!title) { this._toast('Give the recipe a title.'); q('.rc-f-title').focus(); return; }
        const payload = {
          title,
          description: q('.rc-f-desc').value.trim(),
          ingredients: lines('.rc-f-ings'),
          instructions: lines('.rc-f-steps'),
          notes: q('.rc-f-notes').value.trim(),
          color: chosen,
          image: q('.rc-f-image').value.trim() || null,
          tags: q('.rc-f-tags').value.split(',').map((x) => x.trim()).filter(Boolean),
        };
        const target = this._target(r);
        if (target) payload.config_entry_id = target;
        saving = true;
        try {
          if (r) {
            payload.recipe_id = r.id;
            await this._hass.callService('recipecards', 'update_recipe', payload);
          } else {
            await this._hass.callService('recipecards', 'add_recipe', payload);
          }
          await this._load();
          close();
        } catch (e) {
          saving = false;
          console.error('RecipeCards: save failed', e);
          this._toast(`Could not save recipe: ${(e && (e.message || e.error)) || e}`);
        }
      };

      const m = this._modal(r ? 'Edit recipe' : 'Add recipe', body, [
        { label: 'Cancel', style: 'ghost', onClick: (close) => close() },
        { label: r ? 'Save changes' : 'Add recipe', onClick: save },
      ]);

      m.body.querySelectorAll('.rc-swatch').forEach((sw) => sw.addEventListener('click', () => {
        chosen = sw.getAttribute('data-colour');
        m.body.querySelectorAll('.rc-swatch').forEach((o) => o.setAttribute('aria-selected', String(o === sw)));
      }));
      // Ctrl/Cmd+Enter saves
      m.body.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); save(m.close); }
      });
      setTimeout(() => m.body.querySelector('.rc-f-title')?.focus(), 60);
    }

    async _delete(r) {
      if (!this._canEdit()) { this._toast('Only an administrator can change recipes.'); return; }
      if (!confirm(`Delete "${r.title}"?`)) return;
      try {
        const payload = { recipe_id: r.id };
        const target = this._target(r);
        if (target) payload.config_entry_id = target;
        await this._hass.callService('recipecards', 'delete_recipe', payload);
        try { localStorage.removeItem('rc-ticks-' + r.id); } catch (e) { /* ignore */ }
        if (this._selected === r.id) { this._selected = null; this._view = this._config.view || 'collection'; }
        await this._load();
      } catch (e) {
        console.error('RecipeCards: delete failed', e);
        this._toast(`Could not delete recipe: ${(e && (e.message || e.error)) || e}`);
      }
    }
  }

  const RC_VERSION = '2.3.0';
  try {
    RecipeCardsCard.scaleParts = scaleParts;  // for tests
    if (!customElements.get('recipecards-card')) {
      customElements.define('recipecards-card', RecipeCardsCard);
      console.info(
        `%c RECIPE-CARDS %c v${RC_VERSION} `,
        'color:#fff;background:#7B4B2A;font-weight:700',
        'color:#7B4B2A;background:#fff;font-weight:700');
    }
    window.customCards = window.customCards || [];
    if (!window.customCards.some((c) => c.type === 'recipecards-card')) {
      window.customCards.push({
        type: 'recipecards-card',
        name: 'Recipe Cards',
        description: 'Browse, cook from, and manage your recipes',
        preview: false,
      });
    }
  } catch (error) {
    console.error('RecipeCards: could not register the custom element', error);
  }
})();
