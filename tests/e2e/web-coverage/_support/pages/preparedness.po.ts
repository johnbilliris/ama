import type { Page, Locator } from "@playwright/test";

/**
 * Preparedness page — /preparedness (FR-009 readiness, FR-024 lessons).
 */
export class PreparednessPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly readinessChecklist: Locator;
  readonly lessonsList: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1, name: /preparedness/i });
    this.readinessChecklist = page.getByTestId("readiness-checklist");
    this.lessonsList = page.getByTestId("lessons-list");
  }

  async goto(): Promise<void> {
    await this.page.goto("/preparedness");
    await this.heading.waitFor({ state: "visible" });
  }
}
