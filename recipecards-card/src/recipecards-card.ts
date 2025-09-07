import { LitElement, html, css, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { HomeAssistant, fireEvent } from 'home-assistant-js-websocket';
import { haStyle } from '@material/ha-styles/base';
import { haCardStyle } from '@material/ha-styles/card';
import { haDialogStyle } from '@material/ha-styles/dialog';
import { haTabsStyle } from '@material/ha-styles/tabs';
import { HaButtonMenu, HaIconButton, HaTabs, HaCircularProgress, HaAlert, HaSelect, HaChip, HaTextfield, HaTextarea, HaButton, HaIconButtonRow } from '@material/mwc-components';
import { isComponentLoaded } from '@material/mwc-ripple';

interface Recipe {
  id: string;
  title: string;
  description: string;
  ingredients: string[];
  notes: string;
  instructions: string[];
  color: string;
  image?: string;
  prep_time?: number;
  cook_time?: number;
  total_time?: number;
  _entry_id?: string;
  _entry_title?: string;
}

interface RecipeCardsConfig {
  type: string;
  entity?: string;
  entry_id?: string;
  recipe_id?: string;
  group_by?: 'entry' | 'none';
  title?: string;
  view?: 'collection' | 'detail' | 'tray';
}

@customElement('recipecards-card')
export class RecipeCardsCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) public config?: RecipeCardsConfig;

  @state() private recipes: Recipe[] = [];
  @state() private currentView: 'collection' | 'detail' | 'tray' = 'collection';
  @state() private selectedRecipe?: Recipe;
  @state() private loading = true;
  @state() private error?: string;
  @state() private searchQuery = '';
  @state() private selectedEntry = 'all';
  @state() private showAddDialog = false;
  @state() private showEditDialog = false;
  @state() private editingRecipe?: Recipe;
  @state() private saving = false;
  @state() private saveError?: string;
  @state() private trayIndex = 0;

  static styles = css`
    ${haStyle}
    ${haCardStyle}
    ${haDialogStyle}
    ${haTabsStyle}
    :host {
      --ha-card-border-radius: var(--ha-card-border-radius, 8px);
      --primary-color: var(--mdc-theme-primary, #03a9f4);
      --card-background-color: var(--mdc-theme-surface, #fff);
      --divider-color: var(--mdc-theme-divider-color, rgba(0,0,0,0.12));
      --primary-text-color: var(--mdc-theme-on-surface, #000);
    }
    .card-container {
      display: block;
      padding: 16px;
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }
    .search-field {
      flex: 1;
      max-width: 300px;
    }
    .recipes-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 16px;
    }
    .recipe-tile {
      cursor: pointer;
      transition: transform 0.2s;
    }
    .recipe-tile:hover {
      transform: translateY(-2px);
    }
    .recipe-header {
      background-color: var(--primary-color);
      color: white;
      padding: 12px;
      border-radius: var(--ha-card-border-radius) var(--ha-card-border-radius) 0 0;
    }
    .recipe-info {
      display: flex;
      gap: 8px;
      margin: 8px 0;
      flex-wrap: wrap;
    }
    .detail-tabs {
      margin-bottom: 16px;
    }
    .tab-content {
      padding: 16px;
    }
    .image {
      max-width: 100%;
      height: auto;
      border-radius: 4px;
    }
    .tray-container {
      display: flex;
      overflow-x: auto;
      gap: 8px;
      padding: 8px 0;
      scrollbar-width: thin;
    }
    .tray-item {
      min-width: 120px;
      cursor: pointer;
    }
    .modal-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .color-picker {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .color-swatch {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      cursor: pointer;
      border: 2px solid transparent;
    }
    .color-swatch.selected {
      border-color: var(--primary-color);
    }
    .time-chips {
      display: flex;
      gap: 8px;
      margin: 8px 0;
    }
    @media (max-width: 600px) {
      .recipes-grid {
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      }
    }
  `;

  connectedCallback() {
    super.connectedCallback();
    this.loadRecipes();
  }

  shouldUpdate(changedProps: Map<string, unknown>) {
    if (changedProps.has('hass') && this.config) {
      this.loadRecipes();
    }
    return true;
  }

  private async loadRecipes() {
    if (!this.hass || !this.config) return;
    this.loading = true;
    try {
      let recipes: Recipe[] = [];
      if (this.config.recipe_id) {
        const r = await this.hass.callWS<Recipe>({
          type: 'recipecards/recipe_get',
          recipe_id: this.config.recipe_id,
        });
        recipes = r ? [r] : [];
      } else {
        const list = await this.hass.callWS<Recipe[]>({ type: 'recipecards/recipe_list' });
        recipes = list || [];
        if (this.config.entry_id) {
          recipes = recipes.filter(r => r._entry_id === this.config.entry_id);
        }
      }
      this.recipes = recipes;
      this.loading = false;
    } catch (err) {
      this.error = 'Failed to load recipes';
      this.loading = false;
      console.error(err);
    }
  }

  private async searchRecipes(query: string, maxTime?: number) {
    try {
      const results = await this.hass.callWS<Recipe[]>({
        type: 'recipecards/recipe_search',
        query,
        max_time: maxTime,
      });
      this.recipes = results;
    } catch (err) {
      console.error('Search failed', err);
    }
  }

  private handleSearch(e: Event) {
    const target = e.target as HTMLInputElement;
    this.searchQuery = target.value;
    this.searchRecipes(this.searchQuery);
  }

  private viewRecipe(recipe: Recipe) {
    this.selectedRecipe = recipe;
    this.currentView = 'detail';
  }

  private backToCollection() {
    this.currentView = 'collection';
    this.selectedRecipe = undefined;
  }

  private openAdd() {
    this.editingRecipe = undefined;
    this.showAddDialog = true;
  }

  private openEdit(recipe: Recipe) {
    this.editingRecipe = { ...recipe };
    this.showEditDialog = true;
  }

  private closeDialog() {
    this.showAddDialog = false;
    this.showEditDialog = false;
    this.editingRecipe = undefined;
    this.saveError = undefined;
  }

  private async saveRecipe() {
    if (!this.hass || !this.editingRecipe && !this.showAddDialog) return;
    this.saving = true;
    this.saveError = undefined;
    try {
      const data = {
        title: this.editingRecipe?.title || '',
        description: this.editingRecipe?.description || '',
        ingredients: this.editingRecipe?.ingredients || [],
        notes: this.editingRecipe?.notes || '',
        instructions: this.editingRecipe?.instructions || [],
        color: this.editingRecipe?.color || '#FFD700',
        image: this.editingRecipe?.image || '',
        prep_time: this.editingRecipe?.prep_time,
        cook_time: this.editingRecipe?.cook_time,
        total_time: this.editingRecipe?.total_time,
      };
      if (this.editingRecipe) {
        data['recipe_id'] = this.editingRecipe.id;
        await this.hass.callService('recipecards', 'update_recipe', data);
      } else {
        await this.hass.callService('recipecards', 'add_recipe', data);
      }
      this.closeDialog();
      this.loadRecipes();
    } catch (err) {
      this.saveError = 'Failed to save recipe';
      console.error(err);
    } finally {
      this.saving = false;
    }
  }

  private deleteRecipe(recipe: Recipe) {
    if (confirm('Delete this recipe?')) {
      this.hass.callService('recipecards', 'delete_recipe', { recipe_id: recipe.id });
      this.loadRecipes();
    }
  }

  private formatTime(minutes?: number) {
    if (!minutes) return 'Unknown';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h ? `${h}h ${m}m` : `${m} min`;
  }

  private renderCollection() {
    const filtered = this.recipes.filter(r => 
      r.title.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
      r.description.toLowerCase().includes(this.searchQuery.toLowerCase())
    );
    const entryIds = [...new Set(this.recipes.map(r => r._entry_id))];
    return html`
      <ha-card>
        <div class="header">
          <h2>${this.config?.title || 'Recipe Collection'}</h2>
          <ha-icon-button .label="Add Recipe" @click=${this.openAdd} icon="mdi:plus"></ha-icon-button>
        </div>
        <ha-textfield class="search-field" label="Search recipes" .value=${this.searchQuery} @input=${this.handleSearch} iconTrailing="mdi:magnify"></ha-textfield>
        ${filtered.length ? html`
          <div class="recipes-grid">
            ${filtered.map(recipe => html`
              <ha-card class="recipe-tile" @click=${() => this.viewRecipe(recipe)}>
                ${recipe.image ? html`<img class="image" src=${recipe.image} alt="Recipe image">` : ''}
                <div class="recipe-header" style="background-color: ${recipe.color}">
                  <h3>${recipe.title}</h3>
                  <p>${recipe.description}</p>
                </div>
                <div class="time-chips">
                  <ha-chip label="Prep: ${this.formatTime(recipe.prep_time)}"></ha-chip>
                  <ha-chip label="Cook: ${this.formatTime(recipe.cook_time)}"></ha-chip>
                  <ha-chip label="Total: ${this.formatTime(recipe.total_time)}"></ha-chip>
                </div>
                <ha-icon-button-row slot="trailing" .label="Actions">
                  <ha-icon-button @click=${(e: Event) => { e.stopPropagation(); this.openEdit(recipe); }} icon="mdi:pencil"></ha-icon-button>
                  <ha-icon-button @click=${(e: Event) => { e.stopPropagation(); this.deleteRecipe(recipe); }} icon="mdi:delete"></ha-icon-button>
                </ha-icon-button-row>
              </ha-card>
            `)}
          </div>
        ` : html`<ha-alert alert-type="info">No recipes found. Add one to start!</ha-alert>`}
      </ha-card>
    `;
  }

  private renderDetail() {
    if (!this.selectedRecipe) return html``;
    return html`
      <ha-card>
        <div class="header">
          <ha-icon-button .label="Back" @click=${this.backToCollection} icon="mdi:arrow-left"></ha-icon-button>
          <h2>${this.selectedRecipe.title}</h2>
        </div>
        ${this.selectedRecipe.image ? html`<img class="image" src=${this.selectedRecipe.image} alt="Recipe image">` : ''}
        <ha-tabs slot="primary" .activeTabIndex=${0}>
          <ha-tab label="Ingredients"></ha-tab>
          <ha-tab label="Instructions"></ha-tab>
          <ha-tab label="Notes"></ha-tab>
        </ha-tabs>
        <div class="tab-content">
          <ul>
            ${this.selectedRecipe.ingredients.map(ing => html`<li>${ing}</li>`)}
          </ul>
        </div>
        <div class="tab-content">
          <ol>
            ${this.selectedRecipe.instructions.map(step => html`<li>${step}</li>`)}
          </ol>
        </div>
        <div class="tab-content">
          <p>${this.selectedRecipe.notes}</p>
        </div>
        <ha-icon-button-row slot="trailing" .label="Actions">
          <ha-icon-button @click=${() => this.openEdit(this.selectedRecipe!)} icon="mdi:pencil"></ha-icon-button>
          <ha-icon-button @click=${() => this.deleteRecipe(this.selectedRecipe!)} icon="mdi:delete"></ha-icon-button>
        </ha-icon-button-row>
      </ha-card>
    `;
  }

  private renderTray() {
    return html`
      <ha-card>
        <div class="header">
          <h2>${this.config?.title || 'Recipe Tray'}</h2>
          <ha-icon-button .label="Add" @click=${this.openAdd} icon="mdi:plus"></ha-icon-button>
        </div>
        <div class="tray-container">
          ${this.recipes.map((recipe, index) => html`
            <ha-card class="tray-item" @click=${() => { this.trayIndex = index; this.selectedRecipe = recipe; }}>
              ${recipe.image ? html`<img class="image" src=${recipe.image} alt="Recipe image">` : ''}
              <div class="recipe-header" style="background-color: ${recipe.color}">
                <h3>${recipe.title}</h3>
              </div>
              <ha-icon-button-row>
                <ha-icon-button @click=${(e: Event) => { e.stopPropagation(); this.openEdit(recipe); }} icon="mdi:pencil"></ha-icon-button>
                <ha-icon-button @click=${(e: Event) => { e.stopPropagation(); this.deleteRecipe(recipe); }} icon="mdi:delete"></ha-icon-button>
              </ha-icon-button-row>
            </ha-card>
          `)}
        </div>
        ${this.renderDetail()}
      </ha-card>
    `;
  }

  private renderDialog() {
    const recipe = this.editingRecipe || { title: '', description: '', ingredients: [], notes: '', instructions: [], color: '#FFD700', prep_time: undefined, cook_time: undefined, total_time: undefined };
    const isEdit = !!this.editingRecipe;
    return html`
      <ha-dialog open ?hideActions=${this.saving} @closed=${this.closeDialog}>
        <ha-header>
          <ha-icon-button slot="navigationIcon" @click=${this.closeDialog} icon="mdi:close"></ha-icon-button>
          <h2 slot="title">${isEdit ? 'Edit' : 'Add'} Recipe</h2>
        </ha-header>
        <div class="modal-form">
          <ha-textfield label="Title" .value=${recipe.title} @input=${(e: Event) => recipe.title = (e.target as HTMLInputElement).value}></ha-textfield>
          <ha-textfield label="Description" .value=${recipe.description} @input=${(e: Event) => recipe.description = (e.target as HTMLInputElement).value}></ha-textfield>
          <ha-textarea label="Ingredients (one per line)" .value=${recipe.ingredients.join('\n')} @input=${(e: Event) => recipe.ingredients = (e.target as HTMLInputElement).value.split('\n').map(s => s.trim()).filter(Boolean)}></ha-textarea>
          <ha-textarea label="Instructions (one per line)" .value=${recipe.instructions.join('\n')} @input=${(e: Event) => recipe.instructions = (e.target as HTMLInputElement).value.split('\n').map(s => s.trim()).filter(Boolean)}></ha-textarea>
          <ha-textarea label="Notes" .value=${recipe.notes} @input=${(e: Event) => recipe.notes = (e.target as HTMLInputElement).value}></ha-textarea>
          <ha-textfield label="Image (base64 or URL)" .value=${recipe.image || ''} @input=${(e: Event) => recipe.image = (e.target as HTMLInputElement).value}></ha-textfield>
          <ha-textfield label="Prep Time (minutes)" type="number" .value=${recipe.prep_time || ''} @input=${(e: Event) => recipe.prep_time = parseInt((e.target as HTMLInputElement).value) || undefined}></ha-textfield>
          <ha-textfield label="Cook Time (minutes)" type="number" .value=${recipe.cook_time || ''} @input=${(e: Event) => recipe.cook_time = parseInt((e.target as HTMLInputElement).value) || undefined}></ha-textfield>
          <ha-textfield label="Total Time (minutes)" type="number" .value=${recipe.total_time || ''} @input=${(e: Event) => recipe.total_time = parseInt((e.target as HTMLInputElement).value) || undefined}></ha-textfield>
          <div class="color-picker">
            <label>Color:</label>
            ${['#FFD700', '#FF6B35', '#E91E63', '#9C27B0'].map(color => html`
              <div class="color-swatch ${recipe.color === color ? 'selected' : ''}" style="background-color: ${color}" @click=${() => recipe.color = color}></div>
            `)}
          </div>
          ${this.saveError ? html`<ha-alert alert-type="error">${this.saveError}</ha-alert>` : ''}
        </div>
        <div slot="primaryAction">
          <ha-button @click=${this.saveRecipe} ?disabled=${this.saving}>
            ${this.saving ? html`<ha-circular-progress active size="small" slot="prefix"></ha-circular-progress>` : ''}
            ${isEdit ? 'Update' : 'Add'}
          </ha-button>
        </div>
      </ha-dialog>
    `;
  }

  render() {
    if (this.loading) {
      return html`<ha-circular-progress active></ha-circular-progress>`;
    }
    if (this.error) {
      return html`<ha-alert alert-type="error">${this.error}</ha-alert>`;
    }
    const content = this.currentView === 'detail' ? this.renderDetail() : this.currentView === 'tray' ? this.renderTray() : this.renderCollection();
    return html`
      ${content}
      ${this.showAddDialog || this.showEditDialog ? this.renderDialog() : ''}
    `;
  }

  static getStubConfig(): TemplateResult {
    return html``;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'recipecards-card': RecipeCardsCard;
  }
}

if (customElements.get('recipecards-card') == null) {
  customElements.define('recipecards-card', RecipeCardsCard);
}
