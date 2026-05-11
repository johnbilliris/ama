/**
 * Spec-036 T-I01 — simulation-chat-pane sub-agent + watermark tests.
 *
 * Drives the exposed `__testables.applyEvent` reducer + renders the
 * `SimulationMarkdown` component to verify the `[SIMULATION] ` prefix is
 * surfaced as a red-bold pill (not just plain text).
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import {
  __testables,
} from "@/components/simulation-chat-pane";

describe("simulation-chat-pane sub-agent rendering", () => {
  it("appends a sub_agent.reply event as a new sub_agent message", () => {
    const setMessages = vi.fn();
    __testables.applyEvent(
      "assistant-1",
      {
        // The runtime carries `sub_agent.reply` even though `streamChat`'s
        // typed union doesn't list it yet — apply works via runtime check.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        event: "sub_agent.reply" as any,
        data: {
          thread_id: "thread-weather-1",
          role: "weather",
          reply_markdown: "[SIMULATION] Wind 55 km/h",
          prompt_hash: "abcd1234efgh",
        },
      },
      setMessages,
    );
    expect(setMessages).toHaveBeenCalledTimes(1);
    const reducer = setMessages.mock.calls[0][0] as (prev: unknown[]) => unknown[];
    const next = reducer([]);
    expect(next).toEqual([
      expect.objectContaining({
        id: "thread-weather-1",
        role: "sub_agent",
        subAgentRole: "weather",
        promptHash: "abcd1234efgh",
        content: "[SIMULATION] Wind 55 km/h",
      }),
    ]);
  });

  it("highlights the [SIMULATION] prefix in red bold", () => {
    render(
      <__testables.SimulationMarkdown markdown="[SIMULATION] hazard observed" />,
    );
    const pill = screen.getByTestId("simulation-prefix-emphasis");
    expect(pill).toHaveTextContent("[SIMULATION]");
    expect(pill.className).toContain("text-red-700");
    expect(pill.className).toContain("font-bold");
  });

  it("renders MessageBubble sub_agent role pill and prompt hash badge", () => {
    render(
      <__testables.MessageBubble
        message={{
          id: "thread-1",
          role: "sub_agent",
          content: "[SIMULATION] reply body",
          subAgentRole: "logistics",
          promptHash: "fedcba9876543210",
        }}
      />,
    );
    expect(screen.getByTestId("sub-agent-message")).toBeInTheDocument();
    expect(screen.getByTestId("sub-agent-role-pill")).toHaveTextContent(
      /logistics/i,
    );
    const hash = screen.getByTestId("sub-agent-prompt-hash");
    expect(hash).toHaveTextContent("fedcba98");
    expect(hash.getAttribute("aria-label")).toContain("fedcba9876543210");
  });
});
