/**
 * Spec-036 T-I02 — delivery-receipt badge for simulation messages.
 *
 * Renders the FR-007 (chat receipt) status produced by the simulation
 * comms pipeline: `queued` → `sent` → `delivered` → `read` (or `failed`).
 * Each state has a dedicated `aria-label` so screen-readers announce the
 * delivery state without relying on iconography.
 */
import type { CSSProperties } from "react";

export type SimulationReceiptStatus =
  | "queued"
  | "sent"
  | "delivered"
  | "read"
  | "failed";

interface SimulationReceiptBadgeProps {
  status: SimulationReceiptStatus;
  /** Optional channel label (e.g. "SMS", "EAS"). Surfaces in the title. */
  channel?: string;
  className?: string;
  style?: CSSProperties;
}

const STATUS_META: Record<
  SimulationReceiptStatus,
  { label: string; icon: string; classes: string; aria: string }
> = {
  queued: {
    label: "Queued",
    icon: "•",
    classes: "bg-gray-100 text-gray-700 ring-gray-300",
    aria: "Message queued for delivery",
  },
  sent: {
    label: "Sent",
    icon: "✓",
    classes: "bg-blue-50 text-blue-700 ring-blue-200",
    aria: "Message sent to delivery channel",
  },
  delivered: {
    label: "Delivered",
    icon: "✓✓",
    classes: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    aria: "Message delivered to recipient",
  },
  read: {
    label: "Read",
    icon: "✓✓",
    classes: "bg-emerald-100 text-emerald-900 ring-emerald-300",
    aria: "Message read by recipient",
  },
  failed: {
    label: "Failed",
    icon: "✕",
    classes: "bg-red-100 text-red-700 ring-red-300",
    aria: "Message delivery failed",
  },
};

export function SimulationReceiptBadge({
  status,
  channel,
  className,
  style,
}: SimulationReceiptBadgeProps) {
  const meta = STATUS_META[status];
  const ariaLabel = channel
    ? `${meta.aria} via ${channel} (simulation)`
    : `${meta.aria} (simulation)`;
  return (
    <span
      role="status"
      aria-label={ariaLabel}
      className={`inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-[10px] font-medium ring-1 ${meta.classes} ${className ?? ""}`}
      style={style}
      data-testid="simulation-receipt-badge"
      data-status={status}
      title={ariaLabel}
    >
      <span aria-hidden="true">{meta.icon}</span>
      <span>{meta.label}</span>
    </span>
  );
}

export default SimulationReceiptBadge;
