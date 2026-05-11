// spec-038 Playwright E2E — axe-core a11y scan on help layout
// NOTE: This spec is skipped by default because Playwright browsers are not
// installed in CI for this run. Operator will execute via the
// docs/runbooks/help/screenshot-capture-runbook.md flow.
import { test, expect } from '@playwright/test';

test.skip('axe-core a11y scan on help layout [stub]', async ({ page }) => {
  await page.goto('/help');
  await expect(page).toHaveTitle(/Help/);
});