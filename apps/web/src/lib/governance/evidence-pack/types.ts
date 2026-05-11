/**
 * T039 — TypeScript types for spec-037 evidence-pack artefacts.
 * Mirrors the JSON Schemas under packages/schemas/spec_037/.
 *
 * Citations: FR-021, RES-03.
 */

export type ArtefactId =
  | 'risk_register'
  | 'adoption_roadmap'
  | 'executive_kpi_surface'
  | 'rai_register'
  | 'feature_value_ledger';

export type CapstoneCriterion =
  | 'lives-saved'
  | 'response-time'
  | 'evacuation-lead-time'
  | 'logistics-efficiency'
  | 'economic-loss-reduction';

export interface PublicationGateMetadata {
  manual_row_count: number;
  total_row_count: number;
  manual_row_ratio: number;
  manual_row_ratio_threshold?: number;
  auditor_signoff?: AuditorSignoff;
  link_check_status: 'passed' | 'failed' | 'pending';
  last_gate_run_utc: string;
}

export interface AuditorSignoff {
  name: string;
  role: string;
  signoff_date_utc: string;
  basis: string;
}

export interface ArtefactSummary {
  artefact_id: ArtefactId;
  publication_id: string;
  published_at_utc: string;
  manual_row_ratio: number;
  total_row_count: number;
  auditor_signoff_present: boolean;
}

export interface KpiRow {
  kpi_id: string;
  capstone_criterion: CapstoneCriterion;
  kind: 'leading' | 'lagging';
  name: string;
  owner: string;
  refresh_cadence: 'realtime' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'quarterly';
  target_value: number;
  target_unit: string;
  threshold_band: { green: string; amber: string; red: string };
  source_of_truth: { kind: string; ref: string; section?: string };
  consolidates?: string[];
  current_value?: number;
  last_observed_utc?: string;
}

export interface EvidencePackArtefact {
  artefact_id: ArtefactId;
  schema_version: string;
  publication_id: string;
  published_at_utc: string;
  published_by: string;
  metadata: PublicationGateMetadata;
  rows: Record<string, unknown>[];
  superseded_surfaces?: string[];
  tradeoffs?: Record<string, unknown>[];
}

export interface EvidencePackHealth {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  artefacts: Array<{
    artefact_id: ArtefactId;
    last_publication_utc: string;
    manual_row_ratio: number;
    gate_status: 'passed' | 'failed' | 'pending';
  }>;
}
