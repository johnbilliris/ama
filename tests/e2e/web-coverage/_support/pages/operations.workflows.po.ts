import type { Page, Locator } from "@playwright/test";

/**
 * Operations workflows page — /operations/workflows.
 *
 * Watchlist (spec 034): may render `__next_error__`. Defensive selector in place.
 */
export class OperationsWorkflowsPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly errorMarker: Locator;
  readonly workflowList: Locator;
  readonly approveStepButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1 }).first();
    this.errorMarker = page.locator("text=__next_error__");
    this.workflowList = page.getByTestId("workflow-list");
    this.approveStepButton = page.getByRole("button", { name: /approve step/i });
  }

  async goto(): Promise<void> {
    await this.page.goto("/operations/workflows");
    await Promise.race([
      this.heading.waitFor({ state: "visible", timeout: 10000 }).catch(() => null),
      this.errorMarker.waitFor({ state: "visible", timeout: 10000 }).catch(() => null),
    ]);
  }

  async hasNextError(): Promise<boolean> {
    return (await this.errorMarker.count()) > 0;
  }
}
