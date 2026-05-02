/**
 * AxeBuilder helper (T043) — wraps @axe-core/playwright with WCAG 2.2 AA tags.
 */
import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";

export function buildAxe(page: Page): AxeBuilder {
  return new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    // Skip rules that are out of scope for spec 034 (e.g., third-party iframes
    // that the OPenAPI doc page imports). Keep this list short and reviewed.
    .disableRules(["region"]);
}
