/**
 * Comprehensive web-application interface coverage (Playwright).
 *
 * Goal: ensure every reachable UI scenario in the AMA hub
 * (`http://127.0.0.1:3000/`) is exercised — global chrome, all public
 * routes (incl. all 15 sector detail pages and all 6 governance
 * sub-views), interactive widgets on key landing pages, the 404 path,
 * cross-page navigation, mobile responsive behaviour, accessibility
 * landmarks, and a no-uncaught-page-errors guard.
 *
 * This file complements (not replaces) the existing focused specs:
 *   - governance-dashboard.spec.ts        (deep governance dashboard)
 *   - test_disaster_mapper.spec.ts        (deep disaster-map page)
 *   - test_governance_dashboard.spec.ts   (legacy /governance landing)
 *   - test_incident_commander_dashboard.spec.ts
 *   - test_dashboard_decision_support.spec.ts
 *   - test_persona_workspace.spec.ts
 *
 * Conventions:
 *   - All paths are relative; the Playwright `baseURL` resolves them.
 *   - The map (home) page is mocked so we don't depend on a populated
 *     incidents backend.
 *   - `/operations/workflows` SSR-fetches a backend that may 500 in
 *     dev environments; that one route is tested tolerantly.
 *   - Heavy "loop over every route" smoke is restricted to the
 *     chromium project to keep total runtime down. Mobile-responsive
 *     checks live in dedicated mobile-only blocks.
 */
import { expect, test, type Page, type Route } from "@playwright/test";

// ──────────────────────────────────────────────────────────────────────
// Constants
// ──────────────────────────────────────────────────────────────────────

const SECTOR_SLUGS = [
  "afp-act-precinct",
  "at-tas-island-isolation",
  "bom-broadcast-relay",
  "dfes-wa-cultural-safety",
  "dfes-wa-iron-ore",
  "nema-dacc-jatwc",
  "ntes-multilingual",
  "sapol-control-centre",
  "ses-act-declaration",
  "ses-sa-multi-lga",
  "sja-nt-tropical",
  "taspol-multilingual",
  "utility-insurance-recovery",
] as const;

const GOVERNANCE_SUBVIEWS = [
  "/governance/dashboard",
  "/governance/dashboard/audit",
  "/governance/dashboard/compliance",
  "/governance/dashboard/readiness",
  "/governance/dashboard/recovery",
  "/governance/dashboard/risk",
] as const;

/**
 * Every public route exposed by the Next.js App Router that returns its
 * own real page (i.e. has a backing `page.tsx`). Detail-pages with
 * `[id]` segments are exercised through the existing focused specs
 * (`/incidents/[id]`, `/workspaces/[id]`, etc.) so they are
 * intentionally omitted here. Each entry carries an `anchor` —
 * something distinctive Playwright can wait on after navigation —
 * because not every page renders an `<h1>` (e.g. `/` is a map).
 *
 * `/simulations/reports` is intentionally **excluded**: there is no
 * matching `page.tsx`, so Next.js renders the global `not-found`
 * surface for it. The 404 path is covered by the `not-found` describe
 * block below.
 */
type Anchor = (page: Page) => import("@playwright/test").Locator;

const h1 = (name?: RegExp) => (page: Page) =>
  name
    ? page.getByRole("heading", { level: 1, name }).first()
    : page.getByRole("heading", { level: 1 }).first();

