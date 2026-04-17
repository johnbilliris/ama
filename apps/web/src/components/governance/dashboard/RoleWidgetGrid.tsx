"use client";

import type { WidgetDefinition } from "@/lib/api/governance";

interface RoleWidgetGridProps {
  widgets: WidgetDefinition[];
  /** Map widget_id → React component */
  widgetComponents: Record<string, React.ReactNode>;
}

/**
 * Dynamic role-aware widget layout that renders widgets in priority order (US7).
 * Uses CSS grid with responsive column adjustment.
 */
export function RoleWidgetGrid({
  widgets,
  widgetComponents,
}: RoleWidgetGridProps) {
  const sorted = [...widgets].sort((a, b) => a.priority - b.priority);

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {sorted.map((widget) => {
        const component = widgetComponents[widget.widget_id];
        if (!component) return null;

        return (
          <div
            key={widget.widget_id}
            className="min-h-[200px]"
            data-widget-id={widget.widget_id}
            data-widget-type={widget.widget_type}
            data-refresh-group={widget.refresh_group}
          >
            {component}
          </div>
        );
      })}
    </div>
  );
}
