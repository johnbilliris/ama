/**
 * Sector workspaces index (spec-035 T054..T060).
 *
 * Surfaces the 13 net-new sector personas (T187..T199) in one place so they
 * are reachable from the global header nav rather than only via direct URL.
 * Each card composes the spec-035 horizontal subsystems (cultural safety,
 * infrastructure overlay, claims velocity, offline queue, IC approval) in
 * a jurisdiction-specific layout.
 */
import Link from "next/link";

interface SectorEntry {
  slug: string;
  jurisdiction: string;
  title: string;
  description: string;
  fr: string;
  taskId: string;
}

const SECTORS: SectorEntry[] = [
  {
    slug: "sapol-control-centre",
    jurisdiction: "SA",
    title: "SAPOL State Control Centre",
    description: "Multi-LGA coordination dashboard with role-separation enforcement on routes.",
    fr: "FR-014",
    taskId: "T187",
  },
  {
    slug: "ses-sa-multi-lga",
    jurisdiction: "SA",
    title: "SES SA — Multi-LGA evacuation",
    description: "Coordinates evacuation across multiple LGAs with field-coordinator offline support.",
    fr: "FR-015",
    taskId: "T188",
  },
  {
    slug: "dfes-wa-cultural-safety",
    jurisdiction: "WA",
    title: "DFES WA — Cultural-safety subsystem",
    description: "Kimberley/Pilbara elder-routing flow with PIO composer + IC approval.",
    fr: "FR-016",
    taskId: "T189",
  },
  {
    slug: "dfes-wa-iron-ore",
    jurisdiction: "WA",
    title: "DFES WA — Iron-ore haul-road risk",
    description: "Iron-ore haul road infrastructure overlay with $-throughput sensitivity.",
    fr: "FR-017",
    taskId: "T190",
  },
  {
    slug: "at-tas-island-isolation",
    jurisdiction: "TAS",
    title: "AT TAS — Island isolation logistics",
    description: "Strait/island ferry & barge resupply links with field-coordinator offline support.",
    fr: "FR-018",
    taskId: "T191",
  },
  {
    slug: "taspol-multilingual",
    jurisdiction: "TAS",
    title: "Tasmania Police — multilingual public warnings",
    description: "palawa kani elder-routing + Simplified Chinese fallback chain.",
    fr: "FR-019",
    taskId: "T192",
  },
  {
    slug: "afp-act-precinct",
    jurisdiction: "ACT",
    title: "AFP ACT — Federal precinct",
    description: "Federal-tenancy overlay differentiating Commonwealth vs Territory governance.",
    fr: "FR-020",
    taskId: "T193",
  },
  {
    slug: "ses-act-declaration",
    jurisdiction: "ACT",
    title: "ACT SES — Declaration / collision overlay",
    description: "Federal vs territory declaration collision with precinct overlay.",
    fr: "FR-021",
    taskId: "T194",
  },
  {
    slug: "ntes-multilingual",
    jurisdiction: "NT",
    title: "NTES — Multilingual cultural safety",
    description: "Yolŋu Matha / Pitjantjatjara / Warlpiri elder-routing + Simplified Chinese fallback.",
    fr: "FR-022",
    taskId: "T195",
  },
  {
    slug: "sja-nt-tropical",
    jurisdiction: "NT",
    title: "St John NT — Tropical cyclone deployment",
    description: "Field-coordinator offline + risk-matrix recommendation for tropical cyclone.",
    fr: "FR-023",
    taskId: "T196",
  },
  {
    slug: "bom-broadcast-relay",
    jurisdiction: "Federal",
    title: "BoM Broadcast Relay",
    description: "BoM observation streams → multilingual broadcast script with broadcaster acknowledgement.",
    fr: "FR-024",
    taskId: "T197",
  },
  {
    slug: "nema-dacc-jatwc",
    jurisdiction: "Federal",
    title: "NEMA DACC / JATWC tsunami coordination",
    description: "Joint Australian Tsunami Warning Centre coordination with risk-matrix + AWS broadcast.",
    fr: "FR-025",
    taskId: "T198",
  },
  {
    slug: "utility-insurance-recovery",
    jurisdiction: "All",
    title: "Utility / Insurance recovery (SC-005)",
    description: "ICA claims-velocity dashboard wired to the recovery handover PDF for outcome-5 binding.",
    fr: "FR-029",
    taskId: "T199",
  },
];

export default function SectorsIndexPage() {
  return (
    <div className="mx-auto max-w-7xl">
      <header className="preparedness-header page-gutter-header">
        <p className="preparedness-kicker">Operations</p>
        <h1 className="preparedness-title">Sector workspaces</h1>
        <p className="preparedness-copy">
          Jurisdiction- and sector-specific operational workspaces composing the
          cultural-safety, infrastructure-overlay, claims-velocity, and
          offline-resilience subsystems against scenarios drawn from the
          capstone success-criteria table.
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

      <main className="p-6">
        <ul
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
          aria-label="Sector workspace index"
        >
          {SECTORS.map((s) => (
            <li
              key={s.slug}
              data-testid="sector-card"
              data-jurisdiction={s.jurisdiction}
              className="rounded-lg border border-gray-200 bg-white p-4 transition-colors hover:border-blue-300"
            >
              <p className="text-xs uppercase tracking-wide text-gray-500">
                {s.jurisdiction} · {s.taskId} · {s.fr}
              </p>
              <h2 className="mt-1 text-base font-semibold text-gray-900">
                <Link
                  className="text-blue-700 underline"
                  href={`/sectors/${s.slug}`}
                >
                  {s.title}
                </Link>
              </h2>
              <p className="mt-1 text-sm text-gray-600">{s.description}</p>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
