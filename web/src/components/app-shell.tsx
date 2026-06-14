"use client"

import { useState } from 'react'
import { LeftNav } from './left-nav'
import { CommandPalette } from './command-palette'
import { UserMenu } from './user-menu'
import { TenantSwitcher } from './tenant-switcher'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const [isLeftNavOpen, setIsLeftNavOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="h-14 border-b bg-white dark:bg-gray-800 flex items-center px-4">
        <button
          onClick={() => setIsLeftNavOpen(!isLeftNavOpen)}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg mr-2"
          aria-label="Toggle navigation"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>

        <div className="flex-1" />

        <CommandPalette
          isOpen={isCommandPaletteOpen}
          onOpenChange={setIsCommandPaletteOpen}
        />

        <TenantSwitcher className="mr-2" />
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
          <div className="h-full overflow-auto p-6">{children}</div>
        </main>
      </div>
    </div>
  )
}