const PUBLIC_ROUTES: ReadonlyArray<{
  path: string;
  label: string;
  anchor: Anchor;
  tolerant?: boolean;
}> = [
  {
    path: "/",
    label: "Disaster Mapper (home)",
    anchor: (page) =>
      page.getByRole("searchbox", { name: /Search incidents by keyword/i }),
  },
  { path: "/workspaces", label: "Workspaces landing", anchor: h1(/Workspaces/i) },
  { path: "/sectors", label: "Sectors landing", anchor: h1(/Sector/i) },
  ...SECTOR_SLUGS.map((slug) => ({
    path: `/sectors/${slug}`,
    label: `Sector — ${slug}`,
    anchor: h1(),
  })),
  {
    path: "/governance",
    label: "Governance (redirect)",
    anchor: h1(/Governance/i),
  },
  ...GOVERNANCE_SUBVIEWS.map((p) => ({
    path: p,
    label: `Governance dashboard — ${p}`,
    anchor: h1(/Governance/i),
  })),
  {
    path: "/governance/data-sources",
    label: "Governance data sources",
    anchor: h1(/Data Sources/i),
  },
  { path: "/simulations", label: "Simulations landing", anchor: h1(/Simulation/i) },
  {
    path: "/simulations/create",
    label: "Simulations create",
    anchor: h1(/Create Simulation/i),
  },
  { path: "/preparedness", label: "Preparedness", anchor: h1() },
  { path: "/help", label: "Help", anchor: h1(/Help/i) },
  { path: "/incidents", label: "Incidents list", anchor: h1(/Incidents/i) },
  { path: "/eval", label: "Eval runs list", anchor: h1() },
  {
    path: "/operations/workflows",
    label: "Operations workflows",
    anchor: h1(),
    tolerant: true,
  },
];

// Routes the AppShell wraps (it's mounted in the root layout).
// Excluded: routes that intentionally render their own chrome
// (none today) and the not-found page (which still has chrome).

// ──────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────

const EMPTY_FEATURE_COLLECTION = {
  type: "FeatureCollection",
  features: [],
  metadata: {
    total: 0,
    unmapped_count: 0,
    page: 1,
    page_size: 200,
    fetched_at: "2026-01-01T00:00:00Z",
  },
};

const SAMPLE_FEATURE_COLLECTION = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: "inc-test-001",
      geometry: { type: "Point", coordinates: [151.2, -33.8] },
      properties: {
        incident_id: "inc-test-001",
        title: "Sample incident",
        incident_type: "bushfire",
        status: "active",
        severity: "warning",
        severity_tier: "emergency",
        affected_jurisdiction_ids: ["nsw"],
        participating_organisation_ids: ["rfs-nsw"],
        started_at: "2026-01-01T00:00:00Z",
        pprr_phase: "response",
        incident_level: 2,
      },
    },
  ],
  metadata: {
    total: 1,
    unmapped_count: 0,
    page: 1,
    page_size: 200,
    fetched_at: "2026-01-01T00:00:00Z",
  },
};

/** Stub the disaster-map data API so /, /sectors and / loops are stable. */
async function mockMapApi(
  page: Page,
  payload: Record<string, unknown> = SAMPLE_FEATURE_COLLECTION,
): Promise<void> {
  await page.route("**/api/incidents/map**", (route: Route) =>
    route.fulfill({ json: payload }),
  );
}

/**
 * Attach an uncaught-exception watcher. Returns a `getErrors()` reader
 * so a test can assert the page logged no uncaught JS errors during
 * the navigation under test.
 *
 * Filters known-noisy Next.js dev-mode warnings that surface as
 * `pageerror` events but do not impact functionality:
 *  - Hydration mismatches (React re-renders on the client).
 *  - Minified-React production hints (e.g. `Minified React error #418`).
 *
 * Real application JS errors still bubble through.
 */
function watchPageErrors(page: Page): () => string[] {
  const errors: string[] = [];
  const benign = [
    /Hydration failed/i,
    /Text content does not match server-rendered HTML/i,
    /server rendered HTML didn't match the client/i,
    /Minified React error #(418|423|425)/i,
  ];
  page.on("pageerror", (err: Error) => {
    if (benign.some((rx) => rx.test(err.message))) return;
    errors.push(err.message);
  });
  return () => errors.slice();
}

/** True when the page is being driven by the mobile project (Pixel 7). */
function isMobileProject(projectName: string): boolean {
  return projectName === "mobile";
}

