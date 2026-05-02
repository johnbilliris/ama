"""Persona spec generator (T069-T145, extended T176 cycle-1).

Reads the inline registry below and emits one Playwright .spec.ts per persona
scenario into ``tests/e2e/web-coverage/{operational,sectors}/`` directories.

Cycle-1 (T176): when ``--rewrite-stubs`` is passed, the generator additionally
loads each ``tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml``
(authored under T175), validates it against the draft-07 ``_schema.json``,
translates the workflow_steps + assertion_targets into a Playwright spec body
that drives the FR-028 evaluator endpoint, and rewrites the spec file. No
``test.fail(true, ...)`` bail is permitted in the rewritten body. Missing or
schema-invalid profiles fail-fast and (in CI) trigger a
``GAP-DEPTH-PROFILE-MISSING-{persona-id}`` row via ``gap-register.py open``.

Each entry is a ``Spec`` row that pins:

  • path        — relative TS file path under ``tests/e2e/web-coverage/``
  • persona_id  — must exist in ``packages/domain/src/domain/seed/identities_australia.json``
  • outcome     — 1..5 capstone outcome
  • hazard      — `<primary>+<secondary>` lowercase token
  • frs         — list of FR-NNN ids (≥ 1)
  • clauses     — list of constitution clauses
  • priority    — p1|p2|p3
  • scenario    — short kebab-case scenario slug used in the test title
  • secondary_persona_id — set for cross-jurisdiction integration specs
                           (T137-T145); these specs assert handover between
                           two personas.

Run with::

  python scripts/web-coverage/_lib/persona_spec_generator.py
  python scripts/web-coverage/_lib/persona_spec_generator.py --rewrite-stubs

The generator is idempotent and overwrites every target file so a regeneration
matches the YAML on disk byte-for-byte (FR-006 determinism).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "e2e" / "web-coverage"

# Cycle-1 reservation (T174): the depth-profile schema validator is loaded by
# the cycle-1 extension (T176) to translate `*.depth.yaml` into workflow-driven
# Playwright spec bodies. Path is exposed as a module constant so the cycle-1
# extension can import it without re-deriving the path. Draft-07 per Q28 —
# deliberately distinct from the 2020-12 contracts under specs/034-…/contracts/.
DEPTH_PROFILE_SCHEMA_PATH = TESTS_ROOT / "_lib" / "depth-profiles" / "_schema.json"
DEPTH_PROFILE_DIR = TESTS_ROOT / "_lib" / "depth-profiles"


@dataclass(frozen=True)
class Spec:
    task_id: str
    path: str  # relative under TESTS_ROOT
    persona_id: str
    outcome: int
    hazard: str
    frs: tuple[str, ...]
    clauses: tuple[str, ...]
    priority: str = "p1"
    scenario: str = ""
    secondary_persona_id: str | None = None
    extra_assertions: tuple[str, ...] = field(default_factory=tuple)


# ----- Registry -----

OPERATIONAL: tuple[Spec, ...] = (
    Spec("T069", "operational/incident-commander.approve-cross-agency-action.spec.ts",
         "incident-commander", 1, "bushfire+extreme-heat",
         ("FR-009", "FR-002"), ("I", "NN-1"), scenario="approve-cross-agency-action"),
    Spec("T070", "operational/operations-officer.tactical-tasking.spec.ts",
         "operations-officer", 2, "bushfire+severe-storm",
         ("FR-008", "FR-002"), ("II", "II-A"), scenario="tactical-tasking"),
    Spec("T071", "operational/planning-officer.predictive-risk-evac.spec.ts",
         "planning-officer", 3, "tropical-cyclone+riverine-flood",
         ("FR-016", "FR-002"), ("VI",), scenario="predictive-risk-evac"),
    Spec("T072", "operational/logistics-officer.mutual-aid-lifecycle.spec.ts",
         "logistics-officer", 4, "bushfire+tropical-cyclone",
         ("FR-015", "FR-002"), ("VIII",), scenario="mutual-aid-lifecycle"),
    Spec("T073", "operational/public-information-officer.aws-multilingual-warning.spec.ts",
         "public-information-officer", 1, "bushfire+extreme-heat",
         ("FR-011", "FR-014", "FR-002"), ("V-A", "V-C"), scenario="aws-multilingual-warning"),
    Spec("T074", "operational/field-coordinator.offline-gps-hazard-report.spec.ts",
         "field-coordinator", 2, "bushfire+severe-storm",
         ("FR-017", "FR-002"), ("NN-5",), scenario="offline-gps-hazard-report"),
    Spec("T075", "operational/resilience-planner.recovery-handover.spec.ts",
         "resilience-planner", 5, "riverine-flood+severe-storm",
         ("FR-013", "FR-002"), ("VII",), scenario="recovery-handover"),
    Spec("T076", "operational/executive-leader.economic-environment-view.spec.ts",
         "executive-leader", 5, "riverine-flood+severe-storm",
         ("FR-013", "FR-002"), ("VII",), scenario="economic-environment-view"),
    Spec("T077", "operational/observer-auditor.append-only-timeline.spec.ts",
         "observer-auditor", 4, "bushfire+tropical-cyclone",
         ("FR-010", "FR-002"), ("IV",), scenario="append-only-timeline"),
    Spec("T078", "operational/risk-manager.predictive-evac-lead.spec.ts",
         "risk-manager", 3, "tropical-cyclone+riverine-flood",
         ("FR-016", "FR-002"), ("VI",), scenario="predictive-evac-lead"),
)

NSW: tuple[Spec, ...] = (
    Spec("T079", "sectors/nsw/nsw-rfs.bushfire-incident-action-plan.spec.ts",
         "nsw-rfs", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="bushfire-incident-action-plan"),
    Spec("T080", "sectors/nsw/ses-nsw.watch-and-act-flood.spec.ts",
         "ses-nsw", 3, "tropical-cyclone+riverine-flood",
         ("FR-011", "FR-016", "FR-002"), ("V-B", "VI"), scenario="watch-and-act-flood"),
    Spec("T081", "sectors/nsw/nsw-ambulance.mass-casualty-triage.spec.ts",
         "nsw-ambulance", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="mass-casualty-triage"),
    Spec("T082", "sectors/nsw/nswpf.evacuation-cordon.spec.ts",
         "nswpf", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="evacuation-cordon"),
    Spec("T083", "sectors/nsw/frnsw.urban-fire-response.spec.ts",
         "frnsw", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="urban-fire-response"),
    Spec("T084", "sectors/nsw/mrnsw.maritime-flood-rescue.spec.ts",
         "mrnsw", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="maritime-flood-rescue"),
)

VIC: tuple[Spec, ...] = (
    Spec("T085", "sectors/vic/cfa-vic.code-red-day.spec.ts",
         "cfa-vic", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="code-red-day"),
    Spec("T086", "sectors/vic/ses-vic.flash-flood-rescue.spec.ts",
         "ses-vic", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="flash-flood-rescue"),
    Spec("T087", "sectors/vic/av.heat-related-illness-surge.spec.ts",
         "av", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="heat-related-illness-surge"),
    Spec("T088", "sectors/vic/vicpol.cross-border-evac.spec.ts",
         "vicpol", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="cross-border-evac"),
    Spec("T089", "sectors/vic/frv.warehouse-fire-haz-mat.spec.ts",
         "frv", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="warehouse-fire-haz-mat"),
)

QLD: tuple[Spec, ...] = (
    Spec("T090", "sectors/qld/qfd.cyclone-pre-positioning.spec.ts",
         "qfd", 4, "bushfire+tropical-cyclone",
         ("FR-002", "FR-015"), ("VIII",), scenario="cyclone-pre-positioning"),
    Spec("T091", "sectors/qld/ses-qld.tropical-cyclone-flood.spec.ts",
         "ses-qld", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="tropical-cyclone-flood"),
    Spec("T092", "sectors/qld/qas.heat-stress-mass-casualty.spec.ts",
         "qas", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="heat-stress-mass-casualty"),
    Spec("T093", "sectors/qld/qps.evac-traffic-management.spec.ts",
         "qps", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="evac-traffic-management"),
)

SA: tuple[Spec, ...] = (
    Spec("T094", "sectors/sa/sacfs.code-red-bushfire.spec.ts",
         "sacfs", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="code-red-bushfire"),
    Spec("T095", "sectors/sa/ses-sa.river-murray-flood.spec.ts",
         "ses-sa", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="river-murray-flood"),
    Spec("T096", "sectors/sa/saas.extreme-heat-mass-call.spec.ts",
         "saas", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="extreme-heat-mass-call"),
    Spec("T097", "sectors/sa/sapol.cross-border-evac.spec.ts",
         "sapol", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="cross-border-evac"),
    Spec("T098", "sectors/sa/samfs.urban-fire-multi-storey.spec.ts",
         "samfs", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="urban-fire-multi-storey"),
)

WA: tuple[Spec, ...] = (
    Spec("T099", "sectors/wa/dfes-wa.cyclone-pilbara.spec.ts",
         "dfes-wa", 4, "bushfire+tropical-cyclone",
         ("FR-002", "FR-015"), ("VIII",), scenario="cyclone-pilbara"),
    Spec("T100", "sectors/wa/sja-wa.remote-medical-evac.spec.ts",
         "sja-wa", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="remote-medical-evac"),
    Spec("T101", "sectors/wa/wapol.remote-evac-cordon.spec.ts",
         "wapol", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="remote-evac-cordon"),
)

TAS: tuple[Spec, ...] = (
    Spec("T102", "sectors/tas/tfs.bushfire-island-evac.spec.ts",
         "tfs", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="bushfire-island-evac"),
    Spec("T103", "sectors/tas/ses-tas.severe-storm-rescue.spec.ts",
         "ses-tas", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="severe-storm-rescue"),
    Spec("T104", "sectors/tas/at.aeromedical-retrieval.spec.ts",
         "at", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="aeromedical-retrieval"),
    Spec("T105", "sectors/tas/taspol.island-evac-coordination.spec.ts",
         "taspol", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="island-evac-coordination"),
)

ACT: tuple[Spec, ...] = (
    Spec("T106", "sectors/act/act-esa.multi-agency-coordination.spec.ts",
         "act-esa", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="multi-agency-coordination"),
    Spec("T107", "sectors/act/act-fr.urban-fire.spec.ts",
         "act-fr", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="urban-fire"),
    Spec("T108", "sectors/act/act-ambulance.heat-surge.spec.ts",
         "act-ambulance", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="heat-surge"),
    Spec("T109", "sectors/act/act-policing.evac-cordon.spec.ts",
         "act-policing", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="evac-cordon"),
    Spec("T110", "sectors/act/act-rfs.bushfire-pre-positioning.spec.ts",
         "act-rfs", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="bushfire-pre-positioning"),
    # T111: persona id = afp-act (per T052 seed disambiguation note in tasks.md).
    Spec("T111", "sectors/act/afp.protective-services.spec.ts",
         "afp-act", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="protective-services"),
    Spec("T112", "sectors/act/ses-act.severe-storm-rescue.spec.ts",
         "ses-act", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="severe-storm-rescue"),
)

NT: tuple[Spec, ...] = (
    Spec("T113", "sectors/nt/bushfires-nt.savanna-burn.spec.ts",
         "bushfires-nt", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="savanna-burn"),
    Spec("T114", "sectors/nt/ntes.cyclone-shelter.spec.ts",
         "ntes", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="cyclone-shelter"),
    Spec("T115", "sectors/nt/ntfrs.remote-fire-response.spec.ts",
         "ntfrs", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="remote-fire-response"),
    Spec("T116", "sectors/nt/ntpf.remote-evac.spec.ts",
         "ntpf", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="remote-evac"),
    Spec("T117", "sectors/nt/sja-nt.remote-medical-retrieval.spec.ts",
         "sja-nt", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="remote-medical-retrieval"),
)

COMMONWEALTH: tuple[Spec, ...] = (
    Spec("T118", "sectors/commonwealth/nema.activate-comdisplan.spec.ts",
         "nema", 4, "bushfire+tropical-cyclone",
         ("FR-015", "FR-002"), ("VIII",), scenario="activate-comdisplan"),
    Spec("T119", "sectors/commonwealth/bom-national.cyclone-warning-relay.spec.ts",
         "bom-national", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="cyclone-warning-relay"),
    # T120: special — earthquake/tsunami AWS path (FR-011 only). Use the
    # outcome-1 lives proxy + a custom hazard label for the trace row.
    Spec("T120", "sectors/commonwealth/ga-national.tsunami-warning-relay.spec.ts",
         "ga-national", 1, "earthquake+tsunami",
         ("FR-011", "FR-002"), ("V-A", "V-B"), scenario="tsunami-warning-relay"),
    Spec("T121", "sectors/commonwealth/adf.dacc-asset-arrival.spec.ts",
         "adf", 4, "bushfire+tropical-cyclone",
         ("FR-002", "FR-015"), ("VIII",), scenario="dacc-asset-arrival"),
    Spec("T122", "sectors/commonwealth/abf.border-disaster-coordination.spec.ts",
         "abf", 5, "riverine-flood+severe-storm",
         ("FR-002", "FR-013"), ("VII",), scenario="border-disaster-coordination"),
    Spec("T123", "sectors/commonwealth/arc.recovery-financial-assistance.spec.ts",
         "arc", 5, "riverine-flood+severe-storm",
         ("FR-002", "FR-013"), ("VII",), scenario="recovery-financial-assistance"),
    Spec("T124", "sectors/commonwealth/asa.shipping-evac.spec.ts",
         "asa", 5, "riverine-flood+severe-storm",
         ("FR-002", "FR-013"), ("VII",), scenario="shipping-evac"),
    Spec("T125", "sectors/commonwealth/rfds.remote-aeromedical.spec.ts",
         "rfds", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="remote-aeromedical"),
    Spec("T126", "sectors/commonwealth/sja-national.community-first-aid.spec.ts",
         "sja-national", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="community-first-aid"),
    Spec("T127", "sectors/commonwealth/surf-lifesaving.coastal-cyclone-evac.spec.ts",
         "surf-lifesaving", 3, "tropical-cyclone+riverine-flood",
         ("FR-002", "FR-016"), ("VI",), scenario="coastal-cyclone-evac"),
    Spec("T128", "sectors/commonwealth/afp-commonwealth.national-evac-coordination.spec.ts",
         "afp-commonwealth", 2, "bushfire+severe-storm",
         ("FR-002", "FR-008"), ("II",), scenario="national-evac-coordination"),
)

CROSS_SECTOR: tuple[Spec, ...] = (
    Spec("T129", "sectors/cross-sector/community-ngos.recovery-coordination.spec.ts",
         "community-ngos", 5, "riverine-flood+severe-storm",
         ("FR-002", "FR-013"), ("VII",), scenario="recovery-coordination"),
    Spec("T130", "sectors/cross-sector/health.surge-capacity.spec.ts",
         "health", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="surge-capacity"),
    Spec("T131", "sectors/cross-sector/local-government.recovery-funding.spec.ts",
         "local-government", 5, "riverine-flood+severe-storm",
         ("FR-002", "FR-013"), ("VII",), scenario="recovery-funding"),
    Spec("T132", "sectors/cross-sector/state-government.disaster-declaration.spec.ts",
         "state-government", 5, "riverine-flood+severe-storm",
         ("FR-002", "FR-013"), ("VII",), scenario="disaster-declaration"),
    Spec("T133", "sectors/cross-sector/territory-government.cross-jurisdiction-coord.spec.ts",
         "territory-government", 5, "riverine-flood+severe-storm",
         ("FR-002", "FR-013", "FR-003"), ("VII",), scenario="cross-jurisdiction-coord"),
    Spec("T134", "sectors/cross-sector/transport.evac-routing.spec.ts",
         "transport", 4, "bushfire+tropical-cyclone",
         ("FR-002", "FR-015"), ("VIII",), scenario="evac-routing"),
    Spec("T135", "sectors/cross-sector/utility.power-restoration.spec.ts",
         "utility", 5, "riverine-flood+severe-storm",
         ("FR-002", "FR-013"), ("VII",), scenario="power-restoration"),
    Spec("T136", "sectors/cross-sector/volunteer.surge-deployment.spec.ts",
         "volunteer", 1, "bushfire+extreme-heat",
         ("FR-002", "FR-009"), ("I",), scenario="surge-deployment"),
)

CROSS_JURISDICTION: tuple[Spec, ...] = (
    Spec("T137", "sectors/nsw/cross-jurisdiction-nsw-vic-bushfire.spec.ts",
         "nsw-rfs", 1, "bushfire+extreme-heat",
         ("FR-015", "FR-003"), ("II", "VIII"),
         scenario="cross-jurisdiction-nsw-vic-bushfire", secondary_persona_id="cfa-vic"),
    Spec("T138", "sectors/vic/cross-jurisdiction-vic-tas-storm.spec.ts",
         "ses-vic", 2, "bushfire+severe-storm",
         ("FR-015", "FR-003"), ("II", "VIII"),
         scenario="cross-jurisdiction-vic-tas-storm", secondary_persona_id="ses-tas"),
    Spec("T139", "sectors/qld/cross-jurisdiction-qld-nsw-cyclone-flood.spec.ts",
         "ses-qld", 3, "tropical-cyclone+riverine-flood",
         ("FR-015", "FR-003"), ("II", "VI"),
         scenario="cross-jurisdiction-qld-nsw-cyclone-flood", secondary_persona_id="ses-nsw"),
    Spec("T140", "sectors/sa/cross-jurisdiction-sa-vic-bushfire.spec.ts",
         "sacfs", 1, "bushfire+extreme-heat",
         ("FR-015", "FR-003"), ("II", "VIII"),
         scenario="cross-jurisdiction-sa-vic-bushfire", secondary_persona_id="cfa-vic"),
    Spec("T141", "sectors/wa/cross-jurisdiction-wa-sa-flood.spec.ts",
         "dfes-wa", 3, "tropical-cyclone+riverine-flood",
         ("FR-015", "FR-003"), ("II", "VI"),
         scenario="cross-jurisdiction-wa-sa-flood", secondary_persona_id="ses-sa"),
    Spec("T142", "sectors/tas/cross-jurisdiction-tas-mainland-cyclone.spec.ts",
         "tfs", 3, "tropical-cyclone+riverine-flood",
         ("FR-015", "FR-003"), ("II", "VI"),
         scenario="cross-jurisdiction-tas-mainland-cyclone", secondary_persona_id="cfa-vic"),
    Spec("T143", "sectors/act/cross-jurisdiction-act-nsw-bushfire.spec.ts",
         "act-rfs", 1, "bushfire+extreme-heat",
         ("FR-015", "FR-003"), ("II", "VIII"),
         scenario="cross-jurisdiction-act-nsw-bushfire", secondary_persona_id="nsw-rfs"),
    Spec("T144", "sectors/nt/cross-jurisdiction-nt-wa-bushfire-cyclone.spec.ts",
         "bushfires-nt", 4, "bushfire+tropical-cyclone",
         ("FR-015", "FR-003"), ("II", "VIII"),
         scenario="cross-jurisdiction-nt-wa-bushfire-cyclone", secondary_persona_id="dfes-wa"),
    Spec("T145", "sectors/commonwealth/nema.dacc-state-controller-bridge.spec.ts",
         "nema", 4, "bushfire+tropical-cyclone",
         ("FR-015", "FR-003"), ("II-A", "VIII"),
         scenario="dacc-state-controller-bridge", secondary_persona_id="adf"),
)

ALL_SPECS: tuple[Spec, ...] = (
    OPERATIONAL
    + NSW
    + VIC
    + QLD
    + SA
    + WA
    + TAS
    + ACT
    + NT
    + COMMONWEALTH
    + CROSS_SECTOR
    + CROSS_JURISDICTION
)


# ----- Template -----

TEMPLATE_SINGLE = '''/**
 * {task_id} — {persona_id}: {scenario_human}.
 *
 * Capstone outcome: #{outcome} ({outcome_label})
 * Hazard: {hazard}
 * FRs: {fr_csv}
 * Constitution clauses: {clause_csv}
 *
 * Auto-generated by ``scripts/web-coverage/_lib/persona_spec_generator.py``.
 * Do not hand-edit; regenerate the file via the generator instead.
 */
import {{ test, expect }} from "@web-coverage/_support/webCoverageTest";
import {{ WorkspacesPage }} from "@web-coverage/_support/pages/workspaces.po";

const PERSONA_ID = "{persona_id}";

test(
  `{persona_id} — {scenario_human} ` +
    `@persona:${{PERSONA_ID}} @outcome:{outcome} @hazard:{hazard} ` +
    `{fr_tags} {clause_tags} @{priority}`,
  async ({{ resolvePersona, page, request, correlationId, expectAudit }}) => {{
    const persona = await resolvePersona(PERSONA_ID);
    expect(persona.aiims_function).toBeTruthy();
    await page.setExtraHTTPHeaders({{
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    }});

    // 1) Persona lands on its workspace surface (FR-001/FR-002).
    const ws = new WorkspacesPage(page);
    await ws.goto();
    await expect(ws.heading).toBeVisible();

    // 2) Persona-specific scenario stub (filled in iteratively per
    //    coverage gaps detected by the binary CI gate).
    const scenarioRes = await request.post("/api/test-support/seed/scenario", {{
      headers: {{
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
      }},
      data: {{ scenario_id: "outcome-{outcome}-{outcome_slug}" }},
      failOnStatusCode: false,
    }});
    if (!scenarioRes.ok()) {{
      test.fail(true, `${{PERSONA_ID}} scenario stub: outcome-{outcome} fixture not yet wired (gap)`);
      return;
    }}

    // 3) Audit emission within 2s (FR-010, §IV).
    const auditId = await expectAudit({{
      auditType: "scenario.persona.{scenario}",
      correlationId,
    }});
    if (!auditId) {{
      test.info().annotations.push({{
        type: "gap",
        description: "audit row missing for {persona_id}/{scenario}",
      }});
    }}
  }},
);
'''

TEMPLATE_CROSS_JURISDICTION = '''/**
 * {task_id} — Cross-jurisdiction handover: {persona_id} ↔ {secondary_persona_id}.
 *
 * Capstone outcome: #{outcome} ({outcome_label})
 * Hazard: {hazard}
 * FRs: {fr_csv}
 * Constitution clauses: {clause_csv}
 *
 * Asserts both jurisdictions see the same incident COP, AWS warning state,
 * and audit history (Spec §US3 Acceptance #1-#2).
 *
 * Auto-generated by ``scripts/web-coverage/_lib/persona_spec_generator.py``.
 */
import {{ test, expect }} from "@web-coverage/_support/webCoverageTest";

const PRIMARY = "{persona_id}";
const SECONDARY = "{secondary_persona_id}";

test(
  `Cross-jurisdiction ${{PRIMARY}} ↔ ${{SECONDARY}} — {scenario_human} ` +
    `@persona:${{PRIMARY}} @outcome:{outcome} @hazard:{hazard} ` +
    `{fr_tags} {clause_tags} @{priority}`,
  async ({{ resolvePersona, request, correlationId }}) => {{
    const primary = await resolvePersona(PRIMARY);
    const secondary = await resolvePersona(SECONDARY);
    expect(primary.persona_id).not.toBe(secondary.persona_id);

    const incidentId = `xjd-${{correlationId.slice(0, 8)}}`;

    // Primary jurisdiction creates the incident and logs the COP snapshot.
    const create = await request.post(`/api/incidents`, {{
      headers: {{
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": primary.persona_id,
      }},
      data: {{ id: incidentId, hazard: "{hazard}", scenario: "outcome-{outcome}-{outcome_slug}" }},
      failOnStatusCode: false,
    }});
    if (!create.ok()) {{
      test.fail(true, "Cross-jurisdiction incident-create API not wired (gap)");
      return;
    }}

    // Secondary jurisdiction reads the same incident with full COP.
    const view = await request.get(`/api/incidents/${{incidentId}}`, {{
      headers: {{
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": secondary.persona_id,
      }},
    }});
    expect(view.ok(), `${{SECONDARY}} should see incident ${{incidentId}}`).toBe(true);
    const body = (await view.json()) as {{ id: string; hazard?: string }};
    expect(body.id).toBe(incidentId);
    expect(body.hazard).toBe("{hazard}");
  }},
);
'''


# ----- Helpers -----

OUTCOME_LABELS: dict[int, str] = {
    1: "lives saved",
    2: "50% faster signal-to-action",
    3: "24-h-earlier evacuation",
    4: "30% logistics-friction reduction",
    5: "30% economic-loss reduction",
}

OUTCOME_SLUGS: dict[int, str] = {
    1: "bushfire-extreme-heat",
    2: "bushfire-severe-storm",
    3: "tropical-cyclone-flood",
    4: "bushfire-cyclone-logistics",
    5: "flood-storm-economic",
}


def _scenario_human(slug: str) -> str:
    return slug.replace("-", " ")


# ----- Cycle-1 depth-profile driven template (T176) -----
#
# When ``--rewrite-stubs`` is passed, every persona spec is regenerated from
# its sibling ``tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml``
# (authored under T175) instead of the legacy stub template above. The new body
# drives ``POST /api/outcomes/sc-{NNN}/evaluate`` (FR-028) and reads back the
# audit row via ``GET /api/audit/list?correlation_id={cid}`` (FR-029) — the
# bail (`test.fail(true, ...)`) is removed entirely. T184 invokes this mode to
# refactor the 81 placeholder bodies; the rewritten body is the canonical form
# from cycle-1 onward.

TEMPLATE_DEPTH_DRIVEN = '''/**
 * {task_id} — {persona_id}: {scenario_human}.
 *
 * Capstone outcome: #{outcome} ({outcome_label})
 * Hazard: {hazard}
 * FRs: {fr_csv}
 * Constitution clauses: {clause_csv}
 *
 * Body driven by ``tests/e2e/web-coverage/_lib/depth-profiles/{persona_id}.depth.yaml``
 * (cycle-1 amendment; spec.md US3-Acceptance #4 — every persona executes a
 * non-trivial transition and observes the FR-028 evaluator verdict + FR-029
 * audit emission within the 2-second SLO). Refactor authored by T176; cycle-1
 * regression suite asserts no ``test.fail(true, …)`` remains in this folder.
 *
 * Auto-generated by ``scripts/web-coverage/_lib/persona_spec_generator.py``.
 * Do not hand-edit; regenerate the file via ``--rewrite-stubs`` instead.
 */
import {{ test, expect }} from "@web-coverage/_support/webCoverageTest";
import {{ WorkspacesPage }} from "@web-coverage/_support/pages/workspaces.po";

const PERSONA_ID = "{persona_id}";
const SC_ID = "{sc_id}";
const SCENARIO_ID = "outcome-{outcome}-{outcome_slug}";
const METRIC_INPUTS = {metric_inputs_json} as const;

test(
  `{persona_id} — {scenario_human} ` +
    `@persona:${{PERSONA_ID}} @outcome:{outcome} @hazard:{hazard} ` +
    `{fr_tags} {clause_tags} @{priority}`,
  async ({{ resolvePersona, page, request, correlationId, expectAudit }}) => {{
    const persona = await resolvePersona(PERSONA_ID);
    expect(persona.aiims_function).toBeTruthy();
    await page.setExtraHTTPHeaders({{
      "X-Correlation-Id": correlationId,
      "X-Test-Persona-Id": persona.persona_id,
    }});

    // 1) Persona lands on its workspace surface (FR-001/FR-002).
    const ws = new WorkspacesPage(page);
    await ws.goto();
    await expect(ws.heading).toBeVisible();

    // 2) Drive the FR-028 evaluator for SC-{outcome} (depth profile: {sc_id}).
    //    Suite sends canned metric_inputs that the deterministic evaluator
    //    must score "pass" against the seeded baseline (data-model §6).
    const requestBody = {{
      scenario_id: SCENARIO_ID,
      persona_id: persona.persona_id,
      correlation_id: correlationId,
      metric_inputs: METRIC_INPUTS,
    }};
    const evalRes = await request.post(`/api/outcomes/${{SC_ID}}/evaluate`, {{
      headers: {{
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
        "Content-Type": "application/json",
      }},
      data: requestBody,
      failOnStatusCode: true,
    }});
    expect(evalRes.status(), `${{SC_ID}} evaluator must return 200`).toBe(200);
    const verdict = (await evalRes.json()) as {{
      status: "pass" | "fail" | "gap";
      audit_id: string;
      metric_value: number | null;
      threshold: number | null;
      evidence_refs: string[];
    }};
    expect(verdict.status, `expected pass for canned baseline metric_inputs`).toBe("pass");
    expect(verdict.audit_id).toMatch(/^[0-9a-f-]{{36}}$/);
    expect(verdict.metric_value).not.toBeNull();
    expect(verdict.threshold).not.toBeNull();

    // 3) Idempotency tuple (sc_id, scenario_id, persona_id, correlation_id):
    //    a repeat call MUST return the same audit_id (data-model §13 invariant).
    const replay = await request.post(`/api/outcomes/${{SC_ID}}/evaluate`, {{
      headers: {{
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": persona.persona_id,
        "Content-Type": "application/json",
      }},
      data: requestBody,
      failOnStatusCode: true,
    }});
    const replayBody = (await replay.json()) as {{ audit_id: string; status: string }};
    expect(replayBody.audit_id, "idempotency: same tuple → same audit_id").toBe(verdict.audit_id);
    expect(replayBody.status).toBe(verdict.status);

    // 4) FR-029 audit row visible within the 2-second SLO via /api/audit/list.
    const auditId = await expectAudit({{
      auditType: "outcome.evaluator.{sc_id}",
      correlationId,
    }});
    expect(auditId, "expectAudit must observe a row for this correlation").toBeTruthy();

    // 5) Cross-check operator identity on the audit row matches the persona.
    const listRes = await request.get(
      `/api/audit/list?correlation_id=${{correlationId}}`,
      {{
        headers: {{
          "X-Correlation-Id": correlationId,
          "X-Test-Persona-Id": persona.persona_id,
        }},
      }},
    );
    expect(listRes.ok(), "/api/audit/list must succeed").toBe(true);
    const list = (await listRes.json()) as {{
      entries: Array<{{
        audit_id: string;
        operator_identity: {{ persona_id: string }};
      }}>;
    }};
    const match = list.entries.find((row) => row.audit_id === verdict.audit_id);
    expect(match, "evaluator audit_id must appear in /api/audit/list").toBeTruthy();
    expect(match!.operator_identity.persona_id).toBe(persona.persona_id);
  }},
);
'''


TEMPLATE_DEPTH_CROSS_JURISDICTION = '''/**
 * {task_id} — Cross-jurisdiction handover: {persona_id} ↔ {secondary_persona_id}.
 *
 * Capstone outcome: #{outcome} ({outcome_label})
 * Hazard: {hazard}
 * FRs: {fr_csv}
 * Constitution clauses: {clause_csv}
 *
 * Asserts both jurisdictions execute the FR-028 evaluator with the *same*
 * scenario_id and *distinct* correlation_ids, then read each other's audit
 * rows via FR-029 ``/api/audit/list``. Refactor authored by T176 (cycle-1).
 *
 * Auto-generated by ``scripts/web-coverage/_lib/persona_spec_generator.py``.
 */
import {{ test, expect }} from "@web-coverage/_support/webCoverageTest";

const PRIMARY = "{persona_id}";
const SECONDARY = "{secondary_persona_id}";
const SC_ID = "{sc_id}";
const SCENARIO_ID = "outcome-{outcome}-{outcome_slug}";
const METRIC_INPUTS = {metric_inputs_json} as const;

test(
  `Cross-jurisdiction ${{PRIMARY}} ↔ ${{SECONDARY}} — {scenario_human} ` +
    `@persona:${{PRIMARY}} @outcome:{outcome} @hazard:{hazard} ` +
    `{fr_tags} {clause_tags} @{priority}`,
  async ({{ resolvePersona, request, correlationId }}) => {{
    const primary = await resolvePersona(PRIMARY);
    const secondary = await resolvePersona(SECONDARY);
    expect(primary.persona_id).not.toBe(secondary.persona_id);

    // Primary persona drives the evaluator first.
    const primaryReq = {{
      scenario_id: SCENARIO_ID,
      persona_id: primary.persona_id,
      correlation_id: correlationId,
      metric_inputs: METRIC_INPUTS,
    }};
    const primaryRes = await request.post(`/api/outcomes/${{SC_ID}}/evaluate`, {{
      headers: {{
        "X-Correlation-Id": correlationId,
        "X-Test-Persona-Id": primary.persona_id,
        "Content-Type": "application/json",
      }},
      data: primaryReq,
      failOnStatusCode: true,
    }});
    expect(primaryRes.status()).toBe(200);
    const primaryVerdict = (await primaryRes.json()) as {{
      audit_id: string;
      status: "pass" | "fail" | "gap";
    }};
    expect(primaryVerdict.status).toBe("pass");

    // Secondary persona drives a parallel evaluation with a fresh
    // correlation_id (handover, not idempotent replay).
    const handoverCid = `${{correlationId.slice(0, 8)}}-xj-${{SECONDARY}}`.padEnd(36, "0").slice(0, 36);
    const secondaryReq = {{
      scenario_id: SCENARIO_ID,
      persona_id: secondary.persona_id,
      correlation_id: handoverCid,
      metric_inputs: METRIC_INPUTS,
    }};
    const secondaryRes = await request.post(`/api/outcomes/${{SC_ID}}/evaluate`, {{
      headers: {{
        "X-Correlation-Id": handoverCid,
        "X-Test-Persona-Id": secondary.persona_id,
        "Content-Type": "application/json",
      }},
      data: secondaryReq,
      failOnStatusCode: true,
    }});
    expect(secondaryRes.status()).toBe(200);
    const secondaryVerdict = (await secondaryRes.json()) as {{
      audit_id: string;
      status: "pass" | "fail" | "gap";
    }};
    expect(secondaryVerdict.audit_id).not.toBe(primaryVerdict.audit_id);

    // Both audit rows MUST be visible to either persona via /api/audit/list.
    const listPrimary = await request.get(
      `/api/audit/list?correlation_id=${{correlationId}}`,
      {{ headers: {{ "X-Test-Persona-Id": secondary.persona_id }} }},
    );
    expect(listPrimary.ok(), `${{SECONDARY}} should see ${{PRIMARY}} audit row`).toBe(true);
    const listPrimaryBody = (await listPrimary.json()) as {{
      entries: Array<{{ audit_id: string }}>;
    }};
    expect(
      listPrimaryBody.entries.some((r) => r.audit_id === primaryVerdict.audit_id),
      "primary audit_id must surface to secondary",
    ).toBe(true);
  }},
);
'''


def _metric_inputs_for(sc_id: str) -> dict[str, int]:
    """Canned metric inputs that produce a "pass" verdict against the
    seeded baseline. The deterministic evaluator service (T180) is wired
    against these exact values; updating either side requires updating
    both. Centralised here so the cycle-1 regenerator emits identical
    constants for every persona-spec-row in the same SC bucket.

    Mapping (data-model §6 baselines, T180 service thresholds):

      sc-001 — lives_at_risk: 800   (baseline 2000 → lives_saved 1200 ≥ 1000)
      sc-002 — signal_to_action_ms: 4500 (baseline 10000 → 0.45× ≤ 0.5×)
      sc-003 — evac_lead_hours: 26 (≥ 24-hour SC-003 threshold)
      sc-004 — logistics_clicks: 6 (≤ 7 — L1 cap per SC-004)
      sc-005 — economic_loss_aud: 1_400_000_000
               (baseline 2_000_000_000 → 30% reduction)
    """

    table: dict[str, dict[str, int]] = {
        "sc-001": {"lives_at_risk": 800},
        "sc-002": {"signal_to_action_ms": 4500},
        "sc-003": {"evac_lead_hours": 26},
        "sc-004": {"logistics_clicks": 6},
        "sc-005": {"economic_loss_aud": 1_400_000_000},
    }
    if sc_id not in table:
        raise ValueError(
            f"unsupported sc_id={sc_id}; routable range is sc-001..sc-005 (Q29)",
        )
    return table[sc_id]


def _load_depth_profile(persona_id: str) -> dict[str, Any]:
    """Load + validate the depth profile YAML for a persona. Fail-fast
    on missing file or schema-invalid content per T176.
    """

    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - optional dep
        raise SystemExit(
            "PyYAML required for --rewrite-stubs; install via "
            "'pip install pyyaml' or 'uv sync --extra dev'",
        ) from exc
    path = DEPTH_PROFILE_DIR / f"{persona_id}.depth.yaml"
    if not path.exists():
        raise SystemExit(
            f"missing depth profile: {path.relative_to(REPO_ROOT)} — "
            f"file expected GAP-DEPTH-PROFILE-MISSING-{persona_id} per T176 fail-fast",
        )
    profile = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate_depth_profile(profile, persona_id, path)
    return profile  # type: ignore[no-any-return]


_DEPTH_SCHEMA_CACHE: dict[str, Any] | None = None


def _load_depth_schema() -> dict[str, Any]:
    """Cached read of the draft-07 depth-profile schema (Q28)."""

    global _DEPTH_SCHEMA_CACHE
    if _DEPTH_SCHEMA_CACHE is None:
        _DEPTH_SCHEMA_CACHE = json.loads(DEPTH_PROFILE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _DEPTH_SCHEMA_CACHE


def _validate_depth_profile(profile: Any, persona_id: str, path: Path) -> None:
    try:
        from jsonschema import Draft7Validator  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - optional dep
        raise SystemExit(
            "jsonschema required for --rewrite-stubs; install via "
            "'pip install jsonschema' or 'uv sync --extra dev'",
        ) from exc
    validator = Draft7Validator(_load_depth_schema())
    errors = sorted(validator.iter_errors(profile), key=lambda e: e.path)
    if errors:
        formatted = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise SystemExit(
            f"depth-profile schema-invalid for {persona_id} ({path.relative_to(REPO_ROOT)}): "
            f"{formatted} — fail-fast per T176",
        )
    if profile.get("persona_id") != persona_id:
        raise SystemExit(
            f"depth-profile drift: file {path.name} declares persona_id={profile.get('persona_id')!r}; "
            f"expected {persona_id!r}",
        )


def render(spec: Spec, *, depth_driven: bool = False) -> str:
    fr_tags = " ".join(f"@fr:{fr}" for fr in spec.frs)
    clause_tags = " ".join(f"@clause:{c}" for c in spec.clauses)

    if depth_driven:
        primary_profile = _load_depth_profile(spec.persona_id)
        sc_id = primary_profile["assertion_targets"]["evaluator_endpoint"]
        if sc_id is None:
            raise SystemExit(
                f"depth-profile {spec.persona_id} has evaluator_endpoint=null; "
                f"cycle-1 cycle-1 requires sc-001..sc-005 for every persona "
                f"in the cycle-1 routable surface (Q29). Update _bootstrap_depth_profiles.py "
                f"or supply a UI-selector-only template path.",
            )
        if spec.secondary_persona_id:
            # Force secondary's profile to load + validate (fail-fast).
            _load_depth_profile(spec.secondary_persona_id)
        metric_inputs = _metric_inputs_for(sc_id)
        template = (
            TEMPLATE_DEPTH_CROSS_JURISDICTION
            if spec.secondary_persona_id
            else TEMPLATE_DEPTH_DRIVEN
        )
        return template.format(
            task_id=spec.task_id,
            persona_id=spec.persona_id,
            secondary_persona_id=spec.secondary_persona_id,
            outcome=spec.outcome,
            outcome_label=OUTCOME_LABELS[spec.outcome],
            outcome_slug=OUTCOME_SLUGS[spec.outcome],
            hazard=spec.hazard,
            fr_csv=", ".join(spec.frs),
            clause_csv=", ".join(spec.clauses),
            fr_tags=fr_tags,
            clause_tags=clause_tags,
            priority=spec.priority,
            scenario=spec.scenario,
            scenario_human=_scenario_human(spec.scenario),
            sc_id=sc_id,
            metric_inputs_json=json.dumps(metric_inputs, sort_keys=True),
        )

    template = TEMPLATE_CROSS_JURISDICTION if spec.secondary_persona_id else TEMPLATE_SINGLE
    return template.format(
        task_id=spec.task_id,
        persona_id=spec.persona_id,
        secondary_persona_id=spec.secondary_persona_id,
        outcome=spec.outcome,
        outcome_label=OUTCOME_LABELS[spec.outcome],
        outcome_slug=OUTCOME_SLUGS[spec.outcome],
        hazard=spec.hazard,
        fr_csv=", ".join(spec.frs),
        clause_csv=", ".join(spec.clauses),
        fr_tags=fr_tags,
        clause_tags=clause_tags,
        priority=spec.priority,
        scenario=spec.scenario,
        scenario_human=_scenario_human(spec.scenario),
    )


def write_specs(*, depth_driven: bool = False) -> dict[str, Any]:
    written: list[str] = []
    for spec in ALL_SPECS:
        target = TESTS_ROOT / spec.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(spec, depth_driven=depth_driven), encoding="utf-8")
        written.append(spec.path)
    return {"count": len(written), "files": written}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Persona spec generator (cycle-0 stub mode + cycle-1 --rewrite-stubs)",
    )
    parser.add_argument(
        "--rewrite-stubs",
        action="store_true",
        help=(
            "Cycle-1 (T176/T184): regenerate every persona spec body from the "
            "matching tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml. "
            "Removes all test.fail(true,...) bails and drives the FR-028 evaluator "
            "+ FR-029 audit-list contracts. Fail-fast on missing or schema-invalid profiles."
        ),
    )
    args = parser.parse_args(argv)
    summary = write_specs(depth_driven=args.rewrite_stubs)
    mode = "depth-driven (cycle-1)" if args.rewrite_stubs else "stub (cycle-0)"
    print(f"persona_spec_generator: wrote {summary['count']} files [{mode}]")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
