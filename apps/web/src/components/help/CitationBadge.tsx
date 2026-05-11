/** spec-038 T-AA109 — inline citation badge. */
export interface CitationBadgeProps {
  index: number;
  citation: { source_id: string; source_title: string; anchor: string; snippet?: string };
}

export function CitationBadge({ index, citation }: CitationBadgeProps) {
  return (
    <a
      href={`/help/articles/${citation.source_id}${citation.anchor}`}
      aria-label={`Citation ${index}: ${citation.source_title}`}
      title={citation.snippet ?? citation.source_title}
      className="ml-1 inline-flex items-center rounded bg-blue-50 px-1 text-xs text-blue-700 underline"
    >
      [{index}]
    </a>
  );
}
