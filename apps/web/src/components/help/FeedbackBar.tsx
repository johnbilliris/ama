"use client";
/** spec-038 T-AA113 — feedback bar (helpful / not helpful). */
import { useState } from "react";

export interface FeedbackBarProps {
  targetKind: "article" | "chat_turn";
  targetId: string;
}

export function FeedbackBar({ targetKind, targetId }: FeedbackBarProps) {
  const [submitted, setSubmitted] = useState<null | "helpful" | "not_helpful">(null);

  async function submit(rating: "helpful" | "not_helpful", comment?: string) {
    try {
      await fetch("/api/help/chat/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_kind: targetKind, target_id: targetId, rating, comment }),
      });
      setSubmitted(rating);
    } catch {
      setSubmitted(null);
    }
  }

  if (submitted) {
    return <p role="status" className="text-xs text-gray-600">Thanks — your feedback was recorded.</p>;
  }

  return (
    <div role="group" aria-label="Was this helpful?" className="mt-2 flex gap-2 text-xs">
      <span>Was this helpful?</span>
      <button type="button" onClick={() => submit("helpful")} aria-label="Mark helpful">👍</button>
      <button type="button" onClick={() => submit("not_helpful")} aria-label="Mark not helpful">👎</button>
    </div>
  );
}
