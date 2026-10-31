import type { NoticeAdmin } from '@/features/notices/types.ts'
import { http } from '@/shared/api/http.ts'
import type {
  AuditEventAdmin,
  AuditFilters,
  DiscountPlan,
  FundAdmin,
  FundHealth,
  FundHealthFilters,
  Paged,
  PlanApprove,
  PlanDiscount,
  PlanDiscountPayload,
  PlanPrice,
  PlanRequest,
  PlatformOverview,
  PlatformPlans,
  Pricing,
  UserAdmin,
  UserDetailAdmin,
  UserFilter,
} from './types.ts'

export const PAGE_SIZE = 30

export const listPlanRequests = (status?: PlanRequest['status']) =>
  http.get<PlanRequest[]>('/admin/plan-requests', { params: { status } })

export const approvePlanRequest = (id: number, payload: PlanApprove) =>
  http.post<PlanRequest>(`/admin/plan-requests/${id}/approve`, payload)

export const rejectPlanRequest = (id: number, comment: string) =>
  http.post<PlanRequest>(`/admin/plan-requests/${id}/reject`, { admin_comment: comment })

export const listFunds = () => http.get<FundAdmin[]>('/admin/funds', { params: { limit: 100 } })

// ── Цены, скидки и промокоды ──────────────────────────────────────────────

export const getPricing = () => http.get<Pricing>('/admin/pricing/')

export const setPlanPrice = (plan: DiscountPlan, price: number) =>
  http.put<PlanPrice>(`/admin/pricing/prices/${plan}`, { price_tjs: price })

export const createDiscount = (payload: PlanDiscountPayload) =>
  http.post<PlanDiscount>('/admin/pricing/discounts', payload)

export const updateDiscount = (id: number, payload: PlanDiscountPayload) =>
  http.put<PlanDiscount>(`/admin/pricing/discounts/${id}`, payload)

export const deleteDiscount = (id: number) => http.delete<void>(`/admin/pricing/discounts/${id}`)

// ── Аналитика ─────────────────────────────────────────────────────────────

export const getOverview = (months = 12) =>
  http.get<PlatformOverview>('/admin/analytics/overview', { params: { months } })

export const getPlansStats = (months = 12) =>
  http.get<PlatformPlans>('/admin/analytics/plans', { params: { months } })

export const listFundHealth = (filters: FundHealthFilters, skip = 0, limit = PAGE_SIZE) =>
  http.get<Paged<FundHealth>>('/admin/analytics/funds', {
    params: {
      q: filters.q || undefined,
      plan: filters.plan ?? undefined,
      inactive: filters.inactive || undefined,
      sort: filters.sort,
      skip,
      limit,
    },
  })

export const listUsers = (q: string, filter: UserFilter, skip = 0, limit = PAGE_SIZE) =>
  http.get<Paged<UserAdmin>>('/admin/users', { params: { q: q || undefined, filter, skip, limit } })

export const getUser = (id: number) => http.get<UserDetailAdmin>(`/admin/users/${id}`)

export const listAudit = (filters: AuditFilters, skip = 0, limit = PAGE_SIZE) =>
  http.get<AuditEventAdmin[]>('/admin/audit', {
    params: { fund_id: filters.fund_id ?? undefined, entity: filters.entity ?? undefined, skip, limit },
  })

// ── Уведомления совету фонда ──────────────────────────────────────────────

export const sendNotice = (fundId: number, text: string) =>
  http.post<NoticeAdmin>(`/admin/funds/${fundId}/notices`, { text })

export const listSentNotices = (fundId: number) =>
  http.get<NoticeAdmin[]>('/admin/notices', { params: { fund_id: fundId, limit: 20 } })
