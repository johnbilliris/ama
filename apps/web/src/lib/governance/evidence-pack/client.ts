/**
 * T039 — Evidence Pack API client (server-side fetch helpers).
 *
 * Uses the existing MSAL token interceptor pattern (apps/web/src/lib/api/).
 * Read-only — these helpers never POST/PUT/DELETE.
 *
 * Server-side (Server Components, Route Handlers) bypasses the Next.js /api
 * proxy and reads from API_PROXY_UPSTREAM directly because relative URLs have
 * no origin during SSR. Client-side reads from NEXT_PUBLIC_API_BASE (which is
 * "/api" relative so the browser hits the same-origin proxy rewrite).
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
  if (typeof window === 'undefined') {
    return (
      process.env.API_PROXY_UPSTREAM ??
      process.env.NEXT_PUBLIC_API_BASE ??
      'http://localhost:8000/api'
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE ?? '/api';
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
