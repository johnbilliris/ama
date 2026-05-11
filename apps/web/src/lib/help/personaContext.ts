/**
 * spec-038 T-AA097 — persona context client hook.
 *
 * Mirrors the backend persona resolver (apps/api/app/services/help/persona_resolver.py).
 * Returns the active persona + source (idp_default | user_override) + the
 * ranked union of entitled personas for multi-role users.
 */

import { useEffect, useState } from "react";

export type PersonaSource = "idp_default" | "user_override";

export interface PersonaContext {
  active: string;
  source: PersonaSource;
  entitlements: { personaId: string; authorityRank: number }[];
}

const DEFAULT: PersonaContext = {
  active: "operational-default",
  source: "idp_default",
  entitlements: [{ personaId: "operational-default", authorityRank: 0 }],
};

export function usePersonaContext(initial?: PersonaContext): {
  context: PersonaContext;
  switchPersona: (personaId: string) => void;
} {
  const [context, setContext] = useState<PersonaContext>(initial ?? DEFAULT);

  useEffect(() => {
    if (initial) return;
    // hydrate from /api/v1/personas/me when available
    let cancelled = false;
    fetch("/api/v1/personas/me", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => {
        if (cancelled || !j) return;
        const entitlements = (j.entitlements ?? []).slice().sort(
          (a: { authorityRank: number }, b: { authorityRank: number }) => b.authorityRank - a.authorityRank,
        );
        setContext({ active: j.active ?? entitlements[0]?.personaId ?? DEFAULT.active, source: "idp_default", entitlements });
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [initial]);

  function switchPersona(personaId: string) {
    setContext((prev) => ({ ...prev, active: personaId, source: "user_override" }));
  }

  return { context, switchPersona };
}
