import Link from 'next/link'

/** 404 fallback for any unmatched route. */
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-4 text-center">
      <div className="text-4xl font-semibold text-primary mb-2">404</div>
      <div className="text-sm text-muted mb-6">This page doesn&apos;t exist.</div>
      <Link
        href="/chat"
        className="px-4 py-2 rounded-xl surface-2 border border-base text-sm text-primary surface-hover transition-all"
      >
        Back to chat
      </Link>
    </div>
  )
}