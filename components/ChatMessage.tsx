'use client'
import { cn } from '@/lib/utils'
import type { Message } from '@/lib/types'
import { Bot, User } from 'lucide-react'


export default function ChatMessage({ m }: { m: Message }) {
    const isUser = m.role === 'user'
    return (
        <div className={cn('flex w-full items-start gap-3', isUser ? 'justify-end' : 'justify-start')}>
            {!isUser && (
                <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-500 text-white"><Bot className="h-4 w-4" /></div>
            )}
            <div className={cn('max-w-[78%] rounded-2xl px-4 py-2 shadow-soft',
                isUser ? 'bg-brand-600 text-white' : 'bg-white/80 dark:bg-zinc-900/80')}
            >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</p>
            </div>
            {isUser && (
                <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-200 dark:bg-zinc-800"><User className="h-4 w-4" /></div>
            )}
        </div>
    )
}