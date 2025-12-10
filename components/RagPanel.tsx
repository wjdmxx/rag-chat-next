'use client'
import { useState } from 'react'
import type { RagDoc } from '@/lib/types'
import { Search, Link as LinkIcon, X } from 'lucide-react'


export default function RagPanel({ results }: { results: RagDoc[] }) {
    const [selectedDoc, setSelectedDoc] = useState<RagDoc | null>(null)

    return (
        <>
            <aside className="hidden h-[calc(100vh-56px)] w-80 shrink-0 flex-col border-l border-zinc-200/60 bg-white/70 p-3 backdrop-blur dark:border-zinc-800/60 dark:bg-zinc-950/60 xl:flex">
                <div className="mb-3 flex items-center gap-2 shrink-0">
                    <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-200">内容来源</h2>
                </div>
                <div className="space-y-2 overflow-y-auto pr-1 flex-1">
                    {results.length === 0 && (
                        <div className="flex h-full flex-col items-center justify-center text-zinc-400">
                            <p className="text-xs">暂无内容</p>
                        </div>
                    )}
                    {results.map((r, i) => (
                        <article
                            key={`${r.id}-${i}`}
                            onClick={() => setSelectedDoc(r)}
                            className="cursor-pointer hover:border-brand-500 transition-colors rounded-2xl border border-zinc-200 bg-white p-3 shadow-soft dark:border-zinc-800 dark:bg-zinc-900"
                        >
                            <div className="flex items-start justify-between gap-3">
                                <h3 className="line-clamp-2 text-sm font-semibold leading-snug">{r.title}</h3>
                            </div>
                            <p className="mt-1 line-clamp-3 text-xs text-zinc-600 dark:text-zinc-300">{r.snippet}</p>
                        </article>
                    ))}
                </div>
            </aside>

            {selectedDoc && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" onClick={() => setSelectedDoc(null)}>
                    <div
                        className="relative flex max-h-[80vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-zinc-900"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="flex shrink-0 items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
                            <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">{selectedDoc.title}</h3>
                            <button
                                onClick={() => setSelectedDoc(null)}
                                className="rounded-lg p-1 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        <div className="overflow-y-auto p-6">
                            <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">
                                {selectedDoc.snippet}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}