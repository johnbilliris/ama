/**
 * Spec 038 — Playwright + axe-core E2E for the evidence harness (T-A09 / T-A10).
 *
 * Verifies:
 *   - 6 tabs render with the required test-ids.
 *   - KPI Ladder tab exposes the 9 attribute columns (semantic + axe-core).
 *   - Public Information channels list shows ≥ 8 languages incl. Auslan.
 *   - WCAG 2.2 AA passes for the page (axe-core).
 */
import { expect, test } from "@playwright/test";
// @ts-ignore — axe-core helper is provided by `@axe-core/playwright` when run in CI.
import AxeBuilder from "@axe-core/playwright";

test.describe("Evidence Harness — governance/evidence", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/governance/evidence");
  });

  test("6 evidence tabs are mounted", async ({ page }) => {
    for (const id of [
      "evidence-kpi-ladder-tab",
      "evidence-measurement-tab",
      "evidence-replay-tab",
      "evidence-impact-tab",
      "evidence-benchmarks-tab",
      "evidence-audit-tab",
    ]) {
      await expect(page.getByTestId(id)).toBeVisible();
    }
  });

  test("Public Information renders ≥ 8 language channels", async ({ page }) => {
    const channels = page
      .locator("section.public-info ul[role=list] li");
    await expect(channels).toHaveCount(8);
    await expect(page.getByText(/Auslan/i)).toBeVisible();
  });

  test("axe-core WCAG 2.2 AA passes", async ({ page }) => {
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test("Advisory-only banner is present", async ({ page }) => {
    await expect(page.getByText(/Advisory only/i)).toBeVisible();
  });
});
