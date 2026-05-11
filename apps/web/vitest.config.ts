/**
 * Vitest configuration for apps/web (spec-032 FR-T02, T904).
 *
 * Vitest + React Testing Library against Next.js 16.2 / React 19. JSDOM env
 * gives DOM APIs without a browser; co-located with apps/web/__tests__/.
 */
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: [
      "__tests__/**/*.test.{ts,tsx}",
      "tests/unit/**/*.test.{ts,tsx}",
      "tests/integration/**/*.test.{ts,tsx}",
      "tests/a11y/**/*.test.{ts,tsx}",
    ],
    setupFiles: ["__tests__/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["src/**"],
      exclude: ["src/**/*.d.ts", "src/**/__mocks__/**"],
    },
  },
});
