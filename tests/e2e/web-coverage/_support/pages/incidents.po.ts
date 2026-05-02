import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

/**
 * Page object for /incidents — common operating picture (FR-003, FR-007, FR-018).
 */
export class IncidentsPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly incidentList: Locator;
  readonly mapCanvas: Locator;
  readonly issueWarningButton: Locator;
  readonly assignTaskButton: Locator;
  readonly approveActionButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1, name: /incidents/i });
    this.incidentList = page.getByTestId("incident-list");
    this.mapCanvas = page.getByTestId("incident-map");
    this.issueWarningButton = page.getByRole("button", { name: /issue warning/i });
    this.assignTaskButton = page.getByRole("button", { name: /assign task/i });
    this.approveActionButton = page.getByRole("button", { name: /approve cross-agency action/i });
  }

  async goto(): Promise<void> {
    await this.page.goto("/incidents");
    await this.heading.waitFor({ state: "visible" });
  }

  async openIncident(incidentId: string): Promise<void> {
    await this.page.getByTestId(`incident-row-${incidentId}`).click();
    await this.mapCanvas.waitFor({ state: "visible" });
  }

  async assertIncidentVisible(incidentId: string): Promise<void> {
    await expect(this.page.getByTestId(`incident-row-${incidentId}`)).toBeVisible();
  }
}
