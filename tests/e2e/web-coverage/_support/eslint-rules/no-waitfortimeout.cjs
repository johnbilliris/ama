/**
 * Custom ESLint rule: disallow `page.waitForTimeout(...)` and `await page.waitForTimeout(...)`
 * inside the `tests/e2e/web-coverage/` suite.
 *
 * Rationale: deterministic web-coverage tests must rely on event-driven Playwright waits
 * (locator.waitFor, waitForResponse, web-first assertions). Sleep-based waits hide flake
 * and break trace replay determinism (FR-006).
 *
 * Failure → CI gate red.
 */
"use strict";

module.exports = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Disallow page.waitForTimeout in web-coverage tests; use deterministic waits instead.",
      recommended: true,
    },
    schema: [],
    messages: {
      noWait:
        "Avoid page.waitForTimeout — use locator.waitFor / waitForResponse / expect(...).toHaveText for deterministic waits.",
    },
  },
  create(context) {
    return {
      CallExpression(node) {
        const { callee } = node;
        if (
          callee &&
          callee.type === "MemberExpression" &&
          callee.property &&
          callee.property.name === "waitForTimeout"
        ) {
          context.report({ node, messageId: "noWait" });
        }
      },
    };
  },
};
