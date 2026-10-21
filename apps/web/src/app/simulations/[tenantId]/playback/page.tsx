"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getSimulation, type SimulationDetail } from "@/lib/api/simulations";
import {
  getAllPlaybackEvents,
  type PlaybackEvent,
} from "@/lib/api/simulation-playback";
import { PlaybackTimeline } from "@/components/playback-timeline";
import { PlaybackControls } from "@/components/playback-controls";
import { PlaybackAnnotationPanel } from "@/components/playback-annotation-panel";
import { useReportSimulationLifecycle } from "@/components/simulation-lifecycle";

export default function PlaybackPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const [tenant, setTenant] = useState<SimulationDetail | null>(null);
  const [events, setEvents] = useState<PlaybackEvent[]>([]);
  const [playbackStatus, setPlaybackStatus] = useState<"full" | "partial" | "none">("full");
  const [currentSimTime, setCurrentSimTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentUserOid, setCurrentUserOid] = useState<string>("");

  const rafRef = useRef<number | null>(null);
  const lastWallRef = useRef<number>(0);

  useEffect(() => {
    if (!tenantId) return;
    (async () => {
      try {
        const [sim, batch] = await Promise.all([
          getSimulation(tenantId),
          getAllPlaybackEvents(tenantId, true),
        ]);
        setTenant(sim);
        setEvents(batch.events);
        setPlaybackStatus(batch.playback_status);
        setCurrentUserOid(sim.created_by);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, [tenantId]);

  const totalDuration = useMemo(() => {
    if (events.length === 0) return 0;
    return Math.max(...events.map((e) => e.sim_time_offset));
  }, [events]);

  const annotations = useMemo(
    () => events.filter((e) => e.event_type === "annotation"),
    [events],
  );

  useEffect(() => {
    if (!isPlaying) return;
    lastWallRef.current = performance.now();
    const step = (now: number) => {
      const dt = (now - lastWallRef.current) / 1000;
      lastWallRef.current = now;
      setCurrentSimTime((prev) => {
        const next = prev + dt * playbackSpeed;
        if (next >= totalDuration) {
          setIsPlaying(false);
          return totalDuration;
        }
        return next;
      });
      rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [isPlaying, playbackSpeed, totalDuration]);

  const visibleEvents = useMemo(
    () =>
      events
        .filter((e) => e.sim_time_offset <= currentSimTime)
        .sort((a, b) => a.event_seq - b.event_seq),
    [events, currentSimTime],
  );

  const onScrub = useCallback(
    (t: number) => {
      setCurrentSimTime(Math.max(0, Math.min(t, totalDuration)));
    },
    [totalDuration],
  );

  // AUD-018 — keep the layout-owned marker truthful on the playback route,
  // including while the tenant fetch is still in flight or has failed.
  useReportSimulationLifecycle(tenant?.status ?? null);

  if (loading) return <div className="p-6">Loading playback…</div>;
  if (error) {
    const restricted = /403/.test(error);
    return (
      <div className="mx-auto max-w-2xl p-6">
        <h1 className="mb-2 text-2xl font-bold">
          {restricted ? "Playback access restricted" : "Playback error"}
        </h1>
        <p className="mb-4 text-sm text-gray-600">{error}</p>
        <Link
          href={`/simulations/${tenantId}`}
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to simulation
        </Link>
      </div>
    );
  }
  if (!tenant) return null;

  if (events.length === 0) {
    return (
      <div className="mx-auto max-w-2xl p-6">
        <h1 className="mb-2 text-2xl font-bold">No events recorded</h1>
        <p className="mb-4 text-sm text-gray-600">
          No events were recorded for this simulation. Playback is not available.
        </p>
        <Link
          href={`/simulations/${tenantId}`}
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to simulation
        </Link>
      </div>
    );
  }

  return (
    <div className="playback-page">
      <header className="playback-page-header">
        <div>
          <h1 className="text-xl font-bold">Playback — {tenant.scenario_type}</h1>
          <p className="text-sm text-gray-600">
            {tenant.tenant_id} · {events.length} events · status {playbackStatus}
          </p>
        </div>
        <Link
          href={`/simulations/${tenant.tenant_id}`}
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to simulation
        </Link>
      </header>

      {playbackStatus === "partial" && (
        <p role="alert" className="playback-partial-warning">
          Some events may be missing — this simulation experienced recording issues.
        </p>
      )}

      <PlaybackTimeline
        events={events}
        currentPosition={currentSimTime}
        totalDuration={totalDuration}
        onScrub={onScrub}
      />

      <PlaybackControls
        isPlaying={isPlaying}
        playbackSpeed={playbackSpeed}
        currentSimTime={currentSimTime}
        totalDuration={totalDuration}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onSpeedChange={setPlaybackSpeed}
      />

      <div className="playback-main">
        <section className="playback-event-list">
          <h3>Events ({visibleEvents.length})</h3>
          <ul>
            {visibleEvents
              .slice(-100)
              .reverse()
              .map((e) => (
                <li key={e.id}>
                  <span className="playback-event-seq">#{e.event_seq}</span>
                  <span className="playback-event-type">{e.event_type}</span>
                  <span className="playback-event-offset">
                    {e.sim_time_offset.toFixed(1)}s
                  </span>
                </li>
              ))}
          </ul>
        </section>

        <PlaybackAnnotationPanel
          tenantId={tenant.tenant_id}
          currentSimTime={currentSimTime}
          annotations={annotations}
          currentUserOid={currentUserOid}
          onCreated={(ann) => setEvents((prev) => [...prev, ann])}
          onUpdated={(upd) =>
            setEvents((prev) => prev.map((e) => (e.id === upd.id ? upd : e)))
          }
          onDeleted={(id) => setEvents((prev) => prev.filter((e) => e.id !== id))}
          onSeek={onScrub}
        />
      </div>
    </div>
  );
}
