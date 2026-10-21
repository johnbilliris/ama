import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import {
  InfrastructureOverlay,
  LAYERS,
} from "../../../src/components/infrastructure-overlay";
import {
  ClaimsVelocityDashboard,
  type ClaimsVelocitySnapshot,
} from "../../../src/components/claims-velocity";
import {
  CulturalSafetyPanel,
} from "../../../src/components/cultural-safety";

describe("infrastructure overlay (T051)", () => {
  it("renders four distinguishable layers", () => {
    render(<InfrastructureOverlay />);
    expect(LAYERS).toHaveLength(4);
    LAYERS.forEach((l) => {
      expect(screen.getByTestId(`overlay-toggle-${l.kind}`)).toBeTruthy();
    });
  });

  it("toggles a layer on click", () => {
    let captured: string[] = [];
    render(
      <InfrastructureOverlay
        onChange={(enabled) => {
          captured = enabled;
        }}
      />,
    );
    fireEvent.click(screen.getByTestId("overlay-toggle-iron_ore_haul_road"));
    expect(captured).toContain("iron_ore_haul_road");
  });
});

describe("claims-velocity dashboard (T052)", () => {
  const snapshot: ClaimsVelocitySnapshot = {
    as_at: "2025-03-01T00:00:00Z",
    claims_lodged: 1000,
    claims_closed: 250,
    dollars_lodged: 50_000_000,
    dollars_paid: 12_500_000,
    lga_breakdown: [
      {
        lga_code: "13800",
        lga_name: "Lismore",
        claims_lodged: 500,
        claims_closed: 100,
        dollars_lodged: 25_000_000,
        dollars_paid: 6_000_000,
      },
      {
        lga_code: "10810",
        lga_name: "Ballina",
        claims_lodged: 500,
        claims_closed: 150,
        dollars_lodged: 25_000_000,
        dollars_paid: 6_500_000,
      },
    ],
  };

  it("renders the dashboard with both LGAs", () => {
    render(<ClaimsVelocityDashboard snapshot={snapshot} />);
    expect(screen.getByText("Lismore")).toBeTruthy();
    expect(screen.getByText("Ballina")).toBeTruthy();
  });

  it("re-sorts when a column header is clicked", () => {
    render(<ClaimsVelocityDashboard snapshot={snapshot} />);
    const closedHeader = screen.getByRole("button", { name: /Closed/ });
    fireEvent.click(closedHeader);
    fireEvent.click(closedHeader);
    const sortableHeader = closedHeader.closest("th");
    expect(sortableHeader).not.toBeNull();
    expect(sortableHeader?.getAttribute("aria-sort")).toMatch(/ascending|descending/);
  });
});

describe("cultural safety panel (T050)", () => {
  it("offers community-language pickers and routing controls", () => {
    render(
      <CulturalSafetyPanel
        jurisdiction="WA"
        variants={[]}
        state="pending_elder"
        awsLevel="advice"
      />,
    );
    expect(screen.getByTestId("cultural-safety-panel")).toBeTruthy();
    expect(screen.getByTestId("cultural-safety-language-select")).toBeTruthy();
    expect(screen.getByTestId("cultural-safety-elder-route")).toBeTruthy();
  });

  it("only surfaces IC override on emergency_warning timeout", () => {
    const { rerender } = render(
      <CulturalSafetyPanel
        jurisdiction="WA"
        variants={[]}
        state="timeout_lifesafety_override"
        awsLevel="watch_and_act"
      />,
    );
    expect(screen.queryByTestId("cultural-safety-ic-override")).toBeNull();
    rerender(
      <CulturalSafetyPanel
        jurisdiction="WA"
        variants={[]}
        state="timeout_lifesafety_override"
        awsLevel="emergency_warning"
      />,
    );
    expect(screen.getByTestId("cultural-safety-ic-override")).toBeTruthy();
  });
});
