import type { Plan } from '@/features/funds/types.ts'

export type { PlanRequest } from '@/features/admin/types.ts'

export type PlatformTab = 'requests' | 'funds'

export interface FundAdmin {
  id: number
  name: string
  code: string
  plan: Plan
  effective_plan: Plan
  plan_expires_at: string | null
  member_limit: number | null
  members_count: number
  created_at: string
}

export interface PlanApprove {
  months?: number | null
  member_limit?: number | null
  admin_comment?: string | null
}
