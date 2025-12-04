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