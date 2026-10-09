import { http } from '@/shared/api/http.ts'
import type { AccountTransfer } from '@/features/announcements/types.ts'
import type { Contribution, ContributionStatus } from '@/features/contributions/types.ts'
import type { Requisite } from '@/features/dashboard/types.ts'
import type { Account, FundInfo, FundRole, MemberStatus, Plan } from '@/features/funds/types.ts'
import type { TargetFund } from '@/features/targetFunds/types.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import type {
  Expense,
  ExpenseCreate,
  FundSettingsUpdate,
  Member,
  PlanRequest,
  RequisiteCreate,
  TargetFundCreate,
  TransferCreate,
} from './types.ts'

// Управление фондом — /council/funds/{fundId}/...
const council = (fundId: number) => `/council/funds/${fundId}`

// ── Contributions ──
export const listContributions = (fundId: number, status?: ContributionStatus) =>
  http.get<Contribution[]>(`${council(fundId)}/contributions/`, { params: { status, limit: 100 } })

export const approveContribution = (fundId: number, id: number) =>
  http.post<Contribution>(`${council(fundId)}/contributions/${id}/approve`, { comment_admin: null })

export const rejectContribution = (fundId: number, id: number, reason: string) =>
  http.post<Contribution>(`${council(fundId)}/contributions/${id}/reject`, { comment_admin: reason })

// ── Members ──
export const listMembers = (fundId: number) => http.get<Member[]>(`${council(fundId)}/members/`)

export const approveMember = (fundId: number, id: number) => http.post(`${council(fundId)}/members/${id}/approve`)

export const rejectMember = (fundId: number, id: number) => http.post(`${council(fundId)}/members/${id}/reject`)

export const updateMemberStatus = (fundId: number, id: number, status: MemberStatus) =>
  http.patch(`${council(fundId)}/members/${id}/status`, { status })

export const updateMemberRole = (fundId: number, id: number, role: FundRole) =>
  http.patch(`${council(fundId)}/members/${id}/role`, { role })

export const transferChairman = (fundId: number, memberId: number) =>
  http.post(`${council(fundId)}/members/transfer-chairman`, { member_id: memberId })

// ── Expenses ──
export const listExpenses = (fundId: number) => http.get<Expense[]>(`/funds/${fundId}/expenses/`, { params: { limit: 100 } })

export const createExpense = (fundId: number, payload: ExpenseCreate) =>
  http.post<Expense>(`${council(fundId)}/expenses/`, payload)

export const deleteExpense = (fundId: number, id: number) => http.delete<void>(`${council(fundId)}/expenses/${id}`)

// ── Target funds ──
export const createTargetFund = (fundId: number, payload: TargetFundCreate) =>
  http.post<TargetFund>(`${council(fundId)}/target-funds/`, payload)

export const toggleTargetFund = (fundId: number, id: number) =>
  http.post<TargetFund>(`${council(fundId)}/target-funds/${id}/toggle`)

export const deleteTargetFund = (fundId: number, id: number) => http.delete<void>(`${council(fundId)}/target-funds/${id}`)

// ── Accounts & transfers ──
export const enableAccount = (fundId: number, currency: Currency) =>
  http.post<Account[]>(`${council(fundId)}/accounts`, { currency })

export const disableAccount = (fundId: number, currency: Currency) =>
  http.post<Account[]>(`${council(fundId)}/accounts/${currency}/disable`)

export const listTransfers = (fundId: number) => http.get<AccountTransfer[]>(`${council(fundId)}/transfers/`)

export const createTransfer = (fundId: number, payload: TransferCreate) =>
  http.post<AccountTransfer>(`${council(fundId)}/transfers/`, payload)

// ── Requisites ──
export const listRequisites = (fundId: number) => http.get<Requisite[]>(`${council(fundId)}/requisites`)

export const createRequisite = (fundId: number, payload: RequisiteCreate) =>
  http.post<Requisite>(`${council(fundId)}/requisites`, payload)

export const toggleRequisite = (fundId: number, id: number) =>
  http.post<Requisite>(`${council(fundId)}/requisites/${id}/toggle`)

export const deleteRequisite = (fundId: number, id: number) => http.delete<void>(`${council(fundId)}/requisites/${id}`)

// ── Settings & plan ──
export const updateSettings = (fundId: number, payload: FundSettingsUpdate) =>
  http.patch<FundInfo>(`${council(fundId)}/settings`, payload)

export const listPlanRequests = (fundId: number) => http.get<PlanRequest[]>(`${council(fundId)}/plan-requests/`)

export const createPlanRequest = (fundId: number, plan: Plan, months: number, comment: string | null) =>
  http.post<PlanRequest>(`${council(fundId)}/plan-requests/`, { plan, months, comment })
