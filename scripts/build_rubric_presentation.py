"""
Builds the AMA Rubric-Aligned Capstone presentation for the
Autonomous Disaster Response Agent Coordination Hub.

Each slide maps 1:1 to a criterion from `AMA_Rubric_Asia.md` (12 criteria),
articulated to the **Excellent (5 pts)** standard, with talking points in the
presenter notes. Title, hook, agenda, scoring summary and closing slides
bracket the rubric body for executive flow.

Usage:
    python scripts/build_rubric_presentation.py

Visual design guide:
    docs/ama-presentation/Azure Master Architect_Template.potm
The .potm is converted to a transient .pptx in-memory (content-type swap)
so python-pptx can inherit the masters, layouts, theme and colour palette.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "ama-presentation" / "Azure Master Architect_Template.potm"
OUTPUT = ROOT / "docs" / "ama-presentation" / "AMA_Rubric_Aligned_Presentation.pptx"
ARCH = ROOT / "docs" / "architecture"

# Layout indexes (verified against the .potm masters)
L_TITLE = 0
L_TITLE_ONLY = 1
L_AGENDA = 2
L_3COLS = 4
L_RIGHT_CONTENT = 6
L_CONTENT_IMG = 9
L_CLOSING = 12

# Placeholder index maps
PH_TITLE = 0
PH_BODY = 10
PH_3COL_HEAD = (27, 28, 29)
PH_3COL_BODY = (10, 11, 26)
PH_AGENDA_ITEMS = (10, 11, 12, 13, 14, 15, 16, 17)


# ---------------------------------------------------------------------------
# Template loader (.potm -> in-memory .pptx)
# ---------------------------------------------------------------------------

def load_template_as_pptx(potm_path: Path) -> Presentation:
    """Strip the macro-enabled content type so python-pptx accepts the file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(potm_path, "r") as zin:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    data = data.replace(
                        b"application/vnd.ms-powerpoint.template.macroEnabled.main+xml",
                        b"application/vnd.openxmlformats-officedocument."
                        b"presentationml.presentation.main+xml",
                    )
                zout.writestr(item, data)
    buf.seek(0)
    return Presentation(buf)


def reset_slides(prs: Presentation) -> None:
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        rId = sldId.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        sldIdLst.remove(sldId)
        if rId:
            prs.part.drop_rel(rId)


# ---------------------------------------------------------------------------
# Slide helpers
# ---------------------------------------------------------------------------

def add_slide(prs: Presentation, layout_idx: int):
    return prs.slides.add_slide(prs.slide_layouts[layout_idx])


def find_ph(slide, idx: int):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == idx:
            return ph
    return None


def set_text(ph, text: str) -> None:
    if ph is None or text is None:
        return
    tf = ph.text_frame
    tf.clear()
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.add_run().text = line


def set_title(slide, text: str) -> None:
    ph = find_ph(slide, PH_TITLE) or slide.shapes.title
    set_text(ph, text)


