import type { Page, Locator } from "@playwright/test";

/**
 * Simulations page — /simulations (FR-021, FR-022).
 */
export class SimulationsPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly simulationList: Locator;
  readonly playbackTimeline: Locator;
  readonly startButton: Locator;
  readonly pauseButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1, name: /simulation/i });
    this.simulationList = page.getByTestId("simulation-list");
    this.playbackTimeline = page.getByTestId("playback-timeline");
    this.startButton = page.getByRole("button", { name: /start simulation/i });
    this.pauseButton = page.getByRole("button", { name: /pause simulation/i });
  }

  async goto(): Promise<void> {
    await this.page.goto("/simulations");
    await this.heading.waitFor({ state: "visible" });
  }
}
