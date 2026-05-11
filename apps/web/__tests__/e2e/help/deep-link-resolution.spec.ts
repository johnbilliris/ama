// spec-038 Playwright E2E — AR-001 deep link resolves screen + article + chat prefill
// NOTE: This spec is skipped by default because Playwright browsers are not
// installed in CI for this run. Operator will execute via the
// docs/runbooks/help/screenshot-capture-runbook.md flow.
import { test, expect } from '@playwright/test';

test.skip('AR-001 deep link resolves screen + article + chat prefill [stub]', async ({ page }) => {
  await page.goto('/help');
  await expect(page).toHaveTitle(/Help/);
});