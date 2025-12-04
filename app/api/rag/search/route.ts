import { NextRequest, NextResponse } from 'next/server'
import type { RagDoc } from '@/lib/types'


const corpus: Pick<RagDoc, 'title' | 'snippet' | 'url'>[] = [
    { title: 'Project README', snippet: 'How to run, develop, and deploy the project to Vercel.', url: 'https://vercel.com' },
    { title: 'API Contract: /chat', snippet: 'Expected request/response shape for the chat endpoint.', url: 'https://example.com' },
    { title: 'RAG Design Notes', snippet: 'Retriever settings, top-k, chunking, and scoring calibration.', url: 'https://example.com' },
    { title: 'Evaluation Checklist', snippet: 'Latency, accuracy, grounding, and robustness checks.', url: 'https://example.com' }
]


export async function POST(req: NextRequest) {
    const { query } = await req.json() as { query: string }
    const base = (query ?? '').trim()
    const results: RagDoc[] = corpus.map((c, i) => ({
        id: `doc_${i}_${Math.random().toString(36).slice(2, 7)}`,
        title: c.title,
        url: c.url,
        snippet: c.snippet,
        score: Math.max(0.25, Math.random())
    })).sort((a, b) => b.score - a.score)


    // In your real retriever, use `base` to score docs.
    return NextResponse.json({ results })
}