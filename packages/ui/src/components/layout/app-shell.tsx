"use client";

import type { PropsWithChildren } from "react";
import { useState } from "react";

const NAV_LINKS = [
  { href: "/", label: "Disaster Map", icon: "🗺️" },
  { href: "/workspaces", label: "Workspaces", icon: "👥" },
  { href: "/sectors", label: "Sectors", icon: "🏛️" },
  { href: "/governance", label: "Governance", icon: "🛡️" },
  { href: "/simulations", label: "Simulations", icon: "🔬" },
  { href: "/preparedness", label: "Preparedness", icon: "📋" },
  { href: "/help", label: "Help", icon: "❓" },
];

export function AppShell({ children }: PropsWithChildren) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="ama-app-shell">
      <header className="ama-nav" role="banner">
        <div className="ama-nav-inner">
          <a href="/" className="ama-nav-brand" aria-label="Autonomous Disaster Response Coordination Hub home">
            <span className="ama-nav-logo" aria-hidden="true">⚡</span>
            <span className="ama-nav-wordmark">
              <span className="ama-nav-wordmark-primary">Autonomous Disaster Response Coordination Hub</span>
            </span>
          </a>

          <nav className={`ama-nav-links ${mobileMenuOpen ? "ama-nav-links--open" : ""}`} aria-label="Main navigation">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="ama-nav-link">
                <span className="ama-nav-link-icon" aria-hidden="true">{link.icon}</span>
                {link.label}
              </a>
            ))}
          </nav>

          <button
            className="ama-nav-hamburger"
            onClick={() => setMobileMenuOpen((v) => !v)}
            aria-expanded={mobileMenuOpen ? "true" : "false"}
            aria-label="Toggle navigation"
          >
            <span className={`ama-hamburger-bar ${mobileMenuOpen ? "ama-hamburger-bar--open" : ""}`} />
          </button>
        </div>
      </header>

      <main className="ama-main">{children}</main>

      <footer className="ama-footer" role="contentinfo">
        <div className="ama-footer-inner">
          <div className="ama-footer-brand">
            <span className="ama-footer-logo" aria-hidden="true">⚡</span>
            <span>Autonomous Disaster Response Coordination Hub</span>
          </div>
          <p className="ama-footer-acknowledgement">
            We acknowledge the Traditional Owners of Country throughout Australia and recognise their continuing connection to land, waters, and culture.
          </p>
          <div className="ama-footer-links">
            <a href="/governance">Governance</a>
            <span className="ama-footer-dot" aria-hidden="true">·</span>
            <a href="/preparedness">Preparedness</a>
            <span className="ama-footer-dot" aria-hidden="true">·</span>
            <a href="/simulations">Simulations</a>
          </div>
          <p className="ama-footer-copy">Built for the Azure Master Architect Program</p>
        </div>
      </footer>
    </div>
  );
}
