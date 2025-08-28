/**
 * Setups an element synchronously from the provided lit-html template and puts it in the DOM.
 *
 * @template {Element} T - Is an element or a node
 * @param {import('./renderable.js').LitHTMLRenderable} template
 * @param {import('./fixture-no-side-effect.js').FixtureOptions} [options]
 * @param {import('./scopedElementsWrapper.js').ScopedElementsTemplateGetter} [getScopedElementsTemplate]
 * @returns {T}
 */
export function litFixtureSync<T extends Element>(template: import('./renderable.js').LitHTMLRenderable, options?: import('./fixture-no-side-effect.js').FixtureOptions, getScopedElementsTemplate?: import('./scopedElementsWrapper.js').ScopedElementsTemplateGetter): T;
/**
 * Setups an element asynchronously from the provided lit-html template and puts it in the DOM.
 *
 * @template {Element} T - Is an element or a node
 * @param {import('./renderable.js').LitHTMLRenderable} template
 * @param {import('./fixture-no-side-effect.js').FixtureOptions} [options]
 * @returns {Promise<T>}
 */
export function litFixture<T extends Element>(template: import('./renderable.js').LitHTMLRenderable, options?: import('./fixture-no-side-effect.js').FixtureOptions): Promise<T>;
//# sourceMappingURL=litFixture.d.ts.map