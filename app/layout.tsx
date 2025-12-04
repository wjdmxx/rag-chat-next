import type { Metadata } from 'next'
import './globals.css'
import { cn } from '@/lib/utils'


export const metadata: Metadata = {
    title: 'RAG Chat • Next.js Starter',
    description: 'Beautiful chat UI + RAG panel (mocked APIs).'
}


export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body className={cn('min-h-screen antialiased bg-white text-zinc-900 dark:bg-zinc-950 dark:text-zinc-50')}>
                {/* background accents */}
                <div className="pointer-events-none fixed inset-0 -z-10">
                    <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-brand-400/30 blur-3xl" />
                    <div className="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-indigo-400/20 blur-3xl" />
                    <div className="absolute inset-0 bg-grid" />
                </div>
                {children}
            </body>
        </html>
    )
}