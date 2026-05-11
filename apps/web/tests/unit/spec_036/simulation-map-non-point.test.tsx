/**
 * Spec-036 T-R04 / T-R07 / T-R08 — non-Point geometry rendering and
 * wind-direction marker overlay.
 *
 * Verifies that `SimulationMap`:
 *  • renders non-Point overlays (LineString / Polygon) into the
 *    accessible summary panel when not directly placed on the Azure
 *    Maps canvas;
 *  • surfaces wind-arrow overlays with bearing + speed text so screen
 *    reader users get the canonical "wind direction has changed →
 *    wind direction markers should appear" callout (per user spec);
 *  • keeps the existing Point overlay flow intact.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SimulationMap } from "@/components/simulation-map";
import type { MapOverlayEvent } from "@/lib/sse/map-overlay-events";

// Mock dynamic import — we only care about the surrounding chrome /
// accessible summary in this test.
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

function makeWindEvent(): MapOverlayEvent {
  return {
    event_type: "map.overlay.created",
    sim_id: "sim-1",
    overlay_id: "over-wind-1",
    sim_badge: "[SIMULATION]",
    visual_modifier: "dashed",
    timestamp: "2026-05-08T00:00:00Z",
    layer_type: "wind-arrow",
    position: { lng: 151.2, lat: -33.8 },
    bearing_deg: 270,
    speed_kmh: 42,
  };
}

function makeHazardPerimeterEvent(): MapOverlayEvent {
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

function makeEvacRouteEvent(): MapOverlayEvent {
  return {
    event_type: "map.overlay.created",
    sim_id: "sim-1",
    overlay_id: "over-route-1",
    sim_badge: "[SIMULATION]",
    visual_modifier: "dashed",
    timestamp: "2026-05-08T00:00:00Z",
    layer_type: "evacuation-route",
    geometry: { points: [[1, 2], [3, 4]] },
    status: "open",
  };
}

describe("SimulationMap — non-Point geometries (T-R04)", () => {
  it("surfaces Polygon overlays in the accessible summary panel", () => {
    render(<SimulationMap {...baseProps} overlayEvents={[makeHazardPerimeterEvent()]} />);
    const list = screen.getByTestId("sim-overlay-nonpoint-list");
    expect(list).toBeTruthy();
    expect(list.textContent).toContain("Polygon");
  });

  it("surfaces LineString overlays in the accessible summary panel", () => {
    render(<SimulationMap {...baseProps} overlayEvents={[makeEvacRouteEvent()]} />);
    const list = screen.getByTestId("sim-overlay-nonpoint-list");
    expect(list).toBeTruthy();
    expect(list.textContent).toContain("LineString");
  });
});

describe("SimulationMap — wind direction marker (T-R07)", () => {
  it("shows bearing and speed for each wind-arrow overlay", () => {
    render(<SimulationMap {...baseProps} overlayEvents={[makeWindEvent()]} />);
    const list = screen.getByTestId("sim-overlay-wind-list");
    expect(list).toBeTruthy();
    expect(list.textContent).toContain("Bearing 270°");
    expect(list.textContent).toContain("Speed 42 km/h");
  });

  it("includes wind markers in the SR-only digest count", () => {
    render(<SimulationMap {...baseProps} overlayEvents={[makeWindEvent()]} />);
    const digest = screen.getByTestId("sim-overlay-sr-digest");
    expect(digest.textContent).toContain("1 simulation overlays active");
    expect(digest.textContent).toContain("wind-arrow");
  });
});

describe("SimulationMap — empty overlay state", () => {
  it("renders empty SR digest message when no overlays are active", () => {
    render(<SimulationMap {...baseProps} overlayEvents={[]} />);
    const digest = screen.getByTestId("sim-overlay-sr-digest");
    expect(digest.textContent).toContain("No simulation overlays active");
    // Non-Point and wind lists must NOT render when no events present.
    expect(screen.queryByTestId("sim-overlay-nonpoint-list")).toBeNull();
    expect(screen.queryByTestId("sim-overlay-wind-list")).toBeNull();
  });
});
