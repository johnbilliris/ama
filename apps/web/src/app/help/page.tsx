/**
 * Help & support landing page.
 *
 * Surfaces operator-facing entry points to the constitutional preamble,
 * AIIMS persona reference, sector-specific scenarios, governance posture,
 * and offline runbooks. Chrome mirrors the Governance Dashboard so the hub
 * presents one consistent visual language across all top-level routes.
 */
import Link from "next/link";

interface HelpArticleRef {
  slug: string;
  label: string;
}

interface HelpLink {
  href: string;
  label: string;
  description: string;
  external?: boolean;
  icon?: string;
  cta?: string;
  helpArticles?: HelpArticleRef[];
}

const QUICK_START: HelpLink[] = [
  {
    href: "/",
    label: "Disaster Map",
    description: "Operating picture across federated signals, warnings, and overlays.",
    icon: "🗺️",
    cta: "Open map",
    helpArticles: [
      { slug: "screen-by-screen/disaster-mapper", label: "Disaster mapper guide" },
      { slug: "screen-by-screen/multi-jurisdiction-filter", label: "Multi-jurisdiction filter" },
    ],
  },
  {
    href: "/workspaces",
    label: "Workspaces",
    description: "Persona-driven operating views aligned to AIIMS functions.",
    icon: "🧭",
    cta: "Open workspaces",
    helpArticles: [
      { slug: "screen-by-screen/persona-switcher", label: "Persona switcher" },
      { slug: "getting-started", label: "Getting started" },
    ],
  },
  {
    href: "/sectors",
    label: "Sectors",
    description: "Jurisdiction- and sector-specific scenarios from the capstone success criteria.",
    icon: "🏛️",
    cta: "Open sectors",
    helpArticles: [
      { slug: "cross-border-bushfire-nema", label: "Cross-border bushfire (NEMA)" },
    ],
  },
  {
    href: "/governance/dashboard",
    label: "Governance Dashboard",
    description: "Constitutional gates, compliance, audit trail, readiness, recovery, and risk.",
    icon: "🛡️",
    cta: "Open dashboard",
    helpArticles: [
      { slug: "screen-by-screen/governance-dashboard", label: "Governance dashboard tour" },
      { slug: "screen-by-screen/audit-observer-view", label: "Audit observer view" },
      { slug: "constitution-principle-v", label: "Constitution principle V" },
    ],
  },
  {
    href: "/preparedness",
    label: "Preparedness",
    description: "Pre-event jurisdiction coverage, frameworks, and coordination gaps.",
    icon: "📋",
    cta: "Open preparedness",
    helpArticles: [
      { slug: "getting-started", label: "Getting started" },
      { slug: "accessibility-how-to", label: "Accessibility how-to" },
    ],
  },
  // AUD-017 / FR-022 — no simulation affordance is exposed from the live
  // help catalogue. The exercise routes stay directly addressable and carry
  // their own navigation under the /simulations layout.
];

const REFERENCE_LINKS: HelpLink[] = [
  {
    href: "https://github.com/Azure/ama",
    label: "Source repository",
    description: "Code, specs, contracts, and operator runbooks.",
    external: true,
    icon: "📦",
    cta: "View on GitHub",
  },
  {
    href: "https://learn.microsoft.com/azure/well-architected/",
    label: "Azure Well-Architected Framework",
    description: "Reliability, security, cost, operational excellence, and performance pillars.",
    external: true,
    icon: "📐",
    cta: "Read on Microsoft Learn",
  },
  {
    href: "https://www.aidr.org.au/",
    label: "Australian Institute for Disaster Resilience",
    description: "AIDR handbooks, AIIMS doctrine, and PPRR guidance referenced by the hub.",
    external: true,
    icon: "📚",
    cta: "Visit AIDR",
  },
];

const FAQ: Array<{ q: string; a: string }> = [
  {
    q: "Where is my data hosted?",
    a: "All telemetry, signals, and operator state are processed and stored in Azure Australia regions. The hub enforces an AU-region guardrail across every page.",
  },
  {
    q: "How do I report an incident or escalate?",
    a: "Open the Disaster Map, locate the relevant signal or sector, and use the Incident Commander workspace to raise an approval or warning. All decisions are captured to the audit trail.",
  },
  {
    q: "What if I lose connectivity in the field?",
    a: "Field Coordinator workspaces and sector pages run an offline subsystem that queues critical actions and syncs once connectivity is restored.",
  },
  {
    q: "Where can I see system health and constitutional gates?",
    a: "The Governance Dashboard surfaces all 10 constitutional gates, data freshness, degraded-mode posture, and compliance against AIDR + AIIMS principles.",
  },
];

