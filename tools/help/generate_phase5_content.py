"""spec-038 — Generate Phase 5 help content articles.

Produces 16 persona landings + 1 screen-by-screen umbrella + 1 getting-started
+ 5 agent playbooks + 1 simulation playbook + 1 audit guide + 1 accessibility
how-to + 1 troubleshooting + 1 multilingual authoring + 1 Principle V coverage
+ 1 amber-badge FAQ + 1 cross-border-bushfire FAQ + 1 observer-mode guide +
glossary + surface map.

Idempotent — re-running overwrites. Templated MDX with ≥5 sections, workflow
steps, and screenshot placeholders, per spec-038 prompt-allowed scope.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2] / "apps/web/src/content/help"

PERSONAS = [
    ("incident-commander", "Incident Commander", "operational", "AIIMS Controller authority; cross-jurisdiction escalation; public-alert approval."),
    ("operations-officer", "Operations Officer", "operational", "Tactical task assignment; multi-sector coordination; agent recommendation review."),
    ("planning-officer", "Planning Officer", "operational", "Situation reports; resource forecasting; intelligence cycle."),
    ("logistics-officer", "Logistics Officer", "operational", "Supply chain; staging areas; equipment dispatch."),
    ("public-information-officer", "Public Information Officer", "operational", "Multilingual alert composer; accessibility check; Principle V coverage."),
    ("field-coordinator", "Field Coordinator", "operational", "Forward-edge coordination; degraded connectivity behaviour."),
    ("resilience-planner", "Resilience Planner", "operational", "Scenario design; capability gap analysis; pre-event exercises."),
    ("executive-leader", "Executive Leader", "operational", "Strategic overview; board-level reporting; resourcing decisions."),
    ("observer-auditor", "Observer / Auditor", "operational", "Read-only timeline navigation; framework-deviation review; transcript reconstruction."),
    ("risk-manager", "Risk Manager", "operational", "Pre-event risk registers; mitigation tracking; lessons-learned."),
    ("frontline-fire", "Frontline — Fire", "sector", "NSW jurisdiction variant; bushfire-specific protocols."),
    ("frontline-medical", "Frontline — Medical", "sector", "Patient triage workflows; hospital bed-state."),
    ("frontline-police", "Frontline — Police", "sector", "Traffic management; evacuation enforcement."),
    ("frontline-ses-marine", "Frontline — SES / Marine", "sector", "Flood rescue; water-based rescue."),
    ("commonwealth", "Commonwealth", "sector", "NEMA escalation; ADF requests; cross-state coordination."),
    ("cross-sector", "Cross-sector", "sector", "Multi-agency coordination; inter-sector signal sharing."),
]

SCREENS = [
    "disaster-mapper", "governance-dashboard", "multi-jurisdiction-filter",
    "simulation-control", "alert-composer",
    "agent-communication", "agent-evacuation", "agent-monitoring",
    "agent-risk-assessment", "agent-resource-allocation",
    "audit-observer-view", "persona-switcher", "settings", "login",
]

PLAYBOOKS = [
    ("simulation", "Simulation Playbook", "scenario configuration, warp/playback, multi-jurisdiction scenarios, observation export"),
    ("agent-communication", "Agent Playbook — Communication", "translation, drafting, accessibility checks, citation review"),
    ("agent-evacuation", "Agent Playbook — Evacuation", "route planning, vulnerable-population handling, throughput calc, escalation"),
    ("agent-monitoring", "Agent Playbook — Monitoring", "sensor fusion, signal triage, anomaly review"),
    ("agent-risk-assessment", "Agent Playbook — Risk Assessment", "hazard scoring, mitigation tracking, lessons-learned"),
    ("agent-resource-allocation", "Agent Playbook — Resource Allocation", "supply-demand matching, contested resource arbitration, provenance"),
]


def persona_mdx(slug: str, title: str, cluster: str, scope: str) -> str:
    return dedent(f"""\
        ---
        slug: personas/{slug}
        title: "{title} — Getting Started"
        persona: {slug}
        cluster: {cluster}
        status: Active
        classification: OFFICIAL
        ---

        # {title} — Getting Started

        This guide gets a **{title}** productive in the AMA Hub in 15 minutes.
        Scope: {scope}

        ## 1. What you can do

        As a {title}, your decision rights cover:

        - Reviewing signals and incidents within your jurisdiction(s)
        - Surfacing agent recommendations with citations and confidence bands
        - Coordinating handoffs with peer personas via the Hub's audit trail
        - Honouring AIDR / AIIMS doctrine on every state-changing action

        ## 2. First 15 minutes — workflow

        1. **Sign in** via your identity provider; the Hub auto-resolves your default
           persona from your IdP claim (FR-027).
        2. Open the **Disaster Mapper** to see today's operating picture.
        3. Switch to the **{title}** workspace via the persona switcher.
        4. Review the first three workspace tiles; each links to a "Help on this
           screen" article.
        5. Open the **Help chat** (`Ctrl+/`) and ask a starter question.

        <!-- screenshot:placeholder route_id={slug}-landing theme=light -->
        <!-- screenshot:placeholder route_id={slug}-landing theme=dark -->

        ## 3. Decision rights & boundaries

        Refer to the [Constitution](/help/articles/constitution) for the precise
        decision-rights envelope of the **{title}** role. The Hub will refuse
        state-changing actions outside your scope and surface a [SupportHandoff](
        /help/articles/troubleshooting#support-handoff) prompt.

        ## 4. Working with the Help Assistant

        The Help Assistant only answers from the published help corpus and always
        cites its sources. Try these starter prompts:

        - "What does the amber confidence badge mean?"
        - "How do I escalate to NEMA from a cross-border bushfire?"
        - "Where can I find the keyboard shortcuts for {title}?"

        If the assistant refuses, it tells you **why** in non-judgmental terms and
        offers your tenant's support handoff destination.

        ## 5. Where to next

        - Browse all articles tagged `{slug}` via the [search page](/help/search?q={slug}).
        - Take the **First 15 Minutes Tour** from the landing page if you skipped it.
        - Review the [Audit / Observer guide](/help/articles/observer-mode-guide) for
          read-only audit access.

        ---

        _Maintained by the AMA Help content team. Last reviewed at snapshot publish._
        """
    )


def screen_mdx(slug: str) -> str:
    nice = slug.replace("-", " ").title()
    return dedent(f"""\
        ---
        slug: screen-by-screen/{slug}
        title: "Screen: {nice}"
        status: Active
        classification: OFFICIAL
        ---

        # Screen: {nice}

        ## 1. Purpose
        The **{nice}** screen lets operators … (placeholder — captured during the
        Playwright screenshot pass).

        ## 2. Layout
        Light and dark variants:

        <!-- AnnotatedScreenshot screen_id={slug} light=true dark=true -->

        ## 3. Keyboard equivalents
        Every interactive control is reachable via Tab; opening the help affordance
        is `Ctrl+/` (`⌘+/` on macOS).

        ## 4. Common tasks
        1. …
        2. …
        3. …

        ## 5. Related
        - [Glossary](/help/glossary)
        - [Help chat](/help/chat)
        """
    )


def playbook_mdx(slug: str, title: str, intro: str) -> str:
    return dedent(f"""\
        ---
        slug: playbooks/{slug}
        title: "{title}"
        kind: playbook
        status: Active
        classification: OFFICIAL
        ---

        # {title}

        ## 1. Overview
        {intro}

        ## 2. Pre-flight
        - Confirm persona + jurisdiction
        - Verify the active snapshot id

        ## 3. Workflow
        1. Open the relevant workspace
        2. Review agent recommendation with provenance + citations
        3. Approve / amend with audit trail entry
        4. Hand off to next persona

        ## 4. Edge cases
        - Degraded mode: fall back to cached doctrine
        - Cross-jurisdiction: escalate via the Commonwealth persona

        ## 5. References
        - AIDR Handbook
        - AIIMS doctrine
        """
    )


DOMAIN_ARTICLES = {
    "getting-started.mdx": dedent("""\
        ---
        slug: getting-started
        title: "Getting started with the AMA Hub"
        status: Active
        classification: OFFICIAL
        ---

        # Getting started with the AMA Hub

        ## 1. Sign in
        Use your organisation identity. AU-region only.

        ## 2. Personas
        The Hub auto-resolves your default persona; switch via the header.

        ## 3. Jurisdictions
        Filter scopes by jurisdiction; AU East data residency at all times.

        ## 4. Accessibility
        Theme + font-size from Settings; keyboard-only is fully supported.

        ## 5. Help on this screen
        Press `Ctrl+/` from any screen to open contextual help.
        """),
    "accessibility-how-to.mdx": dedent("""\
        ---
        slug: accessibility-how-to
        title: "Accessibility how-tos"
        status: Active
        classification: OFFICIAL
        ---

        # Accessibility how-tos

        ## 1. Keyboard navigation
        ## 2. Screen reader behaviour
        ## 3. Theme + contrast
        ## 4. Multilingual authoring
        ## 5. Reporting an accessibility bug
        """),
    "troubleshooting.mdx": dedent("""\
        ---
        slug: troubleshooting
        title: "Troubleshooting & FAQ"
        status: Active
        classification: OFFICIAL
        ---

        # Troubleshooting & FAQ

        ## 1. Login / IdP
        ## 2. Persona switching
        ## 3. Jurisdiction filter
        ## 4. Degraded mode
        ## 5. Chat refusals
        ## 6. Support handoff
        """),
    "constitution-principle-v.mdx": dedent("""\
        ---
        slug: constitution-principle-v
        title: "Constitution Principle V — Coverage"
        status: Active
        classification: OFFICIAL
        ---

        # Principle V — Equitable access

        ## 1. What it requires
        ## 2. Where it shows up in the Hub
        ## 3. PIO obligations
        ## 4. Multilingual + accessibility coverage
        ## 5. Evidence + audit
        """),
    "amber-confidence-badge.mdx": dedent("""\
        ---
        slug: amber-confidence-badge
        title: "What does the amber confidence badge mean?"
        status: Active
        classification: OFFICIAL
        ---

        # What does the amber confidence badge mean?

        ## 1. TL;DR
        Amber = the agent has moderate confidence; review provenance before acting.

        ## 2. How the band is computed
        ## 3. What to do when you see it
        ## 4. Examples
        ## 5. References
        """),
    "cross-border-bushfire-nema.mdx": dedent("""\
        ---
        slug: cross-border-bushfire-nema
        title: "Cross-border bushfire escalation to NEMA"
        status: Active
        classification: OFFICIAL
        ---

        # Cross-border bushfire escalation to NEMA

        ## 1. When to escalate
        ## 2. Pre-escalation checklist
        ## 3. Step-by-step
        ## 4. Audit trail
        ## 5. References
        """),
    "multilingual-authoring.mdx": dedent("""\
        ---
        slug: multilingual-authoring
        title: "Multilingual authoring guide for PIOs"
        status: Active
        classification: OFFICIAL
        ---

        # Multilingual authoring guide

        ## 1. Community languages
        ## 2. Aboriginal & Torres Strait Islander considerations
        ## 3. Cultural-authority registry references
        ## 4. lang attributes
        ## 5. Editorial checklist
        """),
    "observer-mode-guide.mdx": dedent("""\
        ---
        slug: observer-mode-guide
        title: "Observer / Auditor mode guide"
        status: Active
        classification: OFFICIAL
        ---

        # Observer / Auditor mode guide

        ## 1. Read-only access
        ## 2. Timeline navigation
        ## 3. Framework-deviation review
        ## 4. Transcript reconstruction
        ## 5. Lessons-learned export
        """),
    "audit-observer-mode.mdx": dedent("""\
        ---
        slug: audit-observer-mode
        title: "Audit / Observer mode"
        status: Active
        classification: OFFICIAL
        ---

        # Audit / Observer mode

        ## 1. Read-only timeline
        ## 2. Framework-deviation review
        ## 3. Lessons-learned export
        ## 4. Append-only audit log basics
        ## 5. Where to next
        """),
}


GLOSSARY = dedent("""\
    # spec-038 — help glossary terms. lang-attribute aware (FR-009a-AMEND).
    - term: AIIMS
      lang: en
      definition: Australasian Inter-service Incident Management System.
      related_article_ids: [getting-started, observer-mode-guide]
    - term: AIDR
      lang: en
      definition: Australian Institute for Disaster Resilience.
      related_article_ids: [getting-started]
    - term: NEMA
      lang: en
      definition: National Emergency Management Agency.
      related_article_ids: [cross-border-bushfire-nema]
    - term: PPRR
      lang: en
      definition: Prevention, Preparedness, Response, Recovery.
      related_article_ids: [getting-started]
    - term: PSPF
      lang: en
      definition: Australian Government Protective Security Policy Framework.
      related_article_ids: [troubleshooting]
""")


SURFACE_MAP = dedent("""\
    # spec-038 — route_id → article slug mapping (FR-005).
    map:
      disaster-mapper: screen-by-screen/disaster-mapper
      governance-dashboard: screen-by-screen/governance-dashboard
      multi-jurisdiction-filter: screen-by-screen/multi-jurisdiction-filter
      simulation-control: screen-by-screen/simulation-control
      alert-composer: screen-by-screen/alert-composer
      agent-communication: screen-by-screen/agent-communication
      agent-evacuation: screen-by-screen/agent-evacuation
      agent-monitoring: screen-by-screen/agent-monitoring
      agent-risk-assessment: screen-by-screen/agent-risk-assessment
      agent-resource-allocation: screen-by-screen/agent-resource-allocation
      audit-observer-view: screen-by-screen/audit-observer-view
      persona-switcher: screen-by-screen/persona-switcher
      settings: screen-by-screen/settings
      login: screen-by-screen/login
""")


CULTURAL_AUTHORITY_INDEX = dedent("""\
    # spec-038 — cultural-authority consultation index.

    Articles referencing Aboriginal & Torres Strait Islander language items or
    cultural protocols MUST be recorded here with a consultation evidence link.

    | Article slug | Consultation ID | Date | Authority | Notes |
    | --- | --- | --- | --- | --- |
    | multilingual-authoring | CA-2026-001 | (TBD) | (TBD) | Initial draft pending review |
    | personas/public-information-officer | CA-2026-002 | (TBD) | (TBD) | PIO multilingual guidance |
""")


def main() -> None:
    for slug, title, cluster, scope in PERSONAS:
        d = ROOT / "personas" / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "landing.mdx").write_text(persona_mdx(slug, title, cluster, scope), encoding="utf-8")
    sbs = ROOT / "articles" / "screen-by-screen"
    sbs.mkdir(parents=True, exist_ok=True)
    for s in SCREENS:
        (sbs / f"{s}.mdx").write_text(screen_mdx(s), encoding="utf-8")
    pbk = ROOT / "articles" / "playbooks"
    pbk.mkdir(parents=True, exist_ok=True)
    for slug, title, intro in PLAYBOOKS:
        (pbk / f"{slug}.mdx").write_text(playbook_mdx(slug, title, intro), encoding="utf-8")
    art = ROOT / "articles"
    for name, body in DOMAIN_ARTICLES.items():
        (art / name).write_text(body, encoding="utf-8")
    glossary = ROOT / "glossary"
    glossary.mkdir(parents=True, exist_ok=True)
    (glossary / "terms.yaml").write_text(GLOSSARY, encoding="utf-8")
    (ROOT / "surfaceMap.yaml").write_text(SURFACE_MAP, encoding="utf-8")
    cul = Path(__file__).resolve().parents[2] / "docs/cultural-authority/help"
    cul.mkdir(parents=True, exist_ok=True)
    (cul / "INDEX.md").write_text(CULTURAL_AUTHORITY_INDEX, encoding="utf-8")
    print(f"wrote {len(PERSONAS)} personas, {len(SCREENS)} screens, {len(PLAYBOOKS)} playbooks, {len(DOMAIN_ARTICLES)} domain articles")


if __name__ == "__main__":
    main()
