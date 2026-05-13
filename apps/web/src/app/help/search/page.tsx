/** spec-038 T-AA101 — help search page. */
import { DegradedSearchBanner } from "@/components/help/DegradedSearchBanner";

export const metadata = { title: "Search · Help · AMA Hub" };

interface SearchResult {
  id: string;
  slug: string;
  title: string;
  kind: string;
  summary?: string;
}

async function fetchResults(q: string): Promise<{ items: SearchResult[] }> {
  if (!q) return { items: [] };
  try {
    const r = await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/api/help/search?q=${encodeURIComponent(q)}`, {
      cache: "no-store",
    });
    if (!r.ok) return { items: [] };
    return (await r.json()) as { items: SearchResult[] };
  } catch {
    return { items: [] };
  }
}

export default async function HelpSearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const sp = await searchParams;
  const q = sp.q ?? "";
  const { items } = await fetchResults(q);
  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-3 text-xl font-semibold">Help search</h1>
      <form className="mb-4" method="get">
        <label className="sr-only" htmlFor="q">Search</label>
        <input id="q" name="q" defaultValue={q} className="w-full rounded border px-2 py-1" />
      </form>
      {items.length === 0 ? (
        <DegradedSearchBanner />
      ) : (
        <ol>
          {items.map((r) => (
            <li key={r.id}>
              <a className="text-blue-700 underline" href={`/help/articles/${r.slug}`}>{r.title}</a>
              {r.kind === "glossary" ? <span className="ml-2 text-xs">[glossary]</span> : null}
              {r.summary ? <p className="text-sm text-gray-600">{r.summary}</p> : null}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
