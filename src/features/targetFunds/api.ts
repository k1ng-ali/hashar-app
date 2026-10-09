import { http } from '@/shared/api/http.ts'
import type { TargetFund, TargetFundDetail } from './types.ts'

export const listTargetFunds = (fundId: number, activeOnly = false) =>
  http.get<TargetFund[]>(`/funds/${fundId}/target-funds/`, { params: { active_only: activeOnly } })

export const getTargetFund = (fundId: number, id: number) =>
  http.get<TargetFundDetail>(`/funds/${fundId}/target-funds/${id}`)
