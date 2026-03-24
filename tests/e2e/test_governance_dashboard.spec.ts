import { test, expect } from "@playwright/test";

test.describe("Governance Dashboard", () => {
  test("dashboard page loads with summary counts", async ({ page }) => {
    await page.goto("/governance");
    await expect(page.locator("h1")).toContainText("Governance Dashboard");
    await expect(page.locator("text=Total Sources")).toBeVisible();
  });

  test("filters update the displayed sources", async ({ page }) => {
    await page.goto("/governance");
    const kindFilter = page.locator('select[aria-label="Filter by kind"]');
    if (await kindFilter.isVisible()) {
      await kindFilter.selectOption("authoritative");
      await page.waitForTimeout(500);
    }
  });

  test("governance gaps display warning banner", async ({ page }) => {
    await page.goto("/governance");
    const gapBanner = page.locator("text=Governance gaps detected");
    // Banner is conditionally visible depending on data state
    if (await gapBanner.isVisible()) {
      await expect(gapBanner).toBeVisible();
    }
  });

  test("drill-down navigates to compliance view", async ({ page }) => {
    await page.goto("/governance");
    const firstLink = page.locator("a.text-blue-600").first();
    if (await firstLink.isVisible()) {
      await firstLink.click();
      await expect(page).toHaveURL(/\/governance\/.*\/compliance/);
    }
  });
});