function HelpRow({ link }: { link: HelpLink }) {
  const rowClass =
    "help-quick-row grid grid-cols-1 items-start gap-4 rounded-xl border border-[color:var(--ama-border-subtle)] bg-[color:var(--ama-surface-elevated)] p-5 shadow-[var(--ama-shadow-xs)] md:grid-cols-3";
  const ctaLabel = link.cta ?? (link.external ? "Open link" : "Open page");
  const arrow = link.external ? "↗" : "→";

  const NameCell = (
    <div className="flex items-start gap-3">
      <span
        aria-hidden="true"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-xl ring-1 ring-blue-100"
      >
        {link.icon ?? "•"}
      </span>
      <div className="min-w-0">
        <p className="preparedness-kicker">
          {link.external ? "Reference" : "Hub section"}
        </p>
        {link.external ? (
          <a
            className="mt-1 block text-base font-semibold text-gray-900 hover:text-[color:var(--ama-color-ocean)] hover:underline"
            href={link.href}
            target="_blank"
            rel="noreferrer noopener"
          >
            {link.label}
          </a>
        ) : (
          <Link
            className="mt-1 block text-base font-semibold text-gray-900 hover:text-[color:var(--ama-color-ocean)] hover:underline"
            href={link.href}
          >
            {link.label}
          </Link>
        )}
      </div>
    </div>
  );

  const BlurbCell = (
    <p className="text-sm leading-relaxed text-gray-600">{link.description}</p>
  );

  const HelpCell = (
    <div>
      <p className="preparedness-kicker mb-1">Help articles</p>
      {link.helpArticles && link.helpArticles.length > 0 ? (
        <ul className="list-none space-y-1 p-0">
          {link.helpArticles.map((a) => (
            <li key={a.slug}>
              <Link
                className="inline-flex items-start gap-1 text-sm text-[color:var(--ama-color-ocean)] hover:underline"
                href={`/help/articles/${a.slug}`}
              >
                <span aria-hidden="true">→</span>
                <span>{a.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : link.external ? (
        <a
          className="inline-flex items-start gap-1 text-sm text-[color:var(--ama-color-ocean)] hover:underline"
          href={link.href}
          target="_blank"
          rel="noreferrer noopener"
        >
          <span aria-hidden="true">↗</span>
          <span>Visit reference</span>
        </a>
      ) : (
        <p className="text-sm text-gray-500">No related help articles yet.</p>
      )}
    </div>
  );

  return (
    <div className={rowClass}>
      {NameCell}
      {BlurbCell}
      {HelpCell}
    </div>
  );
}

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-7xl">
      <header className="preparedness-header page-gutter-header">
        <p className="preparedness-kicker">Support</p>
        <h1 className="preparedness-title">Help &amp; reference</h1>
        <p className="preparedness-copy">
          Quick links, doctrine references, and frequently asked questions for
          operators of the Autonomous Disaster Response Coordination Hub.
        </p>
        <div
          data-testid="au-region-banner"
          role="note"
          aria-label="Data residency"
          className="mt-3 inline-flex items-center rounded border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-900"
        >
          Hosted in Australia · AU data residency
        </div>
      </header>

      <div className="space-y-6 p-6">
        <section aria-labelledby="quick-start-heading">
          <h2
            id="quick-start-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700"
          >
            Quick start
          </h2>
          <ul
            className="list-none space-y-3 p-0"
            aria-label="Quick start destinations"
          >
            {QUICK_START.map((link) => (
              <li key={link.href}>
                <HelpRow link={link} />
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="reference-heading">
          <h2
            id="reference-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700"
          >
            Doctrine &amp; reference
          </h2>
          <ul
            className="list-none space-y-3 p-0"
            aria-label="External reference material"
          >
            {REFERENCE_LINKS.map((link) => (
              <li key={link.href}>
                <HelpRow link={link} />
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="faq-heading">
          <h2
            id="faq-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700"
          >
            Frequently asked questions
          </h2>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <dl className="grid gap-4">
              {FAQ.map(({ q, a }) => (
                <div key={q} className="border-t border-gray-100 pt-3 first:border-t-0 first:pt-0">
                  <dt className="text-sm font-semibold text-gray-900">{q}</dt>
                  <dd className="mt-1 text-sm text-gray-600">{a}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>
      </div>
    </div>
  );
}
