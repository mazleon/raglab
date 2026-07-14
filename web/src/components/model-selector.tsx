"use client"

import { cn } from '@/lib/utils'
import { useConfig } from '@/hooks/use-config'
interface ModelSelectorProps {
  selectedModel?: string
  selectedEmbedding?: string
  selectedPipeline?: string
  onModelChange: (id: string) => void
  onEmbeddingChange: (id: string) => void
  onPipelineChange: (id: string) => void
  compact?: boolean
}

function SelectGroup<T extends { id: string; name: string; description: string; available?: boolean }>({
  label,
  items,
  value,
  onChange,
  compact,
}: {
  label: string
  items: T[]
  value?: string
  onChange: (id: string) => void
  compact?: boolean
}) {
  const selected = items.find(i => i.id === value)
  return (
    <div className={compact ? '' : 'space-y-2'}>
      {!compact && (
        <label className="text-[10px] font-semibold uppercase tracking-wider text-muted">{label}</label>
      )}
      <div className="relative">
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            'w-full appearance-none border border-base rounded-xl surface text-sm text-muted',
            'focus:outline-none focus:border-cyan-500/40 transition-all cursor-pointer',
            compact ? 'px-2.5 py-2 pr-7 text-xs min-w-[100px]' : 'px-3 py-2.5 pr-9',
          )}
        >
          {items.length === 0 && (
            <option value="" className="surface-2 text-subtle">Loading...</option>
          )}
          {items.map((item) => (
            <option
              key={item.id}
              value={item.id}
              disabled={item.available === false}
              className="surface-2"
            >
              {item.name}{item.available === false ? ' (config required)' : ''}
            </option>
          ))}
        </select>
        {/* Dropdown arrow */}
        <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-subtle">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      {!compact && selected && (
        <p className="text-[10px] text-subtle mt-1">{selected.description}</p>
      )}
    </div>
  )
}

export function ModelSelector(props: ModelSelectorProps) {
  const { data: config, isLoading } = useConfig()
  const { compact = false, selectedModel, selectedEmbedding, selectedPipeline, onModelChange, onEmbeddingChange, onPipelineChange } = props

  if (isLoading) {
    return (
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-10 rounded-xl surface animate-pulse" />
        ))}
      </div>
    )
  }

  if (compact) {
    return (
      <div className="flex items-center space-x-2">
        <SelectGroup
          label="Pipeline"
          items={config?.pipelines || []}
          value={selectedPipeline}
          onChange={onPipelineChange}
          compact
        />
        <SelectGroup
          label="Model"
          items={config?.models || []}
          value={selectedModel}
          onChange={onModelChange}
          compact
        />
        <SelectGroup
          label="Embedding"
          items={config?.embeddings || []}
          value={selectedEmbedding}
          onChange={onEmbeddingChange}
          compact
        />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-3 gap-4">
      <SelectGroup
        label="Pipeline Architecture"
        items={config?.pipelines || []}
        value={selectedPipeline}
        onChange={onPipelineChange}
      />
      <SelectGroup
        label="LLM Model"
        items={config?.models || []}
        value={selectedModel}
        onChange={onModelChange}
      />
      <SelectGroup
        label="Embedding Model"
        items={config?.embeddings || []}
        value={selectedEmbedding}
        onChange={onEmbeddingChange}
      />
    </div>
  )
}
