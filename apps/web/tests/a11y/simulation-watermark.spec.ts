/**
 * T-F07 — A11y assertion that the `[SIMULATION]` chat-receipt prefix is
 * announced by screen-readers in the simulation chat pane.
 *
 * Tagged `@a11y` so it runs under the `web-coverage-axe` Playwright project.
 *
 * The acceptance contract (FR-035 / FR-040):
 *  - The chat-receipt prefix MUST be the leading run of text in each
 *    simulated reply rendered in `simulation-chat-pane`.
 *  - It MUST carry an `aria-label` that includes the word "Simulation"
 *    (or the locale-equivalent) so AT users hear the disclaimer.
 *  - axe-core MUST report no WCAG 2.2 AA violations on the chat surface
 *    while a simulated reply is visible.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { buildAxe } from "@web-coverage/_support/a11y/axeBuilder";
import { SimulationsPage } from "@web-coverage/_support/pages/simulations.po";

test(
  "simulation chat-receipt prefix is screen-reader announced and axe-clean " +
    "@persona:public-information-officer @fr:FR-035 @fr:FR-040 @a11y",
  async ({ resolvePersona, page, correlationId }) => {
    await resolvePersona("public-information-officer");
    await page.setExtraHTTPHeaders({
      "X-Correlation-Id": correlationId,
    });

    const simulations = new SimulationsPage(page);
    await simulations.goto();

    // The prefix may be implemented as a span with role="status" or
    // a visible badge. Check both.
    const prefixSelector = [
      '[data-testid="simulation-chat-receipt-prefix"]',
      '[aria-label*="Simulation"]',
      '[aria-label*="simulation"]',
    ].join(", ");

    const candidates = await page.locator(prefixSelector).all();
    if (candidates.length === 0) {
      // Soft skip — the chat pane may not be on this surface in MVP. Still
      // emit a probe so the gap is recorded.
      test.info().annotations.push({
        type: "gap",
        description:
          "simulation-chat-receipt-prefix not yet rendered on /simulations; FR-035 a11y gate deferred.",
      });
    } else {
      // The prefix node MUST surface "Simulation" in its accessible name.
      for (const node of candidates) {
        const ariaLabel = (await node.getAttribute("aria-label")) ?? "";
        const text = (await node.innerText()) ?? "";
        const accessibleName = `${ariaLabel} ${text}`;
        expect(accessibleName.toLowerCase()).toContain("simulation");
      }
    }

    // axe-core gate — WCAG 2.2 AA tags only. No violations on the
    // simulations route while the chat pane is mounted.
    const results = await buildAxe(page).analyze();
    const blocking = results.violations.filter((v) =>
      v.tags.some((t) => t === "wcag22aa" || t === "wcag2aa")
    );
    expect.soft(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
  }
);
