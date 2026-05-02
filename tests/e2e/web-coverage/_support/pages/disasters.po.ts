import type { Page, Locator } from "@playwright/test";

/**
 * Page object for /disasters — disaster declarations and timelines.
 *
 * NOTE: This route is on the spec-034 watchlist for `__next_error__` markers.
 * The PO uses defensive selectors so the assertion in
 * `tests/e2e/web-coverage/cross-cutting/audit-trail.spec.ts` can capture the
 * error state when present and route the failure into the gap register.
 */
export class DisastersPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly errorMarker: Locator;
  readonly declarationList: Locator;
  readonly declareButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { level: 1 }).first();
    this.errorMarker = page.locator("text=__next_error__");
    this.declarationList = page.getByTestId("declaration-list");
    this.declareButton = page.getByRole("button", { name: /declare disaster/i });
  }

  async goto(): Promise<void> {
    await this.page.goto("/disasters");
    // Don't waitFor heading — page may render error marker instead.
    await Promise.race([
      this.heading.waitFor({ state: "visible", timeout: 10000 }).catch(() => null),
      this.errorMarker.waitFor({ state: "visible", timeout: 10000 }).catch(() => null),
    ]);
  }

  async hasNextError(): Promise<boolean> {
    return (await this.errorMarker.count()) > 0;
  }
}
