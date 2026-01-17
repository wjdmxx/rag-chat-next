# 项目代码详细介绍

本项目是一个基于 RAG (Retrieval-Augmented Generation) 的设备维修智能问答系统。前端使用 Next.js 构建，后端服务包括一个用于文档检索的 RAG 服务和一个 LLM (Large Language Model) 接口。

## 1. 前端架构与功能实现

前端采用 Next.js App Router 架构，使用 React Hooks 进行状态管理，Tailwind CSS 进行样式设计。

### 1.1 数据类型定义 (`lib/types.ts`)

首先定义了系统中的核心数据结构：消息、RAG 文档和会话。

```typescript
export type Role = 'user' | 'assistant' | 'system'

export interface Message {
    id: string
    role: Role
    content: string
    createdAt: number
}

export interface RagDoc {
    id: string
    title: string
    url?: string
    snippet: string
    score: number
}

export interface Session {
    id: string
    title: string
    messages: Message[]
    ragResults: RagDoc[]
    createdAt: number
}
```

### 1.2 主页面逻辑 (`app/page.tsx`)

这是应用的核心入口，负责整合各个组件，管理全局状态（会话列表、当前会话、输入状态），并处理与后端 API 的交互。

**主要功能点：**
1.  **会话管理**：初始化创建新会话，支持切换会话。
2.  **消息发送 (`onSend`)**：
    -   乐观更新 UI（先显示用户消息）。
    -   调用 `/api/chat` 接口。
    -   接收流式或一次性响应，更新助手回复和 RAG 参考文档。
3.  **布局结构**：响应式布局，包含 Header、Sidebar（左侧）、聊天区（中间）、RagPanel（右侧）。

```tsx
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

    // 初始化第一个会话
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

        // 乐观更新：先显示用户消息
        setSessions(prev => prev.map(s => {
            if (s.id === activeId) {
                // 如果是第一条消息，更新会话标题
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
            const currentMessages = [...activeSession.messages, userMsg]

            // 调用后端 API
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

            // 更新助手回复和 RAG 结果
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
            // 错误处理
            const errorMsg: Message = {
                id: uid('m'), role: 'assistant', content: "抱歉，出错了。", createdAt: Date.now()
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

    // 自动滚动到底部
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
                            <div className="flex items-center gap-2 text-xs text-zinc-500">
                                <span className="h-2 w-2 animate-pulse rounded-full bg-zinc-400" />Assistant is typing…
                            </div>
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
```

### 1.3 UI 组件详解

#### 聊天输入框 (`components/ChatComposer.tsx`)
简洁的输入框组件，支持回车发送。

```tsx
'use client'
import { FormEvent, useState } from 'react'
import { CornerDownLeft } from 'lucide-react'

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
                <button className="inline-flex shrink-0 items-center gap-1 rounded-xl bg-brand-600 px-6 py-2 text-sm font-medium text-white hover:bg-brand-700 whitespace-nowrap" type="submit">
                    发送 <CornerDownLeft className="h-4 w-4" />
                </button>
            </div>
        </form>
    )
}
```

#### 消息气泡 (`components/ChatMessage.tsx`)
根据消息角色（User/Assistant）展示不同的样式和头像。

```tsx
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
```

#### RAG 参考文档面板 (`components/RagPanel.tsx`)
展示检索到的知识库文档，点击可查看详情。

