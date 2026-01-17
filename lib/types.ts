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
    status?: string
}

export interface Session {
    id: string
    title: string
    messages: Message[]
    ragResults: RagDoc[]
    createdAt: number
}