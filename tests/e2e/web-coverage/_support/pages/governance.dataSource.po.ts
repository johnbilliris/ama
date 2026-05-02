import type { Page, Locator } from "@playwright/test";

/**
 * Data source admin page — /governance/data-sources (FR-014).
 */
export class GovernanceDataSourcePage {
  readonly page: Page;
  readonly heading: Locator;
  readonly sourceTable: Locator;
  readonly addSourceButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1, name: /data sources/i });
    this.sourceTable = page.getByTestId("data-source-table");
    this.addSourceButton = page.getByRole("button", { name: /add data source/i });
  }

  async goto(): Promise<void> {
    await this.page.goto("/governance/data-sources");
    await this.heading.waitFor({ state: "visible" });
  }
}
