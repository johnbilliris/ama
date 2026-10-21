import { createRequire } from "module";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

const require = createRequire(import.meta.url);
const noWaitForTimeout = require("../../tests/e2e/web-coverage/_support/eslint-rules/no-waitfortimeout.cjs");

const config = [
  ...nextCoreWebVitals,
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
    rules: {
      "react-hooks/purity": "off",
      "react-hooks/refs": "off",
      "react-hooks/set-state-in-effect": "off"
    }
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

export default config;
