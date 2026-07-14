/** Route-segment loading fallback (Suspense). Data-level loading is handled by
 * each page's React Query `isLoading` state; this covers the brief chunk/segment
 * transition so the shell never flashes empty. */
export default function Loading() {
  return (
    <div className="flex items-center justify-center py-24" role="status" aria-label="Loading">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-[var(--border)] border-t-[var(--accent)]" />
    </div>
  )
}