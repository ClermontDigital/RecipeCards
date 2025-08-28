import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';

interface RecipeCardsConfig {
  type: string;
  entity: string;
  title?: string;
  view?: 'collection' | 'detail';
}

interface Recipe {
  id: string;
  title: string;
  description: string;
  ingredients: string[];
  notes: string;
  instructions: string[];
  color: string;
}

declare global {
  interface Window {
    customCards: Array<any>;
    hass: any;
  }
}

@customElement('recipecards-card')
export class RecipeCardsCard extends LitElement {
  public hass!: any;
  public config?: RecipeCardsConfig;
  
  private flipped = false;
  private recipe?: Recipe;
  private recipes: Recipe[] = [];
  private loading = true;
  private error?: string;
  private currentView: 'collection' | 'detail' = 'collection';
  private showAddModal = false;
  private showEditModal = false;
  private editingRecipe?: Recipe;
  private selectedColor = '#FFD700';
  private saving = false;
  private errorMessage?: string;

  static get properties() {
    return {
      hass: { attribute: false },
      config: { attribute: false },
      flipped: { state: true },
      recipe: { state: true },
      recipes: { state: true },
      loading: { state: true },
      error: { state: true },
      currentView: { state: true },
      showAddModal: { state: true },
      showEditModal: { state: true },
      editingRecipe: { state: true },
      selectedColor: { state: true },
      saving: { state: true },
      errorMessage: { state: true }
    };
  }

