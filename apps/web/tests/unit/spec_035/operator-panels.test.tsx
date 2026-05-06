import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import IcApprovalCard from "../../../src/app/workspaces/[personaId]/_panels/ic-approval-card";
import ObserverAuditorTimeline from "../../../src/app/workspaces/[personaId]/_panels/observer-auditor-timeline";
import SpanOfControlWarning from "../../../src/app/workspaces/[personaId]/_panels/span-of-control-warning";
import PlanningIapComposer from "../../../src/app/workspaces/[personaId]/_panels/planning-iap-composer";
import PioAwsComposer from "../../../src/app/workspaces/[personaId]/_panels/pio-aws-composer";
import RiskMatrix from "../../../src/app/workspaces/[personaId]/_panels/risk-matrix";
import ResilienceHandoverPdf from "../../../src/app/workspaces/[personaId]/_panels/resilience-handover-pdf";
import FieldCoordinatorOffline from "../../../src/app/workspaces/[personaId]/_panels/field-coordinator-offline";

describe("operator panels (T036–T044) smoke", () => {
  it("renders IC approval card with confidence pill", () => {
    render(
      <IcApprovalCard
        scenarioId="42"
        rationale="Forward command post viable."
        sources={[]}
        confidence={0.9}
        approverIdentity="ic@example"
      />,
    );
    expect(screen.getByTestId("ic-approval-card")).toBeTruthy();
    expect(screen.getByText(/confidence 90%/i)).toBeTruthy();
  });

  it("renders observer/auditor timeline as append-only", () => {
    render(
      <ObserverAuditorTimeline
        rows={[
          {
            audit_id: "a-1",
            outcome: "approved",
            timestamp: "2025-01-01T00:00:00Z",
            actor: "ic@example",
            rationale: "test",
          },
        ]}
      />,
    );
    expect(screen.getByTestId("observer-auditor-timeline")).toBeTruthy();
    expect(screen.getByText(/append-only/i)).toBeTruthy();
  });

  it("suppresses span-of-control warning for planning officer", () => {
    const reports = Array.from({ length: 9 }, (_, i) => ({
      id: `r-${i}`,
      name: `Report ${i}`,
    }));
    const { container } = render(
      <SpanOfControlWarning appRole="planning-officer" directReports={reports} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("shows span-of-control warning for IC over threshold", () => {
    const reports = Array.from({ length: 9 }, (_, i) => ({
      id: `r-${i}`,
      name: `Report ${i}`,
    }));
    render(
      <SpanOfControlWarning appRole="incident-commander" directReports={reports} />,
    );
    expect(screen.getByTestId("span-of-control-warning")).toBeTruthy();
  });

  it("renders other panels without throwing", () => {
    render(<PlanningIapComposer scenarioId="1" />);
    render(<PioAwsComposer />);
    render(<RiskMatrix scenarioId="1" />);
    render(
      <ResilienceHandoverPdf payloadFactory={() => ({ scenario_id: "1" })} />,
    );
    render(<FieldCoordinatorOffline />);
    expect(screen.getByTestId("planning-iap-composer")).toBeTruthy();
    expect(screen.getByTestId("pio-aws-composer")).toBeTruthy();
    expect(screen.getByTestId("risk-matrix")).toBeTruthy();
    expect(screen.getByTestId("resilience-handover-pdf")).toBeTruthy();
    expect(screen.getByTestId("field-coordinator-offline")).toBeTruthy();
  });
});
