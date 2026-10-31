import type { Contribution, ContributionStatus, ResidentBalance } from '@/features/contributions/types.ts'
import type { ExpenseCategory } from '@/features/expenses/types.ts'
import type { FundRole, MemberStatus, Plan } from '@/features/funds/types.ts'
import type { TargetFundCategory } from '@/features/targetFunds/types.ts'
import type { Currency } from '@/shared/lib/currency.ts'

export type VerificationView = 'pending' | 'history'

// ── Receipts history ──
export interface CurrencyTotal {
  currency: Currency
  amount: number
  count: number
}

export interface ContributionHistory {
  items: Contribution[]
  total_count: number
  totals: CurrencyTotal[]
}

export interface HistoryFilters {
  status: ContributionStatus | null
  currency: Currency | null
  requisite_id: number | null
  q: string
}

// ── Expenses ──
export interface ExpenseCreate {
  title: string
  category: ExpenseCategory
  amount: number
  currency: Currency
  description: string
  receipt_images: string[]
  target_fund_id: number | null
  allow_overdraft: boolean
}

// ── Members ──
export interface Member {
  id: number
  user_id: number
  full_name: string
  phone: string | null
  email: string | null
  avatar_url: string | null
  role: FundRole
  status: MemberStatus
  address_unit: string | null
  message: string | null
  joined_at: string | null
  left_at: string | null
  blocked_at: string | null
  created_at: string
  // У активных — на сегодня, у вышедших и заблокированных — на момент ухода
  balance: ResidentBalance | null
  // Возвращение или разблокировка: решение о начислениях за период отсутствия
  absence: Absence | null
}

export interface Absence {
  reason: 'left' | 'blocked'
  since: string
  from_period: string | null
  to_period: string | null
  months_count: number
  amount: number
  currency: Currency
  debt_before: number
}

// ── Target funds ──
export interface TargetFundCreate {
  title: string
  description: string
  target_amount: number
  currency: Currency
  category: TargetFundCategory
  /** Ключ загруженного фото (POST /uploads/receipt) */
  image: string | null
}

/** Правка сбора. Валюту менять нельзя; image: нет поля — фото прежнее, null — убрать, ключ — новое */
export interface TargetFundUpdate {
  title: string
  description: string
  target_amount: number
  category: TargetFundCategory
  image?: string | null
}

// ── Accounts ──
export type RequisiteKind = 'card' | 'account'

export interface RequisiteCreate {
  currency: Currency
  kind: RequisiteKind
  bank_name: string
  card_or_account_number: string
  recipient_name: string
  phone_number?: string | null
  note?: string | null
}

export interface TransferCreate {
  from_currency: Currency | null
  from_amount: number | null
  to_currency: Currency | null
  to_amount: number | null
  comment: string
  allow_overdraft: boolean
}

// ── Settings ──
export interface FundSettingsUpdate {
  name?: string
  description?: string | null
  address?: string | null
  base_currency?: Currency
  monthly_rate?: number
}

// ── Plan ──
export interface PlanRequestCreate {
  plan: Plan
  months: number
  contact: string
  comment: string | null
  promo_code: string | null
  /** Цена за месяц, которую видел председатель: изменилась — сервер вернёт 409. */
  expected_price_tjs: number | null
}

export type PromoStatus = 'none' | 'applied' | 'not_better'

/** Расчёт сервера для формы заявки — зеркало PlanQuoteOut. */
export interface PlanQuote {
  plan: Plan
  months: number
  list_price_tjs: number | null
  price_tjs: number | null
  total_tjs: number | null
  discount_label: string | null
  promo_status: PromoStatus
  /** Тот же тариф по той же цене: срок добавится к дате окончания. */
  is_extension: boolean
  carryover_tjs: number | null
  carryover_days: number | null
}

export interface PlanRequest {
  id: number
  fund_id: number
  fund_name: string
  plan: Plan
  months: number
  /** Цена за месяц на момент заявки: без скидки и к оплате. null — individual. */
  list_price_tjs: number | null
  price_tjs: number | null
  discount_label: string | null
  status: 'pending' | 'approved' | 'rejected'
  contact: string
  comment: string | null
  admin_comment: string | null
  requested_by_name: string | null
  reviewed_at: string | null
  created_at: string
  /** Ожидающая заявка на другой тариф: остаток текущего и сколько дней нового он даст. */
  carryover_tjs: number | null
  /** null — у individual цену вводит админ, дни считаются по ней. */
  carryover_days: number | null
}
