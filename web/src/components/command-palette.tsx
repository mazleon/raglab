"use client"

import { useState, useEffect, useRef, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'

const actions = [
  {
    group: 'Navigation',
    items: [
      { label: 'New Chat', description: 'Start a new conversation', href: '/chat', icon: 'chat' },
      { label: 'Browse Agents', description: 'View and manage AI agents', href: '/agents', icon: 'agent' },
      { label: 'Explore Knowledge', description: 'Browse indexed documents', href: '/knowledge', icon: 'knowledge' },
      { label: 'View Memory', description: 'View memory timeline', href: '/memory', icon: 'memory' },
    ],
  },
  {
    group: 'Analysis',
    items: [
      { label: 'New Experiment', description: 'Create a new benchmark', href: '/experiments', icon: 'experiment' },
      { label: 'View Evaluations', description: 'Check evaluation metrics', href: '/evaluations', icon: 'evaluation' },
    ],
  },
  {
    group: 'Configuration',
    items: [
      { label: 'Settings', description: 'Configure API keys and preferences', href: '/settings', icon: 'settings' },
    ],
  },
]

function ActionIcon({ icon }: { icon: string }) {
  const paths: Record<string, ReactNode> = {
    chat: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h8M8 16h8m-8-8h8M3 12l6 6 6-6M3 6l6 6 6-6" />,
    agent: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />,
    knowledge: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13V20m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253m0-13V20m0-13C13.168 18.477 14.754 18 16.5 18c1.747 0 3.332-.477 4.5-1.253m0 0V20m0 0C13.168 18.477 14.754 18 16.5 18c1.747 0 3.332-.477 4.5-1.253" />,
    memory: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />,
    experiment: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-5.384-.986a2 2 0 01-1.148-1.148l-.986-5.384a2 2 0 00-3.6 0L5.924 8.884a2 2 0 00-.547 1.022l.986 5.384a2 2 0 001.148 1.148l5.384.986a2 2 0 003.6 0z" />,
    evaluation: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H9a2 2 0 01-2-2V7z" />,
    settings: <><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.955 2.288a1.724 1.724 0 002.573 1.066c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c-.94 1.543-2.826.826-2.288 2.955a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.955a1.724 1.724 0 00-2.573-1.066c-.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543.94 3.31-.826 2.955a1.724 1.724 0 002.573 1.066z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></>,
  }
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      {paths[icon] || paths.chat}
    </svg>
  )
}

export function CommandPalette({ isOpen, onOpenChange }: { isOpen: boolean; onOpenChange: (open: boolean) => void }) {
  if (!isOpen) return null
  // eslint-disable-next-line react-hooks/purity
  return <CommandPaletteContent key={Date.now()} onOpenChange={onOpenChange} />
}

function CommandPaletteContent({ onOpenChange }: { onOpenChange: (open: boolean) => void }) {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const flatItems = actions.flatMap(g => g.items)
  const filtered = flatItems.filter(item =>
    item.label.toLowerCase().includes(search.toLowerCase()) ||
    item.description.toLowerCase().includes(search.toLowerCase())
  )

  useEffect(() => { inputRef.current?.focus() }, [])

  useEffect(() => {
    const down = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); onOpenChange(false) }
      if (e.key === 'Escape') { e.preventDefault(); onOpenChange(false) }
      if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIndex(i => Math.min(i + 1, filtered.length - 1)) }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIndex(i => Math.max(i - 1, 0)) }
      if (e.key === 'Enter' && filtered[selectedIndex]) { e.preventDefault(); router.push(filtered[selectedIndex].href); onOpenChange(false) }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtered, selectedIndex])

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="fixed left-1/2 top-[15%] w-full max-w-lg -translate-x-1/2 animate-scale-in">
        <div className="glass-panel rounded-2xl shadow-2xl shadow-violet-500/20 overflow-hidden border-cyan-500/10">
          {/* Search */}
          <div className="p-3 border-b border-base">
            <div className="relative">
              <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                ref={inputRef}
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setSelectedIndex(0) }}
                placeholder="Search actions..."
                className="w-full px-4 py-2.5 pl-10 surface border border-base rounded-xl text-sm text-primary placeholder:text-subtle focus:outline-none focus:border-cyan-500/30 transition-all"
              />
            </div>
          </div>

          {/* Results */}
          <div className="max-h-80 overflow-y-auto p-2">
            {filtered.length === 0 ? (
              <div className="text-center py-8 text-subtle">
                <svg className="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 2a10 10 0 100 20 10 10 0 000-20z" />
                </svg>
                <p className="text-xs">No results found</p>
              </div>
            ) : (
              actions.map((group) => {
                const groupItems = filtered.filter(f => group.items.some(i => i.label === f.label))
                if (groupItems.length === 0) return null
                return (
                  <div key={group.group}>
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-subtle px-3 py-2">
                      {group.group}
                    </div>
                    {groupItems.map((item) => {
                      const idx = filtered.indexOf(item)
                      const isSelected = idx === selectedIndex
                      return (
                        <button
                          key={item.label}
                          className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-150 flex items-center space-x-3 ${
                            isSelected
                              ? 'bg-gradient-to-r from-cyan-500/10 to-violet-500/10 text-white shadow-sm neon-ring'
                              : 'text-muted hover:text-muted surface-hover'
                          }`}
                          onClick={() => { router.push(item.href); onOpenChange(false) }}
                          onMouseEnter={() => setSelectedIndex(idx)}
                        >
                          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                            isSelected ? 'bg-gradient-to-br from-cyan-500/20 to-violet-500/20 text-cyan-400' : 'surface text-subtle'
                          }`}>
                            <ActionIcon icon={item.icon} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-medium">{item.label}</div>
                            <div className="text-[10px] text-subtle truncate">{item.description}</div>
                          </div>
                          {isSelected && (
                            <kbd className="flex-shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-mono">↵</kbd>
                          )}
                        </button>
                      )
                    })}
                  </div>
                )
              })
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-base surface">
            <div className="flex items-center justify-between text-[10px] text-subtle">
              <div className="flex items-center space-x-3">
                <span><kbd className="px-1 py-0.5 rounded surface-2 font-mono">↑↓</kbd> Navigate</span>
                <span><kbd className="px-1 py-0.5 rounded surface-2 font-mono">↵</kbd> Select</span>
              </div>
              <span><kbd className="px-1 py-0.5 rounded surface-2 font-mono">⌘K</kbd> Toggle · <kbd className="px-1 py-0.5 rounded surface-2 font-mono">ESC</kbd> Close</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
