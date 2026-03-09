"use client";

import { startTransition, useDeferredValue, useState } from "react";

import { publishAlert } from "../../lib/api/alerts";
import { approveRecommendation } from "../../lib/api/recommendations";
import { AlertLanguagePreview } from "./alert-language-preview";

interface PublicAlertComposerProps {
  recommendationId: string;
  alertId: string;
  languages?: string[];
}

export function PublicAlertComposer({ recommendationId, alertId, languages = ["en-AU"] }: PublicAlertComposerProps) {
  const [rationale, setRationale] = useState("Cross-checked against authoritative flood intelligence.");
  const [status, setStatus] = useState("Awaiting commander action");
  const deferredStatus = useDeferredValue(status);

  const contentBlocks = {
    headline: "Prepare to evacuate if directed.",
    body: "Follow emergency services instructions for your area.",
  };

  function handleApproveAndPublish() {
    startTransition(async () => {
      await approveRecommendation(recommendationId, {
        approverPersonaId: "persona-incident-commander",
        outcome: "approved",
        rationale,
      });
      await publishAlert(alertId, "persona-incident-commander");
      setStatus("Approved and published to outbound channels");
    });
  }

  return (
    <section className="alert-composer">
      <h2 className="alert-composer-title">Public alert approval</h2>
      <p className="alert-composer-copy">
        Capture commander rationale before publishing the reviewed community alert.
      </p>

      <AlertLanguagePreview contentBlocks={contentBlocks} languages={languages} />

      <label className="alert-composer-field">
        <span>Approval rationale</span>
        <textarea
          value={rationale}
          onChange={(event: { target: { value: string } }) => setRationale(event.target.value)}
          rows={4}
          className="alert-composer-input"
        />
      </label>
      <button
        type="button"
        onClick={handleApproveAndPublish}
        className="alert-composer-button"
      >
        Approve and publish alert
      </button>
      <p className="alert-composer-status">{deferredStatus}</p>
    </section>
  );
}
