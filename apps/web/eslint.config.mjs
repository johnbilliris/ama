import { createRequire } from "module";
import { fixupConfigRules } from "@eslint/compat";
import * as espree from "espree";
import typescriptParser from "@typescript-eslint/parser";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

const require = createRequire(import.meta.url);
const noWaitForTimeout = require("../../tests/e2e/web-coverage/_support/eslint-rules/no-waitfortimeout.cjs");

const config = [
  ...fixupConfigRules(nextCoreWebVitals),
  {
    files: ["**/*.{cts,mts}"],
    languageOptions: {
      parser: typescriptParser
    }
  },
  {
    files: ["**/*.{js,jsx,mjs,cjs}"],
    languageOptions: {
      parser: espree,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: {
          jsx: true
        }
      }
    }
  },
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
