/** spec-038 T-AA112 — refusal card with non-judgmental wording. */
const COPY: Record<string, string> = {
  out_of_scope: "I can only help with using the AMA Hub itself. Please contact your support handoff for this question.",
  cross_tenant: "I can't share information that belongs to another tenant. Please raise a cross-tenant request via your governance lead.",
  no_corpus_match: "I couldn't find guidance in the help corpus for that question. Try rephrasing, or contact your support handoff.",
  pii_blocked: "The question contained information our model gateway redacts to protect privacy. Please rephrase without personal identifiers and try again.",
  above_official_classification: "That topic is classified above OFFICIAL and is not available through the help assistant. Contact your governance lead for access via the proper channel.",
  deprecated_no_replacement: "The page you asked about has been withdrawn from the published help corpus and has no replacement. Your support handoff can route you to the correct resource.",
};

export function RefusalCard({ reason }: { reason: string }) {
  const text = COPY[reason] ?? "I'm unable to answer that question right now. Please contact your support handoff.";
  return (
    <aside role="note" aria-label={`Refusal: ${reason}`} className="rounded border border-yellow-400 bg-yellow-50 p-2 text-sm">
      <p>{text}</p>
    </aside>
  );
}
