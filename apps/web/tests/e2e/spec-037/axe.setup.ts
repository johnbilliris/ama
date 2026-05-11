/**
 * T025 — axe-core scaffolding for spec-037 Playwright e2e suite.
 * Citations: NN-3, FR-021, CHK083.
 */
import AxeBuilder from '@axe-core/playwright';
import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export interface InjectAndCheckOptions {
  /** axe rule tags. Default: WCAG 2.2 AA bundle. */
  tags?: string[];
  /** Optional CSS selector to scope the check to a sub-tree. */
  include?: string;
}

/**
 * Reusable axe-core helper that injects axe into the page, runs the audit,
 * and asserts there are zero serious or critical violations.
 *
 * Used by tests under `apps/web/tests/e2e/spec-037/*.spec.ts` to gate the
 * Executive KPI page against WCAG 2.2 AA per NN-3 + FR-021.
 */
export async function injectAndCheck(page: Page, opts: InjectAndCheckOptions = {}): Promise<void> {
  const tags = opts.tags ?? ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];
  let builder = new AxeBuilder({ page }).withTags(tags);
  if (opts.include) {
    builder = builder.include(opts.include);
  }
  const results = await builder.analyze();
  const blocking = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
  expect(
    blocking,
    `axe-core found ${blocking.length} blocking violation(s):\n` +
      blocking.map((v) => `  - [${v.impact}] ${v.id}: ${v.help}`).join('\n'),
  ).toEqual([]);
}
