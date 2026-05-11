"use client";
/** spec-038 T-AA119 — one-click support-handoff button using tenant SupportHandoffRecord. */
import { useEffect, useState } from "react";

interface Handoff {
  label: string;
  destination_url?: string;
  email?: string;
  phone?: string;
}

export function SupportHandoffButton() {
  const [handoff, setHandoff] = useState<Handoff | null>(null);

  useEffect(() => {
    fetch("/api/v1/help/support-handoff", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => setHandoff(j))
      .catch(() => undefined);
  }, []);

  if (!handoff) return null;
  const href = handoff.destination_url ?? (handoff.email ? `mailto:${handoff.email}` : handoff.phone ? `tel:${handoff.phone}` : "#");
  return (
    <a href={href} className="inline-flex items-center rounded bg-blue-600 px-3 py-1 text-sm text-white">
      Contact {handoff.label}
    </a>
  );
}
