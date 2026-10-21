import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { useHelpChatMock } = vi.hoisted(() => ({
  useHelpChatMock: vi.fn(),
}));

vi.mock("@/lib/help/chatStore", () => ({
  useHelpChat: useHelpChatMock,
}));

import { ChatPanel } from "@/components/help/ChatPanel";

const citation = {
  source_id: "cross-border-bushfire-nema",
  source_title: "Cross-border bushfire coordination and NEMA acknowledgement",
  anchor: "the-nema-acknowledgement-step",
  snippet: "The Hub interrupts with the NEMA acknowledgement dialog.",
};

function renderChat(messages: Array<Record<string, unknown>>) {
  useHelpChatMock.mockReturnValue({
    messages,
    input: "",
    isStreaming: false,
    error: null,
    setInput: vi.fn(),
    send: vi.fn(),
    cancel: vi.fn(),
  });
  return render(<ChatPanel persona="operational-default" />);
}

describe("Help chat response rendering", () => {
  beforeEach(() => {
    useHelpChatMock.mockReset();
  });

  it("renders assistant Markdown structure and keeps citations in a Sources list", () => {
    renderChat([
      {
        id: "assistant-1",
        role: "assistant",
        content: "## NEMA acknowledgement\n\nChoose **Hand off to NEMA**.\n\n1. Open the alert.\n2. Select hand off.",
        citations: [citation],
      },
    ]);

    expect(screen.getByRole("heading", { name: "NEMA acknowledgement", level: 2 })).toBeInTheDocument();
    expect(screen.getByText("Hand off to NEMA").tagName).toBe("STRONG");
    expect(screen.getAllByRole("list")[0]).toHaveTextContent("Open the alert.");
    expect(screen.getByRole("region", { name: "Sources" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Citation 1: Cross-border bushfire coordination and NEMA acknowledgement" }))
      .toHaveAttribute(
        "href",
        "/help/articles/cross-border-bushfire-nema#the-nema-acknowledgement-step",
      );
  });

  it("encodes nested article slugs and links the citation to its heading", () => {
    renderChat([
      {
        id: "assistant-2",
        role: "assistant",
        content: "A source without an anchor.",
        citations: [{ ...citation, source_id: "playbooks/agent fire", anchor: "" }],
      },
    ]);

    expect(screen.getByRole("link", { name: /Citation 1:/ })).toHaveAttribute(
      "href",
      "/help/articles/playbooks/agent%20fire",
    );
  });

  it("keeps user-authored Markdown as plain text", () => {
    renderChat([
      {
        id: "user-1",
        role: "user",
        content: "**literal text**\n- not a rendered list",
      },
    ]);

    const log = screen.getByRole("log", { name: "Help chat" });
    expect(log.querySelector(".whitespace-pre-wrap")?.textContent).toBe(
      "**literal text**\n- not a rendered list",
    );
    expect(within(log).queryByRole("list")).toBeNull();
    expect(within(log).queryByText("literal text", { selector: "strong" })).toBeNull();
  });
});
