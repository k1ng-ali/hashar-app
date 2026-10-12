import type { FundRole, Plan } from '@/features/funds/types.ts'

export type { PlanRequest } from '@/features/admin/types.ts'

export type PlatformTab = 'requests' | 'funds'

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
