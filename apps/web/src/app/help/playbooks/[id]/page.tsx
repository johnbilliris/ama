/** spec-038 T-AA105 — long-form playbook page. */
export default async function PlaybookPage({ params }: { params: Promise<{ id: string }> }) {
  const p = await params;
  return (
    <article className="mx-auto max-w-4xl p-6">
      <h1 className="text-2xl font-semibold">Playbook: {p.id}</h1>
      <p>Long-form playbook content rendered from MDX in <code>apps/web/src/content/help/articles/playbooks/{p.id}.mdx</code>.</p>
    </article>
  );
}
