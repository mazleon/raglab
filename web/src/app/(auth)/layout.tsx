import type { ReactNode } from 'react'

/** Bare shell for auth pages (login/register) — no app chrome. */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-screen space-bg">{children}</div>
}