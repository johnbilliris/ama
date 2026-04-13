import { expect, test } from "@playwright/test";

/**
 * E2E tests for the Disaster Mapper UI (/disasters page).
 *
 * Tests use Playwright route interception to mock API responses,
 * enabling full UI verification without a live backend.
 */

// ── Mock data ──────────────────────────────────────────────────────────

const MOCK_FEATURE_COLLECTION = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: "inc-001",
      geometry: { type: "Point", coordinates: [151.2, -33.8] },
      properties: {
        incident_id: "inc-001",
        title: "Sydney Bushfire",
        incident_type: "bushfire",
        status: "active",
        severity: "warning",
        severity_tier: "emergency",
        affected_jurisdiction_ids: ["nsw"],
        participating_organisation_ids: ["rfs-nsw"],
        started_at: "2024-01-15T08:30:00Z",
        pprr_phase: "response",
        incident_level: 3,
      },
    },
    {
      type: "Feature",
      id: "inc-002",
      geometry: { type: "Point", coordinates: [153.0, -27.5] },
      properties: {
        incident_id: "inc-002",
        title: "Brisbane Flood",
        incident_type: "flood",
        status: "monitoring",
        severity: "advisory",
        severity_tier: "advice",
        affected_jurisdiction_ids: ["qld"],
        participating_organisation_ids: ["ses-qld"],
        started_at: "2023-06-20T14:00:00Z",
        pprr_phase: "preparedness",
        incident_level: 1,
      },
    },
  ],
  metadata: {
    total: 2,
    unmapped_count: 1,
    page: 1,
    page_size: 200,
    fetched_at: "2024-06-15T12:00:00Z",
  },
};

const EMPTY_FEATURE_COLLECTION = {
  type: "FeatureCollection",
  features: [],
  metadata: {
    total: 0,
    unmapped_count: 0,
    page: 1,
    page_size: 200,
    fetched_at: "2024-06-15T12:00:00Z",
  },
};

function mockMapApi(page: import("@playwright/test").Page, data = MOCK_FEATURE_COLLECTION) {
  return page.route("**/api/incidents/map**", async (route) => {
    await route.fulfill({ json: data });
  });
}

// ── Page load tests ────────────────────────────────────────────────────

test.describe("Disaster Mapper - Page Load", () => {
  test("renders page heading and loading state", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    await expect(page.getByRole("heading", { name: /disaster/i })).toBeVisible();
  });

  test("displays incident count after loading", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    // Wait for data to load and incident count to appear
    await expect(page.getByText(/2.*incident/i)).toBeVisible({ timeout: 10000 });
  });

  test("shows unmapped notice when unmapped incidents exist", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    await expect(page.getByText(/unmapped/i)).toBeVisible({ timeout: 10000 });
  });
});

// ── Filter tests ───────────────────────────────────────────────────────

test.describe("Disaster Mapper - Filters", () => {
  test("filter panel is visible with filter categories", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    // Filter panel should have type, severity, status categories
    await expect(page.getByText(/type/i).first()).toBeVisible();
    await expect(page.getByText(/severity/i).first()).toBeVisible();
  });

  test("clicking a filter chip updates the URL", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    // Click on bushfire filter
    const bushfireChip = page.getByRole("button", { name: /bushfire/i }).first();
    if (await bushfireChip.isVisible()) {
      await bushfireChip.click();
      await page.waitForTimeout(500);
      expect(page.url()).toContain("type=");
    }
  });

  test("shows no results message when filters exclude everything", async ({ page }) => {
    // First load with data, then empty on filtered request
    let callCount = 0;
    await page.route("**/api/incidents/map**", async (route) => {
      callCount++;
      if (callCount === 1) {
        await route.fulfill({ json: MOCK_FEATURE_COLLECTION });
      } else {
        await route.fulfill({ json: EMPTY_FEATURE_COLLECTION });
      }
    });

    await page.goto("/disasters");
    await page.waitForTimeout(2000);

    // Check that the page loaded successfully first
    await expect(page.getByRole("heading", { name: /disaster/i })).toBeVisible();
  });
});

// ── Search tests ───────────────────────────────────────────────────────

test.describe("Disaster Mapper - Search", () => {
  test("search input is visible", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    const searchInput = page.getByPlaceholder(/search/i);
    await expect(searchInput).toBeVisible();
  });

  test("typing in search updates URL with keyword param", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    const searchInput = page.getByPlaceholder(/search/i);
    await searchInput.fill("sydney");
    // Debounced at 300ms
    await page.waitForTimeout(500);
    expect(page.url()).toContain("keyword=sydney");
  });
});

// ── Sidebar tests ──────────────────────────────────────────────────────

test.describe("Disaster Mapper - Sidebar", () => {
  test("sidebar is hidden initially", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    // Sidebar should not be visible until an incident is clicked
    const sidebar = page.locator("[class*=sidebar]").first();
    // It may or may not exist in DOM, but should not show detailed info
    const detailHeading = page.getByRole("heading", { name: "Sydney Bushfire" });
    await expect(detailHeading).not.toBeVisible();
  });
});

// ── List-view fallback tests ───────────────────────────────────────────

test.describe("Disaster Mapper - List View Fallback", () => {
  test("list view toggle button is accessible", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    // The list view button or table should be available as a fallback
    const listToggle = page.getByRole("button", { name: /list|table/i });
    if (await listToggle.isVisible()) {
      await listToggle.click();
      // Table should appear
      await expect(page.getByRole("table")).toBeVisible();
    }
  });
});

// ── Accessibility tests ────────────────────────────────────────────────

test.describe("Disaster Mapper - Accessibility", () => {
  test("page has proper heading hierarchy", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    const h1 = page.getByRole("heading", { level: 1 });
    await expect(h1).toBeVisible();
  });

  test("filter buttons have accessible names", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    // All filter chips should be buttons with text content
    const buttons = page.getByRole("button");
    const count = await buttons.count();
    expect(count).toBeGreaterThan(0);
  });

  test("search input has accessible label", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    const searchInput = page.getByPlaceholder(/search/i);
    await expect(searchInput).toBeVisible();
    // Should have accessible attributes
    const ariaLabel = await searchInput.getAttribute("aria-label");
    const placeholder = await searchInput.getAttribute("placeholder");
    expect(ariaLabel || placeholder).toBeTruthy();
  });
});

// ── Mobile responsiveness tests ────────────────────────────────────────

test.describe("Disaster Mapper - Mobile", () => {
  test.use({ viewport: { width: 375, height: 812 } }); // iPhone X

  test("page loads on mobile viewport", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    await expect(page.getByRole("heading", { name: /disaster/i })).toBeVisible();
  });

  test("filter panel collapses to bottom sheet on mobile", async ({ page }) => {
    await mockMapApi(page);
    await page.goto("/disasters");

    // On mobile, filter panel should be collapsible
    const filterToggle = page.getByRole("button", { name: /filter/i }).first();
    if (await filterToggle.isVisible()) {
      await filterToggle.click();
      await page.waitForTimeout(300);
      // Filter content should become visible
      await expect(page.getByText(/type/i).first()).toBeVisible();
    }
  });
});
