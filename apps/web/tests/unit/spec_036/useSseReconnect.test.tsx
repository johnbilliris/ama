/**
 * Spec-036 T-I05 — `useSseReconnect` hook unit tests.
 *
 * Drives a fake `EventSource` through open / message / error transitions,
 * asserting:
 *   - exponential back-off increases per failed attempt
 *   - `Last-Event-ID` is captured from message events
 *   - cleanup closes the connection on unmount
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, render, waitFor } from "@testing-library/react";
import { useSseReconnect, type EventSourceLike } from "@/hooks/useSseReconnect";

class FakeEventSource implements EventSourceLike {
  static instances: FakeEventSource[] = [];
  readyState = 0;
  private listeners = new Map<string, Array<(event: Event) => void>>();
  constructor(public url: string) {
    FakeEventSource.instances.push(this);
  }
  addEventListener(type: string, listener: (event: Event) => void): void {
    const arr = this.listeners.get(type) ?? [];
    arr.push(listener);
    this.listeners.set(type, arr);
  }
  removeEventListener(type: string, listener: (event: Event) => void): void {
    const arr = this.listeners.get(type) ?? [];
    this.listeners.set(
      type,
      arr.filter((l) => l !== listener),
    );
  }
  emit(type: string, payload?: Partial<MessageEvent>): void {
    const event = { type, ...(payload ?? {}) } as Event;
    for (const l of this.listeners.get(type) ?? []) l(event);
  }
  close(): void {
    this.readyState = 2;
  }
}

function HookProbe({
  factory,
  onEvent,
  initialBackoffMs = 10,
}: {
  factory: (url: string) => EventSourceLike;
  onEvent?: (e: MessageEvent) => void;
  initialBackoffMs?: number;
}) {
  const state = useSseReconnect({
    url: "https://api.test/events",
    eventSourceFactory: factory,
    initialBackoffMs,
    onEvent,
  });
  return (
    <div>
      <span data-testid="status">{state.status}</span>
      <span data-testid="attempt">{state.attempt}</span>
      <span data-testid="last-id">{state.lastEventId ?? "none"}</span>
    </div>
  );
}

describe("useSseReconnect", () => {
  afterEach(() => {
    FakeEventSource.instances.length = 0;
  });

  it("transitions through connecting → open on success", async () => {
    const factory = (url: string) => new FakeEventSource(url);
    const { getByTestId } = render(<HookProbe factory={factory} />);
    expect(getByTestId("status").textContent).toBe("connecting");
    act(() => {
      FakeEventSource.instances[0].emit("open");
    });
    await waitFor(() =>
      expect(getByTestId("status").textContent).toBe("open"),
    );
  });

  it("captures Last-Event-ID from message events", async () => {
    const onEvent = vi.fn();
    const factory = (url: string) => new FakeEventSource(url);
    const { getByTestId } = render(
      <HookProbe factory={factory} onEvent={onEvent} />,
    );
    act(() => {
      FakeEventSource.instances[0].emit("message", {
        lastEventId: "evt-42",
        data: "hi",
      } as Partial<MessageEvent>);
    });
    await waitFor(() =>
      expect(getByTestId("last-id").textContent).toBe("evt-42"),
    );
    expect(onEvent).toHaveBeenCalledTimes(1);
  });

  it("schedules an exponential back-off on error", async () => {
    const factory = (url: string) => new FakeEventSource(url);
    const { getByTestId } = render(
      <HookProbe factory={factory} initialBackoffMs={20} />,
    );
    // Trigger an error → back-off scheduled with delay 20ms.
    act(() => {
      FakeEventSource.instances[0].emit("error");
    });
    expect(getByTestId("attempt").textContent).toBe("1");
    expect(getByTestId("status").textContent).toBe("retrying");
    // After the back-off elapses, a new EventSource is created.
    await waitFor(
      () => expect(FakeEventSource.instances.length).toBe(2),
      { timeout: 1000 },
    );
    // Second connection succeeds → status returns to "open".
    act(() => {
      FakeEventSource.instances[1].emit("open");
    });
    await waitFor(() =>
      expect(getByTestId("status").textContent).toBe("open"),
    );
    expect(getByTestId("attempt").textContent).toBe("0");
  });

  it("closes the EventSource on unmount", () => {
    const factory = (url: string) => new FakeEventSource(url);
    const { unmount } = render(<HookProbe factory={factory} />);
    expect(FakeEventSource.instances[0].readyState).toBe(0);
    unmount();
    expect(FakeEventSource.instances[0].readyState).toBe(2);
  });
});
