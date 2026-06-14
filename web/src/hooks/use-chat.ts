"use client"

import { useQueryClient } from '@tanstack/react-query'
import { useState, useCallback } from 'react'

export function useChat() {
  const queryClient = useQueryClient()
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = useCallback(async (content: string, pipeline?: string) => {
    setIsLoading(true)

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: content,
          config: pipeline ? `configs/${pipeline}.yaml` : 'configs/naive.yaml',
          ingest_path: 'examples/docs',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const result = await response.json()

      // Update experiments cache
      queryClient.invalidateQueries({ queryKey: ['experiments'] })

      return result
    } catch (error) {
      console.error('Error in useChat:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [queryClient])

  return {
    sendMessage,
    isLoading,
  }
}