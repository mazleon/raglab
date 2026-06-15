import type { ReactNode } from 'react'
import { Inter } from 'next/font/google'
import { QueryProvider } from '@/components/query-provider'
import { AppShell } from '@/components/app-shell'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <AppShell>{children}</AppShell>
        </QueryProvider>
      </body>
    </html>
  )
}