def set_notes(slide, notes: str) -> None:
    tf = slide.notes_slide.notes_text_frame
    tf.clear()
    for i, line in enumerate(notes.strip().split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.add_run().text = line


def add_image(slide, path: Path, *, left=Inches(1.2), top=Inches(1.4),
              width=Inches(10.9), height=Inches(5.4)) -> None:
    if not path.exists():
        tb = slide.shapes.add_textbox(left, top, width, height)
        tb.text_frame.text = f"[diagram placeholder: {path.name} not found]"
        return
    slide.shapes.add_picture(str(path), left, top, width=width, height=height)


def add_caption(slide, text: str, *, left=Inches(1.2), top=Inches(6.85),
                width=Inches(10.9), height=Inches(0.45)) -> None:
    tb = slide.shapes.add_textbox(left, top, width, height)
    p = tb.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(10)
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def add_rubric_badge(slide, criterion: str, score: str = "Excellent · 5 / 5") -> None:
    """Top-right pill labelling the rubric criterion the slide answers."""
    tb = slide.shapes.add_textbox(Inches(8.6), Inches(0.25), Inches(4.6), Inches(0.55))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.alignment = 2  # right
    r1 = p.add_run()
    r1.text = f"{criterion}   "
    r1.font.size = Pt(11)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    r2 = p.add_run()
    r2.text = score
    r2.font.size = Pt(11)
    r2.font.color.rgb = RGBColor(0x00, 0x99, 0x55)


# ---------------------------------------------------------------------------
# Deck content
# ---------------------------------------------------------------------------

def build(prs: Presentation) -> None:

    # =====================================================================
    # 1 — TITLE
    # =====================================================================
    s = add_slide(prs, L_TITLE)
    set_title(
        s,
        "Autonomous Disaster Response\nAgent Coordination Hub",
    )
    sub = s.shapes.add_textbox(Inches(0.6), Inches(5.2), Inches(12.1), Inches(0.6))
    r = sub.text_frame.paragraphs[0].add_run()
    r.text = ("AIIMS-aligned, multi-agent coordination platform · Azure-sovereign · "
              "Australia first, regional reference architecture next")
    r.font.size = Pt(18)
    r.font.bold = True

    foot = s.shapes.add_textbox(Inches(0.6), Inches(6.1), Inches(12.1), Inches(0.5))
    r = foot.text_frame.paragraphs[0].add_run()
    r.text = "Azure Master Architect Capstone   ·   Rubric-Aligned Submission   ·   May 2026"
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    set_notes(s, """
KEY MESSAGE: This is not a slide deck about a future system. It is the architecture, the code, the proof and the platform — built, tested, and ready to defend against the rubric.

TALK TRACK (60s):
- Open with stillness. "Australia loses people, homes and economic capacity to natural disasters every year — and the Royal Commission's 2020 finding was unambiguous: the bottleneck is coordination."
- Frame the posture. "I want to take you through twelve rubric criteria one by one. Each slide answers a single criterion at the Excellent level, anchored in the Constitution, the spec catalogue, the codebase, and the Evidence Harness."
- Set the contract with the panel. "Where I'm asserting a number, it is reproducible from the repo. Where I'm asserting a guarantee, it is encoded as a CI gate. Where I'm asserting a trade-off, I will name it."
- Close the open. "Forty minutes. Eight rubric categories. Twelve criteria. One reference architecture you can take home."

DELIVERY: Eye contact. Pause. Then advance.
""")

    # =====================================================================
    # 2 — EXECUTIVE HOOK
    # =====================================================================
    s = add_slide(prs, L_3COLS)
    set_title(s, "The hook — why this problem, why now, why this team")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "33 lives lost")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "3,000+ buildings destroyed")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "~A$100B economic cost")
    set_text(
        find_ph(s, PH_3COL_BODY[0]),
        "Black Summer 2019–20: 33 direct deaths, 417 indirect deaths from smoke. "
        "~24 million hectares burned nationally. The Royal Commission's central finding "
        "was that coordination — not capability — is the dominant improvement opportunity.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[1]),
        "2022 eastern-Australia floods (~A$9.6B): Lismore's worst flood on record; 3,000+ "
        "Lismore homes affected, 900+ declared uninhabitable. The 2022 NSW Independent "
        "Flood Inquiry named warning, evacuation and inter-agency coordination failures.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[2]),
        "Black Summer alone: ~A$100B in losses (Read & Denniss, *The Conversation*, 2020) — "
        "Australia's costliest natural disaster on record. We do not lack capital. We lack "
        "an architecture that turns federated authority into coordinated action.",
    )
    set_notes(s, """
KEY MESSAGE: I am not selling capability — I am attacking coordination latency, the variable everyone has stopped trying to bend.

TALK TRACK (75s):
- Walk left to right. Black Summer numbers, then Northern Rivers, then the cost line.
- Avoid hand-waving. Each number on this slide passed a written claim-validation audit (`AMA_Capstone_Claim_Audit.md`). Where I dropped precision (e.g. ~A$100B vs $103B), I dropped it deliberately.
- Bridge to the rubric. "The next twelve slides answer the rubric one criterion at a time. Each is built to land at the Excellent level — and each carries the evidence in the speaker notes."

EXEC HOOK: "If a future Royal Commission asks 'why didn't anyone build this' — that question is answered today, in this room."

PAUSE on the third column. Hold for two beats before advancing.
""")

    # =====================================================================
    # 3 — AGENDA / RUBRIC MAP
    # =====================================================================
    s = add_slide(prs, L_AGENDA)
    set_title(s, "RUBRIC MAP — twelve criteria, twelve slides, one solution")
    agenda_items = (
        "Design — System architecture, modularity, scalability",
        "Design — Use of design patterns",
        "Development — Application demo (executive hook)",
        "Development — Implementation completeness",
        "Monitoring — Logging and metrics",
        "Monitoring — Error handling and alerting",
        "AI Integration — Use of AI technologies",
        "AI Integration — AI model selection and deployment",
    )
    for ph_idx, item in zip(PH_AGENDA_ITEMS, agenda_items):
        set_text(find_ph(s, ph_idx), item)
    set_notes(s, """
KEY MESSAGE: Rubric-by-rubric. No criterion left implicit.

TALK TRACK (45s):
- "I have laid the deck out by rubric criterion, in rubric order, so the panel can score in real time. The first eight categories appear here; Agentic Behaviour, Additional Architecture and Presentation follow on the next page."
- Don't read every line. Highlight rows 3 and 7 — Application Demo and Use of AI technologies — as the audience anchors.
""")

    # =====================================================================
    # 4 — RUBRIC: System architecture, modularity, scalability
    # =====================================================================
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Architecture — modular, multi-tenant, Azure-native, scale-down to scale-out")
    add_rubric_badge(s, "DESIGN · System architecture / modularity / scalability")
    add_image(s, ARCH / "c4" / "container.png")
    add_caption(
        s,
        "C4 Container view · 32 Bicep modules · Azure-native managed services · "
        "docs/architecture/c4/container.png",
    )
    set_notes(s, """
RUBRIC: DESIGN — System architecture, modularity, scalability.
EXCELLENT CLAIM: "Clear, well documented architecture with modular components and scalability considerations."

EVIDENCE (talking points):
- **Modularity**: 32 Bicep modules under `infra/modules/`; five operational agents under `apps/agents/{name}/agent.py` with shared infrastructure in `apps/agents/common/` (handoffs, llm_mixin, llm_client, content_safety). Domain isolated as a workspace package (`packages/domain`, 25 models).
- **Multi-tenancy by jurisdiction tuple**: Cosmos partition key + Rego policy layer (`tenant-isolation`, `cross_env`, `identity_consistency`). Federation is a first-class architectural primitive, not a retrofit.
- **Scale path documented**: pilot (single jurisdiction), state production (multi-incident concurrent), national (all states + Commonwealth). Cost ladder bands published in the FinOps slide; SKU choices make pilot serverless and state production reserved-capacity.
- **C4 model**: Context, Container, Component, Code views all checked into `docs/architecture/c4/`. Every diagram lives next to its source `.drawio` so it never goes stale.
- **WAF alignment**: Reliability, Security, Cost, Operational Excellence and Performance Efficiency are mapped pillar-by-pillar in `docs/architecture/governance/waf-pillar-mapping.png`.
- **Scalability primitives**: Container Apps consumption + KEDA scaling, Cosmos serverless, Service Bus partitioned queues, Front Door at the edge, Azure AI Search shard-aware. No bespoke load-balancing.

TALK TRACK (90s):
- "Three architectural commitments: modular by agent, multi-tenant by jurisdiction, Azure-native end-to-end."
- "Scale is a path, not a slide. Pilot rides serverless. State production buys reserved capacity. National scale is multi-region active-passive."
- Anticipated Q&A: "Why not microservices for everything?" — Five operational agents fit the AIIMS function model exactly; further splitting would create coordination cost, not reduce it.
""")

    # =====================================================================
    # 5 — RUBRIC: Use of design patterns
    # =====================================================================
    s = add_slide(prs, L_3COLS)
    set_title(s, "Design patterns — chosen for life-safety, named in the codebase")
    add_rubric_badge(s, "DESIGN · Use of design patterns")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Constitution-as-code")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Typed agent handoff + reflection")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Three-tier graceful fallback")
    set_text(
        find_ph(s, PH_3COL_BODY[0]),
        "Six core principles + five non-negotiables in `.specify/memory/constitution.md` "
        "v1.2.0. Encoded as Rego policies (`au_region`, `safety-guardrails`, "
        "`tenant-isolation`, `secret_hygiene`, `posture`, `identity_consistency`, "
        "`cross_env`) that fail any PR weakening the rails. Policy-as-code, not policy-as-PDF.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[1]),
        "AgentHandoffEvent (`apps/agents/common/handoffs.py`): typed, async, 3 retries inside "
        "a 300s window, dead-letter on failure. Reflection guardrail sits between Risk "
        "Assessment and Communication, critiquing every recommendation against the AIDR "
        "ten Warning Principles before any draft alert can leave Risk.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[2]),
        "LLMCallMixin (`apps/agents/common/llm_mixin.py`) implements LLM → template_fallback "
        "→ safety_fallback. The Communication agent **always** produces a defensible alert. "
        "Constitutional Non-Negotiable #5 — graceful degradation — is enforced as a runtime "
        "primitive, not an aspiration.",
    )
    set_notes(s, """
RUBRIC: DESIGN — Use of design patterns.
EXCELLENT CLAIM: "Appropriate and effective use of relevant design patterns."

EVIDENCE (talking points):
- **Domain Driven Design** — 25 first-class domain models (`packages/domain/src/domain/models/`): Organisation, Persona, Jurisdiction, Incident, Signal, HazardAssessment, Recommendation, ApprovalDecision, CoordinationTask, PublicAlert, OperatingFramework, JurisdictionPolicy, ProvenanceRecord, DeadLetterEntry…
- **Strategy + Chain of Responsibility** — handoff chains per data source via `HandoffChainDefinition`; primary/secondary agent assignments via `AgentGovernanceAssignment`.
- **Event Sourcing** — `timelineEvent` records every signal, recommendation, approval, alert, task, system, handoff, dead_letter, llm_call. The audit container is append-only, Cosmos `Strong` consistency, single AU region, 7-year Locked Blob mirror.
- **Saga / Compensation** — async handoff with retry-then-dead-letter; recovery through named operator review SLA in the dead-letter UI.
- **Reflection / Critic** — Risk Assessment outputs are critiqued by a guardrail policy before reaching Communication. Failed reflections produce structured rejection codes that feed back into eval datasets.
- **Hexagonal Architecture** — FastAPI routes thin; business logic in services; Cosmos in repositories; Pydantic at validators; agents at the adapter boundary.

TALK TRACK (75s):
- "Three patterns we lean on hardest: constitution-as-code, typed handoff with reflection, three-tier fallback."
- "Each is named in the codebase, not in a slide. If you `grep` the repo for `AgentHandoffEvent`, `LLMCallMixin`, `safety-guardrails`, you will find the pattern in implementation form."
""")

    # =====================================================================
    # 6 — RUBRIC: Application Demo
    # =====================================================================
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Application demo — Blue Mountains bushfire, baseline vs AMA-assisted, end-to-end")
    add_rubric_badge(s, "DEVELOPMENT · Application Demo")
    body = (
        "EXECUTIVE HOOK\n"
        "Two browsers, side by side. Same scenario. Same deterministic seed. Same simulated "
        "population. One window: a duty officer with no AMA assist. The other: the AMA agent "
        "network, in flight.\n\n"
        "WHAT YOU WILL SEE — five live markers, called out as they happen:\n"
        "  1. Signal ingestion under 10 s (left-panel meter + event-log timestamps)\n"
        "  2. Recommendation generation in under 30 s (chat-pane recommendation card)\n"
        "  3. Approval request landing on a NAMED Incident Controller (IC Approval Card)\n"
        "  4. Multilingual draft — six languages plus an Auslan stub (PIO AWS Composer)\n"
        "  5. Audit chain reachable in TWO clicks (audit_id link → Decision Chain panel)\n\n"
        "WHY IT MATTERS\n"
        "The baseline run produces no recommendation, no approval, no multilingual alert — only "
        "raw signals. The AMA-assisted run produces a defensible alert in minutes, with a complete "
        "audit chain reachable from any output back to source. The whole demo runs from "
        "`docs/ama-presentation/AMA_Live_Demo_Instructions.md`."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
RUBRIC: DEVELOPMENT — Application Demo.
EXCELLENT CLAIM: "Clean and clear demonstration of the use case. Provide hook to executive team."

DEMO PROTOCOL:
- Pre-flight three terminals (apps/api · apps/agents · apps/web). Open two browsers labelled "Baseline" and "AMA-assisted".
- Use the verbatim seed prompt from `AMA_Live_Demo_Instructions.md` §2 — deterministic seed=42 ensures reproducibility for the panel later.
- Run quick actions in order: SITREP → Risk → Deploy → Alert → Escalate (5 buttons in the simulation chat pane).
- Open the Incident Commander workspace tab → IC Approval Card → click Approve → audit_id link appears.
- Open the PIO workspace → AWS Composer → tick all 6 languages + auslan → Draft variants → Run accessibility scan → Request IC approval.
- Stop both simulations → open `/simulations/reports/{tenantId}` for each → put side by side. AMA column populated, baseline column shows "—".

DEMO RECOVERY: pre-recorded fallback at `docs/canary/demo-recording.mp4`. State this *before* starting the demo so the audience trusts the recovery path.

EXEC HOOK MOMENT: When the multilingual alert appears, point to the Auslan tile and say: "This is the difference between a system that *aligns* with the Australian Warning System and one that *embeds* it."

TALK TRACK (45s before demo):
- "I will run both windows. I will narrate to your watch. The point is not that the AMA window is faster — the point is that the AMA window produces a *defensible* alert with a complete audit chain. Speed is the headline; trust is the differentiator."
""")

    # =====================================================================
    # 7 — RUBRIC: Implementation completeness
    # =====================================================================
    s = add_slide(prs, L_3COLS)
    set_title(s, "Implementation completeness — every required feature shipped, with evidence")
    add_rubric_badge(s, "DEVELOPMENT · Implementation completeness")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Five agents, all live")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Platform & data plane")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Test coverage & specs")
    set_text(
        find_ph(s, PH_3COL_BODY[0]),
        "Monitoring · Risk Assessment · Evacuation · Resource Allocation · Communication. "
        "All five operational agents implemented under `apps/agents/`, registered in the "
        "agent runtime, exercised in the simulation harness. LLM-enabled agents (Risk, "
        "Communication) carry token-budgeted fallback; rule-based agents have deterministic "
        "tests.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[1]),
        "FastAPI service (`apps/api`), Next.js operator UI (`apps/web`), 32 Bicep modules "
        "(`infra/modules/`), 25 domain models, 46 seeded Australian data sources across 7 "
        "trust tiers, OpenAPI 3.1 contract with 13 governance-dashboard endpoints + signal "
        "ingest + approvals + tasks + alerts + scenarios + dead-letter + handoffs + health.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[2]),
        "531 test files: 173 unit · 156 contract · 134 integration · 25 simulation · "
        "10 devops · 6 benchmark · 5 e2e · 2 load. 42 specifications under `specs/` — every "
        "feature carries a Spec, Plan, Tasks, Quickstart and Contracts triple. The Evidence "
        "Harness (spec 040) re-runs each scenario per release.",
    )
    set_notes(s, """
RUBRIC: DEVELOPMENT — Implementation completeness.
EXCELLENT CLAIM: "Fully implements all required features."

EVIDENCE (verified against the workspace at deck-build time, May 2026):
- `apps/agents/{monitoring,risk_assessment,evacuation,resource_allocation,communication}/agent.py` — all five present.
- `apps/api/app/` — FastAPI app with routes, services, repositories, validators, middleware.
- `apps/web/` — Next.js 14 operator UI, persona workspaces (incident-commander, public-information-officer, etc.), simulation control, governance dashboard, Help & Docs chat.
- `infra/main.bicep` + 32 modules under `infra/modules/`.
- `packages/domain/src/domain/models/` — 25 models; `packages/domain/src/domain/seed/data_sources_australia.json` — 46 sources.
- `specs/` — 42 directories, each with `spec.md`, `plan.md`, `tasks.md`, `quickstart.md`, contracts/.
- Tests: ~531 files counted by `AMA_Capstone_Claim_Audit.md` (workspace verification).
- 85+ persona definitions across 10 operational + 58 active sector + 17 technical, under `.github/agents/`.

TALK TRACK (75s):
- "Completeness is not a vibe — it's a count. Five agents, 32 modules, 46 sources, 25 models, 13 dashboard endpoints, 531 tests, 42 specs. Each number is reproducible from the repo with a single shell command."
- "I want to draw your attention to the third column. Specs **before** code. Forty-two of them. The Constitution is the spine, the specs are the ribs, the code is the flesh — never the other way around."
""")

    # =====================================================================
    # 8 — RUBRIC: Logging and metrics
    # =====================================================================
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Logging & metrics — structured, KPI-instrumented, SLO-driven")
    add_rubric_badge(s, "MONITORING · Logging and metrics")
    add_image(s, ARCH / "security" / "sli-slo-model.png")
    add_caption(
        s,
        "SLI/SLO model · App Insights + Log Analytics + Cosmos audit + Locked Blob mirror · "
        "docs/architecture/security/sli-slo-model.png",
    )
    set_notes(s, """
RUBRIC: MONITORING — Logging and metrics.
EXCELLENT CLAIM: "Implements structured logging and relevant metrics."

STRUCTURED LOGGING (talking points):
- **One audit-event schema** (`contracts/audit-event.schema.json`) writes to a Cosmos Strong-consistency container with a 7-year Locked Blob mirror. Every signal → fusion → recommendation → approval → publish step lands a row.
- **Correlation IDs end-to-end** — propagated through HTTP, agent handoffs, LLM calls, ACS dispatch. Track an alert from public delivery back to the originating Tier 1 signal in two clicks (`/governance/dashboard/audit`).
- **LLM call telemetry** — every model call records input tokens, output tokens, model version, latency, refusal rate, fallback path taken. Per-incident cost is queryable in the FinOps workspace.
- **timelineEvent rows** by type: signal, recommendation, approval, alert, task, system, handoff, dead_letter, llm_call. KQL workbooks pre-built under `infra/observability/` and `infra/dashboards/`.

METRICS / KPIs:
- **Three operational SLOs** (rolling 30-day): signal-to-recommendation P95 <30s · recommendation-to-approval-request P95 <5s · alert-publish-after-approval P95 <60s.
- **Five capstone outcome KPIs** (per spec 040 Evidence Harness): modelled lives saved · response-time reduction · evacuation lead-time uplift · logistics efficiency · modelled economic loss reduction. Each carries 9 attributes (formula, unit, owner role, refresh cadence, target, alert threshold, baseline source, provenance, confidence band).
- **Bootstrap 95% CI** over ≥1,000 resamples; ±1 SD fallback labelled small-sample. Determinism tolerance ±2% / ±1 absolute.
- **Governance KPIs**: manual-row share per artefact (≤50%, blocks publication above) · tampering-attempt rate (target 0) · carve-out review cadence (auto-revoke on AU GA).

TALK TRACK (75s):
- "Three SLO families: operational, outcome, and governance. Each is in production telemetry, not a slide."
- "If you take one thing from this slide — every artefact in the system, public-facing or internal, has a confidence band. We do not publish a number we cannot defend statistically."
""")

    # =====================================================================
    # 9 — RUBRIC: Error handling and alerting
    # =====================================================================
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Error handling & alerting — degrade gracefully, escalate intelligently")
    add_rubric_badge(s, "MONITORING · Error handling and alerting")
    add_image(s, ARCH / "sequence" / "graceful-degradation.png")
    add_caption(
        s,
        "Graceful degradation sequence · 3-tier fallback · burn-rate alerts at 2%/h and 5%/h · "
        "docs/architecture/sequence/graceful-degradation.png",
    )
    set_notes(s, """
RUBRIC: MONITORING — Error handling and alerting.
EXCELLENT CLAIM: "Robust error handling and alerting mechanisms."

ROBUST ERROR HANDLING (talking points):
- **Three-tier LLM fallback** — LLMCallMixin (`apps/agents/common/llm_mixin.py`): LLM → template_fallback → safety_fallback. The Communication agent **always** produces a defensible alert.
- **Typed handoff with retry & dead-letter** — AgentHandoffEvent: 3 retries within a 300s window; failures land in a dead-letter container with a named operator-review SLA. Status: pending → delivered/failed → dead_lettered.
- **HTTP error contract** — RFC 7807 ProblemDetails responses for every failure mode. 503 + ProblemDetails on persistent audit-write failure (FR-044/045 spec 040). 409 Conflict on append-only tampering attempts — *and* a tampering-attempt audit row is written by the rejection itself.
- **Active-passive across AU East / AU Southeast** — Cosmos multi-region replication is `Session` for non-audit data, `Strong` per-operation override on the audit container (deliberately single-region — the trade-off is explicit and constitutional). RTO target <15 min, RPO <60 s.
- **Ingestion safety net** — DeadLetterEntry tracks failed signal processing/handoffs with retry metadata and resolution workflow on the Governance Dashboard.

ALERTING:
- **SRE Workbook fast-burn convention**: 2%/h burn rate raises Sev2 ticket; 5%/h burn rate pages Sev1 (named on-call). 30-day SLO horizon.
- **Alert on anomalies, not noise** — refusal rate, reflection-failure rate, model-latency drift, grounding-source drift are first-class observability signals.
- **Action runbooks** — every alert ID maps to a runbook in `docs/operator-runbooks/` and `docs/runbooks/`.

TALK TRACK (75s):
- "When something fails in this platform, the platform does not. It downgrades, surfaces the degradation prominently in the operator UI, and keeps producing alerts."
- "Constitutional non-negotiable #5 — graceful degradation — is the most expensive promise we made. It is also the one we are proudest of."
""")

    # =====================================================================
    # 10 — RUBRIC: Use of AI technologies
    # =====================================================================
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "AI technology — Foundry, Agent Framework, RAG, Content Safety, multilingual")
    add_rubric_badge(s, "AI INTEGRATION · Use of AI technologies")
    add_image(s, ARCH / "c4" / "agent-runtime-llm-gateway.png")
    add_caption(
        s,
        "Agent runtime + LLM gateway · Microsoft Foundry · Agent Framework · "
        "Azure AI Search RAG · Azure AI Content Safety · "
        "docs/architecture/c4/agent-runtime-llm-gateway.png",
    )
    set_notes(s, """
RUBRIC: AI INTEGRATION — Use of AI technologies.
EXCELLENT CLAIM: "Effective integration of AI models or services with clear purpose."

PURPOSE-DRIVEN AI (talking points):
- **Microsoft Foundry** is the agent surface (GA Q1 2026) — managed identity end-to-end, RAG-grounded agents with mandatory citations, model portability across Azure OpenAI deployments, content-safety perimeter we don't have to build.
- **Microsoft Agent Framework** orchestrates the five-agent network — handoff, reflection, dead-letter as primitives, not bespoke plumbing. Decision recorded in spec `033-maf-adoption`.
- **Azure AI Search (Foundry RAG)** grounds every agent on the AIDR Handbook collection (Incident Management 2023, Evacuation Planning 2023, Public Information & Warnings 2021, AWS Companion 2022, Community Recovery 2018, Emergency Management Arrangements 2023). Citations are mandatory and emitted into every response — uncited model output is rejected by the gateway.
- **Azure AI Content Safety** — hate, violence, self-harm, sexual + jailbreak/prompt-injection shields on by default. Domain-specific blocked-keyword list (`apps/agents/common/content_safety.py`).
- **Azure Communication Services** — multilingual SMS/voice/email channels. Six languages live (en-AU, zh-Hans, ar, vi, el, it) plus Auslan video stub; jurisdiction-appropriate Aboriginal & Torres Strait Islander language packs per deployment.

CLEAR PURPOSE — agent ↔ AIIMS function ↔ AIDR handbook:
- Monitoring → Intelligence (AIIMS) → AIDR §3.
- Risk Assessment → Intelligence/Planning → AIDR Public Information & Warnings (10 principles).
- Evacuation → Operations → AIDR Evacuation Planning (5 stages).
- Resource Allocation → Logistics → AIDR Incident Management.
- Communication → Public Information → Australian Warning System (3 levels, nested model).

TALK TRACK (90s):
- "Five Microsoft AI services. One mission. Each is named to a purpose and a function — never a model in search of a job."
- "If a regulator asks 'what is your AI doing here', I open the agent-runtime diagram and walk left to right. Every component is purpose-attributed."
""")

    # =====================================================================
    # 11 — RUBRIC: AI model selection and deployment
    # =====================================================================
    s = add_slide(prs, L_3COLS)
    set_title(s, "Model selection & deployment — dual-purpose, AU-sovereign, gateway-mediated")
    add_rubric_badge(s, "AI INTEGRATION · AI model selection & deployment")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Dual deployment by purpose")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Gateway-mediated calls")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Sovereign by design")
    set_text(
        find_ph(s, PH_3COL_BODY[0]),
        "**Reasoning model** (GPT-4 class) — Risk Assessment fusion, complex recommendation "
        "generation. **Drafting model** (low-latency multilingual) — Communication agent "
        "alert generation across six languages. Routed by purpose, not by URL — model swap "
        "is a config change, not a re-architecture.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[1]),
        "Every LLM call traverses a model gateway that enforces token budgets, **prompt "
        "shielding**, **PII minimisation**, **content safety**, and the **AU-residency "
        "carve-out allowlist**. Correlation IDs propagate; fallback chain (LLM → template → "
        "safety) is gateway-orchestrated. No agent calls a model directly.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[2]),
        "Constitution v1.2.0 §Non-Negotiable #2: **all data stays in AU**. Bounded carve-out "
        "for Foundry model-hosting endpoints when not yet GA in AU East/Southeast — "
        "**inference only, never persistence**, behind data-minimisation, on a named "
        "auto-revoking allowlist with documented justification, approver, and review date.",
    )
    set_notes(s, """
RUBRIC: AI INTEGRATION — AI model selection and deployment.
EXCELLENT CLAIM: "Appropriate model choice and secure deployment strategy."

MODEL SELECTION RATIONALE (talking points):
- **Right model for the job**: a 'reasoning' deployment for complex multi-signal fusion (where deliberation matters more than latency), a 'drafting' deployment for multilingual alert generation (where latency matters more than depth). One-model-fits-all is a false economy in life-safety contexts.
- **Vendor portability is structural, not aspirational**: The agent-side interface is OpenAPI + Pydantic — the model is replaceable. Spec 033 names this commitment.
- **Cost-aware**: AI inference is **not** the dominant operational cost line — ACS message volume is. The model gateway lets us swap drafting to a smaller open-weight deployment if economics shift, without touching agent contracts.

SECURE DEPLOYMENT:
- **Managed Identity end-to-end** — no LLM secrets except the explicit-listed third-party tokens, all in Key Vault with rotation.
- **Private Endpoints** for all data services (Cosmos, Storage, Service Bus, Key Vault, Container Registry, Application Insights, Log Analytics).
- **Model Gateway responsibilities**: token budget enforcement, content safety, prompt shielding, PII minimisation, correlation ID propagation, AU-carve-out enforcement (auto-revokes when model GA in AU), citation enforcement.
- **AU sovereignty carve-out**: The carve-out list is auditable — each entry records model name, region, business justification, approver identities, and review date. Auto-revokes when AU-region availability changes. Regulated data (incidents, alerts, recommendations, operator actions, audit, evidence, PII, PSPF-marked content) **never leaves Australia** under any circumstance.

TALK TRACK (90s):
- "Two models, one gateway, one sovereignty rule with one bounded exception."
- "The carve-out is the smallest concession we could engineer. Inference only. Never data. Auto-revokes the day the model lands in AU East. Until that day, the gateway minimises every prompt that traverses the boundary."
""")

    # =====================================================================
    # 12 — RUBRIC: Autonomy and orchestration
    # =====================================================================
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Autonomy & orchestration — agents propose, humans dispose")
    add_rubric_badge(s, "AGENTIC BEHAVIOUR · Autonomy and orchestration")
    body = (
        "AUTONOMY — what agents decide on their own:\n"
        "  • Monitoring agent ingests, normalises and trust-tier-scores every signal\n"
        "  • Risk Assessment agent fuses signals into ranked recommendations with "
        "explanation\n"
        "  • Evacuation agent runs the AIDR five-stage process (Decision · Warning · "
        "Withdrawal · Shelter · Return)\n"
        "  • Resource Allocation agent prioritises cross-agency tasks by life-safety "
        "criticality\n"
        "  • Communication agent drafts AWS-compliant warnings in six languages plus "
        "Auslan\n\n"
        "ORCHESTRATION — how the network coordinates:\n"
        "  • Microsoft Agent Framework runtime; AgentHandoffEvent as the message contract\n"
        "  • Confidence-thresholded handoff (high-confidence fire/weather/hydrology @ 0.8+ "
        "auto-routes Monitoring → Risk Assessment)\n"
        "  • Reflection guardrail between Risk and Communication critiques every "
        "recommendation against the AIDR ten Warning Principles\n"
        "  • Three-tier fallback (LLM → template → safety) guarantees an output\n\n"
        "WHAT HUMANS DECIDE — the immovable boundary:\n"
        "  Constitutional Non-Negotiable #1: **no agent may take irreversible real-world "
        "action without explicit human authorisation.** The Communication agent draft sits "
        "in the IC Approval Card with signal provenance, recommendation rationale, "
        "AWS-level justification, and a per-language preview — a structured decision "
        "interface, not a rubber-stamp button."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
RUBRIC: AGENTIC BEHAVIOUR — Autonomy and orchestration.
EXCELLENT CLAIM: "Agent demonstrates autonomous behaviour and orchestrates tasks effectively."

EVIDENCE (talking points):
- **Bounded autonomy**: each agent has a clear *scope* (Monitoring summarises; doesn't assess. Resource Allocation prioritises; doesn't schedule.) Scope boundaries are encoded in the agent class docstring and tested at the contract level.
- **Trust-tiered ingest**: signals carry one of 7 trust tiers (Tier 1 authoritative-government → Tier 7 derived/computed). Tier 6 (social/unverified — Twitter/X, Facebook, Reddit) is **advisory-only** and cannot solo-trigger a public alert. Cross-tier corroboration plus confidence banding (≥0.80 high · 0.50–0.79 medium · <0.50 low) gate publication (FR-024 / FR-027).
- **Approval surface — IC Approval Card**: rationale + sources + confidence pill (green ≥0.85 / amber ≥0.6 / rose <0.6) + named approver. Approve writes to `/api/outcomes/sc-{N}/evaluate`, then surfaces the audit_id as a clickable link. (Implementation: `apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx`.)
- **Manual-row share KPI**: ≤50% manual-row share per artefact — publication is **blocked** above. If humans are doing more than half the work, the AI is degrading invisibly and must not publish.

TALK TRACK (90s):
- "Memorise the principle: agents propose, humans dispose. Every autonomous decision falls inside a scope boundary; every irreversible action falls behind a named approver."
- "The KPI ceiling on manual rows is the most counter-intuitive guardrail in the system. If humans start doing more than half the work, the platform refuses to publish. That is the autonomy commitment, in failsafe form."
""")

    # =====================================================================
    # 13 — RUBRIC: Multi-agent coordination
    # =====================================================================
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Multi-agent coordination — typed handoff, reflection, dead-letter, replay")
    add_rubric_badge(s, "AGENTIC BEHAVIOUR · Multi-agent coordination")
    add_image(s, ARCH / "c4" / "component-agents.png")
    add_caption(
        s,
        "Agent component view · 5 agents · handoff (3 retries / 300s) · reflection · "
        "dead-letter · sim-warp replay · docs/architecture/c4/component-agents.png",
    )
    set_notes(s, """
RUBRIC: AGENTIC BEHAVIOUR — Multi-agent coordination.
EXCELLENT CLAIM: "Implements coordination patterns such as handoffs, reflections, or state graphs."

COORDINATION PATTERNS (all three present, all three exercised):

**1. Handoff with retry + dead-letter** — `apps/agents/common/handoffs.py`:
- AgentHandoffEvent: typed (Pydantic), correlated (correlation_id end-to-end), retried (3x within a 300s window), dead-lettered (DeadLetterEntry on persistent failure).
- Status machine: pending → delivered/failed → dead_lettered.
- Service Bus + Cosmos at the transport/persistence layer; retry semantics in code, not in the broker.

**2. Reflection / Critic** — between Risk Assessment and Communication:
- Risk recommendations critiqued against the AIDR ten Warning Principles + content safety + plain-English Grade-8 reading level rule.
- Failed reflections produce structured rejection codes that feed back into eval datasets.
- Implemented via reflection prompt + Azure AI Content Safety + domain blocked-keyword list.

**3. State graph / saga** — sim-warp replay (spec 026):
- Every scenario run is replayable from the timeline of events. Sim warp lets an auditor step through the same run later. Time-travel debugging for compliance and after-action review.
- ScenarioRun model carries coordination-gap summary, deterministic seed, and per-agent handoff trace.

CHAIN (typical bushfire path):
  Monitoring → (high-confidence handoff) → Risk Assessment → (reflection guardrail) →
  Communication ⇉ IC Approval (named human) ⇉ Publish ⇉ Audit row (Strong) + Locked Blob
  ↘ Evacuation Agent (route pressure)
  ↘ Resource Allocation Agent (task prioritisation)

TALK TRACK (90s):
- "Three coordination patterns, all present, all exercised by the simulation harness on every release."
- "The reflection guardrail is where Responsible AI becomes operational. Every Risk Assessment recommendation is critiqued against the AIDR Ten Warning Principles before the Communication agent ever sees it."
- "Dead-lettering is not a fallback — it is a documented, named-operator-reviewed workflow on the Governance Dashboard. Failed handoffs do not vanish; they wait for review with their full provenance intact."
""")

    # =====================================================================
    # 14 — RUBRIC: Security
    # =====================================================================
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Security — Zero Trust, AU sovereignty, append-only audit, policy-as-code")
    add_rubric_badge(s, "ADDITIONAL · Security")
    add_image(
        s,
        ARCH / "security" / "trust-boundary.png",
        left=Inches(0.4), top=Inches(1.4), width=Inches(6.4), height=Inches(5.2),
    )
    add_image(
        s,
        ARCH / "security" / "au-residency-data-classification.png",
        left=Inches(7.0), top=Inches(1.4), width=Inches(6.0), height=Inches(5.2),
    )
    add_caption(
        s,
        "Trust boundary · AU-residency data classification · 7 Rego policies · "
        "Cosmos Strong audit + 7-year Locked Blob · docs/architecture/security/",
    )
    set_notes(s, """
RUBRIC: ADDITIONAL ARCHITECTURE — Security.
EXCELLENT CLAIM: "Thoughtful implementation of security measures."

THOUGHTFUL SECURITY (talking points):

**Zero Trust posture**:
- Operator UI is the only public surface. Everything else is private endpoint.
- Managed Identity end-to-end. RBAC matrix at `docs/architecture/security/rbac-matrix.png`.
- No long-lived secrets except the explicit-listed third-party tokens, all in Key Vault with rotation.

**AU sovereignty (Constitution v1.2.0 §Non-Negotiable #2)**:
- All regulated data (incidents, alerts, recommendations, operator actions, audit, evidence, PII, PSPF-marked content) stays in Australian borders (Azure Australia East / Australia Southeast).
- Bounded carve-out: Foundry model-hosting endpoints may sit non-AU, **inference only, never persistence**, on a named auto-revoking allowlist with documented justification and approver.
- Every PR introducing a non-AU data resource fails the pipeline at What-If via the `au_region` Rego policy.

**Append-only audit**:
- Cosmos `Strong` consistency on the audit container, single AU region. 7-year Locked Blob immutability mirror.
- Tampering attempts return 409 Conflict **and** write a tampering-attempt audit row themselves.
- Every signal → fusion → recommendation → approval → publish step lands an audit row before HTTP refusal.

**Policy-as-code (7 Rego bundles)** — `infra/policy/`:
- `au_region` · `cross_env` · `identity_consistency` · `posture` · `secret_hygiene` · `safety-guardrails` · `tenant-isolation`.
- All seven run on every PR. A PR weakening any guardrail fails the pipeline.

**Privacy by Design (Privacy Act 1988 + jurisdiction policies)**:
- Every PII field has a classification tag. Model gateway masks/denies PII transit on prompts traversing the AU carve-out.
- JurisdictionPolicy entities encode privacy + visibility rules per jurisdiction (NSW, VIC, QLD, WA, SA, TAS, NT, ACT, Commonwealth).

**External alignment** — `docs/compliance/`:
- ISO/IEC 42001:2023 (AI Management System) · Australia's Voluntary AI Safety Standard 2024 (10 guardrails) · NIST AI RMF 1.0 (Govern/Map/Measure/Manage) · upcoming Australian Mandatory Guardrails for High-Risk AI.

TALK TRACK (90s):
- "Two diagrams. Left: trust boundary — Zero Trust by default. Right: AU residency — sovereignty as a property, with one named, bounded, auto-revoking exception."
- "Audit immutability is constitutional. Tampering attempts do not just fail — they leave their own audit row. There is no anonymous AI action in this system."
""")

    # =====================================================================
    # 15 — RUBRIC: Performance and reliability
    # =====================================================================
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Performance & reliability — sub-second SLOs, multi-region failover, deterministic replays")
    add_rubric_badge(s, "ADDITIONAL · Performance and reliability")
    body = (
        "OPTIMISED PERFORMANCE — operational SLOs, rolling 30-day horizon:\n"
        "  • Signal-to-recommendation P95 < 30 s\n"
        "  • Recommendation-to-approval-request P95 < 5 s\n"
        "  • Alert-publish-after-approval P95 < 60 s\n"
        "  • End-to-end signal-to-published-alert P95 < 90 s\n"
        "  • Audit-write durability 100% before HTTP refusal\n\n"
        "RELIABLE OPERATION — defended by architecture:\n"
        "  • Active-passive across Azure AU East / AU Southeast — RTO < 15 min, RPO < 60 s\n"
        "  • Cosmos multi-region `Session` for non-audit; `Strong` per-operation override on "
        "the audit container (deliberately single-region; documented trade-off)\n"
        "  • Container Apps + KEDA for elastic horizontal scale\n"
        "  • Service Bus partitioned queues; Event Grid fan-out; Front Door at the edge\n"
        "  • Three-tier graceful degradation (LLM → template → safety) — Communication agent "
        "always produces a defensible alert\n"
        "  • Burn-rate alerts at 2%/h (Sev2) and 5%/h (Sev1) per Google SRE Workbook\n\n"
        "DETERMINISTIC PROOF — Evidence Harness (spec 040):\n"
        "  • 7 canonical scenarios (bushfire · flood · cyclone · urban-fire · mass-casualty · "
        "hazmat · marine SAR), baseline-vs-AMA-assisted, deterministic seed\n"
        "  • Bootstrap 95% CI over ≥1,000 resamples; ±2% / ±1 absolute determinism tolerance\n"
        "  • Sim-warp replay (spec 026) — time-travel debugging for compliance and after-action"
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
RUBRIC: ADDITIONAL ARCHITECTURE — Performance and reliability.
EXCELLENT CLAIM: "Optimised performance and reliable operation."

PERFORMANCE EVIDENCE:
- Performance benchmarks under spec 015; 6 benchmark test files exercise the SLO targets per release.
- LLM call timeout: 30s default with token-budget enforcement; circuit breaker triggers fallback chain.
- Async handoff with retry-then-dead-letter avoids blocking call paths; Service Bus partitioned for ordered delivery within an incident, parallel across incidents.

RELIABILITY EVIDENCE:
- The single-region constraint on the audit container is intentional — `Strong` consistency cannot span regions, and append-only durability outranks read-side global latency for compliance reasons. A true AU East outage degrades audit-write throughput, but never violates the append-only invariant. Degraded mode is documented behaviour.
- Failover targets tested in CI; 6 devops test files exercise deployment + rollback paths.
- 2 load + 2 e2e + 25 simulation tests in the harness — every release exercises the platform under realistic load.

TALK TRACK (90s):
- "Three SLOs that matter, three reliability primitives that defend them, one harness that proves both."
- "If you remember nothing else from this slide — the audit container is `Strong` consistency, single AU region, by design. We chose durability over global read latency because the regulator does not care about latency."
""")

    # =====================================================================
    # 16 — RUBRIC: Deployment and CI/CD
    # =====================================================================
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Deployment & CI/CD — IaC, branch-based promotion, policy-gated, auto-rollback")
    add_rubric_badge(s, "ADDITIONAL · Deployment and CI/CD")
    add_image(s, ARCH / "deployment" / "cicd-pipeline.png")
    add_caption(
        s,
        "CI/CD pipeline · GitHub Actions · 32 Bicep modules · azd · 7 Rego gates · "
        "auto-rollback on health-check failure · docs/architecture/deployment/cicd-pipeline.png",
    )
    set_notes(s, """
RUBRIC: ADDITIONAL ARCHITECTURE — Deployment and CI/CD.
EXCELLENT CLAIM: "Automated deployment with CI/CD pipeline."

CI PIPELINE (`.github/workflows/ci.yml`):
- ruff + pytest (contract + integration) + tsc + Next build + perf benchmarks.
- 7 Rego policy bundles run on every PR (`au_region`, `cross_env`, `identity_consistency`, `posture`, `secret_hygiene`, `safety-guardrails`, `tenant-isolation`).
- Bicep What-If gate — PRs introducing non-AU data resources fail at What-If.

CD PIPELINE (`.github/workflows/cd.yml`, simplified per spec 031):
- Branch-based promotion: `dev` → `staging` → `prod` (replacing the spec-029 workflow_run trigger).
- AZURE_CREDENTIALS JSON federation; OIDC where available.
- `azd` deploys to staging, then production, with health-check + auto-rollback on failure.
- Canary deployment runbook at `docs/canary/`.

INFRASTRUCTURE AS CODE:
- 32 Bicep modules under `infra/modules/`; root composition at `infra/main.bicep`.
- Per-environment parameters (`infra/parameters/`).
- Policy initiatives under `infra/policies/` enforce AU-region constraints + tag standards.
- Terraform alternative under `infra/terraform/` for shops with that preference (constitutional choice — Bicep preferred, Terraform accepted).

TEST PYRAMID (531 files):
- 173 unit · 156 contract · 134 integration · 25 simulation · 10 devops · 6 benchmark · 5 e2e · 2 load.
- Contract tests assert OpenAPI 3.1 schema parity between Pydantic source-of-truth and TypeScript domain twins.
- Devops tests exercise deployment + rollback paths.

TALK TRACK (90s):
- "Branch-based promotion. IaC by Bicep with What-If gates. Seven Rego policy bundles on every PR. Auto-rollback on health-check failure."
- "We deliberately simplified to branch-based dev/staging/prod (spec 031). The previous workflow_run-triggered cascade was clever; clever is the enemy of operable."
""")

    # =====================================================================
    # 17 — RUBRIC: Clarity of explanation and presentation
    # =====================================================================
    s = add_slide(prs, L_3COLS)
    set_title(s, "Clarity & audience tailoring — three altitudes, one narrative")
    add_rubric_badge(s, "PRESENTATION · Clarity of explanation and presentation")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Executive altitude")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Architect altitude")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Operator altitude")
    set_text(
        find_ph(s, PH_3COL_BODY[0]),
        "For BDM and exec sponsor: the **hook** (~A$100B Black Summer · coordination is the "
        "bottleneck) · the **ROI scenario** (one prevented level-3 escalation dwarfs platform "
        "TCO) · the **ask** (90-day shadow-mode pilot inside an existing innovation envelope). "
        "Numbers always paired with provenance.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[1]),
        "For CSA and SSP-M: **C4 diagrams** (System, Container, Component) · **agent runtime + "
        "LLM gateway** · **trust boundary** · **multi-jurisdiction tenancy** · **AIIMS system "
        "context** · **WAF pillar mapping**. Every claim sourced to a spec file or a code path. "
        "Trade-offs named explicitly.",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[2]),
        "For Incident Controllers, PIOs, sector leads: a **live demo** in their workspace, "
        "running the same simulation harness used by the Evidence Harness. Five live "
        "watch-for markers (signal <10s · recommendation <30s · named approver · multilingual "
        "draft · 2-click audit) — no jargon, no hand-waving.",
    )
    set_notes(s, """
RUBRIC: PRESENTATION & DOCUMENTATION — Clarity of explanation and presentation.
EXCELLENT CLAIM: "Clear, concise, and thorough presentation. Ability to identify the target audience and speaks at the appropriate level."

CLARITY DELIVERED (talking points):

**Audience-aware deck construction**:
- Title slide names the audience and the format up front.
- Each rubric slide carries a top-right pill identifying the rubric criterion and the 'Excellent' score-target — so the panel can score in real time.
- Speaker notes carry both the *what* (rubric claim, evidence) and the *how* (talk track, anticipated Q&A).

**Survival rule for Q&A** (from `AMA_Capstone_QnA.md`):
- Repeat the question.
- Anchor in the Constitution or a named spec.
- Give the 30-second answer.
- Then go deep if asked. Never bluff a number.

**Companion documentation in the same folder**:
- `AMA_Capstone_QnA.md` — 21 expected + 20 unexpected panel questions, each with role tag, 30s answer, and depth.
- `AMA_Capstone_Claim_Audit.md` — every quantified claim in the deck checked against repo and external sources, with verification trail.
- `AMA_Live_Demo_Instructions.md` — runbook with watch-for matrix, pre-flight, demo recovery.
- `AMA_Capstone_Disaster_Response_Hub.pptx` — long-form (43-slide) executive narrative deck for handover.

**Cross-walk to standards**:
- `docs/compliance/` — ISO/IEC 42001 · Australia's Voluntary AI Safety Standard · NIST AI RMF.
- `docs/architecture/` — every diagram has a `.md` companion describing intent and decisions.
- `docs/decisions/` — ADRs for every significant architectural choice.

TALK TRACK (60s):
- "I have built this deck so the panel can score it in real time. Each slide carries a rubric pill in the top-right corner, articulated to the Excellent level."
- "If you want depth, the speaker notes are exhaustive. If you want the executive-altitude version, the slide body is enough."
- "If you want the long-form 43-slide narrative for handover, it sits next to this file in `docs/ama-presentation/`."
""")

    # =====================================================================
    # 18 — SCORE PROJECTION
    # =====================================================================
    s = add_slide(prs, L_3COLS)
    set_title(s, "Rubric self-assessment — projecting 60 / 60 (Grade A · Exceptional)")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Design + Development")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Monitoring + AI + Agentic")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Security + Reliability + CI/CD + Presentation")
    set_text(
        find_ph(s, PH_3COL_BODY[0]),
        "System architecture · 5\n"
        "Design patterns · 5\n"
        "Application demo · 5\n"
        "Implementation completeness · 5\n"
        "── Subtotal · 20 / 20",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[1]),
        "Logging & metrics · 5\n"
        "Error handling & alerting · 5\n"
        "Use of AI technologies · 5\n"
        "AI model selection & deployment · 5\n"
        "Autonomy & orchestration · 5\n"
        "Multi-agent coordination · 5\n"
        "── Subtotal · 30 / 30",
    )
    set_text(
        find_ph(s, PH_3COL_BODY[2]),
        "Security · 5\n"
        "Performance & reliability · 5\n"
        "Deployment & CI/CD · 5\n"
        "Clarity of explanation & presentation · 5\n"
        "── Subtotal · 20 / 20\n\n"
        "TOTAL · 60 / 60 · GRADE A (54–60) — EXCEPTIONAL",
    )
    set_notes(s, """
KEY MESSAGE: I am asking the panel to score this against the published rubric and to grade-band against the published scale. I believe the evidence supports an Exceptional grade — and I built the deck to make that grading frictionless.

TALK TRACK (45s):
- "I am self-assessing at 60 out of 60. That is not a claim of perfection — it is a claim that, against the published rubric, every criterion lands at the Excellent descriptor with named evidence."
- "If the panel disagrees on any criterion, the speaker notes name the evidence I would point to. Where the evidence is overstated, the `AMA_Capstone_Claim_Audit.md` is my own audit telling you exactly what I corrected."
- "I would rather be marked down for honest measurement than marked up for clever marketing."

PANEL HUMILITY:
- Acknowledge that grading is the panel's call — never the candidate's.
- Be ready to defend or yield on each line. The rubric is the contract, not the scoreboard.
""")

    # =====================================================================
    # 19 — CALL TO ACTION + CLOSING
    # =====================================================================
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "The ask — a 90-day shadow-mode pilot, one state, one hazard")
    body = (
        "WHAT WE ARE ASKING FOR\n"
        "  • Sponsorship from one state emergency-services agency for a 90-day shadow-mode "
        "pilot\n"
        "  • A named Incident Controller to participate in a weekly Friday tabletop\n"
        "  • Read-only access to one authoritative signal stream (BoM gauges or RFS "
        "Fires Near Me)\n"
        "  • An exit-criteria conversation against the Evidence Harness (spec 040) KPIs\n\n"
        "WHAT YOU GET BACK\n"
        "  • A measurable, baseline-vs-AMA-assisted outcome scorecard with bootstrap "
        "95% CI\n"
        "  • A documented Australian-sovereign reference architecture you can re-use\n"
        "  • Zero production-channel risk: shadow mode is observe-only by design\n"
        "  • A working answer to the hardest question facing emergency management — "
        "how do we go faster, together, in the climate we are inheriting?\n\n"
        "DECISION SURFACE\n"
        "Decision criteria, ROI model, cost ladder and integration spike-plan are in the "
        "long-form deck (`AMA_Capstone_Disaster_Response_Hub.pptx`) and in the repo. The "
        "Q&A brief (`AMA_Capstone_QnA.md`) carries 41 questions with 30-second answers. "
        "The claim audit (`AMA_Capstone_Claim_Audit.md`) is my own honesty layer."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: The ask is small, defensible, lands inside any state's existing innovation envelope, and carries zero production-channel risk.

TALK TRACK (60s):
- "I am not asking for a budget today. I am asking for a 90-day shadow-mode pilot."
- "Shadow mode means we observe and we score; we do not touch a live decision. Bounded downside. Defensible upside."
- "If the answer is yes, the integration spike-plan is on a single page in the appendix. If the answer is 'tell me more first', I will be in this room for the next twenty minutes."

PAUSE before transitioning to closing.
""")

    # =====================================================================
    # 20 — CLOSING
    # =====================================================================
    s = add_slide(prs, L_CLOSING)
    tb = s.shapes.add_textbox(Inches(0.5), Inches(2.8), Inches(12.3), Inches(2.0))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = "Thank you."
    r.font.size = Pt(54)
    r.font.bold = True

    p2 = tb.text_frame.add_paragraph()
    r2 = p2.add_run()
    r2.text = "Questions, challenges, healthy disagreement — all welcome."
    r2.font.size = Pt(20)
    r2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    p3 = tb.text_frame.add_paragraph()
    p3.space_before = Pt(24)
    r3 = p3.add_run()
    r3.text = ("Companion artefacts in docs/ama-presentation/:  "
               "AMA_Capstone_Disaster_Response_Hub.pptx  ·  "
               "AMA_Capstone_QnA.md  ·  AMA_Capstone_Claim_Audit.md  ·  "
               "AMA_Live_Demo_Instructions.md")
    r3.font.size = Pt(12)
    r3.font.color.rgb = RGBColor(0x77, 0x77, 0x77)

    set_notes(s, """
KEY MESSAGE: Open the floor. Welcome the panel. Listen.

TALK TRACK (15s):
- "Thank you. We have twenty minutes for Q&A. I would like to take questions in three buckets — strategic, technical, governance — but jump in any order."

PANEL TIPS:
- Repeat each question for the room before answering.
- For executive questions, anchor in the five Evidence-Harness KPIs.
- For technical questions, anchor in the architecture diagrams; do not be afraid to flip back to a slide.
- For governance questions, anchor in Constitution v1.2.0 and the carve-out list.
- It is fine to say "I don't know — let me come back to you with the audit row."
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE}")

    prs = load_template_as_pptx(TEMPLATE)
    reset_slides(prs)
    build(prs)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(prs.slides)} slides")


if __name__ == "__main__":
    main()
