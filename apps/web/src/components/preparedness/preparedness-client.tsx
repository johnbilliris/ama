"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { listJurisdictions, type JurisdictionSummary } from "../../lib/api/jurisdictions";
import type { PreparednessFramework } from "../../lib/api/frameworks";
import type { PreparednessOrganisation } from "../../lib/api/organisations";
import { listPreparednessOrganisations } from "../../lib/api/organisations";
import { listPreparednessFrameworks } from "../../lib/api/frameworks";
import { JurisdictionSelector } from "./jurisdiction-selector";
import { OperatingModelAnalyzer } from "./operating-model-analyzer";

interface PreparednessClientProps {
  initialJurisdictionParam: string;
}

export function PreparednessClient({ initialJurisdictionParam }: PreparednessClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [jurisdictions, setJurisdictions] = useState<JurisdictionSummary[]>([]);
  const [jurisdictionsLoading, setJurisdictionsLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [organisations, setOrganisations] = useState<PreparednessOrganisation[]>([]);
  const [frameworks, setFrameworks] = useState<PreparednessFramework[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [replayJurisdictions, setReplayJurisdictions] = useState<string[] | null>(null);
  const [replayStale, setReplayStale] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestIdRef = useRef(0);
  const initializedRef = useRef(false);

  // Fetch jurisdictions on mount and resolve initial selection from URL param
  useEffect(() => {
    listJurisdictions()
      .then((data) => {
        setJurisdictions(data);
        if (!initializedRef.current) {
          initializedRef.current = true;
          const validIds = new Set(data.map((j) => j.jurisdiction_id));
          const initial = initialJurisdictionParam
            ? initialJurisdictionParam.split(",").filter((id) => validIds.has(id))
            : [];
          setSelectedIds(initial);
        }
      })
      .catch(() => setError("Failed to load jurisdictions. Please refresh the page."))
      .finally(() => setJurisdictionsLoading(false));
  }, [initialJurisdictionParam]);

  const validIds = jurisdictions.map((j) => j.jurisdiction_id);

  const fetchData = useCallback(
    async (ids: string[]) => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
      const controller = new AbortController();
      abortRef.current = controller;
      const requestId = ++requestIdRef.current;

      if (ids.length === 0) {
        setOrganisations([]);
        setFrameworks([]);
        setIsLoading(false);
        setError(null);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const [orgs, fws] = await Promise.all([
          listPreparednessOrganisations(ids, controller.signal),
          listPreparednessFrameworks(ids, controller.signal),
        ]);
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setOrganisations(orgs);
          setFrameworks(fws);
          setIsLoading(false);
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        if (requestId === requestIdRef.current && !controller.signal.aborted) {
          setError("Failed to load catalogue data. Please try again.");
          setIsLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    if (jurisdictionsLoading) return;
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      fetchData(selectedIds);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
  }, [selectedIds, fetchData, jurisdictionsLoading]);

  useEffect(() => {
    if (replayJurisdictions !== null) {
      const sortedCurrent = [...selectedIds].sort().join(",");
      const sortedReplay = [...replayJurisdictions].sort().join(",");
      setReplayStale(sortedCurrent !== sortedReplay);
    }
  }, [selectedIds, replayJurisdictions]);

  function handleSelectionChange(ids: string[]) {
    const filtered = ids.filter((id) => validIds.includes(id));
    setSelectedIds(filtered);

    const params = new URLSearchParams(searchParams.toString());
    if (filtered.length > 0) {
      params.set("jurisdictions", filtered.join(","));
    } else {
      params.delete("jurisdictions");
    }
    router.replace(`?${params.toString()}`, { scroll: false });
  }

  function handleReplayComplete() {
    setReplayJurisdictions([...selectedIds]);
    setReplayStale(false);
  }

  function handleRetry() {
    fetchData(selectedIds);
  }

  if (jurisdictionsLoading) {
    return <div className="preparedness-loading">Loading jurisdictions…</div>;
  }

  return (
    <div className="preparedness-layout">
      {/* Left: filter panel matching disaster map pattern */}
      <JurisdictionSelector
        jurisdictions={jurisdictions}
        selectedIds={selectedIds}
        onChange={handleSelectionChange}
      />

      {/* Right: main content */}
      <div className="preparedness-main">
        {error && (
          <div className="preparedness-error" role="alert">
            <p>{error}</p>
            <button type="button" className="preparedness-button" onClick={handleRetry}>
              Retry
            </button>
          </div>
        )}

        <OperatingModelAnalyzer
          jurisdictions={jurisdictions}
          organisations={organisations}
          frameworks={frameworks}
          selectedJurisdictionIds={selectedIds}
          isLoading={isLoading}
          replayStale={replayStale}
          onReplayComplete={handleReplayComplete}
        />
      </div>
    </div>
  );
}