```tsx
'use client'
import { useState } from 'react'
import type { RagDoc } from '@/lib/types'
import { X } from 'lucide-react'

export default function RagPanel({ results }: { results: RagDoc[] }) {
    const [selectedDoc, setSelectedDoc] = useState<RagDoc | null>(null)

    return (
        <>
            <aside className="hidden h-[calc(100vh-56px)] w-80 shrink-0 flex-col border-l border-zinc-200/60 bg-white/70 p-3 backdrop-blur dark:border-zinc-800/60 dark:bg-zinc-950/60 xl:flex">
                <div className="mb-3 flex items-center gap-2 shrink-0">
                    <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-200">内容来源</h2>
                </div>
                <div className="space-y-2 overflow-y-auto pr-1 flex-1">
                    {results.length === 0 && (
                        <div className="flex h-full flex-col items-center justify-center text-zinc-400">
                            <p className="text-xs">暂无内容</p>
                        </div>
                    )}
                    {results.map((r, i) => (
                        <article
                            key={`${r.id}-${i}`}
                            onClick={() => setSelectedDoc(r)}
                            className="cursor-pointer hover:border-brand-500 transition-colors rounded-2xl border border-zinc-200 bg-white p-3 shadow-soft dark:border-zinc-800 dark:bg-zinc-900"
                        >
                            <div className="flex items-start justify-between gap-3">
                                <h3 className="line-clamp-2 text-sm font-semibold leading-snug">{r.title}</h3>
                            </div>
                            <p className="mt-1 line-clamp-3 text-xs text-zinc-600 dark:text-zinc-300">{r.snippet}</p>
                        </article>
                    ))}
                </div>
            </aside>

            {/* 详情弹窗 */}
            {selectedDoc && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" onClick={() => setSelectedDoc(null)}>
                    <div className="relative flex max-h-[80vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-zinc-900" onClick={e => e.stopPropagation()}>
                        <div className="flex shrink-0 items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
                            <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">{selectedDoc.title}</h3>
                            <button onClick={() => setSelectedDoc(null)} className="rounded-lg p-1 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800">
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        <div className="overflow-y-auto p-6">
                            <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">
                                {selectedDoc.snippet}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}
```

---

## 2. 后端服务与调用流程

后端逻辑分为 Next.js API Route（业务编排）和 Python RAG Service（核心检索）。

### 2.1 业务编排层 (`app/api/chat/route.ts`)

该文件负责串联整个问答流程：
1.  接收用户输入。
2.  调用 RAG 服务获取相关文档。
3.  构建包含参考文档的 Prompt。
4.  调用 LLM 生成回答。
5.  返回回答和参考文档。

```typescript
import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const client = new OpenAI({
    apiKey: "EMPTY",
    baseURL: "http://localhost:8000/v1", // LLM 服务地址
})

export async function POST(req: NextRequest) {
    try {
        const { messages } = await req.json()
        const lastMessage = messages[messages.length - 1]
        const userText = lastMessage.content

        // 1. 调用 RAG 服务
        let referenceDoc = ""
        let ragResult = null

        try {
            const ragRes = await fetch("http://127.0.0.1:8001/retrieve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: userText })
            })

            if (ragRes.ok) {
                const ragData = await ragRes.json()
                referenceDoc = ragData.document
                ragResult = {
                    id: ragData.id,
                    title: ragData.title,
                    snippet: ragData.document,
                    score: ragData.score,
                    url: ""
                }
            } else {
                console.warn("RAG service returned error:", await ragRes.text())
            }
        } catch (e) {
            console.warn("Failed to connect to RAG service:", e)
        }

        // 2. 构建 Prompt
        // 如果有参考文档，则注入文档内容和严格的格式要求
        const promptContent = referenceDoc
            ? `${userText} Please answer based on the reference document, and translate your answer in Complete Chinese sentence by sentence.
请严格按照以下格式回答，并根据提问内容回答。如提问使用了什么工具，则只回答工具部分。如提问如何维修，请将工具和维修步骤均回答。工具和步骤数量根据参考文档中的信息确定。
回答格式：工具部分：每个工具之间使用顿号连接，不要出现json的格式。步骤部分，使用阿拉伯数字，如第1步。每行一个步骤。见下。
以下是需要的工具。
工具：{工具1}、{工具2}、{工具3}……
以下是具体实施步骤。
步骤：
- 第1步：{步骤1}
- 第2步：{步骤2}
……

Reference Document: ${referenceDoc}`
            : userText

        // 3. 调用 LLM
        const response = await client.chat.completions.create({
            model: "/path/to/your/model/Qwen2.5-14B-Instruct", // 模型路径
            messages: [
                { role: "system", content: "You are a helpful assistant." },
                { role: "user", content: promptContent },
            ],
            max_tokens: 50000
        })

        const reply = response.choices[0].message.content

        // 返回回答和 RAG 结果
        return NextResponse.json({ reply, rag: ragResult ? [ragResult] : [] })

    } catch (error) {
        console.error("Error calling LLM:", error)
        return NextResponse.json({ reply: "抱歉，系统暂时无法响应，请稍后再试。" }, { status: 500 })
    }
}
```

### 2.2 RAG 检索服务 (`rag_service.py`)

