import type { Page, Locator } from "@playwright/test";

/**
 * Page object for /workspaces — persona-driven workspace landing.
 * Spec 034 maps this route to FR-001 / FR-002 (persona resolution + entry).
 */
export class WorkspacesPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly personaBadge: Locator;
  readonly workspaceCards: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1 });
    this.personaBadge = page.getByTestId("persona-badge");
    this.workspaceCards = page.getByTestId("workspace-card");
  }

  async goto(): Promise<void> {
    await this.page.goto("/workspaces");
    await this.heading.waitFor({ state: "visible" });
  }

  async openWorkspace(name: string): Promise<void> {
    await this.workspaceCards.filter({ hasText: name }).first().click();
  }
}
