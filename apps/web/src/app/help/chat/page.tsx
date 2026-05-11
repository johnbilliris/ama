"use client";
/** spec-038 T-AA102 — full-page help chat. */
import { ChatPanel } from "@/components/help/ChatPanel";

export default function HelpChatPage() {
  return (
    <div className="mx-auto h-screen max-w-3xl">
      <h1 className="p-3 text-xl font-semibold">Help chat</h1>
      <ChatPanel persona="operational-default" />
    </div>
  );
}
