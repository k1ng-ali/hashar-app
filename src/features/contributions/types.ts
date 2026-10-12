import type { Currency } from '@/shared/lib/currency.ts'

export type ContributionStatus = 'pending' | 'approved' | 'rejected'
export type ContributionCategory = 'monthly_fee' | 'target_fund'
export type BalanceStatus = 'ok' | 'debt' | 'advance'

export interface Contribution {
  id: number
  user_id: number
  user_name: string
  user_unit: string | null
  amount: number
  currency: Currency
  /** Сколько зачтено в счёт назначения: в базовой валюте (взнос) или валюте сбора. */
  credited_amount: number
  credited_currency: Currency
  requisite_id: number | null
  /** Снимок реквизита: «банк · номер · получатель». */
  requisite_label: string | null
  category: ContributionCategory
  target_fund_id: number | null
  target_fund_title: string | null
  billing_period: string | null
  /** null — чек чужой: участник видит только свои чеки, совет — все. */
  receipt_image: string | null
  status: ContributionStatus
  comment_user: string | null
  comment_admin: string | null
  reviewed_by_name: string | null
  reviewed_at: string | null
  created_at: string
}

export interface ContributionCreate {
  requisite_id: number
  amount: number
  /** Обязательно при оплате не в валюте назначения. */
  credited_amount?: number | null
  category: ContributionCategory
  target_fund_id?: number | null
  billing_period?: string | null
  receipt_image: string
  comment_user?: string | null
}

export interface ResidentBalance {
  status: BalanceStatus
  currency: Currency
  rate: number
  next_rate: number
  balance: number
  total_due: number
  total_paid: number
  pending_amount: number
  has_pending: boolean
  paid_months_count: number
  paid_until_period: string | null
  debt_amount: number
  debt_months_count: number
  advance_amount: number
  advance_months_count: number
  covered_periods: string[]
  unpaid_periods: string[]
  current_period: string
  next_billing_period: string
}