这是一个独立的 Python FastAPI 服务。
-   **功能**：接收文本查询，返回最相似的文档。
-   **核心技术**：使用 CLIP 模型进行文本向量化，计算与预存文档向量的余弦相似度。
-   **多语言支持**：内置翻译逻辑，将中文查询翻译为英文以提高 CLIP 模型的检索准确率。

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import clip
import numpy as np
import json
import os
from openai import AsyncOpenAI

app = FastAPI()

# 初始化 OpenAI 客户端用于翻译
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:7999/v1"
client = AsyncOpenAI(api_key=openai_api_key, base_url=openai_api_base)

# 加载模型和数据
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading CLIP on {device}...")
try:
    model, preprocess = clip.load("ViT-B/32", device=device)
except Exception as e:
    print(f"Error loading CLIP: {e}")
    model = None

# 路径配置（已泛化）
EMBEDDINGS_PATH = "/path/to/embeddings/all_embeddings.npz"
DATA_PATH = "/path/to/data/train_data_all.json"

# 加载 Embeddings 和原始数据
# ... (省略加载代码，与标准 numpy/json 加载一致)

class Query(BaseModel):
    text: str

@app.post("/retrieve")
async def retrieve(query: Query):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    try:
        text = query.text
        
        # 中文检测与翻译
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            print(f"Detected Chinese input: {text}")
            try:
                response = await client.chat.completions.create(
                    model="/path/to/model/Qwen2.5-14B-Instruct",
                    messages=[
                        {"role": "system", "content": "你是一个翻译助手。请将用户输入的中文翻译成英文。只返回英文翻译，不要包含其他内容。"},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1
                )
                translated_text = response.choices[0].message.content.strip()
                text = translated_text
            except Exception as e:
                print(f"Translation failed: {e}")

        # CLIP 向量化
        text_token = clip.tokenize(text[:77], truncate=True).to(device)
        
        with torch.no_grad():
            text_embed = model.encode_text(text_token)
            text_embed = text_embed / text_embed.norm(dim=-1, keepdim=True)
            
            # 计算相似度
            similarities = torch.einsum("jk,ijk->ij", text_embed, embeddings_tensor)
            idx = torch.argmax(similarities, dim=0)
            idx_value = idx.item()
            
        retrieved_doc = data[idx_value]['output']
        title = data[idx_value].get('instruction', 'Document')
        score = float(similarities[idx_value].item())
        
        return {
            "document": retrieved_doc,
            "title": title,
            "score": score,
            "id": str(idx_value)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 3. Prompt 设计详解

Prompt 是连接 RAG 检索结果和 LLM 生成能力的关键桥梁。本项目的 Prompt 设计非常注重**格式控制**和**内容约束**。

**Prompt 模板结构：**

```text
{用户问题} Please answer based on the reference document, and translate your answer in Complete Chinese sentence by sentence.
请严格按照以下格式回答，并根据提问内容回答。如提问使用了什么工具，则只回答工具部分。如提问如何维修，请将工具和维修步骤均回答。工具和步骤数量根据参考文档中的信息确定。
回答格式：工具部分：每个工具之间使用顿号连接，不要出现json的格式。步骤部分，使用阿拉伯数字，如第1步。每行一个步骤。见下。
以下是需要的工具。
工具：{工具1}、{工具2}、{工具3}……
以下是具体实施步骤。
步骤：
- 第1步：{步骤1}
- 第2步：{步骤2}
……

Reference Document: {参考文档内容}
```

**设计意图解析：**

1.  **基准约束 (`Please answer based on the reference document`)**: 强制模型仅使用提供的参考文档作为知识来源，减少幻觉。
2.  **语言控制 (`translate your answer in Complete Chinese`)**: 确保即使参考文档或模型内部思维是英文，最终输出也必须是中文。
3.  **结构化输出**:
    -   明确区分“工具”和“步骤”部分。
    -   规定了具体的标点符号（顿号）和列表格式（`- 第1步：`）。
    -   这种严格的格式使得输出结果不仅易于阅读，也便于后续可能的程序化解析。
4.  **按需回答**: 指令中包含“如提问使用了什么工具，则只回答工具部分”，这赋予了模型根据用户意图裁剪内容的能力，而不是机械地复述所有文档内容。