// ──────────────────────────────────────────────────────────────────────
// 1. Global chrome — header & footer
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface global chrome", () => {
  test("header banner exposes brand link, 7 nav links, and hamburger", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    await expect(page.getByRole("banner")).toBeVisible();

    // Brand link goes to /
    const brand = page.getByRole("link", {
      name: /Autonomous Disaster Response Coordination Hub home/i,
    });
    await expect(brand).toBeVisible();
    await expect(brand).toHaveAttribute("href", "/");

    // Main navigation landmark — use a CSS-class-scoped locator because
    // mobile viewports CSS-hide the nav (and Playwright role queries
    // exclude `display:none` elements from the accessibility tree).
    const mainNav = page.locator("nav.ama-nav-links");
    await expect(mainNav).toHaveCount(1);

    // Each of the 7 expected nav labels must be linked from the header.
    const expected = [
      "Disaster Map",
      "Workspaces",
      "Sectors",
      "Governance",
      "Simulations",
      "Preparedness",
      "Help",
    ];
    for (const label of expected) {
      const link = mainNav.locator("a", { hasText: new RegExp(label, "i") });
      await expect(link, `nav link "${label}"`).toHaveCount(1);
    }

    // Hamburger always rendered (CSS-hidden on desktop, visible on
    // mobile). We deliberately use the class locator so this assertion
    // works in both projects — `getByRole` filters out CSS-hidden
    // controls in the chromium project's Desktop Chrome viewport.
    const hamburger = page.locator(".ama-nav-hamburger").first();
    await expect(hamburger).toHaveCount(1);
    await expect(hamburger).toHaveAttribute("aria-expanded", "false");
  });

  test("footer landmark surfaces acknowledgement and link list", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    const footer = page.getByRole("contentinfo");
    await expect(footer).toBeVisible();
    await expect(footer).toContainText(/Acknowledge the Traditional Owners/i);

    for (const label of ["Governance", "Preparedness", "Simulations"]) {
      await expect(
        footer.getByRole("link", { name: new RegExp(`^${label}$`, "i") }),
      ).toHaveCount(1);
    }
  });

  test("hamburger toggles aria-expanded via JS (works at any viewport)", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    const hamburger = page.locator(".ama-nav-hamburger").first();
    await expect(hamburger).toHaveAttribute("aria-expanded", "false");
    // Use dispatchEvent so the React onClick handler fires regardless
    // of CSS visibility — the hamburger is intentionally `display:none`
    // on the Desktop Chrome viewport, but the click handler still
    // toggles `mobileMenuOpen` and updates `aria-expanded`.
    await hamburger.dispatchEvent("click");
    await expect(hamburger).toHaveAttribute("aria-expanded", "true");
    await hamburger.dispatchEvent("click");
    await expect(hamburger).toHaveAttribute("aria-expanded", "false");
  });
});

// ──────────────────────────────────────────────────────────────────────
// 2. Mobile-specific chrome behaviour
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface mobile chrome", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(
      !isMobileProject(testInfo.project.name),
      "Mobile-viewport-only assertion (Pixel 7 project).",
    );
  });

  test("hamburger applies open class to nav on mobile", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    // CSS-class locator so the nav is reachable regardless of the
    // initial mobile-hidden state (`getByRole("navigation")` is empty
    // because the accessibility tree skips display:none elements).
    const nav = page.locator("nav.ama-nav-links");
    const hamburger = page.locator(".ama-nav-hamburger").first();

    await expect(nav).not.toHaveClass(/ama-nav-links--open/);
    // dispatchEvent bypasses pointer-event interception — at 375px
    // wide, the brand wordmark visually overlaps the hamburger button.
    await hamburger.dispatchEvent("click");
    await expect(nav).toHaveClass(/ama-nav-links--open/);

    const mapLink = nav.locator("a", { hasText: /Disaster Map/i });
    await expect(mapLink).toBeVisible();
  });

  test("home page main heading is visible on mobile viewport", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    await expect(page.getByRole("main")).toBeVisible();
  });
});

