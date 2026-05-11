# spec-038 — Help Assistant refusal templates (FR-013, FR-014, FR-023).

Use one of the templates below verbatim (with the placeholder fills) when
emitting a refusal. The reason code MUST match the SSE ``refusal`` event.

## out_of_scope
> I can only help with using the AMA Hub itself. For ``{topic_summary}`` you
> should contact your support handoff destination ({support_handoff_label}).

## cross_tenant
> I can't share information that belongs to another tenant. If you need it,
> please raise a cross-tenant request via your governance lead.

## no_corpus_match
> I couldn't find guidance in the help corpus for that question. Try
> rephrasing, or contact your support handoff ({support_handoff_label}).

## pii_blocked
> The question contained information our model gateway redacts to protect
> privacy. Please rephrase without personal identifiers and try again.

## above_official_classification
> That topic is classified above OFFICIAL and is not available through the
> help assistant. Contact your governance lead for access via the proper
> channel.

## deprecated_no_replacement
> The page you asked about has been withdrawn from the published help
> corpus and has no replacement. Your support handoff destination
> ({support_handoff_label}) can route you to the correct resource.

## Output style

- Never apologise more than once.
- Never speculate about what the answer "might be".
- Always end with the support-handoff prompt so the user has a next step.
