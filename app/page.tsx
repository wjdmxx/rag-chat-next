'use client'
import Header from '@/components/Header'
import Sidebar from '@/components/Sidebar'
import ChatMessage from '@/components/ChatMessage'
import ChatComposer from '@/components/ChatComposer'
import RagPanel from '@/components/RagPanel'
import type { Message, RagDoc, Session } from '@/lib/types'
import { uid } from '@/lib/utils'
import { useEffect, useState, useRef, useMemo } from 'react'


export default function Page() {
    const [sessions, setSessions] = useState<Session[]>([])
    const [activeId, setActiveId] = useState<string>('')
    const [typing, setTyping] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Initialize first session
    useEffect(() => {
        if (sessions.length === 0 && !activeId) {
            const newId = uid('s')
            const initialSession: Session = {
                id: newId,
                title: '新会话',
                messages: [{
                    id: uid('m'), role: 'assistant', createdAt: Date.now(),
                    content: '您好！我是设备维修智能助手。请问有什么可以帮您？'
                }],
                ragResults: [],
                createdAt: Date.now()
            }
            setSessions([initialSession])
            setActiveId(newId)
        }
    }, [])

    const activeSession = useMemo(() =>
        sessions.find(s => s.id === activeId) || sessions[0],
        [sessions, activeId])

    const messages = activeSession?.messages || []
    const ragResults = activeSession?.ragResults || []

    function handleNewSession() {
        const newId = uid('s')
        const newSession: Session = {
            id: newId,
            title: '新会话',
            messages: [{
                id: uid('m'), role: 'assistant', createdAt: Date.now(),
                content: '您好！我是设备维修智能助手。请问有什么可以帮您？'
            }],
            ragResults: [],
            createdAt: Date.now()
        }
        setSessions(prev => [newSession, ...prev])
        setActiveId(newId)
    }

    async function onSend(text: string) {
        if (!activeSession) return

        const userMsg: Message = { id: uid('m'), role: 'user', content: text, createdAt: Date.now() }

        // Optimistic update
        setSessions(prev => prev.map(s => {
            if (s.id === activeId) {
                // Rename session if it's the first user message (length was 1: assistant hello)
                const newTitle = s.messages.length === 1 ? text : s.title
                return {
                    ...s,
                    title: newTitle,
                    messages: [...s.messages, userMsg]
                }
            }
            return s
        }))

        setTyping(true)
        try {
            // Get current messages for API context
            const currentMessages = [...activeSession.messages, userMsg]

            const res = await fetch('/api/chat', {
                method: 'POST',
                body: JSON.stringify({ messages: currentMessages })
            })
            const data = await res.json() as { reply: string, rag?: RagDoc[] }

            const assistantMsg: Message = {
                id: uid('m'),
                role: 'assistant',
                content: data.reply,
                createdAt: Date.now()
            }

            setSessions(prev => prev.map(s => {
                if (s.id === activeId) {
                    return {
                        ...s,
                        messages: [...s.messages, assistantMsg],
                        ragResults: data.rag ? [...s.ragResults, ...data.rag] : s.ragResults
                    }
                }
                return s
            }))
        } catch (e) {
            const errorMsg: Message = {
                id: uid('m'),
                role: 'assistant',
                content: "抱歉，出错了。",
                createdAt: Date.now()
            }
            setSessions(prev => prev.map(s => {
                if (s.id === activeId) {
                    return { ...s, messages: [...s.messages, errorMsg] }
                }
                return s
            }))
        } finally {
            setTyping(false)
        }
    }


    // keep scroll at bottom on new message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages.length, activeId])


    return (
        <div className="flex min-h-screen flex-col overflow-hidden">
            <Header />
            <main className="mx-auto grid w-full max-w-7xl grid-cols-1 md:grid-cols-[256px_minmax(0,1fr)] xl:grid-cols-[256px_minmax(0,1fr)_320px]">
                <Sidebar
                    sessions={sessions}
                    activeId={activeId}
                    onNew={handleNewSession}
                    onSelect={setActiveId}
                />
                <section className="flex h-[calc(100vh-56px)] flex-col px-4 py-4">
                    <div className="mx-auto mb-4 w-full max-w-3xl flex-1 space-y-4 overflow-y-auto pr-2">
                        {messages.map(m => <ChatMessage key={m.id} m={m} />)}
                        {typing && (
                            <div className="flex items-center gap-2 text-xs text-zinc-500"><span className="h-2 w-2 animate-pulse rounded-full bg-zinc-400" />Assistant is typing…</div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                    <div className="mx-auto w-full max-w-3xl shrink-0">
                        <ChatComposer onSend={onSend} />
                    </div>
                </section>
                <RagPanel results={ragResults} />
            </main>
        </div>
    )
}