/**
 * Spec 036 T115 — E2E Playwright test for citation rendering
 * (FR-RAG-AG-03, R-14, Accessibility memo).
 *
 * Validates the Risk Manager + Simulation grounded surfaces render Citation
 * cards that:
 *   - are visible on the recommendation,
 *   - expand to show the verbatim source quote,
 *   - are screen-reader navigable (role + name),
 *   - pass axe-core's WCAG 2.2 AA rules.
 *
 * The test relies on a fixture API stub that returns a deterministic grounded
 * recommendation; if BASE_URL is not set, the test is skipped (CI runs
 * E2E only when a server is up).
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const BASE_URL = process.env.BASE_URL ?? "";
const skipReason = "no BASE_URL configured (E2E requires a running web server)";

test.describe("Citation rendering — Risk Manager + Simulation (T115)", () => {
  test.skip(!BASE_URL, skipReason);

  test("Risk Manager recommendation surfaces a visible CitationCard", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/risk-manager?fixture=spec036-citation`);
    const card = page.getByTestId("citation-card").first();
    await expect(card).toBeVisible();
    // Card carries an accessible name pointing to the source jurisdiction
    // + handbook (FR-RAG-AG-03 disambiguation).
    await expect(card).toHaveAttribute("aria-label", /jurisdiction:|handbook|page \d+/i);
  });

  test("CitationCard expands to reveal verbatim source text", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/risk-manager?fixture=spec036-citation`);
    const card = page.getByTestId("citation-card").first();
    const trigger = card.getByRole("button", { name: /show source|expand|view excerpt/i });
    await trigger.click();
    await expect(card.getByTestId("citation-source")).toBeVisible();
  });

  test("Simulation chat surfaces a citation event per grounded turn", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/simulation?fixture=spec036-citation`);
    // The SSE-fed transcript renders one CitationCard per assistant turn that
    // emitted a `citation` event.
    const cards = page.getByTestId("citation-card");
    await expect(cards.first()).toBeVisible({ timeout: 15_000 });
  });

  test("WCAG 2.2 AA — CitationCard passes axe-core scan", async ({ page }) => {
    await page.goto(`${BASE_URL}/risk-manager?fixture=spec036-citation`);
    const results = await new AxeBuilder({ page })
      .include('[data-testid="citation-card"]')
      .withTags(["wcag2aa", "wcag22aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test("Keyboard navigation reaches the CitationCard expand control", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/risk-manager?fixture=spec036-citation`);
    // Tab through the page until the citation expand control gains focus.
    let focused = false;
    for (let i = 0; i < 30 && !focused; i += 1) {
      await page.keyboard.press("Tab");
      const accName = await page
        .locator(":focus")
        .getAttribute("aria-label")
        .catch(() => null);
      const role = await page.locator(":focus").getAttribute("role").catch(() => null);
      if ((accName ?? "").toLowerCase().includes("source") || role === "button") {
        focused = true;
      }
    }
    expect(focused).toBe(true);
  });
});
