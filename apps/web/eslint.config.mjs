import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";
import { createRequire } from "module";

const __dirname = dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({ baseDirectory: __dirname });
const require = createRequire(import.meta.url);
const noWaitForTimeout = require("../../tests/e2e/web-coverage/_support/eslint-rules/no-waitfortimeout.cjs");

export default [
  ...compat.extends("next/core-web-vitals"),
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "coverage/**",
      "dist/**",
      "build/**",
      "**/*.min.js"
    ]
  },
  {
    files: ["../../tests/e2e/web-coverage/**/*.{ts,tsx}"],
    plugins: {
      "ama-web-coverage": {
        rules: {
          "no-waitfortimeout": noWaitForTimeout
        }
      }
    },
    rules: {
      "ama-web-coverage/no-waitfortimeout": "error"
    }
  }
];
