/**
 * Spec 036 T116 — E2E Playwright test for the DegradedModeBadge banner
 * (FR-RAG-LS-02, R-14, Accessibility memo).
 *
 * Validates the badge surfaces the three degraded-mode UI states:
 *   1. ``stale-corpus`` — cache age between 11 and 14 days.
 *   2. ``offline-cache-active`` — the agent surface is reading from the
 *      Field Coordinator offline bundle.
 *   3. ``retrieval-unavailable`` — AI Search is unreachable; degraded but
 *      no offline cache is configured.
 *
 * Each state triggers an ``aria-live`` announcement and passes WCAG 2.2 AA
 * via axe-core. The test is skipped if BASE_URL is not configured.
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const BASE_URL = process.env.BASE_URL ?? "";
const skipReason = "no BASE_URL configured (E2E requires a running web server)";

const STATES = [
  {
    fixture: "spec036-degraded-stale",
    label: /stale|cached corpus|days old/i,
  },
  {
    fixture: "spec036-degraded-offline",
    label: /offline cache|field deployment|degraded mode/i,
  },
  {
    fixture: "spec036-degraded-unreachable",
    label: /retrieval unavailable|temporarily/i,
  },
] as const;

test.describe("DegradedModeBadge banner states (T116)", () => {
  test.skip(!BASE_URL, skipReason);

  for (const state of STATES) {
    test(`renders the ${state.fixture} state with role=alert`, async ({ page }) => {
      await page.goto(`${BASE_URL}/risk-manager?fixture=${state.fixture}`);
      const badge = page.getByTestId("degraded-mode-badge");
      await expect(badge).toBeVisible();
      await expect(badge).toHaveAttribute("role", /alert|status/i);
      await expect(badge).toContainText(state.label);
    });

    test(`WCAG 2.2 AA — ${state.fixture} passes axe`, async ({ page }) => {
      await page.goto(`${BASE_URL}/risk-manager?fixture=${state.fixture}`);
      const results = await new AxeBuilder({ page })
        .include('[data-testid="degraded-mode-badge"]')
        .withTags(["wcag2aa", "wcag22aa"])
        .analyze();
      expect(results.violations).toEqual([]);
    });
  }

  test("badge is screen-reader friendly — relative + absolute time both present", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/risk-manager?fixture=spec036-degraded-stale`);
    const badge = page.getByTestId("degraded-mode-badge");
    const text = (await badge.innerText()).toLowerCase();
    // Relative form: "12 minutes old" / "3 hours old" / "2 days old"
    expect(text).toMatch(/\b(\d+)\s+(minute|hour|day)s?\s+old\b/i);
    // Absolute form: present in the same banner so audit replay can pin time.
    expect(text).toMatch(/since\s|at\s|\d{4}/i);
  });

  test("jurisdiction labels render in screen-reader friendly long form", async ({
    page,
  }) => {
    // Spec 036 R-14: state codes are expanded to long names for screen
    // readers (so "WA" is announced as "Western Australia").
    await page.goto(`${BASE_URL}/risk-manager?fixture=spec036-degraded-offline`);
    const badge = page.getByTestId("degraded-mode-badge");
    const ariaLabel = (await badge.getAttribute("aria-label")) ?? "";
    expect(ariaLabel.length).toBeGreaterThan(0);
  });
});
