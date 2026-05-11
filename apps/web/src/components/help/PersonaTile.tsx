/** spec-038 T-AA114 — persona tile used by the help landing union. */
import Link from "next/link";

export interface PersonaTileProps {
  personaId: string;
  title: string;
  description: string;
  active?: boolean;
}

export function PersonaTile({ personaId, title, description, active }: PersonaTileProps) {
  return (
    <Link
      href={`/help/personas/${personaId}`}
      aria-current={active ? "page" : undefined}
      className={`block rounded border p-4 transition ${active ? "border-blue-600 bg-blue-50" : "border-gray-200 hover:border-blue-400"}`}
    >
      <h3 className="font-semibold text-blue-700">{title}</h3>
      <p className="mt-1 text-sm text-gray-600">{description}</p>
    </Link>
  );
}
