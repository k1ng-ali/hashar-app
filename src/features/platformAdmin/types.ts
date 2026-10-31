import type { DiscountKind, FundRole, MemberStatus, Plan } from '@/features/funds/types.ts'
import type { Currency } from '@/shared/lib/currency.ts'

export type { PlanRequest } from '@/features/admin/types.ts'
export type { DiscountKind } from '@/features/funds/types.ts'

export type PlatformTab = 'overview' | 'plans' | 'pricing' | 'requests' | 'funds' | 'users' | 'audit'

/** Председатель или администратор фонда с контактами. */
export interface FundCouncilMember {
  user_id: number
  full_name: string
  role: FundRole
  phone: string | null
  email: string | null
  address_unit: string | null
}

export interface FundAdmin {
  id: number
  name: string
  code: string
  address: string | null
  plan: Plan
  effective_plan: Plan
  plan_expires_at: string | null
  member_limit: number | null
  members_count: number
  council: FundCouncilMember[]
  created_at: string
}

export interface PlanApprove {
  months?: number | null
  member_limit?: number | null
  /** Договорная цена individual за месяц — обязательна для него. */
  monthly_price?: number | null
  admin_comment?: string | null
}

// ── Цены, скидки и промокоды ────────────────────────────────────────────

export type DiscountPlan = 'pro' | 'max'
export type DiscountState = 'active' | 'scheduled' | 'expired' | 'exhausted' | 'disabled'

export interface PlanPrice {
  plan: DiscountPlan
  price_tjs: number
  updated_at: string
}

export interface PlanDiscountPayload {
  title: string
  /** null — распродажа для всех, иначе промокод. */
  code: string | null
  kind: DiscountKind
  value: number
  plans: DiscountPlan[]
  starts_at: string | null
  ends_at: string | null
  /** На сколько оплаченных месяцев действует. null — на все в пределах срока. */
  max_months: number | null
  max_uses: number | null
  is_active: boolean
}

export interface PlanDiscount extends PlanDiscountPayload {
  id: number
  uses: number
  state: DiscountState
  created_at: string
}

export interface Pricing {
  prices: PlanPrice[]
  discounts: PlanDiscount[]
}

// ── Аналитика платформы ─────────────────────────────────────────────────

export interface PlatformTotals {
  users_total: number
  users_new_30d: number
  users_active_7d: number
  users_active_30d: number
  funds_total: number
  funds_new_30d: number
  funds_active_30d: number
  members_active: number
  pending_contributions: number
  pending_members: number
  pending_plan_requests: number
}

export interface VerificationStats {
  verified: number
  unverified: number
  google: number
  sms: number
}

export interface GrowthPoint {
  period: string
  users: number
  funds: number
  users_total: number
  funds_total: number
}

export interface MoneyPoint {
  period: string
  currency: Currency
  contributions: number
  expenses: number
}

export interface CurrencyTotal {
  currency: Currency
  contributions: number
  expenses: number
}

export interface PlatformOverview {
  totals: PlatformTotals
  verification: VerificationStats
  growth: GrowthPoint[]
  money: MoneyPoint[]
  currencies: CurrencyTotal[]
}

export interface RevenuePoint {
  period: string
  amount_tjs: number
  approvals: number
}

export interface ExpiringFund {
  id: number
  name: string
  code: string
  plan: Plan
  plan_expires_at: string
}

export interface PlatformPlans {
  distribution: { plan: Plan; funds: number }[]
  revenue: RevenuePoint[]
  revenue_total_tjs: number
  revenue_30d_tjs: number
  mrr_tjs: number
  requests: { pending: number; approved: number; rejected: number }
  expiring: ExpiringFund[]
}

export type FundSort = 'created' | 'members' | 'activity' | 'pending'

export interface FundHealthFilters {
  q: string
  plan: Plan | null
  inactive: boolean
  sort: FundSort
}

export interface FundHealth {
  id: number
  name: string
  code: string
  address: string | null
  effective_plan: Plan
  plan_expires_at: string | null
  members_active: number
  member_limit: number | null
  pending_members: number
  pending_contributions: number
  stale_contributions: number
  contributions_30d: number
  last_activity_at: string | null
  inactive: boolean
  created_at: string
}

export interface Paged<T> {
  items: T[]
  total: number
}

export type UserFilter = 'all' | 'unverified' | 'admins' | 'deleted'

export interface UserAdmin {
  id: number
  full_name: string
  phone: string | null
  email: string | null
  is_platform_admin: boolean
  verified_at: string | null
  deleted_at: string | null
  providers: string[]
  funds_count: number
  last_seen_at: string | null
  created_at: string
}

export interface UserMembership {
  fund_id: number
  fund_name: string
  role: FundRole
  status: MemberStatus
  address_unit: string | null
  joined_at: string | null
}

export interface UserDetailAdmin extends UserAdmin {
  memberships: UserMembership[]
  sessions_active: number
}

export interface AuditFilters {
  fund_id: number | null
  fund_name: string | null
  entity: string | null
}

export interface AuditEventAdmin {
  id: number
  fund_id: number | null
  fund_name: string | null
  action: string
  entity: string
  entity_id: number | null
  details: Record<string, unknown>
  actor_id: number | null
  actor_name: string | null
  created_at: string
}