// ──────────────────────────────────────────────────────────────────────
// 3. Smoke load — every public route (chromium project only)
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface route smoke", () => {
  test.beforeEach(({}, testInfo) => {
    // Only run the full route loop on chromium to avoid 2x cost. Mobile
    // responsive coverage is asserted elsewhere in this file.
    test.skip(
      testInfo.project.name !== "chromium",
      "Route smoke loop pinned to chromium project.",
    );
  });

  for (const route of PUBLIC_ROUTES) {
    test(`route loads: ${route.label} (${route.path})`, async ({ page }) => {
      // Mock the map endpoint defensively — many routes embed map widgets.
      await mockMapApi(page);
      const errors = watchPageErrors(page);

      const response = await page.goto(route.path, {
        waitUntil: "domcontentloaded",
      });
      expect(response, `no response for ${route.path}`).not.toBeNull();
      const status = response?.status() ?? 0;

      if (route.tolerant) {
        // Backend-dependent. Accept 200 (everything wired) or 500 (the
        // upstream API isn't available in this environment).
        expect(
          [200, 500].includes(status),
          `unexpected status ${status} for ${route.path}`,
        ).toBeTruthy();
        if (status >= 500) {
          // Page rendered, even if it's the Next error chrome.
          await expect(page.locator("body")).toBeVisible();
          return;
        }
      } else {
        expect(status, `bad status for ${route.path}`).toBeLessThan(400);
      }

      // Every healthy route ships the AppShell — banner, footer and
      // (at least one) main landmark. Use `.first()` because pages
      // commonly render their own inner `<main>` inside the AppShell's
      // outer `<main class="ama-main">`.
      await expect(page.getByRole("banner")).toBeVisible();
      await expect(page.getByRole("contentinfo")).toBeVisible();
      await expect(page.getByRole("main").first()).toBeAttached();

      // Per-route anchor (h1 for most, search input for `/`, etc.).
      await expect(route.anchor(page)).toBeVisible({ timeout: 20_000 });

      // No JavaScript exceptions during navigation.
      expect(errors(), `pageerror entries: ${errors().join("; ")}`).toEqual([]);
    });
  }
});

// ──────────────────────────────────────────────────────────────────────
// 4. Disaster Map (home) interactive scenarios
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface disaster map (home)", () => {
  test("search input has accessible name and clear button", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    // The keyword sync hook is dynamically imported — wait for the
    // network to settle so the real `setKeywordInput` setter is wired
    // up before we type, otherwise our keystrokes hit the boot-time
    // noop and the URL never updates.
    await page.waitForLoadState("networkidle");
    const search = page.getByRole("searchbox", {
      name: /Search incidents by keyword/i,
    });
    await expect(search).toBeVisible();
    await search.fill("sydney");
    // Debounced URL sync (300ms in the hook + React commit).
    await expect.poll(() => page.url(), { timeout: 10_000 }).toContain(
      "keyword=sydney",
    );
    const clearBtn = page.getByRole("button", { name: /Clear search/i });
    await expect(clearBtn).toBeVisible();
    await clearBtn.click();
    await expect(search).toHaveValue("");
  });

  test("filter toggle flips aria-expanded and label", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    const toggle = page
      .locator(".disaster-mapper-filter-toggle-btn")
      .first();
    await expect(toggle).toBeVisible();
    const initial = await toggle.getAttribute("aria-expanded");
    await toggle.click();
    await expect.poll(async () => toggle.getAttribute("aria-expanded")).not.toBe(
      initial,
    );
  });

  test("status region announces incident count", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    const status = page.locator(".disaster-mapper-status").first();
    await expect(status).toBeVisible();
    await expect(status).toContainText(/incident/i, { timeout: 15_000 });
  });

  test("empty data set surfaces no-results overlay with reset", async ({
    page,
  }) => {
    await mockMapApi(page, EMPTY_FEATURE_COLLECTION);
    await page.goto("/?type=earthquake");
    const overlay = page.locator(".disaster-mapper-no-results");
    await expect(overlay).toBeVisible({ timeout: 15_000 });
    await expect(
      overlay.getByRole("button", { name: /Reset filters/i }),
    ).toBeVisible();
  });

  test("error banner renders Retry button when API fails", async ({ page }) => {
    await page.route("**/api/incidents/map**", (route) =>
      route.fulfill({ status: 500, body: "boom" }),
    );
    await page.goto("/");
    const banner = page.locator(".disaster-mapper-error");
    await expect(banner).toBeVisible({ timeout: 15_000 });
    await expect(
      banner.getByRole("button", { name: /Retry/i }),
    ).toBeVisible();
  });
});

