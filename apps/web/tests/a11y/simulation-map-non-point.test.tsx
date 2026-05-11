/**
 * Spec-036 T-R08 — accessibility sweep for non-Point map overlays.
 *
 * Verifies that the `SimulationMap`'s accessible summary panel
 * (T-R04 / T-R07 outputs) survives axe-core structural rules:
 *   - non-Point overlay rows are inside an `<ul>` with an
 *     `aria-label` or labelled `<h3>`;
 *   - wind-direction rows expose bearing + speed text without
 *     relying on visual cues alone (so keyboard / SR users still
 *     get the canonical "wind direction has changed" callout);
 *   - the live region is `aria-live="polite"` and not `assertive`
 *     (per WCAG SC 4.1.3 — overlays are informational, not urgent).
 *
 * This is the fast in-vitest gate; the page-level axe sweep lives
 * at `apps/web/tests/a11y/simulation-watermark.spec.ts`.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SimulationMap } from "@/components/simulation-map";
import type { MapOverlayEvent } from "@/lib/sse/map-overlay-events";

vi.mock("next/dynamic", () => ({
  default: () => () => <div data-testid="disaster-map-stub" />,
}));

vi.mock("@ama/ui/components/disaster-map/disaster-map", () => ({
  DisasterMap: () => <div data-testid="disaster-map-stub" />,
}));

const baseProps = {
  tenantId: "tenant-1",
  scenarioType: "bushfire",
  jurisdictions: ["NSW"],
  status: "running" as const,
};

function makePolygonEvent(): MapOverlayEvent {
  return {
    event_type: "map.overlay.created",
    sim_id: "sim-1",
    overlay_id: "over-haz-1",
    sim_badge: "[SIMULATION]",
    visual_modifier: "dashed",
    timestamp: "2026-05-08T00:00:00Z",
    layer_type: "hazard-perimeter",
    geometry: {
      rings: [
        [
          [1, 2],
          [3, 4],
          [5, 6],
          [1, 2],
        ],
      ],
    },
    hazard_class: "bushfire",
    severity: "high",
  };
}

function makeWindEvent(bearing = 270, speed = 42): MapOverlayEvent {
  return {
    event_type: "map.overlay.created",
    sim_id: "sim-1",
    overlay_id: `over-wind-${bearing}`,
    sim_badge: "[SIMULATION]",
    visual_modifier: "dashed",
    timestamp: "2026-05-08T00:00:00Z",
    layer_type: "wind-arrow",
    position: { lng: 151.2, lat: -33.8 },
    bearing_deg: bearing,
    speed_kmh: speed,
  };
}

describe("SimulationMap a11y — non-Point overlays (T-R08)", () => {
  it("non-Point overlay list has accessible label and visible heading", () => {
    render(
      <SimulationMap {...baseProps} overlayEvents={[makePolygonEvent()]} />,
    );
    const list = screen.getByRole("list", {
      name: /non-point geometric overlays/i,
    });
    expect(list).toBeTruthy();
    // Heading provides redundant visible label per WCAG SC 1.3.1.
    expect(
      screen.getByRole("heading", { level: 3, name: /Geometric overlays/i }),
    ).toBeTruthy();
  });

  it("wind-direction list has accessible label and bearing + speed text", () => {
    render(
      <SimulationMap
        {...baseProps}
        overlayEvents={[makeWindEvent(270, 42), makeWindEvent(90, 18)]}
      />,
    );
    const list = screen.getByRole("list", {
      name: /wind direction markers/i,
    });
    expect(list).toBeTruthy();
    // Both wind markers must be exposed as separate list items (SC 1.3.1).
    const items = list.querySelectorAll("li");
    expect(items.length).toBe(2);
    // Bearing + speed text must be visible (not behind aria-hidden).
    expect(items[0].textContent).toContain("Bearing 270°");
    expect(items[0].textContent).toContain("Speed 42 km/h");
  });

  it("uses aria-live='polite' (not 'assertive') for overlay digests", () => {
    render(<SimulationMap {...baseProps} overlayEvents={[makePolygonEvent()]} />);
    const digest = screen.getByTestId("sim-overlay-sr-digest");
    expect(digest.getAttribute("aria-live")).toBe("polite");
    // Per WCAG SC 4.1.3 informational changes use polite, not assertive.
    expect(digest.getAttribute("aria-live")).not.toBe("assertive");
  });

  it("overlay summary section is labelled for navigation by region", () => {
    render(
      <SimulationMap
        {...baseProps}
        overlayEvents={[makePolygonEvent(), makeWindEvent()]}
      />,
    );
    const region = screen.getByRole("region", {
      name: /simulation map overlay summary/i,
    });
    expect(region).toBeTruthy();
  });
});
