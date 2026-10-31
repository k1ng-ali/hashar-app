import type { Currency } from '@/shared/lib/currency.ts'

export type FundRole = 'resident' | 'admin' | 'chairman'
export type MemberStatus = 'pending' | 'active' | 'rejected' | 'blocked' | 'left'
export type Plan = 'free' | 'pro' | 'max' | 'individual'

export interface Account {
  currency: Currency
  is_active: boolean
  balance: number
}

export interface PlanInfo {
  plan: Plan
  effective_plan: Plan
  expires_at: string | null
  member_limit: number | null
  members_count: number
  price_tjs: number | null
  /** Стоимость неиспользованного остатка — при смене тарифа перейдёт в дни нового. */
  remaining_tjs: number | null
  /** После окончания платного тарифа: grace — 7 дней льготы, lapsed — тариф не продлён. */
  lapse: PlanLapse
  /** С этого момента взносы жителей блокируются, если тариф не продлят. */
  blocks_at: string | null
  /** Активных участников больше, чем позволяет Free. */
  over_free_limit: boolean
  /** Взносы жителей сейчас заблокированы. */
  contributions_blocked: boolean
  /** Может ли текущий пользователь внести взнос. */
  can_contribute: boolean
}

export type PlanLapse = 'none' | 'grace' | 'lapsed'

/** Запись истории тарифа: действует с period до следующей записи. */
export interface Rate {
  period: string
  amount: number
}

export type DiscountKind = 'percent' | 'fixed'

/** Распродажа на витрине тарифов. */
export interface PlanSale {
  title: string
  kind: DiscountKind
  value: number
  ends_at: string | null
}

export interface PlanOption {
  plan: Plan
  member_limit: number | null
  /** К оплате за месяц с учётом распродажи. null — по договорённости. */
  price_tjs: number | null
  /** Без скидки. */
  list_price_tjs: number | null
  sale: PlanSale | null
}

/** Карточка фонда для участника — зеркало FundOut. */
export interface FundInfo {
  id: number
  name: string
  description: string | null
  address: string | null
  code: string
  base_currency: Currency
  /** Тариф текущего месяца. */
  monthly_rate: number
  /** Запланированный тариф — вступит в силу с 1-го числа next_rate_period. */
  next_monthly_rate: number | null
  next_rate_period: string | null
  rate_history: Rate[]
  start_period: string
  /** Базовая валюта и начало расчётов заблокированы — уже есть ежемесячные взносы. */
  setup_locked: boolean
  accounts: Account[]
  plan: PlanInfo
  my_role: FundRole
  created_at: string
}

export interface MyFund {
  id: number
  name: string
  address: string | null
  code: string
  base_currency: Currency
  role: FundRole
  status: MemberStatus
  address_unit: string | null
}

export interface FundPublic {
  id: number
  name: string
  address: string | null
  code: string
  members_count: number
  my_status: MemberStatus | null
}

export interface FundCreate {
  name: string
  description: string | null
  address: string | null
  base_currency: Currency
  currencies: Currency[]
  monthly_rate: number
  address_unit: string | null
}

export interface JoinPayload {
  address_unit: string
  message: string | null
}

/** Права в UI — зеркало require_fund_council / require_fund_chairman на бэкенде. */
export interface FundPermissions {
  isCouncil: boolean
  isChairman: boolean
  canManageMembers: boolean
  canChangeRoles: boolean
  canManageFinance: boolean
  canDeleteRecords: boolean
  canManageSettings: boolean
  canPinAnnouncements: boolean
}
