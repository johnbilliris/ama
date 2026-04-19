"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  widgetName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  lastKnownTimestamp: string | null;
}

/**
 * Per-widget error boundary with "data unavailable" message,
 * last-known timestamp, and retry button (FR-031).
 */
export class WidgetErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, lastKnownTimestamp: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      lastKnownTimestamp: new Date().toLocaleTimeString(),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error(
      `[WidgetErrorBoundary] ${this.props.widgetName ?? "Unknown"}: ${error.message}`,
      errorInfo,
    );
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-red-800">
                {this.props.widgetName ?? "Widget"} — Data Unavailable
              </h3>
              <p className="mt-1 text-xs text-red-600">
                {this.state.error?.message ?? "An unexpected error occurred."}
              </p>
              {this.state.lastKnownTimestamp && (
                <p className="mt-1 text-xs text-gray-500">
                  Last known data: {this.state.lastKnownTimestamp}
                </p>
              )}
            </div>
            <button
              onClick={this.handleRetry}
              className="rounded bg-red-100 px-3 py-1 text-xs font-medium text-red-800 hover:bg-red-200"
              aria-label={`Retry loading ${this.props.widgetName ?? "widget"}`}
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
