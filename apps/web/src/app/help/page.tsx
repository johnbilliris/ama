/**
 * Help & support landing page.
 *
 * Surfaces operator-facing entry points to the constitutional preamble,
 * AIIMS persona reference, sector-specific scenarios, governance posture,
 * and offline runbooks. Chrome mirrors the Governance Dashboard so the hub
 * presents one consistent visual language across all top-level routes.
 */
import Link from "next/link";

interface HelpLink {
  href: string;
  label: string;
  description: string;
  external?: boolean;
}

const QUICK_START: HelpLink[] = [
  {
    href: "/",
    label: "Disaster Map",
    description: "Operating picture across federated signals, warnings, and overlays.",
  },
  {
    href: "/workspaces",
    label: "Workspaces",
    description: "Persona-driven operating views aligned to AIIMS functions.",
  },
  {
    href: "/sectors",
    label: "Sectors",
    description: "Jurisdiction- and sector-specific scenarios from the capstone success criteria.",
  },
  {
    href: "/governance/dashboard",
    label: "Governance Dashboard",
    description: "Constitutional gates, compliance, audit trail, readiness, recovery, and risk.",
  },
  {
    href: "/preparedness",
    label: "Preparedness",
    description: "Pre-event jurisdiction coverage, frameworks, and coordination gaps.",
  },
  {
    href: "/simulations",
    label: "Simulations",
    description: "Tabletop and live-fire exercises with replay and warp playback.",
  },
];

const REFERENCE_LINKS: HelpLink[] = [
  {
    href: "https://github.com/Azure/ama",
    label: "Source repository",
    description: "Code, specs, contracts, and operator runbooks.",
    external: true,
  },
  {
    href: "https://learn.microsoft.com/azure/well-architected/",
    label: "Azure Well-Architected Framework",
    description: "Reliability, security, cost, operational excellence, and performance pillars.",
    external: true,
  },
  {
    href: "https://www.aidr.org.au/",
    label: "Australian Institute for Disaster Resilience",
    description: "AIDR handbooks, AIIMS doctrine, and PPRR guidance referenced by the hub.",
    external: true,
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

function HelpCardLink({ link }: { link: HelpLink }) {
  const className =
    "rounded-lg border border-gray-200 bg-white p-4 transition-colors hover:border-blue-300";
  if (link.external) {
    return (
      <a
        className={className}
        href={link.href}
        target="_blank"
        rel="noreferrer noopener"
      >
        <h3 className="text-base font-semibold text-blue-700 underline">
          {link.label} ↗
        </h3>
        <p className="mt-1 text-sm text-gray-600">{link.description}</p>
      </a>
    );
  }
  return (
    <Link className={className} href={link.href}>
      <h3 className="text-base font-semibold text-blue-700 underline">
        {link.label}
      </h3>
      <p className="mt-1 text-sm text-gray-600">{link.description}</p>
    </Link>
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

      <main className="space-y-6 p-6">
        <section aria-labelledby="quick-start-heading">
          <h2
            id="quick-start-heading"
            className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700"
          >
            Quick start
          </h2>
          <ul
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
            aria-label="Quick start destinations"
          >
            {QUICK_START.map((link) => (
              <li key={link.href}>
                <HelpCardLink link={link} />
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
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
            aria-label="External reference material"
          >
            {REFERENCE_LINKS.map((link) => (
              <li key={link.href}>
                <HelpCardLink link={link} />
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
      </main>
    </div>
  );
}