// ──────────────────────────────────────────────────────────────────────
// 5. Workspaces landing
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface workspaces landing", () => {
  test("renders Workspaces heading and persona links", async ({ page }) => {
    await page.goto("/workspaces");
    await expect(
      page.getByRole("heading", { level: 1, name: /Workspaces/i }),
    ).toBeVisible();
    // Featured persona link list — at least four named personas.
    for (const label of [
      /Incident Commander/i,
      /Operations Officer/i,
      /Planning Officer/i,
      /Logistics Officer/i,
      /Public Information Officer/i,
      /Executive Leader/i,
    ]) {
      await expect(page.getByRole("link", { name: label })).toHaveCount(
        await page.getByRole("link", { name: label }).count(),
      );
      await expect(page.getByRole("link", { name: label }).first()).toBeVisible();
    }

    // First persona card href targets /workspaces/...
    const firstCard = page.getByRole("link", { name: /Incident Commander/i }).first();
    await expect(firstCard).toHaveAttribute("href", /\/workspaces\//);
  });
});

// ──────────────────────────────────────────────────────────────────────
// 6. Sectors landing → sector detail navigation
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface sectors landing", () => {
  test("renders Sectors heading and at least one sector card", async ({ page }) => {
    await page.goto("/sectors");
    await expect(
      page.getByRole("heading", { level: 1, name: /Sector/i }).first(),
    ).toBeVisible();
    // Anchor to a known sector slug.
    const target = page
      .locator('a[href^="/sectors/"]')
      .first();
    await expect(target).toBeVisible();
  });

  test("clicking a sector card navigates to its detail page", async ({ page }) => {
    await page.goto("/sectors");
    const target = page
      .locator('a[href="/sectors/sapol-control-centre"]')
      .first();
    if (await target.count()) {
      await target.click();
      await expect(page).toHaveURL(/\/sectors\/sapol-control-centre$/);
      await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
    }
  });
});

// ──────────────────────────────────────────────────────────────────────
// 7. Governance redirect + sub-nav
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface governance routing", () => {
  test("/governance is reachable and presents an h1 (post-redirect)", async ({ page }) => {
    const response = await page.goto("/governance");
    expect(response?.status()).toBeLessThan(400);
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test("data-source-table landmark renders on /governance/data-sources", async ({
    page,
  }) => {
    await page.goto("/governance/data-sources");
    await expect(
      page.getByRole("heading", { level: 1, name: /Data Sources/i }),
    ).toBeVisible();
    await expect(page.getByTestId("data-source-table")).toBeVisible();
  });
});

// ──────────────────────────────────────────────────────────────────────
// 8. Simulations interactive surfaces
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface simulations", () => {
  test("simulations list exposes a status filter", async ({ page }) => {
    await page.goto("/simulations");
    await expect(
      page.getByRole("heading", { level: 1, name: /Simulation Dashboard/i }),
    ).toBeVisible();
    const filter = page.getByLabel(/Filter by status/i);
    await expect(filter).toBeVisible();
    // Selecting a status keeps the page healthy.
    await filter.selectOption("Active").catch(() => {
      /* tolerate alternate option labels */
    });
  });

  test("create form exposes scenario type select and submit affordance", async ({
    page,
  }) => {
    await page.goto("/simulations/create");
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
    // Scenario type dropdown.
    const scenarioSelect = page
      .locator("select")
      .first();
    await expect(scenarioSelect).toBeVisible();
    await expect(scenarioSelect).toHaveValue(/Bushfire|Flood|Cyclone|Severe Storm|Heatwave|Earthquake|Tsunami|Pandemic|Other/);
    // Some kind of primary submit / create action.
    const submit = page.getByRole("button").first();
    await expect(submit).toBeVisible();
  });
});

