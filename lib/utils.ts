import { type ClassValue } from 'clsx'
import clsx from 'clsx'


export function cn(...inputs: ClassValue[]) { return clsx(inputs) }


export const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))


export function uid(prefix = 'id'): string {
    return `${prefix}_${Math.random().toString(36).slice(2, 10)}`
}