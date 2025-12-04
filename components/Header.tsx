'use client'
import { Bot, CircleHelp, Github, Settings } from 'lucide-react'


export default function Header() {
    return (
        <header className="sticky top-0 z-20 border-b border-zinc-200/60 bg-white/70 backdrop-blur dark:border-zinc-800/60 dark:bg-zinc-950/60">
            <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
                <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-brand-600" />
                    <span className="font-semibold tracking-tight">设备维修智能问答系统</span>
                </div>
                <nav className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-300">
                </nav>
            </div>
        </header>
    )
}