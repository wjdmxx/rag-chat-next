import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const client = new OpenAI({
    apiKey: "EMPTY",
    baseURL: "http://localhost:8000/v1",
})

export async function POST(req: NextRequest) {
    try {
        const { messages } = await req.json()
        const lastMessage = messages[messages.length - 1]
        const userText = lastMessage.content

        // 1. Call RAG Service
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
                    snippet: ragData.document, // Full content for display
                    score: ragData.score,
                    url: ""
                }
            } else {
                console.warn("RAG service returned error:", await ragRes.text())
            }
        } catch (e) {
            console.warn("Failed to connect to RAG service (is it running?):", e)
        }

        // 2. Construct Prompt
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

        // 3. Call LLM
        const response = await client.chat.completions.create({
            model: "/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct",
            messages: [
                { role: "system", content: "You are a helpful assistant." },
                {
                    role: "user",
                    content: promptContent
                },
            ],
            max_tokens: 50000
        })

        const reply = response.choices[0].message.content

        // Return reply AND the rag result
        return NextResponse.json({ reply, rag: ragResult ? [ragResult] : [] })

    } catch (error) {
        console.error("Error calling LLM:", error)
        return NextResponse.json({ reply: "抱歉，系统暂时无法响应，请稍后再试。" }, { status: 500 })
    }
}