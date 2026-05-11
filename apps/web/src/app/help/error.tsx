"use client";
/** spec-038 T-AA122 — help error boundary. */
export default function HelpError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div role="alert" className="p-6">
      <h2 className="text-lg font-semibold">Something went wrong loading Help</h2>
      <p className="text-sm text-gray-600">{error.message}</p>
      <button type="button" onClick={reset} className="mt-3 rounded border px-3 py-1 text-sm">Try again</button>
    </div>
  );
}
