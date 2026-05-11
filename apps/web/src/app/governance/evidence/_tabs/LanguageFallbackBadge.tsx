interface LanguageFallbackBadgeProps {
  fallback?: string | null;
}

export default function LanguageFallbackBadge({
  fallback,
}: LanguageFallbackBadgeProps) {
  if (!fallback) return null;

  return (
    <span
      role="status"
      aria-label={`Language fallback used: ${fallback}`}
      className="inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800"
    >
      ⚠ Fallback: {fallback}
    </span>
  );
}
