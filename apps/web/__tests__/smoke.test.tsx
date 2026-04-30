/**
 * Sanity Vitest test (spec-032 T904).
 *
 * Verifies the test infrastructure works end-to-end (Vitest + JSDOM +
 * @testing-library/react + @testing-library/jest-dom matchers).
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

describe("apps/web Vitest tier", () => {
  it("renders a span with text", () => {
    render(<span data-testid="t">hello world</span>);
    expect(screen.getByTestId("t")).toHaveTextContent("hello world");
  });

  it("supports basic assertions", () => {
    expect(2 + 2).toBe(4);
  });
});
