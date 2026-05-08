/**
 * Spec 036 / F-A12 / T240 — Keyboard accessibility tests for ``<CitationCard />``.
 *
 * Asserts (per Plan §F-A12.1):
 *   1. Collapsible header ``<button>`` is in the tab order.
 *   2. ``Enter`` toggles expand/collapse.
 *   3. ``Space`` toggles expand/collapse.
 *   4. ``aria-expanded`` reflects state.
 *   5. ``aria-controls`` references the body element id.
 */

import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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

describe("CitationCard — keyboard accessibility (T240)", () => {
  it("places the collapsible header button in the tab order", () => {
    render(<CitationCard citation={FIXTURE} idPrefix="t240-tab" />);
    const btn = screen.getByRole("button", { name: /show quote/i });
    expect(btn.tabIndex).toBe(0);
  });

  it("toggles expand/collapse via Enter", () => {
    render(<CitationCard citation={FIXTURE} idPrefix="t240-enter" />);
    const btn = screen.getByRole("button", { name: /show quote/i });
    expect(btn.getAttribute("aria-expanded")).toBe("false");

    fireEvent.keyDown(btn, { key: "Enter" });
    expect(screen.getByRole("button", { name: /hide quote/i }).getAttribute("aria-expanded")).toBe(
      "true",
    );

    fireEvent.keyDown(screen.getByRole("button", { name: /hide quote/i }), { key: "Enter" });
    expect(screen.getByRole("button", { name: /show quote/i }).getAttribute("aria-expanded")).toBe(
      "false",
    );
  });

  it("toggles expand/collapse via Space", () => {
    render(<CitationCard citation={FIXTURE} idPrefix="t240-space" />);
    const btn = screen.getByRole("button", { name: /show quote/i });
    fireEvent.keyDown(btn, { key: " " });
    expect(screen.getByRole("button", { name: /hide quote/i }).getAttribute("aria-expanded")).toBe(
      "true",
    );
  });

  it("aria-expanded reflects current expansion state", () => {
    render(<CitationCard citation={FIXTURE} idPrefix="t240-state" />);
    const btn = screen.getByRole("button", { name: /show quote/i });
    expect(btn.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(btn);
    expect(screen.getByRole("button", { name: /hide quote/i }).getAttribute("aria-expanded")).toBe(
      "true",
    );
  });

  it("aria-controls references the panel id", () => {
    render(<CitationCard citation={FIXTURE} idPrefix="t240-controls" />);
    const btn = screen.getByRole("button", { name: /show quote/i });
    const panelId = btn.getAttribute("aria-controls");
    expect(panelId).toBe("t240-controls-panel");

    fireEvent.click(btn);
    const panel = document.getElementById("t240-controls-panel");
    expect(panel).not.toBeNull();
    expect(panel?.tagName.toLowerCase()).toBe("blockquote");
  });

  it("metadata-only citations omit the toggle button entirely", () => {
    const meta: Citation = { ...FIXTURE, licence_mode: "metadata-only", snippet: undefined };
    render(<CitationCard citation={meta} idPrefix="t240-meta" />);
    expect(screen.queryByRole("button", { name: /show quote/i })).toBeNull();
    expect(screen.getByText(/metadata only/i)).toBeTruthy();
  });
});