  static styles = css`
    :host {
      display: block;
      font-family: 'Georgia', serif;
      background: none;
      --card-width: 350px;
      --card-height: 260px;
      --card-radius: 16px;
      --card-shadow: 0 4px 16px rgba(0,0,0,0.10);
      --card-bg: #fffbe6;
      --card-border: 2px solid #bfa14a;
    }
    .container {
      width: var(--card-width);
      margin: 2em auto;
    }
    .tab-bar {
      display: flex;
      background: #f5f0d6;
      border: 2px solid #bfa14a;
      border-bottom: none;
      border-radius: 12px 12px 0 0;
      overflow-x: auto;
      scrollbar-width: thin;
      scrollbar-color: #bfa14a #f5f0d6;
    }
    .tab-bar::-webkit-scrollbar {
      height: 6px;
    }
    .tab-bar::-webkit-scrollbar-track {
      background: #f5f0d6;
    }
    .tab-bar::-webkit-scrollbar-thumb {
      background: #bfa14a;
      border-radius: 3px;
    }
    .tab {
      padding: 0.8em 1.2em;
      background: #f5f0d6;
      border: none;
      border-right: 1px solid #bfa14a;
      color: #7c6f3a;
      font-family: inherit;
      font-size: 0.9em;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.2s;
      min-width: 80px;
      text-align: center;
    }
    .tab:last-child {
      border-right: none;
    }
    .tab:hover {
      background: #e8e0c0;
    }
    .tab.active {
      background: #fffbe6;
      color: #bfa14a;
      font-weight: bold;
    }
    .card-container {
      width: 100%;
      height: var(--card-height);
      perspective: 1200px;
    }
    .card {
      width: 100%;
      height: 100%;
      border-radius: 0 0 var(--card-radius) var(--card-radius);
      box-shadow: var(--card-shadow);
      background: var(--card-bg);
      border: var(--card-border);
      border-top: none;
      position: relative;
      transition: transform 0.7s cubic-bezier(.4,2,.6,1), box-shadow 0.2s;
      transform-style: preserve-3d;
      cursor: pointer;
      user-select: none;
      overflow: hidden;
      will-change: transform;
    }
    .card.flipped {
      transform: rotateY(180deg);
    }
    .face {
      position: absolute;
      width: 100%;
      height: 100%;
      backface-visibility: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 1.5em 1.2em 1.2em 1.2em;
    }
    .front {
      z-index: 2;
    }
    .back {
      transform: rotateY(180deg);
      background: #fffbe6;
    }
    .title {
      font-size: 1.5em;
      font-weight: bold;
      color: #bfa14a;
      margin-bottom: 0.3em;
      letter-spacing: 0.02em;
    }
    .desc {
      font-size: 1em;
      color: #7c6f3a;
      margin-bottom: 0.8em;
    }
    .section {
      margin-bottom: 0.7em;
    }
    .section-title {
      font-size: 1em;
      font-weight: bold;
      color: #a68c3a;
      margin-bottom: 0.2em;
      letter-spacing: 0.01em;
    }
    ul, ol {
      margin: 0 0 0 1.2em;
      padding: 0;
      font-size: 0.98em;
      color: #5a4d1a;
    }
    .notes {
      font-size: 0.95em;
      color: #8c7a3a;
      font-style: italic;
      margin-top: 0.5em;
    }
    .flip-btn {
      align-self: flex-end;
      background: #bfa14a;
      color: #fffbe6;
      border: none;
      border-radius: 8px;
      padding: 0.4em 1.1em;
      font-size: 1em;
      font-family: inherit;
      cursor: pointer;
      margin-top: 1em;
      transition: background 0.2s;
    }
    .flip-btn:hover {
      background: #a68c3a;
    }
    .loading, .error {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #bfa14a;
      font-size: 1.2em;
    }
    .error {
      color: #d32f2f;
      text-align: center;
      padding: 1em;
    }
    .no-recipes {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #7c6f3a;
      font-size: 1.1em;
      text-align: center;
      padding: 1em;
    }
    /* Collection View Styles */
    .collection-container {
      padding: 1em;
      background: #fffbe6;
      border: 2px solid #bfa14a;
      border-radius: var(--card-radius);
      min-height: 300px;
    }
    .collection-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1em;
      padding-bottom: 0.5em;
      border-bottom: 1px solid #bfa14a;
    }
    .collection-title {
      font-size: 1.4em;
      font-weight: bold;
      color: #bfa14a;
    }
    .add-recipe-btn {
      background: #bfa14a;
      color: #fffbe6;
      border: none;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      font-size: 1.5em;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
    }
    .add-recipe-btn:hover {
      background: #a68c3a;
    }
    .recipes-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1em;
      margin-top: 1em;
    }
    .recipe-tile {
      background: #fffbe6;
      border: 2px solid #bfa14a;
      border-radius: 12px;
      padding: 1em;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      position: relative;
      min-height: 120px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .recipe-tile:hover, .recipe-tile:focus {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0,0,0,0.15);
      outline: 2px solid #bfa14a;
      outline-offset: 2px;
    }
    .recipe-tile-header {
      padding: 0.5em;
      border-radius: 8px 8px 0 0;
      margin: -1em -1em 0.5em -1em;
      color: white;
      font-weight: bold;
      position: relative;
    }
    .recipe-tile-title {
      font-size: 1.1em;
      margin-bottom: 0.2em;
    }
    .recipe-tile-desc {
      font-size: 0.9em;
      opacity: 0.9;
    }
    .recipe-tile-info {
      color: #7c6f3a;
      font-size: 0.8em;
      margin: 0.5em 0;
      padding: 0.3em;
      background: rgba(191, 161, 74, 0.1);
      border-radius: 4px;
      text-align: center;
    }
    .recipe-tile-actions {
      display: flex;
      gap: 0.5em;
      margin-top: 0.5em;
    }
    .recipe-action-btn {
      background: none;
      border: 1px solid #bfa14a;
      color: #bfa14a;
      border-radius: 4px;
      padding: 0.3em 0.6em;
      font-size: 0.8em;
      cursor: pointer;
      transition: all 0.2s;
    }
    .recipe-action-btn:hover {
      background: #bfa14a;
      color: #fffbe6;
    }
    .recipe-action-btn.delete:hover {
      background: #d32f2f;
      border-color: #d32f2f;
    }

    /* Modal Styles */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .modal {
      background: #fffbe6;
      border: 2px solid #bfa14a;
      border-radius: var(--card-radius);
      padding: 1.5em;
      max-width: 500px;
      width: 90vw;
      max-height: 80vh;
      overflow-y: auto;
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1em;
      padding-bottom: 0.5em;
      border-bottom: 1px solid #bfa14a;
    }
    .modal-title {
      font-size: 1.3em;
      font-weight: bold;
      color: #bfa14a;
    }
    .modal-close {
      background: none;
      border: none;
      font-size: 1.5em;
      color: #bfa14a;
      cursor: pointer;
    }
    .form-group {
      margin-bottom: 1em;
    }
    .form-label {
      display: block;
      margin-bottom: 0.3em;
      font-weight: bold;
      color: #7c6f3a;
    }
    .form-input, .form-textarea {
      width: 100%;
      padding: 0.5em;
      border: 1px solid #bfa14a;
      border-radius: 4px;
      font-family: inherit;
      font-size: 1em;
      background: #fffbe6;
    }
    .form-textarea {
      min-height: 80px;
      resize: vertical;
    }
    .color-picker {
      display: flex;
      gap: 0.5em;
      flex-wrap: wrap;
      margin-top: 0.5em;
    }
    .color-option {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      border: 2px solid transparent;
      cursor: pointer;
      transition: border-color 0.2s;
    }
    .color-option.selected {
      border-color: #333;
    }
    .modal-actions {
      display: flex;
      gap: 1em;
      justify-content: flex-end;
      margin-top: 1.5em;
    }
    .btn {
      padding: 0.7em 1.5em;
      border: none;
      border-radius: 6px;
      font-family: inherit;
      font-size: 1em;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-primary {
      background: #bfa14a;
      color: #fffbe6;
    }
    .btn-primary:hover {
      background: #a68c3a;
    }
    .btn-secondary {
      background: #f5f0d6;
      color: #7c6f3a;
      border: 1px solid #bfa14a;
    }
    .btn-secondary:hover {
      background: #e8e0c0;
    }
    .btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .error-message {
      background: #fee;
      color: #c33;
      padding: 0.5em;
      border-radius: 4px;
      margin-bottom: 1em;
      border: 1px solid #fcc;
    }
    .loading-spinner {
      display: inline-block;
      width: 16px;
      height: 16px;
      border: 2px solid #bfa14a;
      border-radius: 50%;
      border-top-color: transparent;
      animation: spin 1s ease-in-out infinite;
      margin-right: 0.5em;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Back button for detail view */
    .back-btn {
      background: #f5f0d6;
      color: #7c6f3a;
      border: 1px solid #bfa14a;
      border-radius: 6px;
      padding: 0.5em 1em;
      font-family: inherit;
      cursor: pointer;
      margin-bottom: 1em;
      transition: background 0.2s;
    }
    .back-btn:hover {
      background: #e8e0c0;
    }

    @media (max-width: 400px) {
      :host {
        --card-width: 98vw;
        --card-height: 60vw;
      }
      .container {
        width: var(--card-width);
      }
      .card-container {
        width: 100%;
        height: var(--card-height);
      }
      .recipes-grid {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      }
      .modal {
        width: 95vw;
        padding: 1em;
      }
    }
  `;

