import type { ContributionStatus } from '@/features/contributions/types.ts'
import type { Currency } from '@/shared/lib/currency.ts'

export interface AccountSummary {
  currency: Currency
  balance: number
  month_collected: number
  month_spent: number
}

export interface FundSummary {
  base_currency: Currency
  rate: number
  current_period: string
  accounts: AccountSummary[]
  pending_count: number // чеки на проверке
  pending_members_count: number // заявки на вступление
  active_members_count: number
  debtors_count: number
}

export type OperationType = 'income' | 'expense' | 'transfer'
export type OperationsFilter = 'all' | OperationType

export interface Operation {
  id: string
  type: OperationType
  category: string
  title: string
  subtitle: string
  amount: number
  currency: Currency
  // Для перевода между счетами — списанная сторона
  counter_amount: number | null
  counter_currency: Currency | null
  status: ContributionStatus | null
  receipt_image: string | null
  created_at: string
}

export interface Requisite {
  id: number
  currency: Currency
  kind: 'card' | 'account'
  bank_name: string
  card_or_account_number: string
  recipient_name: string
  phone_number: string | null
  note: string | null
  is_active: boolean
}
