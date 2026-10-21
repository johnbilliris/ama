/**
 * AxeBuilder helper (T043) — wraps @axe-core/playwright with WCAG 2.2 AA tags.
 */
import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";

export function buildAxe(page: Page): AxeBuilder {
  return new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]);
}
