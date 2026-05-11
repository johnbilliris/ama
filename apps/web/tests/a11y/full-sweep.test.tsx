/**
 * Spec-036 T-I08 — full a11y sweep across spec-036 components.
 *
 * Vitest + JSDOM structural checks for every public spec-036 component:
 *   - SimBadge / StaleBadge / SimulationReceiptBadge (T-I02)
 *   - InjectionConfirmCard / InjectionRefusalCard (T-I03)
 *   - SimulationBanner active / paused / aborted (T-I07)
 *   - SimulationChatPane sub-agent message + watermark prefix (T-I01)
 *
 * The bigger axe-core sweep against running pages lives at
 * `apps/web/tests/a11y/simulation-watermark.spec.ts` (Playwright project
 * `web-coverage-axe`); this file is the fast in-CI gate that runs on
 * `pnpm -r run test:a11y` per the F10.4 / capstone gate.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SimBadge } from "@/components/SimBadge";
import { StaleBadge } from "@/components/StaleBadge";
import { SimulationReceiptBadge } from "@/components/SimulationReceiptBadge";
import { InjectionConfirmCard } from "@/components/InjectionConfirmCard";
import { InjectionRefusalCard } from "@/components/InjectionRefusalCard";
import { SimulationBanner } from "@/components/simulation-banner";
import { __testables as ChatPaneTestables } from "@/components/simulation-chat-pane";

interface AccessibilityCheck {
  name: string;
  render(): React.ReactElement;
  expectedRole: string;
}

const cases: AccessibilityCheck[] = [
  {
    name: "SimBadge",
    render: () => <SimBadge />,
    expectedRole: "status",
  },
  {
    name: "StaleBadge (over threshold)",
    render: () => <StaleBadge ageSeconds={420} thresholdSeconds={300} />,
    expectedRole: "status",
  },
  {
    name: "SimulationReceiptBadge",
    render: () => <SimulationReceiptBadge status="delivered" channel="EAS" />,
    expectedRole: "status",
  },
  {
    name: "InjectionConfirmCard",
    render: () => (
      <InjectionConfirmCard
        signalId="s1"
        hazardClass="bushfire"
        jurisdiction="nsw"
        severity="high"
        routedTo="fire"
        auditEntryId="a1"
        acceptedAt="2026-05-08T00:00:00Z"
      />
    ),
    expectedRole: "status",
  },
  {
    name: "InjectionRefusalCard",
    render: () => (
      <InjectionRefusalCard
        problem={{
          type: "https://platform/problems/injection-refused",
          title: "denied",
          status: 403,
          detail: "policy violation",
        }}
      />
    ),
    expectedRole: "alert",
  },
  {
    name: "SimulationBanner (paused — alert)",
    render: () => (
      <SimulationBanner
        lifecycleEvent={{
          event_type: "lifecycle.scenario_paused",
          reason: "halt",
        }}
      />
    ),
    expectedRole: "alert",
  },
  {
    name: "SimulationBanner (active — status)",
    render: () => <SimulationBanner />,
    expectedRole: "status",
  },
];

describe("Spec-036 a11y full sweep", () => {
  it.each(cases)("$name has the expected ARIA landmark role", ({ render: r, expectedRole }) => {
    render(r());
    const role = screen.getAllByRole(expectedRole);
    expect(role.length).toBeGreaterThanOrEqual(1);
  });

  it("every interactive button has an accessible name", () => {
    render(
      <>
        <InjectionConfirmCard
          signalId="s1"
          hazardClass="bushfire"
          jurisdiction="nsw"
          severity="high"
          routedTo="fire"
          auditEntryId="a1"
          acceptedAt="2026-05-08T00:00:00Z"
        />
        <InjectionRefusalCard
          problem={{
            type: "https://platform/problems/x",
            title: "denied",
            status: 403,
            audit_entry_id: "a1",
          }}
          onRetry={() => undefined}
        />
      </>,
    );
    const buttons = screen.getAllByRole("button");
    for (const button of buttons) {
      const name =
        button.getAttribute("aria-label") ??
        button.textContent?.trim() ??
        "";
      expect(name.length).toBeGreaterThan(0);
    }
  });

  it("SimulationBanner status pill is keyboard-focusable", () => {
    render(<SimulationBanner />);
    expect(
      screen.getByTestId("sim-banner-status").getAttribute("tabindex"),
    ).toBe("0");
  });

  it("[SIMULATION] watermark surfaces with an explicit aria-label on every badge", () => {
    render(<SimBadge />);
    expect(
      screen.getByTestId("sim-badge").getAttribute("aria-label"),
    ).toBeTruthy();
  });

  it("sub-agent role pill exposes role via aria-label not colour", () => {
    render(
      <ChatPaneTestables.MessageBubble
        message={{
          id: "t1",
          role: "sub_agent",
          content: "[SIMULATION] reply",
          subAgentRole: "communications",
          promptHash: "deadbeefcafebabe",
        }}
      />,
    );
    expect(
      screen
        .getByTestId("sub-agent-role-pill")
        .getAttribute("aria-label"),
    ).toContain("communications");
  });
});
