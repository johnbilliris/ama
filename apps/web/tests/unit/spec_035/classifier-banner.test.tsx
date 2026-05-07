/**
 * Vitest unit test for the classifier-mask banner (T035).
 */

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import {
  ClassifierBanner,
  type ClassifierOutcome,
} from "../../../src/lib/classifier/banner";

describe("ClassifierBanner (T035)", () => {
  it("renders mask-count and audit-id link when outcome=classifier_mask", () => {
    render(
      <ClassifierBanner
        outcome="classifier_mask"
        maskedFieldCount={3}
        auditId="aud-12345"
      />,
    );
    expect(screen.getByTestId("classifier-mask-banner")).toBeInTheDocument();
    expect(screen.getByTestId("classifier-mask-count").textContent).toContain(
      "3 fields",
    );
    const link = screen.getByTestId(
      "classifier-mask-audit-link",
    ) as HTMLAnchorElement;
    expect(link.getAttribute("href")).toBe("/governance/audit/aud-12345");
  });

  it("singular masked-field copy when count=1", () => {
    render(
      <ClassifierBanner
        outcome="classifier_mask"
        maskedFieldCount={1}
        auditId="aud-1"
      />,
    );
    expect(screen.getByTestId("classifier-mask-count").textContent).toContain(
      "1 field",
    );
    expect(
      screen.getByTestId("classifier-mask-count").textContent,
    ).not.toContain("1 fields");
  });

  it.each<ClassifierOutcome>(["clean", "classifier_deny", "classifier_failed"])(
    "is suppressed when outcome=%s",
    (outcome) => {
      const { container } = render(
        <ClassifierBanner
          outcome={outcome}
          maskedFieldCount={9}
          auditId="aud-not-shown"
        />,
      );
      expect(container.firstChild).toBeNull();
    },
  );
});
