import type { Page, Locator } from "@playwright/test";

/**
 * Eval page — /eval (FR-023 evaluation, FR-016 governance).
 */
export class EvalPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly reportList: Locator;
  readonly metricsTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1, name: /eval/i });
    this.reportList = page.getByTestId("eval-report-list");
    this.metricsTable = page.getByTestId("eval-metrics");
  }

  async goto(): Promise<void> {
    await this.page.goto("/eval");
    await this.heading.waitFor({ state: "visible" });
  }
}
