import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const getIncidentDashboard = vi.fn();
const listSignals = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ incidentId: "aidr-2214-cyclone-cyclone-herbie-western-australia" }),
  useSearchParams: () => new URLSearchParams("returnUrl=%2F"),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={String(href)} {...props}>{children}</a>
  ),
}));

vi.mock("@ama/ui/components/disaster-map/incident-type-icon", () => ({
  IncidentTypeIcon: () => <span data-testid="incident-type-icon" />,
}));

vi.mock("@/lib/api/dashboard", () => ({
  ApiHttpError: class ApiHttpError extends Error {
    constructor(public readonly status: number, message: string) {
      super(message);
    }
  },
  getIncidentDashboard: (...args: unknown[]) => getIncidentDashboard(...args),
}));

vi.mock("@/lib/api/signals", () => ({
  listSignals: (...args: unknown[]) => listSignals(...args),
}));

vi.mock("@/components/dashboard/shared-operating-picture", () => ({
  SharedOperatingPicture: () => <div>Shared operating picture</div>,
}));

vi.mock("@/components/alerts/public-alert-composer", () => ({
  PublicAlertComposer: () => <div>Public alert composer</div>,
}));

vi.mock("@/components/offline/connectivity-banner", () => ({
  ConnectivityBanner: () => null,
}));

vi.mock("@/lib/i18n/runtime", () => ({
  useI18n: () => ({
    locale: "en-AU",
    t: (key: string) => key,
    formatDateTime: (value: string) => value,
    formatNumber: (value: number) => String(value),
  }),
}));

import IncidentPage from "@/app/incidents/[incidentId]/page";

describe("IncidentPage", () => {
  beforeEach(() => {
    getIncidentDashboard.mockReset();
    listSignals.mockReset();
  });

  it("renders incident details after the loading state without changing hook order", async () => {
    getIncidentDashboard.mockResolvedValue({
      incident: {
        incidentId: "aidr-2214-cyclone-cyclone-herbie-western-australia",
        title: "Cyclone Herbie, Western Australia",
        incidentType: "cyclone",
        status: "closed",
        severity: "severe",
      },
      participatingOrganisations: [],
      activeRecommendations: [],
      activeTasks: [],
      signalSummary: {
        authoritativeCount: 0,
        communityCount: 0,
        contradictedCount: 0,
      },
    });
    listSignals.mockResolvedValue([]);

    const view = render(<IncidentPage />);

    expect(screen.getByText("incident.loading")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Cyclone Herbie, Western Australia" }))
      .toBeInTheDocument();

    view.unmount();
  });
});
