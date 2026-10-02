import { getApiBaseUrl } from "@/lib/api/base-url";
/**
 * T039 — Evidence Pack API client (server-side fetch helpers).
 *
 * Uses the existing MSAL token interceptor pattern (apps/web/src/lib/api/).
 * Read-only — these helpers never POST/PUT/DELETE.
 *
 * Server-side requests use the configured API endpoint because relative URLs
 * have no origin during SSR. Client-side requests use the same-origin API proxy.
 *
 * Citations: FR-021, RES-03.
 */
import type {
  ArtefactId,
  ArtefactSummary,
  EvidencePackArtefact,
  EvidencePackHealth,
} from './types';

function _resolveBase(): string {
  return getApiBaseUrl();
}

async function _fetch<T>(path: string, init?: RequestInit): Promise<T> {
  // Next.js extends RequestInit with a `next` field for revalidation; cast to
  // satisfy stock lib.dom.d.ts types without pulling in next-types globally.
  const nextInit = {
    ...init,
    headers: { Accept: 'application/json', ...(init?.headers ?? {}) },
    next: { revalidate: 60 },
  } as RequestInit;
  const res = await fetch(`${_resolveBase()}${path}`, nextInit);
  if (!res.ok) {
    throw new Error(`Evidence-pack API ${res.status}: ${path}`);
  }
  return (await res.json()) as T;
}

export function listArtefacts(): Promise<ArtefactSummary[]> {
  return _fetch('/governance/evidence-pack/artefacts');
}

export function getArtefact(artefactId: ArtefactId): Promise<EvidencePackArtefact> {
  return _fetch(`/governance/evidence-pack/artefacts/${artefactId}`);
}

export function getHistoricalPublication(
  artefactId: ArtefactId,
  publicationId: string,
): Promise<EvidencePackArtefact> {
  return _fetch(
    `/governance/evidence-pack/artefacts/${artefactId}/publications/${publicationId}`,
  );
}

export function getHealth(): Promise<EvidencePackHealth> {
  return _fetch('/governance/evidence-pack/health');
}
