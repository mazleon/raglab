import type { ReactNode } from 'react'
import { AppShell } from '@/components/app-shell'

/** App chrome (header + left nav) for every authenticated page. */
export default function AppLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>
}