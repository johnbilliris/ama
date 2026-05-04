"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode } from "react";

const NAV_ITEMS = [
  { href: "/governance/dashboard", label: "Executive Summary" },
  { href: "/governance/dashboard/compliance", label: "Compliance" },
  { href: "/governance/dashboard/audit", label: "Audit Trail" },
  { href: "/governance/dashboard/readiness", label: "Readiness" },
  { href: "/governance/dashboard/recovery", label: "Recovery" },
  { href: "/governance/dashboard/risk", label: "Risk & Warning" },
];

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();

  return (
    <div className="mx-auto max-w-7xl">
      {/* Page header — matches preparedness style */}
      <header className="preparedness-header" style={{ margin: "1.25rem 1.5rem 0" }}>
        <p className="preparedness-kicker">Governance</p>
        <h1 className="preparedness-title">Governance Dashboard</h1>
        <p className="preparedness-copy">
          Monitor constitutional compliance, operational readiness, recovery
          progress, and risk posture across all jurisdictions.
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

      {/* Tab navigation */}
      <nav
        aria-label="Dashboard views"
        className="border-b border-gray-200"
        style={{ margin: "0 1.5rem" }}
      >
        <ul className="flex space-x-1 overflow-x-auto" role="tablist">
          {NAV_ITEMS.map(({ href, label }) => {
            const isActive =
              pathname === href ||
              (href !== "/governance/dashboard" &&
                pathname?.startsWith(href));
            return (
              <li key={href} role="presentation">
                <Link
                  href={href}
                  role="tab"
                  aria-selected={isActive}
                  className={`inline-block whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                    isActive
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  }`}
                >
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Dashboard content */}
      <main className="p-6">{children}</main>
    </div>
  );
}
