/** spec-038 T-AA116 — conflict notice when retrieved sources disagree. */
export interface ConflictNoticeProps {
  citations: { source_title: string; anchor: string }[];
  notice: string;
}

export function ConflictNotice({ citations, notice }: ConflictNoticeProps) {
  return (
    <aside role="note" aria-label="Sources disagree" className="rounded border border-amber-500 bg-amber-50 p-2 text-sm">
      <p className="font-semibold">Sources disagree</p>
      <p>{notice}</p>
      <ul className="ml-4 list-disc">
        {citations.map((c, i) => (
          <li key={i}>{c.source_title} ({c.anchor})</li>
        ))}
      </ul>
    </aside>
  );
}
