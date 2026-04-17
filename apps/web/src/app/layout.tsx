import type { PropsWithChildren } from "react";
import { AppShell } from "@ama/ui/components/layout/app-shell";

import "./globals.css";

export const metadata = {
  title: "Autonomous Disaster Response Coordination Hub",
  description: "Autonomous Disaster Response Coordination Hub — Situational awareness for Australian emergency management",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en-AU" data-scroll-behavior="smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
