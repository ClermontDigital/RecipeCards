// Minimal buildless version of the RecipeCards Lovelace card.
// This file is auto-served and auto-loaded by the integration; no NPM build needed.
(function() {
  class RecipeCardsCard extends HTMLElement {
    setConfig(config) {
      if (!config || (!config.entity && !config.entry_id && !config.recipe_id)) {
        throw new Error('You need to define an entity, entry_id, or recipe_id');
      }
      this._config = config;
      this._title = config.title || 'Recipe Collection';
      this._view = config.view || (config.recipe_id ? 'detail' : 'collection');
      this._selected = null;
      this._entryFilter = config.entry_id || 'all';
      this.style.display = 'block';
      this.style.padding = '8px';
      this.style.boxSizing = 'border-box';
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._config) return;
      this._load();
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

    async _load(){
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
          if (cfg.entry_id) recipes = recipes.filter(x => x._entry_id === cfg.entry_id);
          if (this._entryFilter && this._entryFilter !== 'all') recipes = recipes.filter(x => x._entry_id === this._entryFilter);
          this._recipes = recipes;
          if (!this._selected && this._recipes.length) this._selected = this._recipes[0].id;
        }
      } catch(e) {
        // Fallback to legacy entity attribute if provided
        try {
          if (cfg.entity) {
            const st = this._hass.states[cfg.entity];
            if (st && st.attributes && st.attributes.id) {
              this._recipes = [st.attributes];
              this._selected = st.attributes.id;
            } else {
              this._recipes = (st && st.attributes && st.attributes.recipes) || [];
            }
          } else {
            throw e;
          }
        } catch(err) {
          this._recipes = [];
          this._error = 'Failed to load recipes';
        }
      }
      this._render();
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
          .rc-tools { display:flex; align-items:center; gap:8px; }
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

      const entryIds = Array.from(new Set((recipes||[]).map(r=>r._entry_id).filter(Boolean)));
      if (this._view === 'tray') {
        const tray = recipes.map(r=>`
          <div class="rc-tile rc-tray" data-id="${this._escape(r.id)}" style="min-width:140px;height:100px;position:relative;display:flex;flex-direction:column;justify-content:flex-end;">
            <div style="position:absolute;top:0;left:0;right:0;height:14px;border-radius:6px 6px 0 0;background:${r.color||'#bfa14a'}"></div>
            <div class="rc-t" style="margin-top:16px">${this._escape(r.title)}</div>
            <div class="rc-actions" style="position:absolute;right:6px;bottom:6px;gap:4px;">
              <button class="rc-btn rc-edit">Edit</button>
              <button class="rc-btn rc-del">Del</button>
            </div>
          </div>
        `).join('');
        const detail = (()=>{
          const r = recipes.find(x=>x.id===this._selected);
          if (!r) return '<ha-alert>Select a card to view</ha-alert>';
          return `
            <div class="rc-detail">
              <h3>${this._escape(r.title)}</h3>
              ${r.description ? `<div>${this._escape(r.description)}</div>` : ''}
              ${r.ingredients?.length ? `<div><b>Ingredients</b><ul>${r.ingredients.map(i=>`<li>${this._escape(i)}</li>`).join('')}</ul></div>` : ''}
              ${r.instructions?.length ? `<div><b>Instructions</b><ol>${r.instructions.map(i=>`<li>${this._escape(i)}</li>`).join('')}</ol></div>` : ''}
              ${r.notes ? `<div><b>Notes</b><div>${this._escape(r.notes)}</div></div>` : ''}
            </div>`;
        })();

        this.innerHTML = `${style}
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <div style="font-weight:bold;">${this._title}</div>
            <mwc-button raised class="rc-add">Add</mwc-button>
          </div>
          <div style="display:flex;gap:10px;overflow:auto;padding:4px 0;">${tray}</div>
          ${detail}
        `;

        this.querySelector('.rc-add')?.addEventListener('click', ()=> this._openAdd());
        this.querySelectorAll('.rc-tray').forEach(tile => {
          const id = tile.getAttribute('data-id');
          tile.addEventListener('click', ()=>{ this._selected = id; this._render(); });
          tile.querySelector('.rc-edit')?.addEventListener('click', (e)=>{ e.stopPropagation(); const r=recipes.find(x=>x.id===id); if(r) this._openEdit(r); });
          tile.querySelector('.rc-del')?.addEventListener('click', (e)=>{ e.stopPropagation(); const r=recipes.find(x=>x.id===id); if(r) this._delete(r); });
        });
        return;
      }
      const filterHtml = (entryIds.length > 1 || (this._config.entry_id && !entryIds.includes(this._config.entry_id))) ? `
        <select class="rc-filter">
          <option value="all" ${this._entryFilter==='all'?'selected':''}>All sets</option>
          ${entryIds.map(id=>`<option value="${id}" ${this._entryFilter===id?'selected':''}>Set ${String(id).slice(0,6)}</option>`).join('')}
        </select>
      ` : '';

      const groupByEntry = (this._config.group_by === 'entry') || (!this._config.group_by && new Set((recipes||[]).map(r=>r._entry_id).filter(Boolean)).size > 1);

      if (!groupByEntry) {
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
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;" class="rc-tools">
          <div style="font-weight:bold;">${this._title}</div>
          <mwc-button raised class="rc-add">Add</mwc-button>
        </div>
        ${recipes.length ? `<div class="rc-grid">${grid}</div>` : `<ha-alert>Click Add to create your first recipe.</ha-alert>`}
      `;

        this.querySelector('.rc-add')?.addEventListener('click', ()=> this._openAdd());
        this.querySelectorAll('.rc-tile').forEach(tile => {
          const id = tile.getAttribute('data-id');
          tile.querySelector('.rc-open')?.addEventListener('click', (e)=>{ e.stopPropagation(); this._selected=id; this._view='detail'; this._render(); });
          tile.querySelector('.rc-edit')?.addEventListener('click', (e)=>{ e.stopPropagation(); const r=recipes.find(x=>x.id===id); if(r) this._openEdit(r); });
          tile.querySelector('.rc-del')?.addEventListener('click', (e)=>{ e.stopPropagation(); const r=recipes.find(x=>x.id===id); if(r) this._delete(r); });
        });
        return;
      }

      // Group by entry
      const groups = {};
      for (const r of recipes) {
        const id = r._entry_id || 'unknown';
        const title = r._entry_title || `Set ${String(id).slice(0,6)}`;
        if (!groups[id]) groups[id] = { title, recipes: [] };
        groups[id].recipes.push(r);
      }

      const blocks = Object.entries(groups).map(([gid, g]) => {
        const grid = g.recipes.map(r=>`
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
        return `
          <div style="display:flex;align-items:center;justify-content:space-between;margin:0 0 8px 0;" class="rc-tools">
            <div style="font-weight:bold;">${this._escape(g.title)}</div>
            <mwc-button raised class="rc-add" data-entry="${gid}">Add</mwc-button>
          </div>
          <div class="rc-grid">${grid}</div>
        `;
      }).join('');

      this.innerHTML = `${style}${blocks || `<ha-alert>Click Add to create your first recipe.</ha-alert>`}`;
      this.querySelectorAll('.rc-add').forEach(btn => btn.addEventListener('click', (e)=>{
        const id = e.currentTarget.getAttribute('data-entry');
        this._entryFilter = id || 'all';
        this._openAdd();
      }));
      this.querySelectorAll('.rc-tile').forEach(tile => {
        const id = tile.getAttribute('data-id');
        tile.querySelector('.rc-open')?.addEventListener('click', (e)=>{ e.stopPropagation(); this._selected=id; this._view='detail'; this._render(); });
        tile.querySelector('.rc-edit')?.addEventListener('click', (e)=>{ e.stopPropagation(); const all=[].concat(...Object.values(groups).map(x=>x.recipes)); const r=all.find(x=>x.id===id); if(r) this._openEdit(r); });
        tile.querySelector('.rc-del')?.addEventListener('click', (e)=>{ e.stopPropagation(); const all=[].concat(...Object.values(groups).map(x=>x.recipes)); const r=all.find(x=>x.id===id); if(r) this._delete(r); });
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
            const payload = {
              recipe_id: r.id,
              title, description, ingredients, instructions, notes
            };
            const target = (this._entryFilter && this._entryFilter!=='all') ? this._entryFilter : (this._config.entry_id || null);
            if (target) payload.config_entry_id = target;
            await this._hass.callService('recipecards', 'update_recipe', payload);
          } else {
            const payload = { title, description, ingredients, instructions, notes };
            const target = (this._entryFilter && this._entryFilter!=='all') ? this._entryFilter : (this._config.entry_id || null);
            if (target) payload.config_entry_id = target;
            await this._hass.callService('recipecards', 'add_recipe', payload);
          }
          dlg.close();
          // reload list to reflect changes
          this._load();
        } catch (e) {
          // eslint-disable-next-line no-console
          console.error('Recipe save failed', e);
        }
      });
    }

    async _delete(r){
      if (!confirm('Delete this recipe?')) return;
      try {
        const payload = { recipe_id: r.id };
        const target = (this._entryFilter && this._entryFilter!=='all') ? this._entryFilter : (this._config.entry_id || null);
        if (target) payload.config_entry_id = target;
        await this._hass.callService('recipecards', 'delete_recipe', payload);
        this._view='collection';
        this._load();
      } catch(e){
        // eslint-disable-next-line no-console
        console.error('Delete failed', e);
      }
    }
  }

  try {
    if (!customElements.get('recipecards-card')) {
      customElements.define('recipecards-card', RecipeCardsCard);
    }
    window.customCards = window.customCards || [];
    window.customCards.push({
      type: 'recipecards-card',
      name: 'RecipeCards Card',
      description: 'Browse, add, edit, and delete recipes',
    });
  } catch (error) {
    console.error('RecipeCards: Error registering custom element:', error);
  }
})();
