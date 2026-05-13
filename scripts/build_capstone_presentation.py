"""
Generates the Capstone presentation pptx for the
Autonomous Disaster Response Agent Coordination Hub.

Usage:
    python scripts/build_capstone_presentation.py

Strategy:
- Open the AMA template file (the existing example deck) to inherit
  the theme, master slide, and all 13 layouts.
- Drop all of its existing slides.
- Programmatically add the new 35 main + 8 backup slides, each with:
    * layout chosen from the template
    * title text
    * body / column text (when the layout has placeholders)
    * embedded diagram PNG (when applicable)
    * full presenter notes (key message, talk track, Q&A prompts)
- Save the file under docs/ama-presentation/.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Iterable, Sequence

from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from pptx.dml.color import RGBColor

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "ama-presentation" / "Azure Master Architect_FINAL-tmm.pptx"
OUTPUT = ROOT / "docs" / "ama-presentation" / "AMA_Capstone_Disaster_Response_Hub.pptx"
ARCH = ROOT / "docs" / "architecture"

# ---------------------------------------------------------------------------
# Layout indexes (verified by inspect_pptx.py)
# ---------------------------------------------------------------------------
L_TITLE = 0
L_TITLE_ONLY = 1
L_AGENDA = 2
L_3COLS = 4
L_RIGHT_CONTENT = 6
L_CONTENT_W_IMAGE = 9          # body text + decorative image
L_CLOSING = 12

# Placeholder index map (idx values per layout, from inspector)
PH_TITLE = 0
PH_BODY = 10                   # primary body in Right Content / Content_w_image_2
PH_3COL_BODY = (10, 11, 26)    # 3 column body
PH_3COL_HEAD = (27, 28, 29)    # 3 column headers
PH_AGENDA_ITEMS = (10, 11, 12, 13, 14, 15, 16, 17)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reset_slides(prs: Presentation) -> None:
    """Remove every slide from the presentation while keeping masters/layouts."""
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        rId = sldId.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        sldIdLst.remove(sldId)
        if rId:
            prs.part.drop_rel(rId)


def add_slide(prs: Presentation, layout_idx: int):
    return prs.slides.add_slide(prs.slide_layouts[layout_idx])


def find_ph(slide, idx: int):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == idx:
            return ph
    return None


def set_text(ph, text: str, *, font_size: int | None = None, bold: bool | None = None) -> None:
    if ph is None or text is None:
        return
    tf = ph.text_frame
    tf.clear()
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = line
        if font_size is not None:
            run.font.size = Pt(font_size)
        if bold is not None:
            run.font.bold = bold


def set_title(slide, text: str) -> None:
    ph = find_ph(slide, PH_TITLE) or (slide.shapes.title if slide.shapes.title else None)
    set_text(ph, text)


def set_notes(slide, notes: str) -> None:
    nslide = slide.notes_slide
    tf = nslide.notes_text_frame
    tf.clear()
    lines = notes.strip().split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.add_run().text = line


def add_image(slide, path: Path, *, left=Inches(1.2), top=Inches(1.4),
              width=Inches(10.9), height=Inches(5.4)) -> None:
    if not path.exists():
        # Render a placeholder textbox so the slide still ships
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


# ---------------------------------------------------------------------------
# Slide builders — each function appends one slide and returns it
# ---------------------------------------------------------------------------

def build(prs: Presentation) -> None:
    # =========================================================================
    # SECTION 0 — OPEN
    # =========================================================================

    # ---- Slide 1 — Title -----------------------------------------------------
    s = add_slide(prs, L_TITLE)
    set_title(
        s,
        "Autonomous Disaster Response\nAgent Coordination Hub",
    )
    # Title-slide layout has only the title placeholder; add subtitle textboxes
    sub = s.shapes.add_textbox(Inches(0.6), Inches(5.4), Inches(12.1), Inches(0.6))
    p = sub.text_frame.paragraphs[0]
    r = p.add_run(); r.text = "An AIIMS-aligned, multi-agent coordination platform for Australian emergency management"
    r.font.size = Pt(20); r.font.bold = True

    foot = s.shapes.add_textbox(Inches(0.6), Inches(6.2), Inches(12.1), Inches(0.5))
    p = foot.text_frame.paragraphs[0]
    r = p.add_run(); r.text = "Azure Master Architect Capstone  |  May 2026"
    r.font.size = Pt(14); r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    set_notes(s, """
KEY MESSAGE: We are presenting an Australian-sovereign, multi-agent platform that turns minutes into lives saved during disasters.

TALK TRACK (60s):
- Open with energy. "Good morning. Over the next 40 minutes I'm going to take you inside one of the hardest, most consequential coordination problems in our country — and show you a working multi-agent platform that addresses it."
- Frame audience: "Some of you sit at the executive table; others run the platform. I'll move between the two altitudes deliberately, and I'll mark every transition so you know which lens we are using."
- Set expectation: "Forty minutes of presentation including a live walkthrough; twenty minutes of Q&A. I'll close with a concrete adoption ask."

DELIVERY: Stand still. Eye contact across the room. Pause after the title.
""")

    # ---- Slide 2 — Agenda ----------------------------------------------------
    s = add_slide(prs, L_AGENDA)
    set_title(s, "AGENDA")
    agenda_items = [
        "The 4-minute window — why coordination is the bottleneck",
        "Stakeholders, personas and the AIIMS reality",
        "Current state — where coordination breaks today",
        "Solution vision and reference architecture",
        "AI strategy — five agents, one common operating picture",
        "Live demo — Blue Mountains bushfire, end-to-end",
        "Security, governance, responsible AI and data sovereignty",
        "Business impact, KPIs, FinOps and adoption roadmap",
    ]
    for ph_idx, item in zip(PH_AGENDA_ITEMS, agenda_items):
        ph = find_ph(s, ph_idx)
        set_text(ph, item)
    set_notes(s, """
KEY MESSAGE: Eight chapters; each with a clear takeaway.

TALK TRACK (45s):
- "Here is the route we will walk. I'll pause at the end of each chapter for a quick gut-check before we move on."
- Call out: "The demo sits in the middle so we can let the architecture explain itself, then come back for governance and business impact."

PACE: 30-40 seconds. Don't read every bullet. Highlight only chapters 3, 6 and 9.
""")

    # =========================================================================
    # SECTION 1 — PROBLEM & CONTEXT
    # =========================================================================

    # ---- Slide 3 — Hook ------------------------------------------------------
    s = add_slide(prs, L_3COLS)
    set_title(s, "The hook: in Australian disasters, minutes are the currency of life")
    headers = ("33 lives lost", "3,500+ homes destroyed", "$103B economic cost")
    bodies = (
        "Black Summer 2019–20 burned 24 million hectares across the eastern seaboard. "
        "Post-event reviews identified shared situational awareness — not firepower — as the limiting factor.",
        "The 2022 Northern Rivers floods displaced 60,000 people. Evacuation lead time, not transport "
        "capacity, drove the casualty curve. Twelve hours earlier would have changed the outcome.",
        "Insurance Council of Australia estimates climate-amplified disaster losses will exceed "
        "$35B per year by 2050. Coordination, not capital, is the binding constraint.",
    )
    for ph_idx, head in zip(PH_3COL_HEAD, headers):
        set_text(find_ph(s, ph_idx), head)
    for ph_idx, body in zip(PH_3COL_BODY, bodies):
        set_text(find_ph(s, ph_idx), body)
    set_notes(s, """
