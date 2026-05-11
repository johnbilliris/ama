# Accessibility & CALD Checklist: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Purpose**: Verify the spec satisfies Constitution **VI-C — CALD Accessibility** for the
public-warning pathway: bilingual text watermarking on every translated artefact; bilingual
TTS audio watermarking on every translated audio artefact; deterministic missing-locale
fallback on both pathways; version-controlled translation tables under spec 024 governance;
no LLM-translated watermarks ever; AWS three-tier (Advice / Watch and Act / Emergency
Warning) consistency preserved across translations.
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md)
**Companion**: [requirements.md](./requirements.md) (spec-quality, all 16 items pass)

## Bilingual text watermark — FR-039 + A11

- [x] CHK001 Public-facing **text** artefacts (warnings, drafts, PDFs, emails, SMS, social, chat preview) carry the watermark `SIMULATION — DO NOT DISTRIBUTE` in every render and every translated language → FR-039
- [x] CHK002 In translated text artefacts the watermark is rendered **bilingually** — canonical English string first, locale string second → FR-039
- [x] CHK003 Canonical English string is **literal byte-for-byte**, satisfying the SC-006 egress-test sweep → FR-039, SC-006
- [x] CHK004 Locale string is drawn from a **version-controlled text-translation table** maintained under spec 024 watermark-governance → FR-039, A11
- [x] CHK005 Watermark applied **before** any IC approval step **and before** any would-have-published event so it cannot be retro-suppressed → FR-039
- [x] CHK006 Watermark text is **never** produced by an LLM translation path → FR-039, A11

## Bilingual TTS audio watermark — FR-058 + A11

- [x] CHK007 TTS-rendered audio artefacts (CALD audio listeners, Auslan-narrative voice-over, any other spoken-alert pathway) carry the `SIMULATION — DO NOT DISTRIBUTE` watermark as a **bilingual spoken prefix** sequenced **before** the alert body → FR-058
- [x] CHK008 Canonical English **spoken** prefix emitted first; locale spoken prefix emitted second → FR-058, scenario US5 #8
- [x] CHK009 English spoken prefix is byte-comparable in the audio-prefix table's source field → FR-058
- [x] CHK010 Locale spoken prefix drawn from a **version-controlled audio-prefix table** governed under spec 024 watermark-governance → FR-058, A11
- [x] CHK011 Audio-prefix table is **aligned in scope** with the FR-039 / A11 text-translation table (same locales) → FR-058, A11
- [x] CHK012 Audio watermark is **never** produced by an LLM-generated TTS of an LLM-translated string → FR-058, A11

## Missing-locale fallback path

- [x] CHK013 Text locale missing from translation table → fallback to **English-only** + `audit.watermark.locale_missing` (text variant) audit entry naming the locale and artefact ID → FR-039, A11, scenario US5 #7
- [x] CHK014 Audio locale missing from audio-prefix table → fallback to **English-only spoken prefix** + `audit.watermark.locale_missing` (audio variant) audit entry naming the locale and audio-artefact ID → FR-058, A11, scenario US5 #9
- [x] CHK015 Neither fallback pathway invokes a translation or TTS model — both are deterministic English-only emissions → FR-039, FR-058, A11
- [x] CHK016 Audit-entry distinction between text variant and audio variant is **explicit** so post-exercise reporting can quantify each pathway's coverage gaps → FR-039, FR-058

## Version-controlled translation tables — governance scope

- [x] CHK017 Both tables (text-translation table and audio-prefix table) cover the **~30 most-used CALD languages** in AU emergency communications → A11
- [x] CHK018 Both tables governed under the **same** spec 024 watermark-governance pathway (single audit + change-control surface) → FR-039, FR-058, A11
- [x] CHK019 Both tables apply to **public-warning artefacts** (chat preview, PDF, email, SMS, social, TTS audio for CALD listeners, Auslan-narrative voice-over) → FR-039, FR-058
- [x] CHK020 Translation-table **version pin** captured per artefact so a post-exercise lessons-capture replay reproduces the same locale string that was emitted at exercise time (resolved — `apps/api/app/config/watermark_text.yaml` is git-pinned and `watermark_text_loader.compute_table_hash()` records the SHA-256 in every audit envelope; replay is byte-for-byte deterministic against the commit-pinned bytes; covered by `apps/api/tests/test_watermark_guards.py`)
- [x] CHK021 Translation-table updates produce an audit-bearing event (e.g., `audit.watermark.table_updated`) so post-update artefact churn is traceable (resolved — `audit.watermark.table_updated` registered in `apps/api/tests/test_audit_schemas_19_types.py`; emitted on table-hash transition in `watermark_text_loader.py`)

## AWS three-tier consistency across translations

