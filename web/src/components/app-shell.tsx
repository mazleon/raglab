"use client"

import { useState, type ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { LeftNav } from './left-nav'
import { CommandPalette } from './command-palette'
import { UserMenu } from './user-menu'
import { TenantSwitcher } from './tenant-switcher'
import { ThemeToggle } from './theme-toggle'

interface AppShellProps {
  children: ReactNode
}

const BARE_ROUTES = ['/login', '/register']

export function AppShell({ children }: AppShellProps) {
  const [isLeftNavOpen, setIsLeftNavOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const pathname = usePathname()

  // Auth pages render without the app chrome.
  if (BARE_ROUTES.some((r) => pathname?.startsWith(r))) {
    return <div className="min-h-screen space-bg">{children}</div>
  }

  return (
    <div className="h-screen flex flex-col space-bg">
      {/* Header */}
      <header className="h-14 glass-panel border-b border-transparent border-base flex items-center px-4 z-30 flex-shrink-0">
        <button
          onClick={() => setIsLeftNavOpen(!isLeftNavOpen)}
          className="p-2 surface-hover rounded-lg mr-2 transition-all hover:scale-105 active:scale-95 text-muted hover:text-primary"
          aria-label="Toggle navigation"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Logo/Brand */}
        <div className="flex items-center space-x-2.5 ml-1">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-primary hidden sm:block tracking-wide">RAGLab</span>
        </div>

        <div className="flex-1" />

        <CommandPalette
          isOpen={isCommandPaletteOpen}
          onOpenChange={setIsCommandPaletteOpen}
        />

        <TenantSwitcher className="mr-2" />
        <ThemeToggle />
        <UserMenu />
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Navigation */}
        <LeftNav
          isOpen={isLeftNavOpen}
          onClose={() => setIsLeftNavOpen(false)}
        />

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          <div className="h-full overflow-auto p-6 animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
