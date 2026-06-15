"use client"

export default function MemoryPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gradient-cyan">Memory</h1>
          <p className="text-sm text-white/40 mt-1">Manage episodic, semantic, and working memory</p>
        </div>
        <button className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-violet-600 text-white rounded-xl font-medium text-sm btn-glow-cyan active:scale-95">
          <span className="flex items-center space-x-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            <span>New Memory</span>
          </span>
        </button>
      </div>

      <div className="flex flex-col items-center justify-center py-20 glass-card rounded-2xl border-dashed border-white/[0.06]">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center mb-5 neon-ring">
          <svg className="w-10 h-10 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-white/70 mb-2">Memory timeline</h3>
        <p className="text-sm text-white/30 mb-8 max-w-md text-center">Your agent&apos;s memories will appear here — episodic, semantic, and working memory</p>
        <button className="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-xl font-medium text-sm shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 active:scale-95 transition-all">
          <span className="flex items-center space-x-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            <span>Explore Memory Features</span>
          </span>
        </button>
      </div>
    </div>
  )
}
