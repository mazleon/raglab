"use client"

/** Route-segment error boundary. Catches a render error anywhere below and
 * offers a reset (re-render) instead of a blank screen. */
import { useEffect } from 'react'

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    // Surface unexpected render errors in the console during dev.
    console.error(error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center py-24 px-4 text-center">
      <div className="text-red-500 mb-2">Something went wrong</div>
      <div className="text-sm text-muted mb-6 max-w-md">{error.message}</div>
      <button
        onClick={reset}
        className="px-4 py-2 rounded-xl surface-2 border border-base text-sm text-primary surface-hover transition-all"
      >
        Try again
      </button>
    </div>
  )
}