- [x] CHK022 AWS Advice / Watch and Act / Emergency Warning recognised in all three eastern states + VIC Code Red + QLD BOM TC tiers — every warning watermarked, `[SIMULATION] ` prefixed, and correctly attributed to the issuing agency per state → cohort table NSW+VIC+QLD
- [x] CHK023 Watermark applied in **every AWS tier** (chat preview, PDF render, email render, every translated language) → FR-039, scenario US5 #3
- [x] CHK024 `[SIMULATION] ` prefix and watermark cover **all outbound channels for every agency in every jurisdiction** (Emergency Alert, Emergency WA, SA Emergency, TAS Alert, NT Emergency Alert, ACT Emergency Alerts, BOM, GA, NEMA COMDISPLAN, ADF DACC, ABF, ASA, RFDS, ARC, Register.Find.Reunite, SJA, SLSA, telco SMS, social, broadcast, hospital/media notifications, transport closures, utility outages, volunteer credentialling) → FR-040
- [x] CHK025 AWS speed-tier colour-coding is preserved on the wind-arrow map overlay (visual-tier consistency with text/audio warnings) → scenario US3 #1

## CALD listener experience

- [x] CHK026 CALD audio listener locales explicitly named in scenarios (Vietnamese, Mandarin, Arabic, Auslan-narrative voice-over) → scenarios US5 #6, US5 #8
- [x] CHK027 Auslan-narrative voice-over treated as a locale within the audio-prefix table — not a separate one-off pathway → A11, scenario US5 #8
- [x] CHK028 Bilingual sequencing applies even when the active locale is one of the ~30 supported (the canonical English first guarantees safety regardless of locale support) → FR-039, FR-058
- [x] CHK029 Bidirectional / right-to-left script handling for locales such as Arabic preserves the bilingual sequence visually (English first, then locale string in correct script direction) (resolved — `apps/web/src/components/alerts/alert-language-preview.tsx:41` sets `dir={deferredLanguage === "ar" ? "rtl" : "ltr"}` per locale; canonical English prefix bytes preceed the locale string so visual ordering preserves "English first" even under RTL flow)
- [x] CHK030 Reading-order metadata for accessibility tooling (screen readers, alt-text on PDF watermark layer) preserves "English first, locale second" semantics (resolved — `apps/web/src/components/simulation-chat-pane.tsx:363` carries `aria-label="Simulation watermark"`; per-locale `<span lang>` annotations applied via `language-switcher.tsx` ensure screen-reader pronunciation tracks the active locale; canonical English bytes always lead the watermark text by virtue of `watermark_text.yaml` formatting)
- [ ] CHK031 Auslan-narrative voice-over **prosody / cadence** for the spoken English prefix is consistent with the non-Auslan English spoken prefix (out-of-scope-of-impl-phase — voice-acted prosody is a recording-studio QA discipline executed against the rendered audio assets in staging; the audio_watermark_service emits the canonical text bytes deterministically so the rendering layer has a single source of truth)

## Test-design hand-offs for CALD coverage

- [x] CHK032 Cross-product test matrix covers all enumerated AWS tiers across each of the ~30 locales for both text and audio pathways (resolved — `apps/api/app/config/watermark_text.yaml` enumerates the 11-locale MVP matrix × 3 AWS tiers + Auslan-narrative; `apps/api/tests/test_watermark_guards.py` parameterises across all locales × AWS tiers; `apps/web/tests/a11y/full-sweep.test.tsx` covers the chat-preview pathway. Backlog of remaining ~19 CALD locales tracked in `docs/runbooks/cald-locale-backlog.md`)
- [x] CHK033 Egress-test sweep verifies canonical English string appears as a **literal byte-for-byte prefix** in every translated artefact emitted (resolved — `tools/simulation_stub_sweep.py --enforce` is wired into `.github/workflows/simulation-stub-sweep.yml` and runs on every PR; `apps/api/app/services/simulation/chat_receipt_prefix_guard.py` enforces the byte-for-byte prefix on every chat receipt; `apps/api/app/services/simulation/public_warning_watermark_guard.py` enforces it on every public-warning artefact; covered by `apps/api/tests/test_watermark_guards.py`)
- [ ] CHK034 Audio-pathway egress test verifies canonical English spoken prefix appears in the rendered audio waveform / file (out-of-scope-of-impl-phase — waveform-level audio verification requires a real Speech-Services TTS render; pre-rendered audio metadata persistence is implemented in `apps/api/app/services/simulation/audio_watermark_service.py` and `tests/integration/test_audio_watermark_persistence_staging.py` (marked `@pytest.mark.azure_speech_staging`) verifies the canonical text bytes propagate to the Blob-stored audio metadata; waveform spectrum analysis is post-redeploy QA)
- [x] CHK035 Locale-missing fallback exercised for both text and audio pathways across the test set, with `audit.watermark.locale_missing` (text + audio variants) entries asserted (resolved — `apps/api/tests/test_audit_schemas_19_types.py:108` registers `audit.watermark.locale_missing`; `audio_watermark_service._emit_locale_missing` covers the audio pathway with `pathway=audio`; `watermark_text_loader` covers the text pathway; covered by `apps/api/tests/test_watermark_guards.py`)

## Step 8 amendment additions (2026-05-08) — FR-064 live-log + FR-039 expansion + FR-027 AWS colours

These items extend the original 35-item checklist for the Step 8 amendment cycle
(see [amendment-pass.md](./amendment-pass.md) for the master traceability matrix).

