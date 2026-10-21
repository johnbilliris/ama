import AxeBuilder from "@axe-core/playwright";
import playwrightTest from "@playwright/test";

const { expect, test } = playwrightTest;

const TABS = [
  ["KPI Ladder", "evidence-kpi-ladder-tab"],
  ["Measurement Method", "evidence-measurement-tab"],
  ["Replay Scorecard", "evidence-replay-tab"],
  ["Impact Chains", "evidence-impact-tab"],
  ["Benchmarks", "evidence-benchmarks-tab"],
  ["Audit Trace", "evidence-audit-tab"],
  ["Public Information", "evidence-public-information-tab"],
] as const;

test.describe("Evidence Harness", () => {
  test("all seven accessible workflows load live data", async ({ page }) => {
    const requests: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("/api/v1/evidence/")) requests.push(request.url());
    });

    await page.goto("/governance/evidence");
    await expect(page.getByRole("heading", { name: "Measurable Success-Criteria Evidence Harness" })).toBeVisible();

    for (const [label, testId] of TABS) {
      const tab = page.getByRole("tab", { name: label });
      await tab.click();
      await expect(tab).toHaveAttribute("aria-selected", "true");
      await expect(page.getByTestId(testId)).toBeVisible();
    }

    await expect.poll(() => new Set(requests.map((url) => {
      const match = url.match(/\/api\/v1\/evidence\/([^?]+)/);
      return match?.[1] ?? "";
    })).size).toBeGreaterThanOrEqual(7);
  });

  test("replay GETs on mount and POSTs only after explicit action", async ({ page }) => {
    const methods: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("/api/v1/evidence/scorecards") || request.url().includes("/replay")) {
        methods.push(request.method());
      }
    });

    await page.goto("/governance/evidence");
    await page.getByRole("tab", { name: "Replay Scorecard" }).click();
    await expect(
      page.getByText("No persisted scorecard exists for this scenario. Run a replay to create one."),
    ).toBeVisible();
    expect(methods).not.toContain("POST");

    await page.getByRole("button", { name: "Run replay" }).click();
    await expect.poll(() => methods.filter((method) => method === "POST").length).toBe(1);
    await expect(page.getByRole("table", { name: "Replay delta scorecard" })).toBeVisible();
  });

  test("KPI ladder exposes nine attributes and risk-adjusted value", async ({ page }) => {
    await page.goto("/governance/evidence");
    const table = page.getByRole("table", { name: "KPI ladder" });
    await expect(table).toBeVisible();
    for (const header of [
      "Formula",
      "Unit",
      "Owner",
      "Cadence",
      "Target",
      "Alert",
      "Baseline",
      "Provenance",
      "Confidence rule",
      "Risk-adjusted target",
    ]) {
      await expect(
        table.getByRole("columnheader", { name: header, exact: true }),
      ).toBeVisible();
    }
  });

  test("Public Information renders eight channels and disclosed Auslan state", async ({ page }) => {
    await page.goto("/governance/evidence");
    await page.getByRole("tab", { name: "Public Information" }).click();
    await expect(page.locator("section.public-info li")).toHaveCount(8);
    await expect(
      page.getByRole("heading", { name: /Auslan/i }),
    ).toBeVisible();
  });

  test("WCAG 2.2 AA has no serious or critical violations", async ({ page }) => {
    await page.goto("/governance/evidence");
    const results = await new AxeBuilder({ page })
      .include("section.workspace-shell")
      .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
      .analyze();
    expect(
      results.violations.filter(
        (violation) => violation.impact === "serious" || violation.impact === "critical",
      ),
    ).toEqual([]);
  });
});
