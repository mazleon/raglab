"use client"

import { Experiment } from '@/types'
import { cn } from '@/lib/utils'

interface ExperimentListProps {
  experiments: Experiment[]
}

export function ExperimentList({ experiments }: ExperimentListProps) {
  if (experiments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 glass-card rounded-2xl border-dashed border-base">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 flex items-center justify-center mb-4 neon-ring">
          <svg className="w-8 h-8 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-5.384-.986a2 2 0 01-1.148-1.148l-.986-5.384a2 2 0 00-3.6 0L5.924 8.884a2 2 0 00-.547 1.022l.986 5.384a2 2 0 001.148 1.148l5.384.986a2 2 0 003.6 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-muted mb-1">No experiments found</h3>
        <p className="text-sm text-subtle mb-6">Run a benchmark to see results here</p>
        <button className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-violet-600 text-white rounded-xl font-medium text-sm btn-glow-cyan active:scale-95">
          New Experiment
        </button>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {experiments.map((experiment, index) => (
        <ExperimentCard key={experiment.experiment_id} experiment={experiment} index={index} />
      ))}
    </div>
  )
}

function ExperimentCard({ experiment, index }: { experiment: Experiment; index: number }) {
  const recallScore = experiment.context_recall_proxy || 0
  const relevancyScore = experiment.answer_relevancy_proxy || 0
  const avgScore = (recallScore + relevancyScore) / 2

  const getScoreBadge = (score: number) => {
    if (score >= 0.8) return { label: 'Excellent', color: 'text-emerald-400', bar: 'from-emerald-400 to-cyan-400' }
    if (score >= 0.6) return { label: 'Good', color: 'text-cyan-400', bar: 'from-cyan-400 to-blue-500' }
    if (score >= 0.4) return { label: 'Fair', color: 'text-amber-400', bar: 'from-amber-400 to-orange-500' }
    return { label: 'Poor', color: 'text-rose-400', bar: 'from-rose-400 to-pink-500' }
  }

  const badge = getScoreBadge(avgScore)

  const getMetricBar = (value: number, label: string) => {
    const pct = Math.min(value * 100, 100)
    const bar = badge.bar
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-muted">{label}</span>
          <span className={cn('font-mono font-medium', value >= 0.6 ? 'text-muted' : 'text-rose-400')}>
            {pct.toFixed(0)}%
          </span>
        </div>
        <div className="w-full h-1.5 surface-2 rounded-full overflow-hidden">
          <div
            className={cn('h-full rounded-full bg-gradient-to-r transition-all duration-500', bar)}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'glass-card rounded-2xl p-5 cursor-pointer animate-fade-in',
        'hover:border-cyan-500/20 hover:shadow-lg hover:shadow-cyan-500/5'
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <h3 className="font-semibold text-primary truncate text-sm">
              {experiment.architecture} — {experiment.embedding}
            </h3>
            <span className={cn('px-2 py-0.5 rounded-full text-[10px] font-semibold surface', badge.color)}>
              {badge.label}
            </span>
          </div>
          <div className="flex items-center space-x-2 text-xs text-subtle">
            <span className="px-1.5 py-0.5 rounded surface font-mono text-[10px]">{experiment.architecture}</span>
            <span>•</span>
            <span>{experiment.embedding}</span>
          </div>
        </div>
        <div className="flex-shrink-0 text-right">
          <div className="text-[10px] text-subtle">
            {new Date(experiment.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
          </div>
        </div>
      </div>

      {/* Score Overview */}
      <div className="mb-4 p-3 rounded-xl bg-gradient-to-br from-cyan-500/5 to-violet-500/5 border border-base">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted">Average Score</span>
          <span className={cn('text-lg font-bold bg-gradient-to-r bg-clip-text text-transparent', badge.bar)}>
            {(avgScore * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full h-2 surface-2 rounded-full overflow-hidden">
          <div
            className={cn('h-full rounded-full bg-gradient-to-r transition-all duration-700', badge.bar)}
            style={{ width: `${avgScore * 100}%` }}
          />
        </div>
      </div>

      {/* Metrics */}
      <div className="space-y-2.5">
        {getMetricBar(recallScore, 'Context Recall')}
        {getMetricBar(relevancyScore, 'Answer Relevancy')}

        <div className="pt-2 mt-2 divider-glow grid grid-cols-2 gap-3">
          <div>
            <div className="text-[10px] text-subtle mb-0.5">Latency</div>
            <div className="text-sm font-semibold text-primary font-mono">
              {experiment.avg_latency_ms.toFixed(0)}<span className="text-[10px] text-subtle font-normal">ms</span>
            </div>
          </div>
          <div>
            <div className="text-[10px] text-subtle mb-0.5">Cost</div>
            <div className="text-sm font-semibold text-primary font-mono">
              ${experiment.total_cost_usd.toFixed(4)}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
