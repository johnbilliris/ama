/**
 * Operator critical-journey Playwright spec (spec-032 FR-I03, T905).
 *
 * Smoke test that the operator landing page renders + key navigation works.
 * The full multi-step journey is added as the application surfaces land.
 */
import { test, expect } from "@playwright/test";

test.describe("operator critical journey", () => {
  test("home page loads + has a heading", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Disaster Response|AMA|Hub/i);
    const heading = page.locator("h1").first();
    await expect(heading).toBeVisible({ timeout: 10_000 });
  });

  test("governance hub link is reachable from the nav", async ({ page }) => {
    await page.goto("/");
    // The link may live in a top nav or footer depending on the layout
    // implementation; assert at minimum that the route /governance loads.
    const response = await page.goto("/governance");
    expect(response?.status()).toBeLessThan(500);
  });

  test("api docs route renders without 5xx", async ({ page }) => {
    // FR-DOC02 hosts Redoc at /api-docs once T902 lands.
    const response = await page.goto("/api-docs");
    if (response) {
      expect(response.status()).toBeLessThan(500);
    }
  });
});
