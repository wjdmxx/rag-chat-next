'use client'
import Header from '@/components/Header'
import Sidebar from '@/components/Sidebar'
import ChatMessage from '@/components/ChatMessage'
import ChatComposer from '@/components/ChatComposer'
import RagPanel from '@/components/RagPanel'
import type { Message, RagDoc } from '@/lib/types'
import { uid, sleep } from '@/lib/utils'
import { useEffect, useState } from 'react'


export default function Page() {
    const [messages, setMessages] = useState<Message[]>([{
        id: uid('m'), role: 'assistant', createdAt: Date.now(),
        content: '您好！我是设备维修智能助手。请问有什么可以帮您？'
    }])
    const [ragResults, setRagResults] = useState<RagDoc[]>([])
    const [typing, setTyping] = useState(false)


    async function onSend(text: string) {
        const user: Message = { id: uid('m'), role: 'user', content: text, createdAt: Date.now() }
        setMessages(prev => [...prev, user])
        
        // 暂时不需要对话功能
    }


    // keep scroll at bottom on new message
    useEffect(() => { window.scrollTo({ top: document.body.scrollHeight }) }, [messages.length])


    return (
        <div className="flex min-h-screen flex-col">
            <Header />
            <main className="mx-auto grid w-full max-w-7xl grid-cols-1 md:grid-cols-[256px_minmax(0,1fr)] xl:grid-cols-[256px_minmax(0,1fr)_320px]">
                <Sidebar />
                <section className="flex min-h-[calc(100vh-56px)] flex-col px-4 py-4">
                    <div className="mx-auto mb-4 w-full max-w-3xl flex-1 space-y-4">
                        {messages.map(m => <ChatMessage key={m.id} m={m} />)}
                        {typing && (
                            <div className="flex items-center gap-2 text-xs text-zinc-500"><span className="h-2 w-2 animate-pulse rounded-full bg-zinc-400" />Assistant is typing…</div>
                        )}
                    </div>
                    <div className="mx-auto w-full max-w-3xl">
                        <ChatComposer onSend={onSend} />
                    </div>
                </section>
                <RagPanel results={ragResults} />
            </main>
        </div>
    )
}