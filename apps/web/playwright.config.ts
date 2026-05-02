import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "../../tests/e2e",
  webServer: {
    command: "corepack pnpm --filter @ama/web dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
    timeout: 120000,
  },
  use: {
    baseURL: "http://127.0.0.1:3000"
  },
  reporter: [
    ["list"],
    ["junit", { outputFile: "../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml" }],
    ["json", { outputFile: "../../tests/e2e/web-coverage/_artifacts/web-coverage.json" }],
    ["../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts"]
  ],
  projects: [
    { name: "chromium", testIgnore: /web-coverage\//, use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", testIgnore: /web-coverage\//, use: { ...devices["Pixel 7"] } },
    {
      name: "web-coverage-chromium",
      testDir: "../../tests/e2e/web-coverage",
      testIgnore: /_support\//,
      use: { ...devices["Desktop Chrome"] }
    },
    {
      name: "web-coverage-mobile",
      testDir: "../../tests/e2e/web-coverage",
      testIgnore: /_support\//,
      use: { ...devices["Pixel 7"] }
    },
    {
      name: "web-coverage-axe",
      testDir: "../../tests/e2e/web-coverage",
      testIgnore: /_support\//,
      grep: /@a11y/,
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
