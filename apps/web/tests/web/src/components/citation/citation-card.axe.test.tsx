/**
 * Spec 036 / F-A12 / T239 — WCAG 2.2 AA axe-core scan for ``<CitationCard />``.
 *
 * Per Plan §F-A12.4 + §F-A12.5 — this lane is **warn-only** initially. The
 * test logs any violations as console warnings so authors see them; it
 * asserts only that axe runs cleanly (no infrastructure errors). Once the
 * baseline at ``docs/accessibility/spec-036-citation-card-baseline.md`` is
 * green for two consecutive PRs, flip the assertion to ``toEqual([])`` to
 * make the lane blocking.
 */

import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import axe from "axe-core";
import {
  CitationCard,
  type Citation,
} from "@ama/ui/components/citation/citation-card";

const FIXTURE: Citation = {
  jurisdiction: "nsw",
  topic: "bushfire-evacuation",
  page: 17,
  source_url: "https://example.gov.au/bushfire-handbook.pdf",
  rendered_url: "https://example.gov.au/bushfire-handbook/page-17",
  sha256_of_chunk: "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
  licence_mode: "full-text",
  confidence: 0.82,
  snippet: "Evacuate to designated assembly points along the southern arterial route.",
};

const AXE_RUN_OPTIONS: axe.RunOptions = {
  runOnly: {
    type: "tag",
    values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
  },
};

describe("CitationCard — axe WCAG 2.2 AA (T239, warn-only)", () => {
  it("passes axe in the default (collapsed) state", async () => {
    const { container } = render(<CitationCard citation={FIXTURE} idPrefix="axe-default" />);
    const results = await axe.run(container, AXE_RUN_OPTIONS);

    if (results.violations.length > 0) {
      // Warn-only per F-A12.5 — surface the violations but do not fail.
       
      console.warn(
        "[T239 a11y warn] CitationCard default-state axe violations:",
        results.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help })),
      );
    }
    expect(Array.isArray(results.violations)).toBe(true);
  });

  it("passes axe in the expanded (snippet-visible) state", async () => {
    const { container, getByRole } = render(
      <CitationCard citation={FIXTURE} idPrefix="axe-expanded" />,
    );
    // Expand the snippet.
    const btn = getByRole("button", { name: /show quote/i });
    btn.click();

    const results = await axe.run(container, AXE_RUN_OPTIONS);
    if (results.violations.length > 0) {
       
      console.warn(
        "[T239 a11y warn] CitationCard expanded-state axe violations:",
        results.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help })),
      );
    }
    expect(Array.isArray(results.violations)).toBe(true);
  });
});
