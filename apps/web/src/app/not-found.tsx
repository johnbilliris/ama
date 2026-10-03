import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-4xl p-6 text-center" style={{ marginTop: "4rem" }}>
      <h1 className="mb-4 text-4xl font-bold">404 — Page Not Found</h1>
      <p className="mb-6 text-gray-500">The page you&apos;re looking for doesn&apos;t exist or has been moved.</p>
      <Link href="/" className="rounded bg-[var(--ama-color-ocean)] px-4 py-2 text-white hover:opacity-90">
        Back to Disaster Mapper
      </Link>
    </div>
  );
}
