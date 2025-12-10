'use client'
import { Plus, MessageSquareMore } from 'lucide-react'
import type { Session } from '@/lib/types'
import { cn } from '@/lib/utils'

interface SidebarProps {
    sessions: Session[]
    activeId: string
    onNew: () => void
    onSelect: (id: string) => void
}

export default function Sidebar({ sessions, activeId, onNew, onSelect }: SidebarProps) {
    return (
        <aside className="hidden h-[calc(100vh-56px)] w-64 shrink-0 border-r border-zinc-200/60 bg-white/70 p-3 backdrop-blur dark:border-zinc-800/60 dark:bg-zinc-950/60 md:block">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-200">会话列表</h2>
                <button
                    onClick={onNew}
                    className="rounded-xl bg-brand-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-brand-700"
                >
                    <Plus className="mr-1 inline h-3.5 w-3.5" />新建
                </button>
            </div>
            <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-120px)]">
                {sessions.map(session => (
                    <button
                        key={session.id}
                        onClick={() => onSelect(session.id)}
                        className={cn(
                            "flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-sm transition-colors",
                            activeId === session.id
                                ? "bg-zinc-100 font-medium text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                                : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-900"
                        )}
                    >
                        <MessageSquareMore className="h-4 w-4 shrink-0" />
                        <span className="truncate flex-1 text-left">{session.title}</span>
                    </button>
                ))}
                {sessions.length === 0 && (
                    <div className="px-2 py-4 text-center text-xs text-zinc-400">
                        暂无历史会话
                    </div>
                )}
            </div>
        </aside>
    )
}