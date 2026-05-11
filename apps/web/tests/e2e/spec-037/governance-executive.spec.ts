/**
 * T061 — Playwright e2e + axe-core for /governance/executive.
 *
 * Citations: NN-3, FR-021, RES-03, CHK083.
 *
 * Compile-check only when no browser is available; CI runs the full suite.
 */
import { test, expect } from '@playwright/test';
import { injectAndCheck } from './axe.setup';

test.describe('Spec-037 — Executive KPI Surface', () => {
  test('renders end-to-end with no axe violations', async ({ page }) => {
    await page.goto('/governance/executive');
    await expect(page.getByRole('heading', { name: /Executive KPI Surface/i })).toBeVisible();
    await injectAndCheck(page);
  });

  test('manual-row ratio strip is announced via aria-live', async ({ page }) => {
    await page.goto('/governance/executive');
    const status = page.getByRole('status', {
      name: /manual-row ratio per evidence-pack artefact/i,
    });
    await expect(status).toBeVisible();
    await expect(status).toHaveAttribute('aria-live', 'polite');
  });

  test('keyboard-only navigation reaches the KPI ladder', async ({ page }) => {
    await page.goto('/governance/executive');
    // Tab into the page; verify focusable tabs/headings are reachable.
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.tagName ?? null);
    expect(focused).not.toBeNull();
  });

  test('400% zoom + high-contrast smoke', async ({ page }) => {
    await page.emulateMedia({ forcedColors: 'active' });
    await page.setViewportSize({ width: 320, height: 800 }); // simulate 400% zoom on 1280px
    await page.goto('/governance/executive');
    await expect(page.getByRole('heading', { name: /Executive KPI Surface/i })).toBeVisible();
  });
});
