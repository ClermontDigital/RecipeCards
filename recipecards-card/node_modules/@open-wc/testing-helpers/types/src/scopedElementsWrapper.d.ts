/**
 * Wraps the template inside a scopedElements component
 *
 * @param {import('./renderable.js').LitHTMLRenderable} template
 * @param {ScopedElementsMap} scopedElements
 * @return {HTMLElement}
 */
export function getScopedElementsTemplate(template: import('./renderable.js').LitHTMLRenderable, scopedElements: ScopedElementsMap): HTMLElement;
export type ScopedElementsMap = import('@open-wc/scoped-elements/html-element.js').ScopedElementsMap;
export type TemplateResult = import('lit/html.js').TemplateResult;
export type ScopedElementsTemplateGetter = typeof getScopedElementsTemplate;
//# sourceMappingURL=scopedElementsWrapper.d.ts.map