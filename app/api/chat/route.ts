import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

// 生成模型客户端 (8000)
const client = new OpenAI({
    apiKey: "EMPTY",
    baseURL: "http://localhost:8000/v1",
})

export async function POST(req: NextRequest) {
    try {
        const { messages } = await req.json()
        const lastMessage = messages[messages.length - 1]
        const userText = lastMessage.content

        // 1. 调用 RAG Service (8003)
        let referenceDoc = ""
        let ragResult = null
        let ragMatched = false

        try {
            const ragRes = await fetch("http://127.0.0.1:8003/retrieve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: userText })
            })

            if (ragRes.ok) {
                const ragData = await ragRes.json()
                ragMatched = ragData.matched === true

                if (ragMatched) {
                    referenceDoc = ragData.document
                    ragResult = {
                        id: ragData.id,
                        title: ragData.title,
                        snippet: ragData.document,
                        score: ragData.score,
                        url: "",
                        status: ragData.status
                    }
                }
                console.log("RAG result:", ragMatched ? "Matched" : "Not matched", ragData.status)
            } else {
                console.warn("RAG service returned error:", await ragRes.text())
            }
        } catch (e) {
            console.warn("Failed to connect to RAG service (is it running?):", e)
        }

        let reply: string

        if (ragMatched && referenceDoc) {
            // 找到匹配内容，使用参考文档生成回答（来自 rag-v2.py 的 prompt）
            const promptContent = `
请根据以下参考文档生成回答：
1. 参考文档风格和结构为示例。
2. 输出回答时，请遵循参考文档的格式和步骤编号。
3. 所有工具名称请翻译为中文。
4. 回答每一句话都翻译成中文（中英文逐句对应）。
5. 避免重复句子或冗余说明，若某些安全或注意事项在多个步骤重复，可仅说明一次并在后续步骤引用。
7. 限制输出内容的长度，应在800字以内。
6. 生成内容的主题为：${userText}

参考文档：
${referenceDoc}
`

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

            reply = response.choices[0].message.content || ""
        } else {
            // 未找到匹配内容，生成拒绝回答（来自 rag-v2.py 的 prompt）
            const rejectPrompt = `
用户提问${userText}。 请结合用户的提问内容生成一段文字，意思是非常抱歉，当前用户的提问内容超出了我的知识范围，无法给出准确的恢复。除了这句话外不要生成任何其它内容。
`

            const response = await client.chat.completions.create({
                model: "/mnt/bit/wxc/projects/zhongche-llm/Qwen2.5-14B-Instruct",
                messages: [
                    { role: "system", content: "You are a helpful assistant." },
                    {
                        role: "user",
                        content: rejectPrompt
                    },
                ],
                max_tokens: 1000
            })

            reply = response.choices[0].message.content || "抱歉，当前问题超出了我的知识范围，无法给出准确的回复。"
        }

        // 返回回复和 RAG 结果
        return NextResponse.json({ reply, rag: ragResult ? [ragResult] : [] })

    } catch (error) {
        console.error("Error calling LLM:", error)
        return NextResponse.json({ reply: "抱歉，系统暂时无法响应，请稍后再试。" }, { status: 500 })
    }
}