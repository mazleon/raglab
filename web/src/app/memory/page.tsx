"use client"

export default function MemoryPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Memory
        </h1>
        <button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
          New Memory
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
        <div className="text-gray-500 dark:text-gray-400 mb-4">
          Memory management and timeline
        </div>
        <div className="text-sm text-gray-400 dark:text-gray-500">
          Manage episodic, semantic, and working memory
        </div>
      </div>
    </div>
  )
}