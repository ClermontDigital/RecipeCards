export { elementUpdated } from "./src/elementUpdated.js";
/** @deprecated please do import { html } from 'lit/static-html.js'; */
declare const deprecatedHtml: (strings: TemplateStringsArray, ...values: unknown[]) => import("lit-html").TemplateResult;
/** @deprecated please do import { unsafeStatic } from 'lit/static-html.js'; */
declare const deprecatedUnsafeStatic: (value: string) => import("lit-html/static.js").StaticValue;
export { deprecatedHtml as html, deprecatedUnsafeStatic as unsafeStatic };
export { fixture, fixtureSync } from "./src/fixture-no-side-effect.js";
export { cachedWrappers, fixtureCleanup, fixtureWrapper } from "./src/fixtureWrapper.js";
export { aTimeout, defineCE, isIE, nextFrame, oneEvent, oneDefaultPreventedEvent, triggerBlurFor, triggerFocusFor, waitUntil } from "./src/helpers.js";
export { litFixture, litFixtureSync } from "./src/litFixture.js";
export { stringFixture, stringFixtureSync } from "./src/stringFixture.js";
//# sourceMappingURL=index-no-side-effects.d.ts.map