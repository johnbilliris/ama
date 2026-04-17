"use client";

import { useEffect, useState } from "react";
import { AuditTrailSearch } from "@/components/governance/dashboard/AuditTrailSearch";
import { AuditDecisionChain } from "@/components/governance/dashboard/AuditDecisionChain";
import { AuditExportDialog } from "@/components/governance/dashboard/AuditExportDialog";
import { WidgetErrorBoundary } from "@/components/governance/dashboard/WidgetErrorBoundary";
import {
  getAuditTrail,
  getDecisionChain,
  createAuditExport,
  getExportStatus,
  type AuditTrailResponse,
  type AuditDecisionChainResponse,
} from "@/lib/api/governance";

/**
 * Audit trail view page with search, decision chains, and export (US3).
 */
export default function AuditPage() {
  const [data, setData] = useState<AuditTrailResponse | null>(null);
  const [chain, setChain] = useState<AuditDecisionChainResponse | null>(null);
  const [showExport, setShowExport] = useState(false);
  const [exportStatus, setExportStatus] = useState<"idle" | "exporting" | "complete" | "failed">("idle");
  const [exportUrl, setExportUrl] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async (filters?: Record<string, string>) => {
    try {
      setLoading(true);
      const result = await getAuditTrail(filters);
      setData(result);
    } catch {
      // handled by boundary
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleEventClick = async (eventId: string) => {
    try {
      const c = await getDecisionChain(eventId);
      setChain(c);
    } catch {
      // silently fail
    }
  };

  const handleExport = async (format: "pdf" | "csv" | "json") => {
    try {
      setExportStatus("exporting");
      const job = await createAuditExport({
        format,
        record_ids: selectedIds,
      });

      // Poll for completion
      let attempts = 0;
      while (attempts < 30) {
        const status = await getExportStatus(job.id);
        if (status.status === "complete") {
          setExportUrl(status.download_url);
          setExportStatus("complete");
          return;
        }
        if (status.status === "failed") {
          setExportError(status.error_message);
          setExportStatus("failed");
          return;
        }
        await new Promise((r) => setTimeout(r, 1000));
        attempts++;
      }
      setExportError("Export timed out");
      setExportStatus("failed");
    } catch (e) {
      setExportError(e instanceof Error ? e.message : "Export failed");
      setExportStatus("failed");
    }
  };

  if (loading && !data) {
    return <div className="h-64 animate-pulse rounded-lg bg-gray-200" />;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Audit Trail</h2>

      <WidgetErrorBoundary widgetName="Audit Trail">
        {data && (
          <AuditTrailSearch
            events={data.events}
            totalCount={data.total_count}
            continuationToken={data.continuation_token}
            onSearch={fetchData}
            onPageNext={(token) => fetchData({ continuation_token: token })}
            onEventClick={handleEventClick}
            onExport={(ids) => {
              setSelectedIds(ids);
              setShowExport(true);
              setExportStatus("idle");
            }}
          />
        )}
      </WidgetErrorBoundary>

      {/* Decision chain slide-out */}
      {chain && (
        <AuditDecisionChain
          eventId={chain.event_id}
          chain={chain.chain}
          chainComplete={chain.chain_complete}
          onClose={() => setChain(null)}
        />
      )}

      {/* Export dialog */}
      {showExport && (
        <AuditExportDialog
          recordCount={selectedIds.length}
          filterSummary={Object.entries(data?.filters_applied ?? {}).map(([k, v]) => `${k}=${v}`).join(", ")}
          onExport={handleExport}
          onClose={() => {
            setShowExport(false);
            setExportStatus("idle");
          }}
          status={exportStatus}
          downloadUrl={exportUrl}
          errorMessage={exportError}
          progress={exportStatus === "exporting" ? 50 : exportStatus === "complete" ? 100 : 0}
        />
      )}
    </div>
  );
}
