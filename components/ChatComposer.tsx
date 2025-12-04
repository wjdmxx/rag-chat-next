'use client'
import { FormEvent, useState } from 'react'
import { CornerDownLeft, Paperclip, Sparkles } from 'lucide-react'


export default function ChatComposer({ onSend }: { onSend: (text: string) => void }) {
    const [text, setText] = useState('')

    const submit = (e: FormEvent) => {
        e.preventDefault()
        const t = text.trim()
        if (!t) return
        onSend(t)
        setText('')
    }

    return (
        <form onSubmit={submit} className="rounded-2xl border border-zinc-200 bg-white/90 p-2 shadow-soft backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/80">
            <div className="flex items-center gap-2">
                <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="请输入您的问题..."
                    rows={1}
                    className="mx-1 w-full resize-none bg-transparent p-2 text-sm outline-none placeholder:text-zinc-400"
                />
                <button className="inline-flex items-center gap-1 rounded-xl bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700" type="submit">
                    发送 <CornerDownLeft className="h-4 w-4" />
                </button>
            </div>
        </form>
    )
}