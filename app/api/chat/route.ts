import { NextRequest, NextResponse } from 'next/server'
import type { RagDoc, Message } from '@/lib/types'


export async function POST(req: NextRequest) {
    const { messages, rag } = (await req.json()) as { messages: Message[]; rag: RagDoc[] }
    const last = messages.at(-1)
    const ragLine = rag?.length ? `\n\nRAG matched ${rag.length} doc(s). Top: ${rag[0].title} (score ${rag[0].score.toFixed(2)}).` : '\n\n(No RAG results yet.)'
    const reply = `You said: "${last?.content ?? ''}"${ragLine}`
    return NextResponse.json({ reply })
}