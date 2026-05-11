/**
 * Spec-036 T-I03 — unit tests for the injection cards.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { InjectionConfirmCard } from "@/components/InjectionConfirmCard";
import { InjectionRefusalCard } from "@/components/InjectionRefusalCard";

describe("InjectionConfirmCard", () => {
  const baseProps = {
    signalId: "sig-1234",
    hazardClass: "bushfire",
    jurisdiction: "nsw",
    severity: "high" as const,
    routedTo: "fire-agency",
    auditEntryId: "audit-abcd",
    acceptedAt: "2026-05-08T05:00:00Z",
  };

  it("renders the signal, hazard, jurisdiction and routing", () => {
    render(<InjectionConfirmCard {...baseProps} />);
    expect(screen.getByTestId("injection-confirm-card")).toHaveTextContent(
      "sig-1234",
    );
    expect(screen.getByText("[SIMULATION]")).toBeInTheDocument();
    expect(screen.getByText(/bushfire/)).toBeInTheDocument();
    expect(screen.getByText(/NSW/)).toBeInTheDocument();
    expect(screen.getByText(/fire-agency/)).toBeInTheDocument();
  });

  it("calls onOpenAudit with the audit id when the button is clicked", () => {
    const handler = vi.fn();
    render(<InjectionConfirmCard {...baseProps} onOpenAudit={handler} />);
    fireEvent.click(
      screen.getByRole("button", { name: /open audit envelope audit-abcd/i }),
    );
    expect(handler).toHaveBeenCalledWith("audit-abcd");
  });
});

describe("InjectionRefusalCard", () => {
  const problem = {
    type: "https://platform/problems/injection-refused",
    title: "Synthetic signal refused",
    status: 403,
    detail: "Severity 'extreme' requires Strategic-Commander approval.",
    audit_entry_id: "audit-deny-1",
    correlation_id: "cid-9",
  };

  it("renders RFC 7807 fields with role=alert", () => {
    render(<InjectionRefusalCard problem={problem} />);
    const card = screen.getByTestId("injection-refusal-card");
    expect(card.getAttribute("role")).toBe("alert");
    expect(screen.getByTestId("refusal-code")).toHaveTextContent(
      "injection-refused",
    );
    expect(screen.getByText(/HTTP 403/)).toBeInTheDocument();
    expect(screen.getByText(problem.title)).toBeInTheDocument();
    expect(screen.getByText(/Severity 'extreme'/)).toBeInTheDocument();
  });

  it("invokes onOpenAudit with the audit id from the problem", () => {
    const handler = vi.fn();
    render(<InjectionRefusalCard problem={problem} onOpenAudit={handler} />);
    fireEvent.click(
      screen.getByRole("button", { name: /open audit envelope audit-deny-1/i }),
    );
    expect(handler).toHaveBeenCalledWith("audit-deny-1");
  });

  it("invokes onRetry when retry is clicked", () => {
    const onRetry = vi.fn();
    render(<InjectionRefusalCard problem={problem} onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
