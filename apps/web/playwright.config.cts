import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "../../tests/e2e",
  // Spec 034 T003 — point Playwright at apps/web/tsconfig.json so the
  // `@web-coverage/*` path alias (defined there) resolves at runtime when
  // loading tests under tests/e2e/web-coverage/. Without this, Playwright
  // walks up from each test file and never finds a tsconfig with the alias.
  tsconfig: "./tsconfig.json",
  // Spec 034 web-coverage shards depend on the FastAPI backend (test-support
  // endpoints + Next.js /api proxy). Start uvicorn alongside the Next.js
  // dev server so a single `playwright test` invocation boots everything.
  // - `cwd: "../.."` runs from the repo root so `app.main:app` resolves via
  //   the editable install AND `packages.domain.*` imports work from cwd.
  // - `AMA_TEST_SUPPORT=1` + `AMA_ENVIRONMENT=dev` flip the dual-guard so
  //   `/api/test-support/personas/{id}` is registered (see
  //   apps/api/app/middleware/test_support_guard.py).
  webServer: [
    {
      command: "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: "../..",
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: true,
      timeout: 120000,
      stdout: "pipe",
      stderr: "pipe",
      env: {
        AMA_TEST_SUPPORT: "1",
        AMA_ENVIRONMENT: "dev",
      },
    },
    {
      command: "corepack pnpm --filter @ama/web dev",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
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
