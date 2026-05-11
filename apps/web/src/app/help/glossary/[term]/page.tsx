/** spec-038 T-AA104 — glossary entry page (lang attribute aware). */
export default async function GlossaryPage({ params }: { params: Promise<{ term: string }> }) {
  const p = await params;
  return (
    <article className="mx-auto max-w-3xl p-6">
      <h1>{p.term}</h1>
      <p>Glossary entry for <code>{p.term}</code>. See related articles via the search bar.</p>
    </article>
  );
}
