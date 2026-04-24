"use client";

const PLAYBACK_SPEEDS = [1, 2, 5, 10] as const;

function fmt(total: number) {
  const t = Math.max(0, Math.floor(total));
  const h = String(Math.floor(t / 3600)).padStart(2, "0");
  const m = String(Math.floor((t % 3600) / 60)).padStart(2, "0");
  const s = String(t % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

export function PlaybackControls({
  isPlaying,
  playbackSpeed,
  currentSimTime,
  totalDuration,
  onPlay,
  onPause,
  onSpeedChange,
}: {
  isPlaying: boolean;
  playbackSpeed: number;
  currentSimTime: number;
  totalDuration: number;
  onPlay: () => void;
  onPause: () => void;
  onSpeedChange: (speed: number) => void;
}) {
  const pct = totalDuration > 0
    ? Math.min(100, (currentSimTime / totalDuration) * 100)
    : 0;

  return (
    <div className="playback-controls">
      <button
        type="button"
        className="playback-controls-button"
        onClick={isPlaying ? onPause : onPlay}
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? "⏸ Pause" : "▶ Play"}
      </button>
      <div
        className="playback-controls-speed"
        role="radiogroup"
        aria-label="Playback speed"
      >
        {PLAYBACK_SPEEDS.map((s) => {
          const active = s === playbackSpeed;
          return (
            <button
              key={s}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => onSpeedChange(s)}
              className={"playback-controls-speed-btn " + (active ? "is-active" : "")}
            >
              {s}×
            </button>
          );
        })}
      </div>
      <span className="playback-controls-clock">
        {fmt(currentSimTime)} / {fmt(totalDuration)}{" "}
        <span className="playback-controls-pct">({pct.toFixed(1)}%)</span>
      </span>
    </div>
  );
}