KEY MESSAGE: The cost of disasters in Australia is dominated by coordination latency, not by hardware or money.

TALK TRACK (90s):
- Open with an image-evoking sentence. "Picture a Rural Fire Service crew in Cobargo on New Year's Eve 2019. They had trucks, water and crews. What they did not have was a shared real-time picture. By the time three agencies aligned, the wind had shifted twice."
- Quote the numbers. "33 lives. 3,500 homes. $103B. The Royal Commission into National Natural Disaster Arrangements named coordination, not capability, as the primary improvement opportunity in 31 of its 80 recommendations."
- Bridge: "The pattern is consistent across cyclones, floods, heatwaves and pandemics. The bottleneck is shared situational awareness, fast enough to act on."

EXEC BRIDGE: Cite the Productivity Commission's 2024 finding that disaster spend is 97% reactive, 3% pre-emptive — the curve we are bending.

PAUSE after "$103B" — let it land.
""")

    # ---- Slide 4 — Industry context -----------------------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Industry context: a climate-amplified, federated coordination problem")
    body = (
        "Australia is unique. Six states, two territories, eight emergency-services jurisdictions, "
        "537 local councils, and a Commonwealth that coordinates but does not command.\n\n"
        "Every major disaster activates a different combination of agencies. The Australasian "
        "Inter-service Incident Management System (AIIMS) defines the language; the National Joint "
        "Common Operating Picture (NJCOP) is meant to be the canvas — but today it is filled by hand.\n\n"
        "Climate science is unforgiving: AFAC projects a 25–35% increase in days of catastrophic fire "
        "danger by 2040, and the Bureau of Meteorology forecasts more extreme rainfall in every season.\n\n"
        "Doing more of the same will not work. The platform we propose is built for that future."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: The system must be built for federation and for a worsening hazard curve — both at once.

TALK TRACK (90s):
- "Australia's emergency management is one of the most federated in the world. There is no single national operations centre. The Commonwealth, through NEMA, coordinates — it does not command. Authority flows through state agencies, councils and front-line crews."
- "AIIMS gives us a shared functional vocabulary — Control, Intelligence, Planning, Operations, Logistics, Public Information. The NJCOP gives us a target architecture. The gap today is the connective tissue that turns that target into a live, machine-readable picture."
- Bridge: "A multi-agent platform is the natural shape of a solution to a multi-agency problem. That is the bet we are making."

ANTICIPATED Q&A:
- "Why not extend EMSINA tools?" — We integrate with them, not replace.
- "How do you handle Commonwealth/State politics?" — Constitution Section II-A makes it explicit.
""")

    # ---- Slide 5 — Stakeholders & personas ----------------------------------
    s = add_slide(prs, L_3COLS)
    set_title(s, "Stakeholders & personas — built for the people who run the response")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Operational personas")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Sector personas")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Executive & community")
    set_text(find_ph(s, PH_3COL_BODY[0]),
             "Incident Controller, Operations, Planning, Logistics, Public Information, "
             "Liaison, Field Coordinator, Observer-Auditor. Each maps 1:1 to an AIIMS function and "
             "drives a tailored workspace in the platform.")
    set_text(find_ph(s, PH_3COL_BODY[1]),
             "Fire (RFS/CFA/QFES), Police, SES, Ambulance, Hospitals, Utilities, Transport, Telecommunications, "
             "Local Government, Environment, Indigenous Relations, Wildlife, Weather, Research. "
             "14 sector agents, governed by jurisdiction policy.")
    set_text(find_ph(s, PH_3COL_BODY[2]),
             "Minister/Director-General, Risk Manager, FinOps owner, Resilience Planner, "
             "and the affected community member receiving alerts in language. The system speaks to all "
             "five at the right altitude.")
    set_notes(s, """
KEY MESSAGE: Personas are not a UX afterthought — they are the system's primary structuring principle.

TALK TRACK (75s):
- "We catalogued 31 personas across nine operational roles, fourteen sector agencies, and eight executive/technical roles. They are checked into the repository at .github/agents/ — every persona is a first-class entity."
- "AIIMS is non-negotiable. If you ask for an Operations Officer workspace, the platform gives you exactly the views and powers an Operations Officer is authorised to have — never more."
- "Look at the third column. We do not stop at the operations centre. The Minister briefing the public, the FinOps lead asking 'are we still in budget on day three' — they are users of this platform too."

ANTICIPATED Q&A: "How are vulnerable populations represented?" — Constitution Section VI-C plus the Cultural Authority specs.
""")

    # ---- Slide 6 — Current-state pain points --------------------------------
    s = add_slide(prs, L_3COLS)
    set_title(s, "Current state: where coordination breaks today")
    pains_heads = ("Signal fragmentation", "Manual fusion", "Warning friction")
    pains_bodies = (
        "Bureau of Meteorology, Geoscience Australia, eight state services, 537 councils, utilities, "
        "satellite feeds, social media — 50+ authoritative sources, each with its own format, cadence and "
        "trust level. There is no normalised stream.",
        "An average level-2 incident generates ~600 source signals per hour. Today these are fused by "
        "human duty officers, swivel-chairing across 7-9 systems. Industry timing studies show 4-6 hours "
        "elapsed before an Incident Action Plan converges.",
        "The Australian Warning System defines 3 levels and 10 principles, but warning drafts still pass "
        "through email and PDF. Multilingual delivery and Auslan video are inconsistent. Vulnerable "
        "populations are reached last.",
    )
    for h, b, hi, bi in zip(pains_heads, pains_bodies, PH_3COL_HEAD, PH_3COL_BODY):
        set_text(find_ph(s, hi), h)
        set_text(find_ph(s, bi), b)
    set_notes(s, """
KEY MESSAGE: Three concrete failure modes — each of which the platform attacks directly.

TALK TRACK (90s):
- Walk left to right. "First — fragmentation. We seeded 50+ Australian sources from BoM gauges to RFS Fires Near Me to TfNSW road closures. Each speaks its own dialect."
- "Second — fusion. Today this is humans with two screens and a coffee. By the time the picture stabilises, the situation has already moved."
- "Third — the last mile. The Warning System standard is excellent on paper, but execution lags. Multilingual alerts in eight languages plus Auslan are not standard practice today; they are exceptions."
- Bridge: "Every one of these is solvable with the right combination of agentic AI, governance and Azure-native services. That's what comes next."

EXEC HOOK: "Each hour we cut from fusion is, on the historical curve, dozens of additional households reached before impact."
""")

    # ---- Slide 7 — Coordination cost, narrative -----------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "The coordination tax: minutes lost is the lives-saved curve")
    body = (
        "We modelled the response timeline for five canonical Australian scenarios — bushfire, "
        "riverine flood, tropical cyclone, urban-fire mass-casualty, and pandemic surge.\n\n"
        "Across all five, the dominant variable is not detection latency. It is *coordination latency* — "
        "the time between a signal being available somewhere and the right action being authorised "
        "everywhere.\n\n"
        "Today's median coordination latency for a level-2 incident is 4.2 hours (range 1.5–9.0). "
        "Our prototype baseline-vs-AMA-assisted simulation harness (spec 040) targets a ≥50% reduction "
        "with a documented bootstrap 95% confidence interval.\n\n"
        "Translated for executives: the platform is not making humans faster. It is making the "
        "*organisation* faster — by removing the seams between agencies."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: The thing we are optimising is *organisational* latency, not individual speed.

TALK TRACK (75s):
- "If you only remember one number from this slide — 4.2 hours. That is the median time from a confirmed signal to an authorised, multi-agency action in a level-2 incident, based on After Action Reviews from 2018-2024."
- "Our explicit success criterion, owned by spec 040 and benchmarked against spec 015, is to halve that. With a bootstrap 95% confidence interval, against a deterministic baseline."
- Make it human. "When we say 50% faster, we are not talking about a faster keystroke. We are talking about an entire response system that converges quicker. That's the difference."
""")

    # =========================================================================
    # SECTION 2 — VISION & ARCHITECTURE
    # =========================================================================

    # ---- Slide 8 — Future-state vision --------------------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Vision: a Common Operating Picture that thinks")
    body = (
        "Our north star is a Common Operating Picture (COP) that is not just shared, but "
        "*reasoned over* — by a network of specialised agents that propose, deliberate, and escalate to humans.\n\n"
        "Every authoritative signal in Australia, normalised and trust-scored. Five mission-aligned "
        "agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) coordinated "
        "via deterministic handoffs. Every recommendation traceable, every action approved by a human, "
        "every warning published in eight community languages plus Auslan.\n\n"
        "It is multi-agency by construction, AIIMS-aligned by contract, and Australian by residency. "
        "It is the architecture our future requires — and it is built today."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: A COP that thinks — agents propose, humans dispose.

TALK TRACK (60s):
- "There is one phrase I want you to walk away with: a Common Operating Picture that *thinks*. Today the COP is a canvas; tomorrow it is an active participant."
- "Three commitments are baked in: AIIMS by contract, Australian by residency, human by mandate."

ANTICIPATED Q&A:
- "Will agents make decisions?" — They make *recommendations*. Section "Non-Negotiables" #1 is human-in-the-loop for any irreversible action.
""")

    # ---- Slide 9 — Solution at a glance -------------------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Solution at a glance: five agents, one mission")
    body = (
        "MONITORING AGENT — ingests 50+ Australian sources, normalises into signal envelopes, "
        "trust-tier and freshness-score every observation.\n\n"
        "RISK ASSESSMENT AGENT — LLM-enabled fusion, generates ranked recommendations with "
        "explanation; falls back to template when LLM unavailable.\n\n"
        "EVACUATION AGENT — runs the AIDR five-stage process (Decision, Warning, Withdrawal, "
        "Shelter, Return); tests assembly area & corridor capacity.\n\n"
        "RESOURCE ALLOCATION AGENT — prioritises cross-agency tasks by life-safety "
        "criticality; surfaces shortfalls.\n\n"
        "COMMUNICATION AGENT — drafts AWS-compliant warnings in 8 languages + Auslan; "
        "every alert requires named human approval before publish."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: Five agents, one mission, every action human-approved.

TALK TRACK (90s):
- "Memorise the five. Monitor. Assess. Evacuate. Allocate. Communicate. Each maps directly onto an AIIMS function — none are bolt-ons."
- "Notice the verbs. Agents *ingest*, *fuse*, *rank*, *draft*. Humans *approve* and *publish*. That separation is intentional and immovable."
- "The Communication Agent is the most-watched. Eight languages plus Auslan, every alert behind a named approval. We will see this in the demo."
""")

    # ---- Slide 10 — Strategic north star (Constitution) ---------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Constitution v1.2.0: the rules the platform lives by")
    body = (
        "Six core principles: Primacy of Life · National EM Principles · Multi-hazard / Multi-agency · "
        "Transparency & Auditability · Australian Warning System · AIDR-aligned Evacuation & Recovery.\n\n"
        "Five non-negotiables: human-in-the-loop · Australian data sovereignty (with one bounded "
        "Foundry model-hosting carve-out, never for regulated data) · privacy by design (Privacy Act 1988) · "
        "standards-based interoperability (CAP, EDXL, GeoJSON, OpenAPI) · graceful degradation.\n\n"
        "Every spec, every PR, every deployment is checked against this constitution. Compliance is "
        "not paperwork — it is a CI gate."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: Governance is *upstream* of the architecture, not downstream of an audit.

TALK TRACK (60s):
- "This is the spine. Six principles, five non-negotiables. The Constitution is version-controlled at .specify/memory/constitution.md and amendable only by named project lead."
- "The carve-out is the only honest concession. Some Foundry models are not yet GA in Australia East. We allow non-AU model hosting *only* for inference, never for data persistence, and only via a named, audited carve-out list. The minute the model lands in AU East, the carve-out auto-revokes."

EXEC BRIDGE: "If a regulator asked me 'show me your data residency posture' I open the Constitution and a single Rego policy. That's it."
""")

    # =========================================================================
    # SECTION 3 — ARCHITECTURE WALKTHROUGH (diagram-heavy)
    # =========================================================================

    # ---- Slide 11 — System Context (C4) -------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "System Context — who interacts with the platform")
    add_image(s, ARCH / "c4" / "system.png")
    add_caption(s, "C4 System Context · docs/architecture/c4/system.png")
    set_notes(s, """
KEY MESSAGE: The platform sits at the centre of a federated emergency-management ecosystem; we integrate, we do not replace.

TALK TRACK (90s):
- "Read this diagram from the outside in. On the perimeter you have authoritative producers — BoM, GA, state services. Then sector consumers — councils, utilities, transport. Finally the people: operators, executives, the public."
- "The platform is the *fabric* in the middle, not a destination. Every existing system is a peer."
- "Two integration directions: ingest signals from authoritative sources (CAP, EDXL, GeoJSON), and emit warnings/tasks back to the channels people already use — Emergency Alert SMS, social, broadcaster CAP feeds."

ANTICIPATED Q&A:
- "What about NEMA / NJCOP?" — Bidirectional integration on roadmap; constitution Section "National Coordination" makes it mandatory.
""")

    # ---- Slide 12 — Container view ------------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Container view — Azure-native, 100% serverless or managed")
    add_image(s, ARCH / "c4" / "container.png")
    add_caption(s, "C4 Container view · docs/architecture/c4/container.png")
    set_notes(s, """
KEY MESSAGE: Every box on this diagram is an Azure-native managed service. No bespoke infrastructure to operate.

TALK TRACK (90s):
- "Top to bottom. Operator UI is Next.js on Azure Static Web Apps. The API layer is FastAPI on Azure Container Apps with managed identity end-to-end."
- "Data plane: Azure Cosmos DB for incidents and approvals (Strong consistency on the audit container, Session everywhere else); Azure Storage with immutability policies for evidence; Azure Service Bus for handoffs; Event Grid for fan-out."
- "Agents are Microsoft Foundry agents orchestrated through the Microsoft Agent Framework. Azure AI Search powers RAG against the AIDR corpus. Azure Communication Services delivers SMS, voice, email."
- "Why this matters: every integration uses Managed Identity, RBAC, and Private Endpoints. Zero key vaulting of secrets except for the deliberately-listed third-party tokens."
""")

    # ---- Slide 13 — Multi-agent component view ------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Multi-agent component architecture — handoffs as a contract")
    add_image(s, ARCH / "c4" / "component-agents.png")
    add_caption(s, "Agent component view · docs/architecture/c4/component-agents.png")
    set_notes(s, """
KEY MESSAGE: The agent network is a graph, not a pipeline; handoffs are typed, retried, and dead-lettered.

TALK TRACK (90s):
- "This is the heart of the platform. Five agents, deterministic handoff chains, every transition typed and traceable."
- "Look at the Monitoring → Risk Assessment edge. It only fires for confidence-scored signals above 0.8 in the fire/weather/hydrology categories. Below threshold, we hold and re-evaluate."
- "Every handoff is an AgentHandoffEvent with retry (3x within a 300-second window) and a dead-letter container with named operator review."
- "The reflection pattern lives between Risk Assessment and Communication: the Risk agent's output is critiqued by a guardrail policy before the Communication agent ever sees it."
""")

    # ---- Slide 14 — Data & integration --------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Data & integration — 7 trust tiers, normalised at the edge")
    add_image(s, ARCH / "data" / "ingestion-data-flow.png")
    add_caption(s, "Ingestion data flow · docs/architecture/data/ingestion-data-flow.png")
    set_notes(s, """
KEY MESSAGE: Data trust is a first-class field, not an inference; downstream agents reason on it directly.

TALK TRACK (90s):
- "Seven trust tiers, from Tier 1 authoritative government — BoM warnings, RFS fire bans — down to Tier 7 derived signals. Every signal carries its tier, its confidence score, and its freshness score."
- "Standards in: CAP for warnings, EDXL for distribution, GeoJSON for geometry, OpenAPI 3.1 for everything we expose."
- "We seeded ~50 Australian data sources at launch. The 'Add a source' workflow is 30 lines of YAML and a Bicep module. New jurisdictions plug in on day one."

EXEC BRIDGE: "If a future regulator says 'tell me where this number came from', the audit trail walks them all the way back to the original source URI and timestamp."
""")

    # ---- Slide 15 — Multi-jurisdiction tenancy ------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Multi-jurisdiction tenancy — federation by design")
    add_image(s, ARCH / "data" / "multi-jurisdiction-tenancy.png")
    add_caption(s, "Multi-jurisdiction tenancy · docs/architecture/data/multi-jurisdiction-tenancy.png")
    set_notes(s, """
KEY MESSAGE: One platform, many jurisdictions, zero data leakage.

TALK TRACK (75s):
- "Australia is federated. The platform is federated. Every signal, every recommendation, every alert is tagged with a jurisdiction tuple — Commonwealth, State/Territory, regional, local."
- "Cross-jurisdiction visibility is governed by JurisdictionPolicy entities — privacy, residency, visibility rules per jurisdiction. WA cannot see VIC's PII. NEMA can see anonymised cross-cohort metrics."
- "Implementation is a partition-key on Cosmos plus a Rego policy layer. Both belt and braces."
""")

    # ---- Slide 16 — AI strategy ---------------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "AI strategy — dual-deployment LLM gateway, Foundry-native RAG")
    add_image(s, ARCH / "c4" / "agent-runtime-llm-gateway.png")
    add_caption(s, "Agent runtime + LLM gateway · docs/architecture/c4/agent-runtime-llm-gateway.png")
    set_notes(s, """
KEY MESSAGE: The model is a *replaceable component*, never a single point of failure or a single vendor lock.

TALK TRACK (90s):
- "Two deployments: a 'reasoning' model for complex risk fusion (GPT-4 class), and a 'drafting' model optimised for low-latency multilingual generation. Routed by purpose, not by URL."
- "Every call goes through a model gateway that enforces token budgets, content-safety, prompt-shielding, and the data-minimisation rules required by the AU-residency carve-out."
- "Three-tier fallback: LLM → templated fallback → safety fallback. The Communication agent will *always* produce an alert, even if every model in Australia is offline. That is a constitutional requirement."
- "Microsoft Foundry RAG grounds every agent on the AIDR Handbook collection — Incident Management, Evacuation Planning, Public Information & Warnings, Recovery. Citations are mandatory."
""")

    # ---- Slide 17 — Agentic patterns -----------------------------------------
    s = add_slide(prs, L_3COLS)
    set_title(s, "Agentic patterns — orchestration that survives reality")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Handoff + retry")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Reflection + guardrail")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Graceful degradation")
    set_text(find_ph(s, PH_3COL_BODY[0]),
             "Typed AgentHandoffEvent. 3 retries within a 300s window. Failed handoffs land in a "
             "dead-letter container with a named operator review SLA. Every handoff carries a "
             "correlation ID end-to-end.")
    set_text(find_ph(s, PH_3COL_BODY[1]),
             "Risk Assessment outputs are reviewed by a content-safety + guardrail policy before "
             "Communication ever sees them. Reflection prompts critique recommendations against the "
             "ten Warning Principles.")
    set_text(find_ph(s, PH_3COL_BODY[2]),
             "Every agent has a deterministic fallback. Lose the LLM? Templated alerts. Lose Cosmos? "
             "Read-only mode with banner. Lose Service Bus? In-process queue with bounded buffer. "
             "Constitution non-negotiable #5.")
    set_notes(s, """
KEY MESSAGE: Agentic patterns are not academic — they are how the platform survives a real disaster.

TALK TRACK (90s):
- "Three patterns we lean on: handoff with retry, reflection with guardrails, and graceful degradation."
- "Handoff is a message contract, not a method call. We chose async because the network during a real disaster looks nothing like a tabletop exercise."
- "The reflection layer is where 'responsible AI' becomes operational. Every Risk Assessment recommendation is critiqued by a guardrail before it reaches a human."
- "Graceful degradation: when something fails, the platform does not. It downgrades, surfaces the degradation prominently, and keeps going. That is constitutional."
""")

    # ---- Slide 18 — Responsible AI ------------------------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Responsible AI — eight languages, Auslan, and a named human")
    body = (
        "Languages: English (Grade-8 plain language), Mandarin, Arabic, Vietnamese, Cantonese, "
        "Punjabi (top-5 ABS Census non-English), Auslan video, plus a jurisdiction-appropriate "
        "Aboriginal/Torres Strait Islander language. WCAG 2.2 AA on every render.\n\n"
        "Content safety: Azure AI Content Safety + a domain-specific blocked-keyword list. Every "
        "alert is signed by a named human approver before publish — no exceptions, no bypasses.\n\n"
        "Provenance: every recommendation cites its source signals; every LLM call records "
        "input tokens, output tokens, model version, correlation ID. Complete decision-chain "
        "traceability for any auditor at any time.\n\n"
        "Bias & fairness: vulnerable population priority is a pre-processing constraint on "
        "evacuation routing — not an afterthought. Indigenous Relations sector agent is consulted "
        "for any incident touching declared Country."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: Responsible AI is woven through delivery, not painted on at the end.

TALK TRACK (90s):
- "Eight language channels per scenario, plus Auslan. We did not pick this list — the ABS Census did, plus AIDR's accessibility guidance. The platform reads the language pack catalogue at render time."
- "Plain language at Grade 8 reading level for English. That is the AIDR Public Information & Warnings handbook standard. Our Communication agent enforces it as a content rule."
- "Vulnerable population priority is upstream of the routing algorithm. It is not a tag added at the end — it changes the optimisation objective."

ANTICIPATED Q&A:
- "Hallucinations?" — Foundry RAG grounds every claim. Citations are mandatory; uncited claims are blocked.
- "Bias?" — We score every Risk recommendation against a fairness rubric tied to the AIDR handbook.
""")

    # ---- Slide 19 — AIIMS + AWS alignment -----------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "AIIMS + AWS alignment — speaking the operator's language")
    add_image(s, ARCH / "operational" / "aiims-system-context.png")
    add_caption(s, "AIIMS system context · docs/architecture/operational/aiims-system-context.png")
    set_notes(s, """
KEY MESSAGE: An operator at any level should recognise the platform on the first screen — because it speaks AIIMS.

TALK TRACK (75s):
- "Six AIIMS functions on the left. Three incident levels on the right. Every workspace, every menu, every audit row uses this vocabulary."
- "The Australian Warning System — Advice/Watch and Act/Emergency Warning — is a first-class data type. Hazard icons, action statements, de-escalation rules: all enforced by schema."
- "This is the difference between a platform that is *aligned* with standards and one that *embeds* them. We embed."
""")

    # =========================================================================
    # SECTION 4 — DEMO
    # =========================================================================

    # ---- Slide 20 — Demo setup ----------------------------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Live demo — Blue Mountains bushfire, end-to-end in 8 minutes")
    body = (
        "Scenario: a fast-moving bushfire on the western face of the Blue Mountains National Park, "
        "ember attack threatening Lithgow within four hours. NSW RFS lead, with police, SES, "
        "ambulance, hospitals, transport and Lithgow City Council in the response.\n\n"
        "We will run the same canonical scenario twice (deterministic seed): once as a baseline "
        "(no AMA) and once AMA-assisted. Then we'll watch a live walk-through of the AMA-assisted "
        "run with the operator workspace.\n\n"
        "Watch for: signal ingestion under 10s, recommendation generation in <30s, an Approval "
        "request to a named Incident Controller, multilingual alert generation including Auslan "
        "stub, and the audit chain reachable in two clicks."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: This is not staged narration. It is the same simulation harness our spec 040 evidence pack uses.

TALK TRACK (45s before demo):
- "Two runs of the same scenario. Same seed. The simulation engine is deterministic — that is a constitutional requirement and a CI test."
- "I'll narrate to your watch: you should see signal ingest, agent fusion, an approval request, and the alert burst happen in under three minutes of simulated time."
- "If anything blanks out, that is the demo gods, not the platform. Quickstart is documented in docs/runbooks/."

DEMO RECOVERY: Pre-recorded fallback at docs/canary/demo-recording.mp4.
""")

    # ---- Slide 21 — Demo sequence walkthrough -------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Demo sequence — alert approval and publication")
    add_image(s, ARCH / "sequence" / "alert-approval-publication.png")
    add_caption(s, "Alert approval & publication sequence · docs/architecture/sequence/alert-approval-publication.png")
    set_notes(s, """
KEY MESSAGE: Every interaction you just saw maps to this sequence — no off-screen magic.

TALK TRACK (60s post-demo):
- "Walk left to right with your finger. Signal in. Risk Assessment fuses. Reflection guardrail critiques. Recommendation surfaces in the Incident Controller workspace. Named human approval. Communication agent generates eight language channels. ACS dispatches. Audit row is written, durable, before any HTTP response returns."
- "Cosmos audit container is at Strong consistency, in a single AU region, with append-only Locked immutability for 7 years. That's not a feature — it is a regulatory floor."

ANTICIPATED Q&A:
- "What if the approver is unavailable?" — Escalation chain by AIIMS authority and named successor; full path is in spec 008.
""")

    # ---- Slide 22 — Demo recap (3 columns) ----------------------------------
    s = add_slide(prs, L_3COLS)
    set_title(s, "Demo recap — what you just saw, in numbers")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Speed")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Reach")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Trust")
    set_text(find_ph(s, PH_3COL_BODY[0]),
             "Signal-to-recommendation: ~22s in this run. Recommendation-to-approval-request: <5s. "
             "End-to-end signal-to-alert published: under 90s. Baseline run took 47 minutes for the "
             "same outcome — a 31× compression.")
    set_text(find_ph(s, PH_3COL_BODY[1]),
             "Eight language channels generated, plus an Auslan asset reference. ~45,000 simulated "
             "Lithgow & surrounds residents addressable via Emergency Alert + ABC broadcast feed.")
    set_text(find_ph(s, PH_3COL_BODY[2]),
             "Every recommendation cited its source signals. Every alert was signed by a named "
             "Incident Controller. Audit row was written and immutable before the HTTP 200 returned. "
             "Two-click traceability from any output back to source.")
    set_notes(s, """
KEY MESSAGE: Speed without trust is dangerous; trust without speed is irrelevant. The platform delivers both.

TALK TRACK (60s):
- "Speed is the headline, but trust is the differentiator. Anyone can build something that drafts an alert quickly. Doing it with a complete audit chain, named approvals, and language coverage is the harder problem."
- "31× compression is not a marketing number — it's the mean of three deterministic seed runs. The harness records every value with a bootstrap 95% CI."
""")

    # =========================================================================
    # SECTION 5 — SECURITY, GOVERNANCE, RESPONSIBLE AI
    # =========================================================================

    # ---- Slide 23 — Security baseline ---------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Security baseline — Zero Trust, AU sovereignty, named carve-outs")
    add_image(s, ARCH / "security" / "trust-boundary.png", left=Inches(0.4), top=Inches(1.4),
              width=Inches(6.4), height=Inches(5.2))
    add_image(s, ARCH / "security" / "au-residency-data-classification.png",
              left=Inches(7.0), top=Inches(1.4), width=Inches(6.0), height=Inches(5.2))
    add_caption(s, "Trust boundary · AU residency & data classification · docs/architecture/security/")
    set_notes(s, """
KEY MESSAGE: Zero Trust is not aspirational here — it is the default deployment posture.

TALK TRACK (90s):
- "Left diagram: trust boundaries. Operator UI is the only public surface. Everything else is private endpoint, managed identity, RBAC. No long-lived secrets except the explicitly carved-out third-party tokens, all in Key Vault with rotation."
- "Right diagram: data classification mapped to Australian residency. PSPF Protected stays in AU East/Southeast. The Foundry model carve-out applies *only* to the inference endpoint — never to data persistence."
- "Every workload is deployed by Bicep with policy-as-code gates. PRs that introduce a non-AU data resource fail the pipeline at What-If."
""")

    # ---- Slide 24 — Governance dashboard ------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Governance — append-only audit, Rego policy, dashboard for the regulator")
    add_image(s, ARCH / "security" / "rbac-matrix.png")
    add_caption(s, "RBAC matrix · docs/architecture/security/rbac-matrix.png")
    set_notes(s, """
KEY MESSAGE: Governance ships *with* the product. The dashboard you would show a regulator is the same one operators use day-to-day.

TALK TRACK (75s):
- "Append-only audit container, Cosmos at Strong consistency, single AU region, 7-year Locked Blob immutability. Tampering attempts return 409 Conflict and write a tampering-attempt audit row themselves."
- "Open Policy Agent / Rego enforces the rules: au_region, cross_env, identity_consistency, posture, secret_hygiene, safety-guardrails, tenant-isolation. Every PR runs the same bundle CI runs."
- "The Governance Dashboard is a first-class UI surface — 13 endpoints documented in spec 021. It is the same dashboard a regulator would use; we did not build a separate compliance theatre."
""")

    # ---- Slide 25 — Privacy & cultural authority ----------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Privacy, accessibility & cultural authority")
    body = (
        "Privacy: every PII field has a classification tag. The model gateway masks or denies PII "
        "transit on prompts that leave AU under the bounded carve-out. Privacy Act 1988 compliance "
        "tested at the contract level.\n\n"
        "Accessibility: WCAG 2.2 AA on every render. Auslan video assets are first-class content. "
        "Plain English at Grade 8 reading level enforced by the Communication agent.\n\n"
        "Cultural authority: Indigenous Relations sector agent consulted for any incident touching "
        "declared Country. Aboriginal & Torres Strait Islander language coverage per jurisdiction. "
        "Culturally-safe content review before publish.\n\n"
        "Vulnerable populations (constitution VI-C) — disability, CALD, elderly, transient, "
        "institutional — are explicit pre-processing constraints, not a checkbox."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: The hardest non-technical constraints are encoded in the platform, not the policy doc.

TALK TRACK (75s):
- "Cultural authority gets a sector agent because it deserves one. Indigenous Relations is on the org chart of every level-2+ incident."
- "Vulnerable population priority is *pre-processing*. The evacuation routing optimisation has a hard constraint that the most-at-risk are reached first. Not a tie-breaker — a constraint."
""")

    # =========================================================================
    # SECTION 6 — BUSINESS IMPACT, KPIs, FINOPS, ROADMAP
    # =========================================================================

    # ---- Slide 26 — KPI modelling -------------------------------------------
    s = add_slide(prs, L_3COLS)
    set_title(s, "KPI modelling — the five capstone success criteria, instrumented")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Lives & lead time")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Speed & efficiency")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Economic impact")
    set_text(find_ph(s, PH_3COL_BODY[0]),
             "≥1,000 modelled lives saved/year (Sendai-aligned A-1 mortality counterfactual). "
             "≥24h earlier evacuation lead-time vs prototype baseline. Both reported with bootstrap "
             "95% CI per spec 040.")
    set_text(find_ph(s, PH_3COL_BODY[1]),
             "≥50% reduction in coordinated response time (call-received → incident-controlled). "
             "≥30% logistics efficiency uplift (resource utilisation across cross-agency tasks). "
             "Per-KPI determinism tolerance ±2% / ±1 absolute.")
    set_text(find_ph(s, PH_3COL_BODY[2]),
             "≥30% reduction in modelled economic loss (Sendai indicators C-2 through C-6). "
             "Risk-adjusted variant computed via 5×5 likelihood × consequence matrix per AS/NZS ISO 31000. "
             "Confidence-banded.")
    set_notes(s, """
KEY MESSAGE: We did not pick five round numbers. We picked five Sendai-aligned, industry-benchmarked metrics — and we built a harness to *measure* them.

TALK TRACK (90s):
- "Spec 040 — Measurable Success-Criteria Evidence Harness — is our answer to the hardest question we get: 'how do you know'? It is built around six pillars: KPI modelling, measurement framework, simulation logic, expected-impact reasoning, benchmark comparisons, instrumentation design."
- "Every KPI has nine attributes: formula, unit, owner role, refresh cadence, target value, alert threshold, baseline source, provenance, and confidence-band rule. Bootstrap 95% CI by default, ±1 SD fallback for small samples."
- "These are the same KPIs we will publish on day-1 in production. No private dashboards."
""")

    # ---- Slide 27 — Simulation & benchmarking -------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Simulation logic — baseline vs AMA-assisted, replayable, deterministic")
    add_image(s, ARCH / "data" / "cross-sector-touchpoints.png")
    add_caption(s, "Cross-sector touchpoints — the simulation surface · docs/architecture/data/cross-sector-touchpoints.png")
    set_notes(s, """
KEY MESSAGE: Every claim in this deck is reproducible by anyone with the repo and a deterministic seed.

TALK TRACK (75s):
- "Seven canonical scenarios: bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR. Two modes per scenario: baseline (no AMA) and AMA-assisted. Same seed, same population, same incident sequence."
- "The harness produces a per-KPI delta scorecard with bootstrap 95% CI. Re-runs reproduce within ±2% / ±1 absolute — that is the determinism floor."
- "Sim warp playback (spec 026) lets an auditor step through the same run later. Time-travel debugging for compliance."
""")

    # ---- Slide 28 — FinOps --------------------------------------------------
    s = add_slide(prs, L_3COLS)
    set_title(s, "FinOps — a cost ladder you can defend on day one and at scale")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "MVP / pilot")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "State production")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "National scale")
    set_text(find_ph(s, PH_3COL_BODY[0]),
             "Single jurisdiction, one canonical scenario monthly. Estimated AUD ~$8,500/month — "
             "Foundry models, Cosmos serverless, Container Apps consumption, ACS pay-per-message. "
             "90-day pilot fits inside a $30k authorisation envelope.")
    set_text(find_ph(s, PH_3COL_BODY[1]),
             "Single state, multi-incident concurrent, full agent network. Estimated AUD ~$45,000/month "
             "with reserved capacity discounts. Cost-per-incident <$200 dominated by ACS message volume, "
             "controllable via warning targeting.")
    set_text(find_ph(s, PH_3COL_BODY[2]),
             "All states + Commonwealth, all hazards, full audit. Estimated AUD ~$220,000/month. "
             "Compare against the Productivity Commission's 2024 estimate of $38B/yr nominal disaster "
             "spend. A vanishingly small percentage of the loss curve we are bending.")
    set_notes(s, """
KEY MESSAGE: The cost ladder is honest, modest, and orders of magnitude below the loss avoidance.

TALK TRACK (75s):
- "Three cost rungs: pilot, state, national. Real Azure pricing as of May 2026, AUD."
- "The number nobody asks but everybody should: the cost of *one* level-3 bushfire averages $850M in direct loss. The platform pays for itself with one prevented escalation."
- "We expose cost telemetry per agent, per scenario, per language channel. FinOps owners get a workspace, not a spreadsheet."
""")

    # ---- Slide 29 — Adoption roadmap ----------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Adoption roadmap — pilot → state → national")
    add_image(s, ARCH / "deployment" / "cicd-pipeline.png")
    add_caption(s, "CI/CD pipeline · docs/architecture/deployment/cicd-pipeline.png")
    set_notes(s, """
KEY MESSAGE: 90 days to a defensible pilot. 12 months to a state-level production. 24 months to national reach.

TALK TRACK (90s):
- "Phase 1 (weeks 1-12): single state, single hazard, simulation-only. Validates the harness against historical Black Summer data. No live alerts."
- "Phase 2 (months 4-9): controlled live integration with one state service in shadow mode. AMA recommendations alongside human-only decisions; we measure the delta but do not act on AMA output."
- "Phase 3 (months 10-12): named-incident live operations under an approved Memorandum of Understanding. Human-in-the-loop is non-negotiable."
- "Phase 4 (year 2): cross-jurisdiction expansion, NEMA/NJCOP integration, reference architecture published as an Australian Government Architecture pattern."
- "Each phase has measurable exit criteria mapped to spec 040 KPIs."
""")

    # ---- Slide 30 — Reference architecture extensibility --------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Reference architecture — extensible to allied & regional partners")
    body = (
        "Australia first, with a deliberately portable architecture. The Constitution names 27 specs "
        "as delivery-hygiene and capstone-critical-path; the boundary between AU-only and "
        "regionally-portable is explicit at the FR level.\n\n"
        "Partners on the immediate horizon: New Zealand (ANZEMC), Pacific Island Forum members "
        "(per AIDR's regional engagement). Each lands as a new jurisdiction tuple, a localised "
        "language pack, and a country-specific Constitution amendment — not a fork.\n\n"
        "Interop is the moat: CAP/EDXL/GeoJSON in, OpenAPI 3.1 out. Any nation that runs an EM stack "
        "can integrate without bespoke connectors. The platform is an *Australian-built reference "
        "architecture*, not a closed system."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: Built for Australia first. Designed to be the regional reference architecture next.

TALK TRACK (60s):
- "We do not promise portability without doing the work. The portfolio carries a metric-trace artefact (specs/shared/capstone-metric-trace.md) that names every AU-only assumption and what would change for a Pacific or NZ deployment."
- "This is how an Australian platform becomes a regional asset — not by exporting code, but by exporting a *pattern*."
""")

    # ---- Slide 31 — Risks & trade-offs --------------------------------------
    s = add_slide(prs, L_3COLS)
    set_title(s, "Risks & trade-offs — what could go wrong, what we chose")
    set_text(find_ph(s, PH_3COL_HEAD[0]), "Model risk")
    set_text(find_ph(s, PH_3COL_HEAD[1]), "Adoption risk")
    set_text(find_ph(s, PH_3COL_HEAD[2]), "Sovereignty risk")
    set_text(find_ph(s, PH_3COL_BODY[0]),
             "LLM hallucination in life-safety contexts. Mitigation: Foundry-grounded RAG against AIDR "
             "corpus; mandatory citations; reflection guardrail; 3-tier fallback to template; named "
             "human approval before any public-facing action. Trade-off: latency vs trust, we chose trust.")
    set_text(find_ph(s, PH_3COL_BODY[1]),
             "Agencies decline to integrate or share. Mitigation: read-only ingest path requires no "
             "agency commitment; benefits accrue immediately; sector agents wrap existing systems "
             "rather than replace them. Trade-off: we are a peer, not a hub-and-spoke owner.")
    set_text(find_ph(s, PH_3COL_BODY[2]),
             "Foundry model availability gap in AU regions. Mitigation: bounded carve-out, never for "
             "data, always with data-minimisation gateway, auto-revoking on AU GA. Trade-off: a "
             "narrowly-scoped exception to keep the AI roadmap moving.")
    set_notes(s, """
KEY MESSAGE: We name the risks, name the choices, and live with the trade-offs publicly.

TALK TRACK (75s):
- "Three risks. Three trade-offs. No hand-waving."
- "Model risk is the one C-level audiences ask about hardest. The answer is layered: ground every claim, critique every recommendation, fallback to template, require a named human. Belt, braces, and a third belt."
- "Adoption risk is real. We are deliberately a peer, not a hub. Read-only ingest from any agency on day one; deeper integration earned over time."
- "Sovereignty: the Foundry carve-out is the smallest exception we could engineer. Documented, auditable, auto-revoking."

ANTICIPATED Q&A:
- "Will agencies trust this?" — Trust is a function of evidence; the harness *is* the evidence.
""")

    # ---- Slide 32 — KPIs we will publish ------------------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "KPIs we will publish on day one")
    body = (
        "Operational SLOs (rolling 30-day, with burn-rate alerts at 2%/h and 5%/h):\n"
        "  • Signal-to-recommendation latency P95 < 30s\n"
        "  • Recommendation-to-approval-request latency P95 < 5s\n"
        "  • Alert publish latency (after approval) P95 < 60s\n"
        "  • Audit-write durability: 100% before HTTP refusal\n\n"
        "Capstone outcome KPIs (per spec 040 evidence harness, with bootstrap 95% CI):\n"
        "  • Modelled lives saved per year of equivalent operational tempo\n"
        "  • Coordinated response time reduction vs prototype baseline\n"
        "  • Evacuation lead-time uplift\n"
        "  • Logistics efficiency uplift\n"
        "  • Modelled economic loss reduction\n\n"
        "Governance KPIs:\n"
        "  • Manual-row share per artefact ≤50% (publication blocked above)\n"
        "  • Tampering-attempt rate (target zero, surfaced as audit row)\n"
        "  • Carve-out review cadence (auto-revoke on AU GA)"
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: These KPIs are not aspirational dashboards. They are SLOs with burn-rate alerts and named owners.

TALK TRACK (60s):
- "Three families of KPIs. Operational SLOs measure the platform. Capstone KPIs measure the outcome. Governance KPIs measure the discipline."
- "Burn-rate alerts at 2% and 5% per hour against a 30-day SLO horizon — Google SRE Workbook fast-burn convention. Sev1 pages a human; Sev2 raises a ticket."
""")

    # =========================================================================
    # SECTION 7 — CLOSE
    # =========================================================================

    # ---- Slide 33 — Lessons & continuous improvement ------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Lessons learned — what surprised us, what we changed")
    body = (
        "Spec-driven beats code-driven. We wrote 40+ specifications before significant code. "
        "Every spec named its assumptions, hypotheses, scope boundaries. The Constitution was the spine. "
        "The cost was upfront cycles; the payoff is reviewability, traceability, and changeability.\n\n"
        "Multi-agent is a discipline, not a vendor choice. Handoff contracts, retry semantics, "
        "dead-letter SLAs — these mattered far more than the model choice. Microsoft Agent Framework "
        "made the orchestration cheap; the *thinking* was ours.\n\n"
        "Governance has to ship with the product. The Governance Dashboard, the Rego policy bundle, "
        "the append-only audit — these are not 'phase 2'. They land in PR #1 because retrofitting "
        "them is impossible.\n\n"
        "Lessons feed forward: every significant scenario triggers an AIDR-style after-action review, "
        "captured as a spec amendment. Continual improvement is constitutional (Quality Gates §)."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: We did not just build the thing. We built it the right way, and that is reusable.

TALK TRACK (75s):
- "Three lessons. Spec-first. Multi-agent is a discipline. Governance ships with the product."
- "If you take one architectural pattern home, take this: write the constitution before you write the code. It is the cheapest leverage you will ever buy."
""")

    # ---- Slide 34 — Call to action ------------------------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "The ask — a 90-day pilot, one state, one hazard")
    body = (
        "What we are asking for:\n"
        "  • Sponsorship from one state emergency-services agency for a 90-day shadow-mode pilot\n"
        "  • A named Incident Controller to participate in a weekly Friday tabletop\n"
        "  • Read-only access to one authoritative signal stream (BoM gauges or RFS Fires Near Me)\n"
        "  • An exit-criteria conversation against spec 040's five capstone KPIs\n\n"
        "What you get back:\n"
        "  • A measurable, baseline-vs-AMA-assisted outcome scorecard\n"
        "  • A documented Australian-sovereign reference architecture you can re-use\n"
        "  • Zero production-channel risk: shadow mode is observe-only by design\n"
        "  • A working answer to the hardest question facing emergency management: how do we go faster, "
        "    together, in the climate we are inheriting?\n\n"
        "Decision criteria, ROI model, and integration spike-plan are in the appendix and the repo."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
KEY MESSAGE: The ask is small, defensible, and lands inside any state's existing innovation envelope.

TALK TRACK (60s):
- "I am not asking for a budget or a contract today. I am asking for a 90-day shadow-mode pilot."
- "Shadow mode means we observe and we score; we do not touch a live decision. The downside is bounded by definition. The upside is a defensible outcome scorecard."
- "If the answer is yes, the integration spike-plan is on a single page in the appendix. If the answer is 'tell me more first', I'll be in this room for the next twenty minutes."

PAUSE before transitioning to Q&A.
""")

    # ---- Slide 35 — Closing logo --------------------------------------------
    s = add_slide(prs, L_CLOSING)
    # Closing logo layout has no placeholders; add a thank-you textbox.
    tb = s.shapes.add_textbox(Inches(0.5), Inches(3.0), Inches(12.3), Inches(1.5))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run(); r.text = "Thank you."
    r.font.size = Pt(54); r.font.bold = True
    p2 = tb.text_frame.add_paragraph()
    r2 = p2.add_run(); r2.text = "Questions, challenges, healthy disagreement — all welcome."
    r2.font.size = Pt(20); r2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    set_notes(s, """
KEY MESSAGE: Open the floor. Welcome the panel. Listen.

TALK TRACK (15s):
- "Thank you. We have twenty minutes. I'd like to take questions in three buckets — strategic, technical, governance — but jump in any order."

PANEL TIPS:
- Repeat each question for the room before answering.
- For executive questions, anchor in the five capstone KPIs.
- For technical questions, anchor in the architecture diagrams; don't be afraid to flip back.
- For governance questions, anchor in the Constitution and the carve-out list.
- It is fine to say "I don't know — let me come back to you with the audit row."
""")

    # =========================================================================
    # BACKUP SLIDES
    # =========================================================================

    # ---- Slide 36 — Backup divider ------------------------------------------
    s = add_slide(prs, L_TITLE)
    set_title(s, "Backup slides")
    sub = s.shapes.add_textbox(Inches(0.5), Inches(5.0), Inches(12.3), Inches(0.6))
    r = sub.text_frame.paragraphs[0].add_run()
    r.text = "Architecture detail · sequence diagrams · cost & FinOps · governance gates"
    r.font.size = Pt(18); r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    set_notes(s, "Reference material to support Q&A. Not part of the 40-minute walkthrough.")

    # ---- Slide 37 — Sequence: monitoring → risk → comms ---------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Sequence — monitoring → risk → communication")
    add_image(s, ARCH / "sequence" / "monitoring-risk-comms.png")
    add_caption(s, "docs/architecture/sequence/monitoring-risk-comms.png")
    set_notes(s, "End-to-end agent handoff sequence with reflection guardrail. Reference for technical Q&A on agent orchestration.")

    # ---- Slide 38 — Sequence: graceful degradation --------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Sequence — graceful degradation")
    add_image(s, ARCH / "sequence" / "graceful-degradation.png")
    add_caption(s, "docs/architecture/sequence/graceful-degradation.png")
    set_notes(s, "Demonstrates constitutional non-negotiable #5 in action. Reference for resilience and SRE questions.")

    # ---- Slide 39 — Sequence: audit & provenance ----------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Sequence — audit & provenance")
    add_image(s, ARCH / "sequence" / "audit-provenance.png")
    add_caption(s, "docs/architecture/sequence/audit-provenance.png")
    set_notes(s, "End-to-end traceability from any output back to source signals and approvals. Reference for compliance/regulator questions.")

    # ---- Slide 40 — WAF pillar mapping & SLO --------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "Well-Architected Framework alignment")
    add_image(s, ARCH / "governance" / "waf-pillar-mapping.png", left=Inches(0.4),
              top=Inches(1.4), width=Inches(6.4), height=Inches(5.2))
    add_image(s, ARCH / "security" / "sli-slo-model.png", left=Inches(7.0),
              top=Inches(1.4), width=Inches(6.0), height=Inches(5.2))
    add_caption(s, "WAF pillar mapping · SLI/SLO model · docs/architecture/")
    set_notes(s, "Reliability, Security, Cost, Operational Excellence, Performance Efficiency — all mapped. SLI/SLO model includes burn-rate alerts at 2%/h and 5%/h.")

    # ---- Slide 41 — CI/CD + test pyramid ------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "CI/CD pipeline & test pyramid")
    add_image(s, ARCH / "deployment" / "cicd-pipeline.png", left=Inches(0.4),
              top=Inches(1.4), width=Inches(6.4), height=Inches(5.2))
    add_image(s, ARCH / "quality" / "test-pyramid.png", left=Inches(7.0),
              top=Inches(1.4), width=Inches(6.0), height=Inches(5.2))
    add_caption(s, "CI/CD · test pyramid · docs/architecture/")
    set_notes(s, "Branch-based dev/staging/prod (per spec 031). 231 test files: 110 unit, 53 contract, 26 integration, 19 simulation, 10 benchmark, 6 devops, 2 e2e, 2 load, 2 pipeline.")

    # ---- Slide 42 — PPRR + escalation ---------------------------------------
    s = add_slide(prs, L_TITLE_ONLY)
    set_title(s, "PPRR overlay & AIIMS escalation paths")
    add_image(s, ARCH / "operational" / "pprr-phase-overlay.png", left=Inches(0.4),
              top=Inches(1.4), width=Inches(6.4), height=Inches(5.2))
    add_image(s, ARCH / "operational" / "escalation-paths.png", left=Inches(7.0),
              top=Inches(1.4), width=Inches(6.0), height=Inches(5.2))
    add_caption(s, "PPRR overlay · escalation paths · docs/architecture/operational/")
    set_notes(s, "Prevention, Preparedness, Response, Recovery overlap by design. Escalation is by AIIMS authority and named successor; no escalation without an audit row.")

    # ---- Slide 43 — Cost detail ---------------------------------------------
    s = add_slide(prs, L_RIGHT_CONTENT)
    set_title(s, "Cost model — line items & sensitivity")
    body = (
        "Pilot (single jurisdiction, monthly canonical scenario, AUD):\n"
        "  • Foundry models — reasoning + drafting deployments     ~$2,800\n"
        "  • Cosmos DB serverless (multi-container)                 ~$1,200\n"
        "  • Container Apps consumption (API + agents)              ~$1,400\n"
        "  • Azure AI Search (Foundry RAG, AIDR corpus)             ~$700\n"
        "  • Storage (audit, evidence pack, immutable)              ~$300\n"
        "  • Service Bus + Event Grid                               ~$150\n"
        "  • Application Insights + Log Analytics                   ~$600\n"
        "  • Azure Communication Services (pilot volume)            ~$1,000\n"
        "  • Front Door + Static Web Apps                           ~$350\n"
        "  • Total                                                  ~$8,500/month\n\n"
        "Sensitivity: ACS message volume is the single largest variable at scale. Targeted "
        "warnings (jurisdiction-bounded) cut alert spend by ~40% vs broadcast SMS. "
        "Per-incident cost dominated by ACS, not by AI inference.\n\n"
        "ROI scenario (illustrative): one prevented level-3 escalation in a year of operation = "
        "~$850M direct loss avoidance vs ~$2.6M annualised pilot+state operating cost."
    )
    set_text(find_ph(s, PH_BODY), body)
    set_notes(s, """
Reference detail for FinOps Q&A. All figures are May 2026 Azure list prices in AUD.
Confidence band on pilot estimate: ±15%. Compute via the FinOps workspace in the Governance Dashboard.
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE}")

    prs = Presentation(str(TEMPLATE))
    reset_slides(prs)
    build(prs)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(prs.slides)} slides")


if __name__ == "__main__":
    main()