  setConfig(config: RecipeCardsConfig) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this.config = config;
    this.currentView = config.view || 'collection';
  }

  private updateRecipes() {
    if (!this.config || !this.hass) {
      return;
    }

    const entityState = this.hass.states[this.config.entity];

    if (!entityState) {
      this.error = `Entity not found: ${this.config.entity}`;
      this.loading = false;
      return;
    }

    const newRecipes = entityState.attributes.recipes || [];
    
    // Only update if recipes have actually changed
    if (JSON.stringify(newRecipes) !== JSON.stringify(this.recipes)) {
      this.recipes = newRecipes;
      if (this.recipes.length > 0 && !this.recipe) {
        this.recipe = this.recipes[0];
      }
    }
    
    this.loading = false;
    this.error = undefined;
  }

  protected shouldUpdate(changedProps: Map<string | number | symbol, unknown>): boolean {
    if (changedProps.has('hass') && this.config) {
      const oldHass = changedProps.get('hass') as any;
      const newHass = this.hass;
      
      // Only update if the specific entity has changed
      if (!oldHass || 
          !oldHass.states[this.config.entity] || 
          oldHass.states[this.config.entity] !== newHass.states[this.config.entity]) {
        this.updateRecipes();
      }
    }
    return true;
  }

  private switchRecipe(recipeId: string) {
    this.flipped = false; // Reset flip state when switching recipes
    this.recipe = this.recipes.find(r => r.id === recipeId);
  }

  private flipCard(e: Event) {
    e.stopPropagation();
    this.flipped = !this.flipped;
  }

  private openAddModal() {
    this.showAddModal = true;
    this.selectedColor = '#FFD700'; // Reset color picker
  }

  private closeAddModal() {
    this.showAddModal = false;
  }

  private openEditModal(recipe: Recipe) {
    this.editingRecipe = recipe;
    this.selectedColor = recipe.color || '#FFD700';
    this.showEditModal = true;
  }

  private closeEditModal() {
    this.showEditModal = false;
    this.editingRecipe = undefined;
  }

  private async addRecipe(formData: FormData) {
    const title = formData.get('title') as string;
    const description = formData.get('description') as string;
    const ingredients = (formData.get('ingredients') as string).split('\n').filter(i => i.trim());
    const notes = formData.get('notes') as string;
    const instructions = (formData.get('instructions') as string).split('\n').filter(i => i.trim());
    const color = formData.get('color') as string || '#FFD700';

    this.saving = true;
    this.errorMessage = undefined;

    try {
      await this.hass.callService('recipecards', 'add_recipe', {
        title,
        description,
        ingredients,
        notes,
        instructions,
        color
      });
      this.closeAddModal();
    } catch (error) {
      console.error('Failed to add recipe:', error);
      this.errorMessage = 'Failed to add recipe. Please check your input and try again.';
      setTimeout(() => this.errorMessage = undefined, 5000);
    } finally {
      this.saving = false;
    }
  }

  private async updateRecipe(formData: FormData) {
    if (!this.editingRecipe) return;

    const title = formData.get('title') as string;
    const description = formData.get('description') as string;
    const ingredients = (formData.get('ingredients') as string).split('\n').filter(i => i.trim());
    const notes = formData.get('notes') as string;
    const instructions = (formData.get('instructions') as string).split('\n').filter(i => i.trim());
    const color = formData.get('color') as string || '#FFD700';

    this.saving = true;
    this.errorMessage = undefined;

    try {
      await this.hass.callService('recipecards', 'update_recipe', {
        recipe_id: this.editingRecipe.id,
        title,
        description,
        ingredients,
        notes,
        instructions,
        color
      });
      this.closeEditModal();
    } catch (error) {
      console.error('Failed to update recipe:', error);
      this.errorMessage = 'Failed to update recipe. Please check your input and try again.';
      setTimeout(() => this.errorMessage = undefined, 5000);
    } finally {
      this.saving = false;
    }
  }

  private async deleteRecipe(recipeId: string, e: Event) {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this recipe?')) return;

    try {
      await this.hass.callService('recipecards', 'delete_recipe', {
        recipe_id: recipeId
      });
    } catch (error) {
      console.error('Failed to delete recipe:', error);
      // Could add error handling UI here
    }
  }

  private viewRecipe(recipe: Recipe) {
    this.recipe = recipe;
    this.currentView = 'detail';
    this.flipped = false;
  }

  private backToCollection() {
    this.currentView = 'collection';
  }

  private sanitizeText(text: string): string {
    // Basic XSS protection - remove potentially dangerous characters
    return text.replace(/[<>]/g, '');
  }

  private renderCollectionView() {
    if (this.recipes.length === 0) {
      return html`
        <div class="collection-container">
          <div class="collection-header">
            <div class="collection-title">${this.config?.title || 'Recipe Collection'}</div>
            <button class="add-recipe-btn" @click=${this.openAddModal} title="Add Recipe">+</button>
          </div>
          <div class="no-recipes">
            🍳 Welcome to your Recipe Collection!<br />
            <br />
            Click the <strong>+</strong> button above to add your first recipe<br />
            and start building your digital cookbook.
          </div>
        </div>
      `;
    }

    return html`
      <div class="collection-container">
        <div class="collection-header">
          <div class="collection-title">${this.config?.title || 'Recipe Collection'}</div>
          <button class="add-recipe-btn" @click=${this.openAddModal} title="Add Recipe">+</button>
        </div>
        <div class="recipes-grid">
          ${this.recipes.map(recipe => html`
            <div class="recipe-tile" @click=${() => this.viewRecipe(recipe)} 
                 @keydown=${(e: KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this.viewRecipe(recipe); } }}
                 tabindex="0" role="button" aria-label="View recipe: ${recipe.title}">
              <div class="recipe-tile-header" style="background-color: ${recipe.color}">
                <div class="recipe-tile-title">${this.sanitizeText(recipe.title)}</div>
                <div class="recipe-tile-desc">${this.sanitizeText(recipe.description)}</div>
              </div>
              <div class="recipe-tile-info">
                <small>🥘 ${recipe.ingredients.length} ingredients • 📝 ${recipe.instructions.length} steps</small>
              </div>
              <div class="recipe-tile-actions">
                <button class="recipe-action-btn" @click=${(e: Event) => { e.stopPropagation(); this.openEditModal(recipe); }}>Edit</button>
                <button class="recipe-action-btn delete" @click=${(e: Event) => this.deleteRecipe(recipe.id, e)}>Delete</button>
              </div>
            </div>
          `)}
        </div>
      </div>
    `;
  }

  private renderDetailView() {
    if (!this.recipe) {
      this.currentView = 'collection';
      return html``;
    }

    return html`
      <div class="container">
        <button class="back-btn" @click=${this.backToCollection}>← Back to Collection</button>
        <div class="tab-bar">
          ${this.recipes.map(recipe => html`
            <button 
              class="tab${this.recipe?.id === recipe.id ? ' active' : ''}"
              @click=${() => this.switchRecipe(recipe.id)}
              title="${recipe.title}"
            >
              ${recipe.title}
            </button>
          `)}
        </div>
        <div class="card-container">
          <div class="card${this.flipped ? ' flipped' : ''}" @click=${this.flipCard}>
            <div class="face front">
              <div>
                <div class="title">${this.recipe?.title}</div>
                <div class="desc">${this.recipe?.description}</div>
                <div class="section">
                  <div class="section-title">Ingredients</div>
                  <ul>
                    ${this.recipe?.ingredients.map(ing => html`<li>${ing}</li>`)}
                  </ul>
                </div>
                <div class="section">
                  <div class="section-title">Notes</div>
                  <div class="notes">${this.recipe?.notes}</div>
                </div>
              </div>
              <button class="flip-btn" @click=${this.flipCard} title="Show instructions">Flip for Instructions</button>
            </div>
            <div class="face back">
              <div>
                <div class="section-title">Instructions</div>
                <ol>
                  ${this.recipe?.instructions.map(step => html`<li>${step}</li>`)}
                </ol>
              </div>
              <button class="flip-btn" @click=${this.flipCard} title="Back to recipe">Back</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  private renderRecipeModal(recipe?: Recipe) {
    const isEdit = !!recipe;
    const title = isEdit ? 'Edit Recipe' : 'Add Recipe';
    const colorOptions = ['#FFD700', '#FF6B35', '#E91E63', '#9C27B0', '#673AB7', '#3F51B5', '#2196F3', '#03A9F4', '#00BCD4', '#009688', '#4CAF50', '#8BC34A', '#CDDC39', '#FFC107', '#FF9800', '#FF5722'];

    return html`
      <div class="modal-overlay" @click=${(e: Event) => { if (e.target === e.currentTarget) { isEdit ? this.closeEditModal() : this.closeAddModal(); } }}>
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title">${title}</div>
            <button class="modal-close" @click=${isEdit ? this.closeEditModal : this.closeAddModal}>×</button>
          </div>
          <form @submit=${(e: Event) => {
            e.preventDefault();
            const formData = new FormData(e.target as HTMLFormElement);
            isEdit ? this.updateRecipe(formData) : this.addRecipe(formData);
          }}>
            <div class="form-group">
              <label class="form-label">Title *</label>
              <input class="form-input" name="title" type="text" required value="${recipe?.title || ''}" />
            </div>
            <div class="form-group">
              <label class="form-label">Description</label>
              <input class="form-input" name="description" type="text" value="${recipe?.description || ''}" />
            </div>
            <div class="form-group">
              <label class="form-label">Ingredients * (one per line)</label>
              <textarea class="form-textarea" name="ingredients" required>${recipe?.ingredients.join('\n') || ''}</textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Instructions * (one per line)</label>
              <textarea class="form-textarea" name="instructions" required>${recipe?.instructions.join('\n') || ''}</textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Notes</label>
              <textarea class="form-textarea" name="notes">${recipe?.notes || ''}</textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Color</label>
              <input type="hidden" name="color" value="${this.selectedColor}" />
              <div class="color-picker">
                ${colorOptions.map(color => html`
                  <div 
                    class="color-option${this.selectedColor === color ? ' selected' : ''}" 
                    style="background-color: ${color}"
                    @click=${() => { this.selectedColor = color; }}
                  ></div>
                `)}
              </div>
            </div>
            ${this.errorMessage ? html`
              <div class="error-message">${this.errorMessage}</div>
            ` : ''}
            <div class="modal-actions">
              <button type="button" class="btn btn-secondary" @click=${isEdit ? this.closeEditModal : this.closeAddModal} ?disabled=${this.saving}>Cancel</button>
              <button type="submit" class="btn btn-primary" ?disabled=${this.saving}>
                ${this.saving ? html`<span class="loading-spinner"></span>` : ''}
                ${isEdit ? 'Update' : 'Add'} Recipe
              </button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  render() {
    if (this.loading) {
      return html`
        <div class="collection-container">
          <div class="collection-header">
            <div class="collection-title">Loading...</div>
          </div>
          <div class="loading">Loading recipes...</div>
        </div>
      `;
    }

    if (this.error) {
      return html`
        <div class="collection-container">
          <div class="collection-header">
            <div class="collection-title">Error</div>
          </div>
          <div class="error">${this.error}</div>
        </div>
      `;
    }

    return html`
      ${this.currentView === 'collection' ? this.renderCollectionView() : this.renderDetailView()}
      ${this.showAddModal ? this.renderRecipeModal() : ''}
      ${this.showEditModal ? this.renderRecipeModal(this.editingRecipe) : ''}
    `;
  }
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'recipecards-card',
  name: 'RecipeCards Card',
  description: 'A retro recipe card for Home Assistant',
});
