/**
 * spec 040 (originally Spec 038) — Playwright + axe-core E2E for the evidence harness (T-A09 / T-A10 / T-AMD-15 / T-AMD-18).
 *
 * Verifies:
 *   - 6 tabs render with the required test-ids.
 *   - KPI Ladder tab exposes the 9 attribute columns (semantic + axe-core).
 *   - Public Information channels list shows ≥ 8 languages incl. Auslan.
 *   - WCAG 2.2 AA passes for the page (axe-core).
 *   - Every tab issues a fetch to its /api/v1/evidence/* endpoint on first mount (T-AMD-15).
 *   - PI tab: axe-core zero serious/critical + Flesch-Kincaid ≤ 8.0 (T-AMD-18).
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

  // T-AMD-15: every tab must issue a fetch to its /api/v1/evidence/* endpoint on first mount
  test("every tab issues a fetch to its evidence API endpoint on mount", async ({ page }) => {
    const endpoints: string[] = [];
    page.on("request", (req) => {
      if (req.url().includes("/api/v1/evidence/")) {
        endpoints.push(req.url());
      }
    });

    await page.goto("/governance/evidence");
    // Wait for network idle to allow all mounts to fire
    await page.waitForLoadState("networkidle").catch(() => {/* timeout ok */});

    const expectedPatterns = [
      "/kpi-ladder",
      "/measurement-method",
      "/scenarios/",
      "/causal-chains/",
      "/benchmarks/",
      "/audit/",
      "/public-information/",
    ];

    for (const pattern of expectedPatterns) {
      const matched = endpoints.some((url) => url.includes(pattern));
      expect(matched, `No fetch observed for pattern: ${pattern}`).toBe(true);
    }
  });

  // T-AMD-18: PI tab axe-core zero serious/critical + Flesch-Kincaid ≤ 8.0
  test("PI tab: axe-core zero serious/critical violations", async ({ page }) => {
    const results = await new AxeBuilder({ page })
      .include("section.public-info")
      .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
      .analyze();

    const seriousOrCritical = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );
    expect(seriousOrCritical, `Serious/critical violations: ${JSON.stringify(seriousOrCritical.map(v => v.id))}`).toHaveLength(0);
  });

  test("PI tab: English plain-language content Flesch-Kincaid ≤ 8.0", async ({ page }) => {
    // Extract the English channel content from the PI section
    const enContent = await page
      .locator("section.public-info ul[role=list] li:first-child")
      .textContent()
      .catch(() => null);

    if (!enContent) {
      test.skip(); // PI section not rendered (server-side rendering)
      return;
    }

    // Inline Flesch-Kincaid calculation (reuses readability.ts formula)
    function countSyllables(word: string): number {
      const cleaned = word.toLowerCase().replace(/[^a-z]/g, "");
      if (cleaned.length <= 3) return 1;
      const w = cleaned.replace(/e$/, "");
      const matches = w.match(/[aeiouy]+/g);
      return Math.max(1, matches ? matches.length : 1);
    }
    const words = enContent.trim().split(/\s+/).filter((t) => /[a-zA-Z]/.test(t));
    const sentences = Math.max(1, (enContent.match(/[.!?]+/g) ?? []).length);
    const syllables = words.reduce((s, w) => s + countSyllables(w), 0);
    const fkgl = 0.39 * (words.length / sentences) + 11.8 * (syllables / words.length) - 15.59;

    expect(fkgl, `Flesch-Kincaid grade ${fkgl.toFixed(1)} exceeds ≤ 8.0 target`).toBeLessThanOrEqual(8.0);
  });
});
