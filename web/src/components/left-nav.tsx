"use client"

import { type ComponentType, type SVGProps } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  label: string
  icon: ComponentType<SVGProps<SVGSVGElement>>
}

const navItems: NavItem[] = [
  { href: '/chat', label: 'Chats', icon: ChatIcon },
  { href: '/agents', label: 'Agents', icon: AgentIcon },
  { href: '/knowledge', label: 'Knowledge', icon: KnowledgeIcon },
  { href: '/memory', label: 'Memory', icon: MemoryIcon },
  { href: '/experiments', label: 'Experiments', icon: ExperimentIcon },
  { href: '/evaluations', label: 'Evaluations', icon: EvaluationIcon },
  { href: '/settings', label: 'Settings', icon: SettingsIcon },
]

/* ── SVG Icon Components ── */
function ChatIcon(props: SVGProps<SVGSVGElement>) {
  return <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h8M8 16h8m-8-8h8M3 12l6 6 6-6M3 6l6 6 6-6" /></svg>
}
function AgentIcon(props: SVGProps<SVGSVGElement>) {
  return <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
}
function KnowledgeIcon(props: SVGProps<SVGSVGElement>) {
  return <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13V20m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253m0-13V20m0-13C13.168 18.477 14.754 18 16.5 18c1.747 0 3.332-.477 4.5-1.253m0 0V20m0 0C13.168 18.477 14.754 18 16.5 18c1.747 0 3.332-.477 4.5-1.253" /></svg>
}
function MemoryIcon(props: SVGProps<SVGSVGElement>) {
  return <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
}
function ExperimentIcon(props: SVGProps<SVGSVGElement>) {
  return <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-5.384-.986a2 2 0 01-1.148-1.148l-.986-5.384a2 2 0 00-3.6 0L5.924 8.884a2 2 0 00-.547 1.022l.986 5.384a2 2 0 001.148 1.148l5.384.986a2 2 0 003.6 0z" /></svg>
}
function EvaluationIcon(props: SVGProps<SVGSVGElement>) {
  return <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H9a2 2 0 01-2-2V7z" /></svg>
}
function SettingsIcon(props: SVGProps<SVGSVGElement>) {
  return <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.955 2.288a1.724 1.724 0 002.573 1.066c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c-.94 1.543-2.826.826-2.288 2.955a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.955a1.724 1.724 0 00-2.573-1.066c-.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543.94 3.31-.826 2.955a1.724 1.724 0 002.573 1.066z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
}

export function LeftNav({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const pathname = usePathname()

  return (
    <aside
      className={cn(
        'fixed left-0 top-14 h-[calc(100vh-3.5rem)] w-64 sidebar-glass',
        'transform transition-all duration-300 ease-out',
        isOpen ? 'translate-x-0 shadow-2xl shadow-violet-500/10' : '-translate-x-full',
        'md:translate-x-0 md:static md:h-full'
      )}
    >
      <div className="h-full overflow-y-auto py-4 pb-24">
        {/* Section label */}
        <div className="px-6 pb-3 mb-3 mx-3 border-b border-white/[0.06]">
          <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/30">Navigation</p>
        </div>

        <nav className="space-y-0.5 px-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/chat' && pathname?.startsWith(item.href))
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'relative flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group',
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/10 to-violet-500/10 text-white shadow-sm neon-ring'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/[0.04]'
                )}
                onClick={() => onClose()}
              >
                {/* Active glow bar */}
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-gradient-to-b from-cyan-400 to-violet-500 shadow-lg shadow-cyan-500/50" />
                )}
                <Icon className={cn(
                  "w-5 h-5 mr-3 transition-all duration-200",
                  "group-hover:scale-110",
                  isActive ? 'text-cyan-400' : 'text-white/40 group-hover:text-white/60'
                )} />
                <span className={isActive ? 'text-white/90' : ''}>{item.label}</span>
                {isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/[0.06] bg-gradient-to-t from-black/20 to-transparent">
          <div className="flex items-center space-x-3 px-3 py-2 rounded-lg bg-white/[0.03]">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-cyan-500/20">
              <span className="text-xs font-bold text-white">R</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white/70 truncate">RAGLab v0.1</p>
              <p className="text-[10px] text-white/30 truncate">Agentic Intelligence</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
