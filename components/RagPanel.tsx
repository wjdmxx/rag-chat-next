'use client'
import { useState } from 'react'
import type { RagDoc } from '@/lib/types'
import { Search, Link as LinkIcon } from 'lucide-react'


export default function RagPanel({ results }: { results: RagDoc[] }) {
    return (
        <aside className="hidden h-[calc(100vh-56px)] w-80 shrink-0 border-l border-zinc-200/60 bg-white/70 p-3 backdrop-blur dark:border-zinc-800/60 dark:bg-zinc-950/60 xl:block">
            <div className="mb-3 flex items-center gap-2">
                <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-200">内容来源</h2>
            </div>
            <div className="space-y-2 overflow-y-auto pr-1 h-full">
                {results.length === 0 && (
                    <div className="flex h-full flex-col items-center justify-center text-zinc-400">
                        <p className="text-xs">暂无内容</p>
                    </div>
                )}
                {results.map(r => (
                    <article key={r.id} className="rounded-2xl border border-zinc-200 bg-white p-3 shadow-soft dark:border-zinc-800 dark:bg-zinc-900">
                        <div className="flex items-start justify-between gap-3">
                            <h3 className="line-clamp-2 text-sm font-semibold leading-snug">{r.title}</h3>
                            <span className="rounded-md bg-emerald-500/15 px-1.5 py-0.5 text-xs text-emerald-700 dark:text-emerald-300">{r.score.toFixed(2)}</span>
                        </div>
                        <p className="mt-1 line-clamp-3 text-xs text-zinc-600 dark:text-zinc-300">{r.snippet}</p>
                    </article>
                ))}
            </div>
        </aside>
    )
}