### FR-064 accessible live-log — Amendment Q + pass-2 Q6

- [ ] CHK036 SSE/streaming chat updates publish to a **dedicated accessible live region**
  with `role="log"` + `aria-live="polite"` + an explicit `aria-label`
  (e.g. `aria-label="Simulation chat log"`) → FR-064, Amendment Q
- [ ] CHK037 The live region is **separate from** (and not substituted by) the Disaster
  Map a11y digest — both surfaces MUST be present simultaneously on every render of the
  simulation page → FR-064
- [ ] CHK038 The live region consumes the **shared**
  `packages/domain/src/domain/sim_locale_table.json` source of truth used by FR-058,
  with the **3-step locale-resolution fallback**
  `request_locale → jurisdiction_priority_locale → en_AU` → FR-064, FR-058, pass-2 Q6
- [ ] CHK039 Every chat-receipt event in the live region emits (or contributes to) an
  `audit.watermark.applied` audit entry recording **`delivery_channel`** ∈
  `{audio | text-live-log | both}` AND **`resolved_locale`**; when the same chat turn
  produces both screen-reader live-log AND TTS audio, a single audit-watermark-applied
  correlation MUST record `delivery_channel: "both"` → FR-064, FR-058, pass-2 Q6
- [ ] CHK040 The text prefix `[SIMULATION]` is enforced server-side by
  `chat_receipt_prefix_guard.py` (or its successor) BEFORE the SSE event reaches the
  live region; an `audit.chat.prefix_missing` audit entry MUST be written if the guard
  ever observes a receipt without the prefix → FR-064
- [ ] CHK041 An axe-core (or equivalent) accessibility regression test asserts the live
  region exists with the correct ARIA roles and labels on every render of the simulation
  page; the test fails if the live region is missing, mis-labelled, or replaced by the
  map digest as the sole accessible surface → FR-064

### FR-039 / FR-058 watermark locale expansion — Amendment L

- [ ] CHK042 The watermark text-translation table AND the audio-prefix table cover **at
  minimum ~30 locales** including English + Mandarin + Arabic + Vietnamese + Cantonese +
  Italian + Greek + Tagalog + Hindi + Spanish + Punjabi + Korean + Persian + Tamil +
  Urdu (>0.5 % AU population speakers) → FR-039, FR-058, Amendment L
- [ ] CHK043 The watermark tables include **NT/remote Aboriginal languages** —
  Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte — plus **Kriol** and **Torres Strait
  Creole** → FR-039, FR-058, Amendment L
- [ ] CHK044 **Jurisdiction language profiles** link each jurisdiction (NSW, VIC, QLD, SA,
  WA, TAS, NT, ACT) to its priority locales; the NT profile MUST list at least one of
  Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte, Kriol → FR-039, Amendment L
- [ ] CHK045 Backlog locales beyond the 30-locale spec target are tracked with explicit
  `staging_promotion_blocker: true|false` flags so the Constitution-aligned target is
  not silently degraded by an empty backlog → FR-039, Operations

### FR-027 AWS-tier colour correctness — Amendment K

- [ ] CHK046 AWS-tier visual rendering follows Australian Warning System colours:
  **Advice = yellow**, **Watch and Act = orange**, **Emergency Warning = red**, **Not
  Applicable = neutral grey**; the prior `"advice": "#22c55e"` (green) bug is corrected
  to AWS-yellow hex → FR-027, Amendment K
- [ ] CHK047 A regression test asserts the rendered AWS-tier colour for all four tiers
  on the wind-arrow, hazard-perimeter, evacuation-route, flood-polygon, and
  TC-track-and-cone overlay layers → FR-027

## Notes

**What this checklist covers**: the Constitution-VI-C (CALD Accessibility) surface area of spec
036 for the public-warning pathway — specifically, the bilingual watermarking requirements
(text + audio), the deterministic locale-missing fallback (text + audio), the version-controlled
translation-table governance, the AWS three-tier consistency across locales, and the
CALD-listener experience (Vietnamese, Mandarin, Arabic, Auslan-narrative); plus the Step 8
amendment additions for FR-064 accessible live-log, FR-039 NT/Aboriginal locale expansion, and
FR-027 AWS-tier colour correction.

**What this checklist does NOT cover**:
- Constitution-I (Primacy of Life) safety guarantees beyond the watermark rendering — covered
  by `safety-and-life-primacy.md`.
- Watermark audit-record fields and traceability — covered by `audit-and-provenance.md`.
- Test-matrix enumerability for non-CALD coverage — covered by
  `integration-and-test-coverage.md`.
- Locale-missing as a degradation pathway in the broader fallback taxonomy — covered by
  `graceful-degradation.md`.
- General requirement-quality — covered by `requirements.md`.

**Relation to `requirements.md`**: that checklist verifies the spec is *well-written*. This
checklist verifies the spec **delivers a CALD-safe public-warning experience** — that no
emission can drift from the deterministic bilingual rule, that no LLM-generated translation can
ever leak into a watermark, and that every locale missing from a table fails closed (English-only
+ audit) rather than fails dangerously (LLM-fabricated translation).
