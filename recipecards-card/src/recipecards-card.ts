import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';

interface RecipeCardsConfig {
  type: string;
  recipe_id?: string;
  title?: string;
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
  config?: RecipeCardsConfig;
  private flipped = false;
  private recipe?: Recipe;
  private recipes: Recipe[] = [];
  private loading = true;
  private error?: string;

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
    }
  `;

  setConfig(config: RecipeCardsConfig) {
    if (!config.type) {
      throw new Error('Card config requires type');
    }
    this.config = config;
    this.loadRecipes();
  }

  private async loadRecipes() {
    try {
      this.loading = true;
      this.error = undefined;
      this.requestUpdate();

      const hass = window.hass;
      if (!hass) {
        throw new Error('Home Assistant not available');
      }

      const recipes = await hass.callWS({
        type: 'recipecards/recipe_list',
      });

      this.recipes = recipes;
      
      // Load the first recipe or the specified recipe
      if (this.recipes.length > 0) {
        const targetRecipeId = this.config?.recipe_id || this.recipes[0].id;
        await this.loadRecipe(targetRecipeId);
      } else {
        this.loading = false;
        this.requestUpdate();
      }
    } catch (err) {
      this.error = err instanceof Error ? err.message : 'Failed to load recipes';
      this.loading = false;
      this.requestUpdate();
    }
  }

  private async loadRecipe(recipeId: string) {
    try {
      const hass = window.hass;
      if (!hass) {
        throw new Error('Home Assistant not available');
      }

      const result = await hass.callWS({
        type: 'recipecards/recipe_get',
        recipe_id: recipeId,
      });

      this.recipe = result;
      this.loading = false;
      this.requestUpdate();
    } catch (err) {
      this.error = err instanceof Error ? err.message : 'Failed to load recipe';
      this.loading = false;
      this.requestUpdate();
    }
  }

  private async switchRecipe(recipeId: string) {
    this.flipped = false; // Reset flip state when switching recipes
    await this.loadRecipe(recipeId);
  }

  private flipCard(e: Event) {
    e.stopPropagation();
    this.flipped = !this.flipped;
    this.requestUpdate();
  }

  render() {
    if (this.loading) {
      return html`
        <div class="container">
          <div class="tab-bar">
            <div class="tab active">Loading...</div>
          </div>
          <div class="card-container">
            <div class="card">
              <div class="face front">
                <div class="loading">Loading recipes...</div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    if (this.error) {
      return html`
        <div class="container">
          <div class="tab-bar">
            <div class="tab active">Error</div>
          </div>
          <div class="card-container">
            <div class="card">
              <div class="face front">
                <div class="error">${this.error}</div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    if (this.recipes.length === 0) {
      return html`
        <div class="container">
          <div class="tab-bar">
            <div class="tab active">No Recipes</div>
          </div>
          <div class="card-container">
            <div class="card">
              <div class="face front">
                <div class="no-recipes">
                  No recipes found.<br />
                  Add some recipes to get started!
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    return html`
      <div class="container">
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
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'recipecards-card',
  name: 'RecipeCards Card',
  description: 'A retro recipe card for Home Assistant',
});
