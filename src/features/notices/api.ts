import { http } from '@/shared/api/http.ts'
import type { NoticeList } from './types.ts'

export const listNotices = (fundId: number) => http.get<NoticeList>(`/council/funds/${fundId}/notices/`)

export const markNoticesRead = (fundId: number) => http.post<void>(`/council/funds/${fundId}/notices/read`)
