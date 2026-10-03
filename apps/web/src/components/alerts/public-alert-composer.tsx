"use client";

import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

import {
  approveAlertDraft,
  deliverAlert,
  getAlertDraft,
  publishAlert,
  updateAlertDraft,
  usesCommunicationAgent,
  type AlertDeliveryReceipt,
} from "../../lib/api/alerts";
import { approveRecommendation } from "../../lib/api/recommendations";
import { AlertLanguagePreview } from "./alert-language-preview";
import { useI18n } from "../../lib/i18n/runtime";

interface PublicAlertComposerProps {
  recommendationId: string;
  alertId: string;
  languages?: string[];
  actorPersonaId?: string | null;
  onWorkflowComplete?: () => void;
}

export function PublicAlertComposer({
  recommendationId,
  alertId,
  languages = ["en-AU"],
  actorPersonaId,
  onWorkflowComplete,
}: PublicAlertComposerProps) {
  const { t } = useI18n();
  const [rationale, setRationale] = useState("Cross-checked against authoritative flood intelligence.");
  const [status, setStatus] = useState("Awaiting commander action");
  const [persistedContentBlocks, setPersistedContentBlocks] = useState<Record<string, string>>({});
  const [headline, setHeadline] = useState("");
  const [body, setBody] = useState("");
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(languages);
  const [selectedChannels, setSelectedChannels] = useState<string[]>(["sms", "push"]);
  const [audienceSegments, setAudienceSegments] = useState<string[]>(["affected-community"]);
  const [loaded, setLoaded] = useState(false);
  const [activeAlertId, setActiveAlertId] = useState(alertId);
  const [draftStatus, setDraftStatus] = useState("unknown");
  const [safetyStatus, setSafetyStatus] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);
  const deferredStatus = useDeferredValue(status);

  useEffect(() => {
    let cancelled = false;
    getAlertDraft(activeAlertId)
      .then((draft) => {
        if (cancelled) return;
        setHeadline(String(draft.content_blocks.headline ?? ""));
        setBody(String(draft.content_blocks.body ?? ""));
        setPersistedContentBlocks(draft.content_blocks);
        setSelectedLanguages(draft.languages.length > 0 ? draft.languages : languages);
        setSelectedChannels(draft.channel_set.length > 0 ? draft.channel_set : ["sms", "push"]);
        setAudienceSegments(draft.audience_segments.length > 0 ? draft.audience_segments : ["affected-community"]);
        setDraftStatus(draft.status);
        setSafetyStatus(draft.content_safety_result);
        setLoaded(true);
      })
      .catch(() => {
        if (cancelled) return;
        setError(t("alerts.loadedDraftFailed"));
      });

    return () => {
      cancelled = true;
    };
  }, [activeAlertId, languages, t]);

  const contentBlocks = useMemo(
    () => ({
      ...persistedContentBlocks,
      headline,
      body,
    }),
    [body, headline, persistedContentBlocks],
  );

  function handleApproveAndPublish() {
    startTransition(async () => {
      try {
        setError(null);
        const prepared = await updateAlertDraft(activeAlertId, {
          contentBlocks,
          audienceSegments,
          languages: selectedLanguages,
          channelSet: selectedChannels,
        });
        setActiveAlertId(prepared.alert_id);
        if (usesCommunicationAgent()) {
          await approveAlertDraft(prepared.alert_id, actorPersonaId || "", rationale);
        } else {
          await approveRecommendation(recommendationId, {
            approverPersonaId: actorPersonaId || "",
            outcome: "approved",
            rationale,
          });
          await publishAlert(prepared.alert_id, actorPersonaId || "");
        }
        const receipts = await deliverAlert(prepared.alert_id);
        const acknowledged = receipts.filter(
          (receipt: AlertDeliveryReceipt) => receipt.status === "acknowledged",
        );
        if (acknowledged.length > 0) {
          setStatus(`Approved and delivered (${acknowledged.length} acknowledged receipt(s))`);
        } else {
          setStatus("Published, but no channel acknowledged delivery");
        }
        onWorkflowComplete?.();
      } catch {
        setError(t("alerts.workflowFailed"));
      }
    });
  }

  if (!loaded && !error) {
    return <section className="alert-composer">{t("common.loading")}</section>;
  }

  return (
    <section className="alert-composer">
      <h2 className="alert-composer-title">{t("alerts.approvalTitle")}</h2>
      <p className="alert-composer-copy">
        {t("alerts.approvalCopy")}
      </p>

      <AlertLanguagePreview contentBlocks={contentBlocks} languages={selectedLanguages} />

      <dl className="alert-composer-summary">
        <dt>Status</dt>
        <dd>{draftStatus}</dd>
        <dt>Safety</dt>
        <dd>{safetyStatus ?? "Not reported"}</dd>
        <dt>Audience</dt>
        <dd>{audienceSegments.join(", ")}</dd>
        <dt>Channels</dt>
        <dd>{selectedChannels.join(", ")}</dd>
      </dl>

      <label className="alert-composer-field">
        <span>Headline</span>
        <input
          value={headline}
          onChange={(event: { target: { value: string } }) => setHeadline(event.target.value)}
          className="alert-composer-input"
        />
      </label>
      <label className="alert-composer-field">
        <span>Body</span>
        <textarea
          value={body}
          onChange={(event: { target: { value: string } }) => setBody(event.target.value)}
          rows={4}
          className="alert-composer-input"
        />
      </label>

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
        disabled={!actorPersonaId || !headline || !body || selectedLanguages.length === 0 || selectedChannels.length === 0}
        className="alert-composer-button"
      >
        Approve and publish alert
      </button>
      <p className="alert-composer-status">{deferredStatus}</p>
      {!actorPersonaId ? <p className="alert-composer-status">Approval actor is not available in this session.</p> : null}
      {error ? <p className="alert-composer-status">{error}</p> : null}
    </section>
  );
}
