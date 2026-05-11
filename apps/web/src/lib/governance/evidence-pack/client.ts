/**
 * T039 — Evidence Pack API client (server-side fetch helpers).
 *
 * Uses the existing MSAL token interceptor pattern (apps/web/src/lib/api/).
 * Read-only — these helpers never POST/PUT/DELETE.
 *
 * Citations: FR-021, RES-03.
 */
import type {
  ArtefactId,
  ArtefactSummary,
  EvidencePackArtefact,
  EvidencePackHealth,
} from './types';

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? '';

async function _fetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...(init?.headers ?? {}) },
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    throw new Error(`Evidence-pack API ${res.status}: ${path}`);
  }
  return (await res.json()) as T;
}

export function listArtefacts(): Promise<ArtefactSummary[]> {
  return _fetch('/api/governance/evidence-pack/artefacts');
}

export function getArtefact(artefactId: ArtefactId): Promise<EvidencePackArtefact> {
  return _fetch(`/api/governance/evidence-pack/artefacts/${artefactId}`);
}

export function getHistoricalPublication(
  artefactId: ArtefactId,
  publicationId: string,
): Promise<EvidencePackArtefact> {
  return _fetch(
    `/api/governance/evidence-pack/artefacts/${artefactId}/publications/${publicationId}`,
  );
}

export function getHealth(): Promise<EvidencePackHealth> {
  return _fetch('/api/governance/evidence-pack/health');
}
