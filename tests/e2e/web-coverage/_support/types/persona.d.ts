/**
 * Persona type declarations consumed by the spec-034 web coverage suite.
 *
 * The shape mirrors the server-side Python `Identity` model (see
 * `packages/domain/src/domain/seed/identities_australia.json`) and the
 * contract in `specs/034-webapp-capstone-coverage/contracts/persona-fixture.contract.md`.
 */

export type AiimsFunction =
  | "control"
  | "operations"
  | "planning"
  | "logistics"
  | "public-information";

export type JurisdictionId =
  | "nsw"
  | "vic"
  | "qld"
  | "sa"
  | "wa"
  | "tas"
  | "act"
  | "nt"
  | "commonwealth"
  | "cross-sector";

export interface PersonaFixture {
  persona_id: string;
  display_name: string;
  organisation_id: string;
  jurisdiction_id: JurisdictionId;
  /**
   * Free-form organisational role title — see contract notes.
   * RBAC checks MUST use {@link aiims_function} not this string.
   */
  role: string;
  permissions: string[];
  aiims_function: AiimsFunction;
  direct_reports: string[];
}

export interface HazardScenarioFixture {
  scenario_id: string;
  outcome: 1 | 2 | 3 | 4 | 5;
  name: string;
  hazards: string[];
  primary_jurisdiction: JurisdictionId;
  secondary_jurisdictions: JurisdictionId[];
  season: string;
  trigger_event: string;
  constitution_clauses: string[];
  applicable_personas: string[];
}
