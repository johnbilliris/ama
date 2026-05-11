/**
 * Infrastructure overlay layers (T051, FR-029 / data-model § 11).
 *
 * Renders four toggleable layer types:
 *   1. iron_ore_haul_road
 *   2. port_critical
 *   3. island_logistics
 *   4. federal_precinct
 *
 * Each layer has a distinct, contrast-checked colour and priority class.
 */

"use client";

import * as React from "react";

export type LayerKind =
  | "iron_ore_haul_road"
  | "port_critical"
  | "island_logistics"
  | "federal_precinct";

interface OverlayLayer {
  kind: LayerKind;
  label: string;
  priority_class: "P1" | "P2" | "P3";
  /** Background CSS colour token (WCAG AA on white). */
  colour: string;
  description: string;
}

export const LAYERS: ReadonlyArray<OverlayLayer> = Object.freeze([
  {
    kind: "iron_ore_haul_road",
    label: "Iron-ore haul road",
    priority_class: "P1",
    colour: "#7c2d12",
    description: "WA Pilbara haul corridors — daily $-throughput sensitivity.",
  },
  {
    kind: "port_critical",
    label: "Port-critical",
    priority_class: "P1",
    colour: "#1e3a8a",
    description: "Bulk-export port footprints with vessel berthing windows.",
  },
  {
    kind: "island_logistics",
    label: "Island logistics",
    priority_class: "P2",
    colour: "#065f46",
    description: "Strait/island ferry & barge resupply links.",
  },
  {
    kind: "federal_precinct",
    label: "Federal precinct",
    priority_class: "P2",
    colour: "#854d0e",
    description: "Commonwealth tenancy / parliamentary triangle overlays.",
  },
]);

export interface InfrastructureOverlayProps {
  initialEnabled?: LayerKind[];
  onChange?: (enabled: LayerKind[]) => void;
}

export function InfrastructureOverlay(
  props: InfrastructureOverlayProps,
): React.ReactElement {
  const { initialEnabled = [], onChange } = props;
  const [enabled, setEnabled] = React.useState<Set<LayerKind>>(
    () => new Set(initialEnabled),
  );

  const toggle = (kind: LayerKind) => {
    setEnabled((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      onChange?.(Array.from(next));
      return next;
    });
  };

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="infrastructure-overlay"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Infrastructure overlays</h2>
        <span className="text-xs text-slate-500">FR-029</span>
      </header>
      <ul className="space-y-2 text-sm">
        {LAYERS.map((layer) => {
          const isOn = enabled.has(layer.kind);
          return (
            <li key={layer.kind} className="flex items-center gap-3">
              <button
                type="button"
                aria-pressed={isOn}
                data-testid={`overlay-toggle-${layer.kind}`}
                onClick={() => toggle(layer.kind)}
                className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                style={
                  isOn
                    ? { background: layer.colour, color: "#ffffff" }
                    : undefined
                }
              >
                {isOn ? "On" : "Off"}
              </button>
              <span
                aria-hidden="true"
                className="inline-block h-3 w-3 rounded-full"
                style={{ background: layer.colour }}
              />
              <span className="font-medium">{layer.label}</span>
              <span className="text-xs text-slate-500">
                {layer.priority_class}
              </span>
              <span className="text-xs text-slate-600">{layer.description}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default InfrastructureOverlay;