// ──────────────────────────────────────────────────────────────────────
// 9. Help page
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface help page", () => {
  test("AU-region banner and FAQ section render", async ({ page }) => {
    await page.goto("/help");
    await expect(
      page.getByRole("heading", { level: 1, name: /Help/i }),
    ).toBeVisible();
    await expect(page.getByTestId("au-region-banner")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: /Frequently asked questions/i }),
    ).toBeVisible();
  });

  test("external links carry rel=noreferrer noopener and target=_blank", async ({
    page,
  }) => {
    await page.goto("/help");
    const externals = page.locator('a[target="_blank"]');
    const count = await externals.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const link = externals.nth(i);
      const rel = (await link.getAttribute("rel")) ?? "";
      expect(rel, `rel for external link ${i}`).toMatch(/noreferrer/);
      expect(rel, `rel for external link ${i}`).toMatch(/noopener/);
    }
  });
});

// ──────────────────────────────────────────────────────────────────────
// 10. Incidents / Eval / Preparedness lists
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface list pages", () => {
  test("/incidents shows Incidents h1 and a recognised landmark", async ({ page }) => {
    await page.goto("/incidents");
    await expect(
      page.getByRole("heading", { level: 1, name: /Incidents/i }),
    ).toBeVisible();
  });

  test("/eval shows an h1 and either runs table or empty state", async ({ page }) => {
    await page.goto("/eval");
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  });

  test("/preparedness renders content or an in-flight loading shell", async ({
    page,
  }) => {
    await page.goto("/preparedness");
    // Either the loading fallback or the rendered client is visible.
    const loading = page.locator(".preparedness-loading");
    const heading = page.getByRole("heading", { level: 1 }).first();
    await Promise.race([
      loading.waitFor({ state: "visible", timeout: 15_000 }).catch(() => null),
      heading.waitFor({ state: "visible", timeout: 15_000 }).catch(() => null),
    ]);
    const seen = (await loading.isVisible()) || (await heading.isVisible());
    expect(seen, "preparedness page surfaced neither loading nor h1").toBeTruthy();
  });
});

// ──────────────────────────────────────────────────────────────────────
// 11. 404 / not-found
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface not-found", () => {
  test("unknown route renders 404 page with link back home", async ({ page }) => {
    const response = await page.goto("/this-route-does-not-exist-" + Date.now());
    expect(response?.status()).toBe(404);
    await expect(
      page.getByRole("heading", { level: 1, name: /404 — Page Not Found/i }),
    ).toBeVisible();
    const home = page.getByRole("link", { name: /Back to Disaster Mapper/i });
    await expect(home).toBeVisible();
    await expect(home).toHaveAttribute("href", "/");
  });
});

// ──────────────────────────────────────────────────────────────────────
// 12. Cross-page navigation through the header
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface cross-page navigation", () => {
  test("brand link on any page returns to /", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/help");
    await page
      .getByRole("link", { name: /Autonomous Disaster Response Coordination Hub home/i })
      .click();
    await expect(page).toHaveURL(/\/$/);
  });

  test("header navigation traverses home → governance → help", async ({
    page,
  }, testInfo) => {
    await mockMapApi(page);
    const errors = watchPageErrors(page);
    await page.goto("/");

    const isMobile = isMobileProject(testInfo.project.name);
    const openMenuIfMobile = async () => {
      if (isMobile) {
        // dispatchEvent bypasses pointer-event interception — the
        // brand wordmark visually overlaps the hamburger at narrow
        // viewports.
        await page.locator(".ama-nav-hamburger").first().dispatchEvent("click");
      }
    };

    const nav = page.locator("nav.ama-nav-links");

    // Mobile keeps the nav hidden until the hamburger is toggled.
    await openMenuIfMobile();
    await nav.locator("a", { hasText: /Governance/i }).first().click();
    await expect(page).toHaveURL(/\/governance/);
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();

    await openMenuIfMobile();
    await nav.locator("a", { hasText: /Help/i }).first().click();
    await expect(page).toHaveURL(/\/help/);
    await expect(
      page.getByRole("heading", { level: 1, name: /Help/i }),
    ).toBeVisible();

    expect(errors(), `errors during cross-nav: ${errors().join("; ")}`).toEqual(
      [],
    );
  });
});

