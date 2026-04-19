"use client";

interface RefreshControlsProps {
  /** Current polling interval in ms */
  pollIntervalMs: number;
  /** Whether auto-refresh is active */
  autoRefresh: boolean;
  /** Toggle auto-refresh on/off */
  onToggleAutoRefresh: () => void;
  /** Trigger manual refresh (bypasses cache) */
  onManualRefresh: () => void;
  /** Whether a refresh is currently in progress */
  refreshing?: boolean;
}

/**
 * Auto/manual refresh toggle with polling interval display (FR-029).
 * Manual refresh sends Cache-Control: no-cache to bypass server cache.
 */
export function RefreshControls({
  pollIntervalMs,
  autoRefresh,
  onToggleAutoRefresh,
  onManualRefresh,
  refreshing = false,
}: RefreshControlsProps) {
  const intervalText =
    pollIntervalMs < 60000
      ? `${Math.round(pollIntervalMs / 1000)}s`
      : `${Math.round(pollIntervalMs / 60000)}min`;

  return (
    <div className="flex items-center gap-3 text-sm">
      {/* Auto-refresh toggle */}
      <label className="flex cursor-pointer items-center gap-2">
        <input
          type="checkbox"
          checked={autoRefresh}
          onChange={onToggleAutoRefresh}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          aria-label="Toggle auto-refresh"
        />
        <span className="text-gray-600">
          Auto-refresh ({intervalText})
        </span>
      </label>

      {/* Manual refresh button */}
      <button
        onClick={onManualRefresh}
        disabled={refreshing}
        className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50"
        aria-label="Refresh dashboard data now"
      >
        {refreshing ? (
          <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        ) : (
          <span aria-hidden="true">↻</span>
        )}
        Refresh
      </button>
    </div>
  );
}
