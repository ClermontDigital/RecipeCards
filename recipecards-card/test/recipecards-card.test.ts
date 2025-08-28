import { expect, fixture, html, oneEvent } from '@open-wc/testing';
import { RecipeCardsCard } from '../src/recipecards-card.js';

// Import test framework types
declare const describe: (name: string, fn: () => void) => void;
declare const it: (name: string, fn: () => void | Promise<void>) => void;
declare const beforeEach: (fn: () => void | Promise<void>) => void;
declare const afterEach: (fn: () => void | Promise<void>) => void;

describe('RecipeCardsCard', () => {
  let element: RecipeCardsCard;

  beforeEach(() => {
    // Mock Home Assistant global
    (window as any).hass = {
      callWS: async (params: any) => {
        if (params.type === 'recipecards/recipe_list') {
          return [
            {
              id: 'recipe1',
              title: 'Pancakes',
              description: 'Fluffy pancakes',
              ingredients: ['1 cup flour', '1 cup milk'],
              notes: 'Serve with syrup',
              instructions: ['Mix ingredients', 'Cook on griddle'],
              color: '#FFD700',
              _entry_id: 'e1'
            },
            {
              id: 'recipe2',
              title: 'Omelette',
              description: 'Classic omelette',
              ingredients: ['3 eggs', 'Cheese'],
              notes: 'Add vegetables if desired',
              instructions: ['Beat eggs', 'Cook in pan'],
              color: '#FFA500',
              _entry_id: 'e2'
            }
          ];
        }
        if (params.type === 'recipecards/recipe_get') {
          return {
            id: params.recipe_id,
            title: 'Test Recipe',
            description: 'Test description',
            ingredients: ['Test ingredient'],
            notes: 'Test notes',
            instructions: ['Test instruction'],
            color: '#FFD700'
          };
        }
        throw new Error('Unknown API call');
      },
      callService: async () => {}
    };
  });

  afterEach(() => {
    delete (window as any).hass;
  });

  it('renders with default config', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for loading to complete
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(element).to.exist;
    expect(element.shadowRoot).to.exist;
  });

  it('shows loading state initially', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    const loadingText = element.shadowRoot?.querySelector('.loading');
    expect(loadingText).to.exist;
    expect(loadingText?.textContent).to.include('Loading recipes');
  });

  it('loads and displays recipe list with tabs', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const tabs = element.shadowRoot?.querySelectorAll('.tab');
    expect(tabs).to.have.length(2);
    expect(tabs?.[0].textContent?.trim()).to.equal('Pancakes');
    expect(tabs?.[1].textContent?.trim()).to.equal('Omelette');
  });

  it('displays first recipe by default', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const title = element.shadowRoot?.querySelector('.title');
    expect(title?.textContent?.trim()).to.equal('Pancakes');
    
    const activeTab = element.shadowRoot?.querySelector('.tab.active');
    expect(activeTab?.textContent?.trim()).to.equal('Pancakes');
  });

  it('switches recipes when tab is clicked', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const secondTab = element.shadowRoot?.querySelectorAll('.tab')[1];
    secondTab?.dispatchEvent(new Event('click'));
    
    // Wait for recipe switch
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const title = element.shadowRoot?.querySelector('.title');
    expect(title?.textContent?.trim()).to.equal('Omelette');
  });

  it('flips card when flip button is clicked', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const flipButton = element.shadowRoot?.querySelector('.flip-btn');
    flipButton?.dispatchEvent(new Event('click'));
    
    const card = element.shadowRoot?.querySelector('.card');
    expect(card?.classList.contains('flipped')).to.be.true;
  });

  it('flips card when card is clicked', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const card = element.shadowRoot?.querySelector('.card');
    card?.dispatchEvent(new Event('click'));
    
    expect(card?.classList.contains('flipped')).to.be.true;
  });

  it('shows instructions on back face', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const flipButton = element.shadowRoot?.querySelector('.flip-btn');
    flipButton?.dispatchEvent(new Event('click'));
    
    const instructions = element.shadowRoot?.querySelector('.back .section-title');
    expect(instructions?.textContent?.trim()).to.equal('Instructions');
  });

  it('resets flip state when switching recipes', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Flip the card
    const flipButton = element.shadowRoot?.querySelector('.flip-btn');
    flipButton?.dispatchEvent(new Event('click'));
    
    const card = element.shadowRoot?.querySelector('.card');
    expect(card?.classList.contains('flipped')).to.be.true;
    
    // Switch recipes
    const secondTab = element.shadowRoot?.querySelectorAll('.tab')[1];
    secondTab?.dispatchEvent(new Event('click'));
    
    // Wait for recipe switch
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Card should be unflipped
    expect(card?.classList.contains('flipped')).to.be.false;
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    (window as any).hass = {
      callWS: async () => {
        throw new Error('API Error');
      }
    };
    
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for error to be handled
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const errorText = element.shadowRoot?.querySelector('.error');
    expect(errorText).to.exist;
    expect(errorText?.textContent?.trim()).to.include('Failed to load recipes');
  });

  it('shows no recipes message when list is empty', async () => {
    // Mock empty recipe list
    (window as any).hass = {
      callWS: async (params: any) => {
        if (params.type === 'recipecards/recipe_list') {
          return [];
        }
        throw new Error('Unknown API call');
      }
    };
    
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for empty list to be handled
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const noRecipesText = element.shadowRoot?.querySelector('.no-recipes');
    expect(noRecipesText).to.exist;
    expect(noRecipesText?.textContent?.trim()).to.include('No recipes found');
  });

  it('loads specific recipe when recipe_id is provided', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ 
      type: 'recipecards-card',
      recipe_id: 'specific-recipe'
    });
    
    // Wait for recipe to load
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const title = element.shadowRoot?.querySelector('.title');
    expect(title?.textContent?.trim()).to.equal('Test Recipe');
  });

  it('displays recipe ingredients correctly', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const ingredients = element.shadowRoot?.querySelectorAll('.front li');
    expect(ingredients).to.have.length(2);
    expect(ingredients?.[0].textContent?.trim()).to.equal('1 cup flour');
    expect(ingredients?.[1].textContent?.trim()).to.equal('1 cup milk');
  });

  it('displays recipe notes correctly', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const notes = element.shadowRoot?.querySelector('.notes');
    expect(notes?.textContent?.trim()).to.equal('Serve with syrup');
  });

  it('displays recipe instructions correctly', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Flip to see instructions
    const flipButton = element.shadowRoot?.querySelector('.flip-btn');
    flipButton?.dispatchEvent(new Event('click'));
    
    const instructions = element.shadowRoot?.querySelectorAll('.back li');
    expect(instructions).to.have.length(2);
    expect(instructions?.[0].textContent?.trim()).to.equal('Mix ingredients');
    expect(instructions?.[1].textContent?.trim()).to.equal('Cook on griddle');
  });

  it('has proper accessibility attributes', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    
    // Wait for recipes to load
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const flipButton = element.shadowRoot?.querySelector('.flip-btn');
    expect(flipButton?.getAttribute('title')).to.equal('Show instructions');
    
    const tabs = element.shadowRoot?.querySelectorAll('.tab');
    expect(tabs?.[0].getAttribute('title')).to.equal('Pancakes');
  });

  it('registers as custom card', () => {
    expect((window as any).customCards).to.exist;
    const cardRegistration = (window as any).customCards.find(
      (card: any) => card.type === 'recipecards-card'
    );
    expect(cardRegistration).to.exist;
    expect(cardRegistration.name).to.equal('RecipeCards Card');
  });

  it('passes config_entry_id to services when entry_id configured', async () => {
    let captured: any | undefined;
    (window as any).hass.callService = async (_d: string, _s: string, data: any) => {
      captured = data;
    };

    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card', entry_id: 'e1' });

    await new Promise((r) => setTimeout(r, 150));

    // Open add modal
    const addBtn = element.shadowRoot?.querySelector('.add-recipe-btn') as HTMLElement;
    addBtn?.click();
    await new Promise((r) => setTimeout(r, 0));

    // Fill and submit minimal form
    const form = element.shadowRoot?.querySelector('form') as HTMLFormElement;
    (form.querySelector('[name="title"]') as HTMLInputElement).value = 'New';
    (form.querySelector('[name="ingredients"]') as HTMLTextAreaElement).value = 'i1';
    (form.querySelector('[name="instructions"]') as HTMLTextAreaElement).value = 's1';
    form.dispatchEvent(new Event('submit'));
    await new Promise((r) => setTimeout(r, 0));

    expect(captured).to.exist;
    expect(captured.config_entry_id).to.equal('e1');
  });

  it('shows entry filter when multiple sets present', async () => {
    element = await fixture(html`<recipecards-card></recipecards-card>`);
    element.setConfig({ type: 'recipecards-card' });
    await new Promise((r) => setTimeout(r, 150));
    const select = element.shadowRoot?.querySelector('select');
    expect(select).to.exist;
  });
}); 