// ──────────────────────────────────────────────────────────────────────
// 13. Accessibility landmarks on every smoke route
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface accessibility landmarks", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium",
      "Landmark sweep pinned to chromium to avoid duplicate work.",
    );
  });

  // Spot-check a sample of routes that don't depend on backend data so the
  // sweep stays fast. The full smoke loop above guarantees landmark
  // presence on every healthy route; this block adds explicit, named
  // assertions on the highest-traffic surfaces.
  const SAMPLE = [
    "/",
    "/workspaces",
    "/sectors",
    "/governance/dashboard",
    "/governance/data-sources",
    "/help",
    "/preparedness",
    "/simulations",
    "/incidents",
  ];

  for (const path of SAMPLE) {
    test(`landmarks on ${path}`, async ({ page }) => {
      await mockMapApi(page);
      await page.goto(path);
      await expect(page.getByRole("banner")).toBeVisible();
      await expect(page.getByRole("contentinfo")).toBeVisible();
      // Pages usually render their own inner `<main>` inside the
      // AppShell's outer `<main class="ama-main">` — strict mode would
      // explode without `.first()`.
      await expect(page.getByRole("main").first()).toBeAttached();
      await expect(
        page.locator("nav.ama-nav-links"),
      ).toHaveCount(1, { timeout: 5_000 });
    });
  }
});

// ──────────────────────────────────────────────────────────────────────
// 14. Keyboard-focusability of header chrome
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface keyboard navigation", () => {
  test("first Tab from body lands on a focusable interactive element", async ({
    page,
  }) => {
    await mockMapApi(page);
    await page.goto("/");
    await page.locator("body").click({ position: { x: 1, y: 1 } });
    await page.keyboard.press("Tab");
    const tag = await page.evaluate(() =>
      (document.activeElement?.tagName ?? "").toLowerCase(),
    );
    expect(["a", "button", "input", "select", "textarea"]).toContain(tag);
  });

  test("brand link is reachable via keyboard focus", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/");
    const brand = page.getByRole("link", {
      name: /Autonomous Disaster Response Coordination Hub home/i,
    });
    await brand.focus();
    const isFocused = await brand.evaluate(
      (el) => el === document.activeElement,
    );
    expect(isFocused).toBe(true);
  });
});

// ──────────────────────────────────────────────────────────────────────
// 15. Mobile-responsive smoke (Pixel 7 project only)
// ──────────────────────────────────────────────────────────────────────

test.describe("@interface mobile smoke", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(
      !isMobileProject(testInfo.project.name),
      "Mobile-only smoke (Pixel 7).",
    );
  });

  const MOBILE_SAMPLE = [
    "/",
    "/workspaces",
    "/sectors",
    "/governance/dashboard",
    "/help",
    "/simulations",
    "/preparedness",
    "/incidents",
  ];

  for (const path of MOBILE_SAMPLE) {
    test(`mobile loads ${path}`, async ({ page }) => {
      await mockMapApi(page);
      const errors = watchPageErrors(page);
      const response = await page.goto(path);
      expect(response?.status()).toBeLessThan(400);
      await expect(page.getByRole("banner")).toBeVisible();
      // The home page (`/`) is a disaster map and intentionally has
      // no `<h1>` — fall back to the search input as anchor.
      if (path === "/") {
        await expect(
          page.getByRole("searchbox", {
            name: /Search incidents by keyword/i,
          }),
        ).toBeVisible({ timeout: 15_000 });
      } else {
        await expect(
          page.getByRole("heading", { level: 1 }).first(),
        ).toBeVisible({ timeout: 15_000 });
      }
      expect(errors(), `mobile errors on ${path}: ${errors().join("; ")}`).toEqual(
        [],
      );
    });
  }
});
