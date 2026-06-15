"use client"

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Conversation, StoredMessage } from '@/types'

async function fetchConversations(): Promise<Conversation[]> {
  const res = await fetch('/api/conversations', { cache: 'no-store' })
  if (!res.ok) return []
  const data = await res.json()
  return data.conversations ?? []
}

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: fetchConversations,
    staleTime: 1000 * 30,
  })
}

export interface ConversationDetail extends Conversation {
  messages: StoredMessage[]
}

export function useConversation(id: string | null) {
  return useQuery({
    queryKey: ['conversation', id],
    enabled: !!id,
    queryFn: async (): Promise<ConversationDetail | null> => {
      if (!id) return null
      const res = await fetch(`/api/conversations/${id}`, { cache: 'no-store' })
      if (!res.ok) return null
      return res.json()
    },
  })
}

export function useDeleteConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await fetch(`/api/conversations/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversations'] }),
  })
}
