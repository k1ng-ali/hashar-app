import type { FundRole } from '@/features/funds/types.ts'
import type { Currency } from '@/shared/lib/currency.ts'

export type AnnouncementCategory = 'news' | 'meeting' | 'emergency' | 'cleanup' | 'finance'

// finance создаётся автоматически при переводах между счетами — вручную выбрать нельзя
export const ANNOUNCEMENT_CATEGORIES: AnnouncementCategory[] = ['news', 'meeting', 'emergency', 'cleanup']
export const ANNOUNCEMENT_FILTERS: AnnouncementCategory[] = [...ANNOUNCEMENT_CATEGORIES, 'finance']

export interface AccountTransfer {
  id: number
  from_currency: Currency | null
  from_amount: number | null
  to_currency: Currency | null
  to_amount: number | null
  comment: string
  created_by_name: string | null
  created_at: string
}

export interface AnnouncementComment {
  id: number
  user_id: number
  user_name: string
  user_unit: string | null
  text: string
  created_at: string
}

export interface Announcement {
  id: number
  title: string
  content: string
  category: AnnouncementCategory
  is_pinned: boolean
  author_id: number
  author_name: string
  author_role: FundRole | null
  likes_count: number
  is_liked: boolean
  comments: AnnouncementComment[]
  transfer: AccountTransfer | null
  created_at: string
}

export interface AnnouncementCreate {
  title: string
  content: string
  category: AnnouncementCategory
  is_pinned: boolean
}
