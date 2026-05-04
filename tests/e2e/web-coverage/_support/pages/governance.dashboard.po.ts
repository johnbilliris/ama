import type { Page, Locator } from "@playwright/test";

/**
 * Governance dashboard page — /governance/dashboard (FR-008, FR-016).
 */
export class GovernanceDashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly healthScoreTile: Locator;
  readonly auditTimeline: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1, name: /governance/i });
    this.healthScoreTile = page.getByTestId("governance-health-score");
    this.auditTimeline = page.getByTestId("audit-timeline");
  }

  async goto(): Promise<void> {
    await this.page.goto("/governance/dashboard");
    await this.heading.waitFor({ state: "visible" });
  }
}
