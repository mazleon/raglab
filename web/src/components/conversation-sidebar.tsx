"use client"

import { cn } from '@/lib/utils'
import { useConversations, useDeleteConversation } from '@/hooks/use-conversations'

interface Props {
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
}

export function ConversationSidebar({ activeId, onSelect, onNew }: Props) {
  const { data: conversations = [], isLoading } = useConversations()
  const del = useDeleteConversation()

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    await del.mutateAsync(id)
    if (id === activeId) onNew()
  }

  return (
    <div className="w-64 flex-shrink-0 border-r border-white/[0.06] flex flex-col bg-black/20">
      <div className="p-3">
        <button
          onClick={onNew}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium bg-gradient-to-r from-cyan-500 to-violet-600 text-white shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 active:scale-[0.98] transition-all"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New chat
        </button>
      </div>

      <div className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-white/25">
        Conversations
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-0.5">
        {isLoading && (
          <div className="px-3 py-2 text-xs text-white/30">Loading…</div>
        )}
        {!isLoading && conversations.length === 0 && (
          <div className="px-3 py-8 text-center text-xs text-white/25">
            No conversations yet.<br />Start a new chat.
          </div>
        )}
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={cn(
              'group w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-all',
              c.id === activeId
                ? 'bg-gradient-to-r from-cyan-500/10 to-violet-500/10 text-white'
                : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]',
            )}
          >
            <svg className="w-3.5 h-3.5 flex-shrink-0 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span className="flex-1 truncate text-xs">{c.title}</span>
            <span
              onClick={(e) => handleDelete(e, c.id)}
              className="opacity-0 group-hover:opacity-100 text-white/30 hover:text-rose-400 transition-all"
              title="Delete"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
