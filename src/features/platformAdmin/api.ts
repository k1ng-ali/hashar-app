import { http } from '@/shared/api/http.ts'
import type { FundAdmin, PlanApprove, PlanRequest } from './types.ts'

export const listPlanRequests = (status?: PlanRequest['status']) =>
  http.get<PlanRequest[]>('/admin/plan-requests', { params: { status } })

export const approvePlanRequest = (id: number, payload: PlanApprove) =>
  http.post<PlanRequest>(`/admin/plan-requests/${id}/approve`, payload)

export const rejectPlanRequest = (id: number, comment: string) =>
  http.post<PlanRequest>(`/admin/plan-requests/${id}/reject`, { admin_comment: comment })

export const listFunds = () => http.get<FundAdmin[]>('/admin/funds', { params: { limit: 100 } })
