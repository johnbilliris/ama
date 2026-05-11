// spec-038 Playwright E2E — persona override flow + persona_source recorded
// NOTE: This spec is skipped by default because Playwright browsers are not
// installed in CI for this run. Operator will execute via the
// docs/runbooks/help/screenshot-capture-runbook.md flow.
import { test, expect } from '@playwright/test';

test.skip('persona override flow + persona_source recorded [stub]', async ({ page }) => {
  await page.goto('/help');
  await expect(page).toHaveTitle(/Help/);
});