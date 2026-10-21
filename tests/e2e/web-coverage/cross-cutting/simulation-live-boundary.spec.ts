/**
 * AUD-017 / FR-022 — the live operational view must contain no simulation
 * affordance, on desktop and on the mobile menu.
 * AUD-018 / FR-021 — every /simulations view identifies itself, including
 * while scrolled and on narrow viewports.
 *
 * The negative assertion inspects every accessible link and the rendered
 * text of the live shell, so it fails on any simulation affordance rather
 * than only on a particular banner test ID.
 */
import { test, expect } from "@web-coverage/_support/webCoverageTest";
import { SimulationsPage } from "@web-coverage/_support/pages/simulations.po";

const LIVE_ROUTES = ["/", "/workspaces", "/preparedness"];

test(
  "live operational shell exposes no simulation affordance " +
    "@persona:incident-controller @fr:FR-022 @clause:VII",
  async ({ page, correlationId }) => {
    await page.setExtraHTTPHeaders({ "X-Correlation-Id": correlationId });

    for (const route of LIVE_ROUTES) {
      await page.goto(route);

      const hrefs = await page.locator("a[href]").evaluateAll((nodes) =>
        nodes.map((n) => (n as HTMLAnchorElement).getAttribute("href") ?? ""),
      );
      expect(
        hrefs.filter((h) => h.includes("/simulations")),
        `${route} must not link to simulation routes`,
      ).toHaveLength(0);

      for (const region of ["banner", "contentinfo"] as const) {
        const text = (await page.getByRole(region).innerText()).toLowerCase();
        expect(text, `${route} ${region} must not mention simulations`).not.toContain(
          "simulation",
        );
      }

      // Mobile menu renders the same navigation list.
      await page.setViewportSize({ width: 390, height: 844 });
      const hamburger = page.getByRole("button", { name: /toggle navigation/i });
      if (await hamburger.count()) {
        await hamburger.first().click();
        const navText = (await page.getByRole("navigation").first().innerText()).toLowerCase();
        expect(navText, `${route} mobile menu must not mention simulations`).not.toContain(
          "simulation",
        );
      }
      await page.setViewportSize({ width: 1280, height: 800 });
    }
  },
);

test(
  "simulation routes stay directly reachable and always identify themselves " +
    "@persona:incident-controller @fr:FR-021 @fr:FR-022",
  async ({ page, correlationId }) => {
    await page.setExtraHTTPHeaders({ "X-Correlation-Id": correlationId });

    const simulations = new SimulationsPage(page);
    await simulations.goto();

    const marker = page.getByTestId("sim-banner-status");
    await expect(marker).toBeVisible();
    await expect(page.getByText(/this is not live data/i)).toBeVisible();

    // Sticky: still visible after scrolling to the bottom of the document.
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await expect(marker).toBeInViewport();

    // Narrow viewport keeps the marker on screen.
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(marker).toBeVisible();
    await page.setViewportSize({ width: 1280, height: 800 });

    // Deep-linking an unknown tenant must still identify the exercise surface
    // in the error state rather than dropping the marker.
    await page.goto("/simulations/does-not-exist");
    await expect(page.getByTestId("sim-banner-status")).toBeVisible();
  },
);
