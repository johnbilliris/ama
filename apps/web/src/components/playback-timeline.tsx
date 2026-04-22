"use client";

import { useMemo } from "react";
import type { PlaybackEvent } from "@/lib/api/simulation-playback";

const EVENT_COLOURS: Record<string, string> = {
  signal_delivered: "#3b82f6",
  chat_turn_user: "#22c55e",
  chat_turn_assistant: "#16a34a",
  tool_invocation: "#a855f7",
  state_change: "#f97316",
  warp_speed_change: "#eab308",
  annotation: "#facc15",
};

/**
 * Horizontal timeline scrubber showing simulated-time positions of
 * events and annotations. Click / drag to scrub.
 */
export function PlaybackTimeline({
  events,
  currentPosition,
  totalDuration,
  onScrub,
}: {
  events: PlaybackEvent[];
  currentPosition: number;
  totalDuration: number;
  onScrub: (simTime: number) => void;
}) {
  const safeDuration = Math.max(totalDuration, 1);

  const markers = useMemo(
    () =>
      events.map((e) => ({
        id: e.id,
        pct: (e.sim_time_offset / safeDuration) * 100,
        colour: EVENT_COLOURS[e.event_type] ?? "#6b7280",
        label: e.event_type,
        offset: e.sim_time_offset,
      })),
    [events, safeDuration],
  );

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    onScrub(pct * safeDuration);
  };

  const playheadPct = Math.max(
    0,
    Math.min(100, (currentPosition / safeDuration) * 100),
  );

  return (
    <div className="playback-timeline">
      <div
        className="playback-timeline-track"
        onClick={handleClick}
        role="slider"
        aria-valuemin={0}
        aria-valuemax={safeDuration}
        aria-valuenow={currentPosition}
        aria-label="Playback position"
        tabIndex={0}
        onKeyDown={(e) => {
          const step = safeDuration / 100;
          if (e.key === "ArrowRight")
            onScrub(Math.min(safeDuration, currentPosition + step));
          else if (e.key === "ArrowLeft")
            onScrub(Math.max(0, currentPosition - step));
        }}
      >
        {markers.map((m) => (
          <span
            key={m.id}
            className="playback-timeline-marker"
            style={{ left: `${m.pct}%`, background: m.colour }}
            title={`${m.label} @ ${m.offset.toFixed(0)}s`}
          />
        ))}
        <span
          className="playback-timeline-playhead"
          style={{ left: `${playheadPct}%` }}
          aria-hidden="true"
        />
      </div>
      <div className="playback-timeline-labels">
        <span>00:00</span>
        <span>{fmt(safeDuration)}</span>
      </div>
    </div>
  );
}

function fmt(total: number) {
  const t = Math.max(0, Math.floor(total));
  const h = String(Math.floor(t / 3600)).padStart(2, "0");
  const m = String(Math.floor((t % 3600) / 60)).padStart(2, "0");
  const s = String(t % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}
