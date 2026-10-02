/**
 * AUD-018 / T-F07 — the simulation identification marker MUST be present and
 * screen-reader announced on the `/simulations` surface.
 *
 * Moved out of `apps/web/tests/a11y/` (which sits outside every configured
 * Playwright `testDir`, so it never ran) into the `web-coverage` tree. It is
 * tagged `@a11y` so the `web-coverage-axe` project selects it, and the
 * `web-coverage-chromium` / `web-coverage-mobile` projects run it too.
 *
 * The acceptance contract (FR-021 / FR-035 / FR-040):
 *  - At least one node MUST carry an accessible name containing "Simulation"
 *    so AT users hear the exercise disclaimer. Absence FAILS; it is not a
 *    soft-skipped gap annotation.
 *  - Every such node's accessible name MUST actually say "simulation".
 *  - axe-core MUST report no WCAG 2.2 AA violations on the surface.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { buildAxe } from "@web-coverage/_support/a11y/axeBuilder";
import { SimulationsPage } from "@web-coverage/_support/pages/simulations.po";

const MARKER_SELECTOR = [
  '[data-testid="sim-banner-status"]',
  '[data-testid="simulation-chat-receipt-prefix"]',
  '[aria-label*="Simulation"]',
  '[aria-label*="simulation"]',
].join(", ");

test(
  "simulation surface is identified to screen readers and axe-clean " +
    "@persona:public-information-officer @fr:FR-021 @fr:FR-035 @fr:FR-040 @a11y",
  async ({ resolvePersona, page, correlationId }) => {
    await resolvePersona("public-information-officer");
    await page.setExtraHTTPHeaders({ "X-Correlation-Id": correlationId });

    const simulations = new SimulationsPage(page);
    await simulations.goto();

    const candidates = await page.locator(MARKER_SELECTOR).all();
    expect(
      candidates.length,
      "/simulations must expose at least one simulation-identifying accessible name",
    ).toBeGreaterThan(0);

    for (const node of candidates) {
      const ariaLabel = (await node.getAttribute("aria-label")) ?? "";
      const text = (await node.innerText().catch(() => "")) ?? "";
      expect(`${ariaLabel} ${text}`.toLowerCase()).toContain("simulation");
    }

    const results = await buildAxe(page).analyze();
    const blocking = results.violations.filter((v) =>
      v.tags.some((t) => t === "wcag22aa" || t === "wcag2aa"),
    );
    expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
  },
);
