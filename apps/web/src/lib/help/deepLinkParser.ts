/**
 * spec-038 T-AA094 — deep-link parser for the `?help=open&surface=...&persona=...` URL contract.
 */

export interface HelpDeepLink {
  open: boolean;
  surface?: string;
  persona?: string;
  article?: string;
  glossary?: string;
}

export function parseHelpDeepLink(url: string | URL): HelpDeepLink {
  const u = typeof url === "string" ? new URL(url, "http://placeholder") : url;
  const q = u.searchParams;
  return {
    open: q.get("help") === "open",
    surface: q.get("surface") ?? undefined,
    persona: q.get("persona") ?? undefined,
    article: q.get("article") ?? undefined,
    glossary: q.get("glossary") ?? undefined,
  };
}

export function isPersonaEntitled(persona: string, entitlements: readonly string[]): boolean {
  return entitlements.includes(persona);
}
