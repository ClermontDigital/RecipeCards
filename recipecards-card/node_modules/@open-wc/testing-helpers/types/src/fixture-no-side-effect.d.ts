/**
 * @typedef {object} FixtureOptions
 * @property {*} [render] optional render function to use
 * @property {Element} [parentNode] optional parent node to render the fixture's template to
 * @property {import('@open-wc/scoped-elements/html-element.js').ScopedElementsMap} [scopedElements] optional scoped-elements
 * definition map
 */
/**
 * Renders a string/TemplateResult and puts it in the DOM via a fixtureWrapper.
 *
 * @example
 * const el = fixtureSync('<my-el><span></span></my-el>');
 *
 * @template {Element} T
 * @param {import('./renderable.js').LitHTMLRenderable} template Either a string or lit-html TemplateResult
 * @param {FixtureOptions} [options]
 * @returns {T} First child of the rendered DOM
 */
export function fixtureSync<T extends Element>(template: import('./renderable.js').LitHTMLRenderable, options?: FixtureOptions): T;
/**
 * Renders a string/TemplateResult and puts it in the DOM via a fixtureWrapper.
 * By default fixture awaits the elements "update complete" Promise.
 * - for [lit-element](https://github.com/polymer/lit-element) that is `el.updateComplete`;
 * - for [stencil](https://github.com/ionic-team/stencil/) that is `el.componentOnReady()`;
 *
 * If none of those specfic Promise hooks are found, it will wait for one frame via
 * `await nextFrame()`.
 *
 * **Note**: this does not guarantee that the element is done rendering -
 * it just waits for the next JavaScript tick.
 *
 * @example
 * const el = await fixture('<my-el><span></span></my-el>');
 * expect(el.fullyRendered).to.be.true;
 *
 * @template {Element} T
 * @param {import('./renderable.js').LitHTMLRenderable} template Either a string or lit-html TemplateResult
 * @param {FixtureOptions} [options]
 * @returns {Promise<T>} A Promise that will resolve to the first child of the rendered DOM
 */
export function fixture<T extends Element>(template: import('./renderable.js').LitHTMLRenderable, options?: FixtureOptions): Promise<T>;
export type FixtureOptions = {
    /**
     * optional render function to use
     */
    render?: any;
    /**
     * optional parent node to render the fixture's template to
     */
    parentNode?: Element;
    /**
     * optional scoped-elements
     * definition map
     */
    scopedElements?: import('@open-wc/scoped-elements/html-element.js').ScopedElementsMap;
};
//# sourceMappingURL=fixture-no-side-effect.d.ts.map