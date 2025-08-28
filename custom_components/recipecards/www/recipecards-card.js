// Minimal buildless version of the RecipeCards Lovelace card.
// This file is auto-served and auto-loaded by the integration; no NPM build needed.
(function() {
  class RecipeCardsCard extends HTMLElement {
    setConfig(config) {
      if (!config || !config.entity) {
        throw new Error('You need to define an entity');
      }
      this._config = config;
      this._title = config.title || 'Recipe Collection';
      this._view = config.view || 'collection';
      this._selected = null;
      this.style.display = 'block';
      this.style.padding = '8px';
      this.style.boxSizing = 'border-box';
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._config) return;
      const st = hass.states[this._config.entity];
      if (!st) {
        this._recipes = [];
        this._error = `Entity not found: ${this._config.entity}`;
      } else {
        this._recipes = (st.attributes && st.attributes.recipes) || [];
        this._error = null;
        if (!this._selected && this._recipes.length) {
          this._selected = this._recipes[0].id;
        }
      }
      this._render();
    }

    getCardSize() {
      return 3;
    }

    _header(html) {
      return `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <div style="font-weight:bold;">${html}</div>
          <mwc-button raised class="rc-add">Add</mwc-button>
        </div>
      `;
    }

    _render() {
      if (!this._config) return;
      const recipes = this._recipes || [];
      const err = this._error;

      const style = `
        <style>
          .rc-grid { display:grid; grid-template-columns: repeat(auto-fill,minmax(180px,1fr)); gap:8px; }
          .rc-tile { border:1px solid var(--divider-color); border-radius:8px; padding:10px; background:var(--card-background-color); cursor:pointer; }
          .rc-t { font-weight:bold; margin-bottom:4px; }
          .rc-actions { display:flex; gap:6px; margin-top:8px; }
          .rc-btn { border:1px solid var(--divider-color); border-radius:6px; padding:4px 8px; background:none; cursor:pointer; }
          .rc-detail h3 { margin: 0 0 6px 0; }
          .rc-back { margin-bottom: 8px; }
          .rc-field { margin: 6px 0; }
          .rc-label { display:block; font-weight:bold; margin-bottom:2px; }
          .rc-input, .rc-textarea { width:100%; box-sizing:border-box; padding:6px; border:1px solid var(--divider-color); border-radius:6px; background:var(--card-background-color); color:var(--primary-text-color); }
          .rc-textarea { min-height: 70px; }
        </style>
      `;

      if (err) {
        this.innerHTML = `${style}<ha-alert alert-type="error">${err}</ha-alert>`;
        return;
      }

      if (this._view === 'detail' && this._selected) {
        const r = recipes.find(x => x.id === this._selected);
        if (!r) { this._view = 'collection'; }
        else {
          this.innerHTML = `${style}
            <mwc-button class="rc-back">Back</mwc-button>
            <div class="rc-detail">
              <h3>${this._escape(r.title)}</h3>
              ${r.description ? `<div>${this._escape(r.description)}</div>` : ''}
              ${r.ingredients?.length ? `<div><b>Ingredients</b><ul>${r.ingredients.map(i=>`<li>${this._escape(i)}</li>`).join('')}</ul></div>` : ''}
              ${r.instructions?.length ? `<div><b>Instructions</b><ol>${r.instructions.map(i=>`<li>${this._escape(i)}</li>`).join('')}</ol></div>` : ''}
              ${r.notes ? `<div><b>Notes</b><div>${this._escape(r.notes)}</div></div>` : ''}
              <div class="rc-actions">
                <button class="rc-btn rc-edit">Edit</button>
                <button class="rc-btn rc-del">Delete</button>
              </div>
            </div>
          `;
          this.querySelector('.rc-back')?.addEventListener('click', ()=>{ this._view='collection'; this._render(); });
          this.querySelector('.rc-edit')?.addEventListener('click', ()=> this._openEdit(r));
          this.querySelector('.rc-del')?.addEventListener('click', ()=> this._delete(r));
          return;
        }
      }

      const grid = recipes.map(r=>`
        <div class="rc-tile" data-id="${this._escape(r.id)}">
          <div class="rc-t">${this._escape(r.title)}</div>
          ${r.description ? `<div>${this._escape(r.description)}</div>` : ''}
          <div class="rc-actions">
            <button class="rc-btn rc-open">Open</button>
            <button class="rc-btn rc-edit">Edit</button>
            <button class="rc-btn rc-del">Delete</button>
          </div>
        </div>
      `).join('');

      this.innerHTML = `${style}
        ${this._header(this._title)}
        ${recipes.length ? `<div class="rc-grid">${grid}</div>` : `<ha-alert>Click Add to create your first recipe.</ha-alert>`}
      `;

      this.querySelector('.rc-add')?.addEventListener('click', ()=> this._openAdd());
      this.querySelectorAll('.rc-tile').forEach(tile => {
        const id = tile.getAttribute('data-id');
        tile.querySelector('.rc-open')?.addEventListener('click', (e)=>{ e.stopPropagation(); this._selected=id; this._view='detail'; this._render(); });
        tile.querySelector('.rc-edit')?.addEventListener('click', (e)=>{ e.stopPropagation(); const r=recipes.find(x=>x.id===id); if(r) this._openEdit(r); });
        tile.querySelector('.rc-del')?.addEventListener('click', (e)=>{ e.stopPropagation(); const r=recipes.find(x=>x.id===id); if(r) this._delete(r); });
      });
    }

    _escape(t){ return String(t ?? '').replace(/[<>]/g,''); }

    _openAdd(){ this._openForm(); }
    _openEdit(r){ this._openForm(r); }

    _openForm(r){
      const wrap = document.createElement('div');
      wrap.innerHTML = `
        <div class="rc-field"><label class="rc-label">Title *</label><input class="rc-input rc-title" value="${r?.title??''}"></div>
        <div class="rc-field"><label class="rc-label">Description</label><input class="rc-input rc-desc" value="${r?.description??''}"></div>
        <div class="rc-field"><label class="rc-label">Ingredients (one per line)</label><textarea class="rc-textarea rc-ings">${(r?.ingredients||[]).join('\n')}</textarea></div>
        <div class="rc-field"><label class="rc-label">Instructions (one per line)</label><textarea class="rc-textarea rc-steps">${(r?.instructions||[]).join('\n')}</textarea></div>
        <div class="rc-field"><label class="rc-label">Notes</label><textarea class="rc-textarea rc-notes">${r?.notes??''}</textarea></div>
        <div class="rc-actions">
          <mwc-button raised class="rc-save">${r? 'Update':'Add'} Recipe</mwc-button>
          <mwc-button class="rc-cancel">Cancel</mwc-button>
        </div>
      `;
      const dlg = document.createElement('ha-dialog');
      dlg.open = true;
      dlg.appendChild(wrap);
      dlg.addEventListener('closed', ()=> dlg.remove());
      document.body.appendChild(dlg);
      wrap.querySelector('.rc-cancel')?.addEventListener('click', ()=> dlg.close());
      wrap.querySelector('.rc-save')?.addEventListener('click', async ()=>{
        const title = wrap.querySelector('.rc-title').value.trim();
        const description = wrap.querySelector('.rc-desc').value.trim();
        const ingredients = wrap.querySelector('.rc-ings').value.split('\n').map(s=>s.trim()).filter(Boolean);
        const instructions = wrap.querySelector('.rc-steps').value.split('\n').map(s=>s.trim()).filter(Boolean);
        const notes = wrap.querySelector('.rc-notes').value.trim();
        try {
          if (r) {
            await this._hass.callService('recipecards', 'update_recipe', {
              recipe_id: r.id,
              title, description, ingredients, instructions, notes
            });
          } else {
            await this._hass.callService('recipecards', 'add_recipe', {
              title, description, ingredients, instructions, notes
            });
          }
          dlg.close();
        } catch (e) {
          // eslint-disable-next-line no-console
          console.error('Recipe save failed', e);
        }
      });
    }

    async _delete(r){
      if (!confirm('Delete this recipe?')) return;
      try {
        await this._hass.callService('recipecards', 'delete_recipe', { recipe_id: r.id });
        this._view='collection';
      } catch(e){
        // eslint-disable-next-line no-console
        console.error('Delete failed', e);
      }
    }
  }

  customElements.define('recipecards-card', RecipeCardsCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'recipecards-card',
    name: 'RecipeCards Card',
    description: 'Browse, add, edit, and delete recipes',
  });
})();

