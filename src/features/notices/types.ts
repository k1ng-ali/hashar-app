import type { Plan } from '@/features/funds/types.ts'

export type NoticeKind =
  | 'admin_message'
  | 'plan_rejected'
  | 'plan_approved'
  | 'plan_expiring'
  | 'plan_expired'
  | 'plan_lapsed'

/** Данные системного уведомления — текст собирается по kind на фронтенде. */
export interface NoticeDetails {
  plan?: Plan
  months?: number
  reason?: string | null
  comment?: string | null
  expires_at?: string | null
  blocks_at?: string | null
  will_block?: boolean
}

export interface Notice {
  id: number
  kind: NoticeKind
  text: string | null
  details: NoticeDetails
  is_unread: boolean
  created_at: string
}

export interface NoticeList {
  items: Notice[]
  unread: number
}

export interface NoticeAdmin extends Notice {
  fund_id: number
  fund_name: string
  author_name: string | null
}
