'use client'
import { Plus, MessageSquareMore, FolderKanban } from 'lucide-react'


export default function Sidebar() {
    return (
        <aside className="hidden h-[calc(100vh-56px)] w-64 shrink-0 border-r border-zinc-200/60 bg-white/70 p-3 backdrop-blur dark:border-zinc-800/60 dark:bg-zinc-950/60 md:block">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-200">会话列表</h2>
                <button className="rounded-xl bg-brand-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-brand-700"><Plus className="mr-1 inline h-3.5 w-3.5" />新建</button>
            </div>
            <div className="space-y-1">
                <button className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-sm hover:bg-zinc-100 dark:hover:bg-zinc-900">
                    <MessageSquareMore className="h-4 w-4" />
                    历史会话
                </button>
                <button className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-sm hover:bg-zinc-100 dark:hover:bg-zinc-900">
                    <FolderKanban className="h-4 w-4" />
                    知识库
                </button>
            </div>
        </aside>
    )
}