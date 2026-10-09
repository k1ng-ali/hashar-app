import { http } from '@/shared/api/http.ts'
import type { Contribution, ContributionCreate, ContributionStatus, ResidentBalance } from './types.ts'

export const listMyContributions = (fundId: number, status?: ContributionStatus) =>
  http.get<Contribution[]>(`/funds/${fundId}/contributions/my`, { params: { status, limit: 100 } })

export const getMyBalance = (fundId: number) => http.get<ResidentBalance>(`/funds/${fundId}/contributions/my/balance`)

export const createContribution = (fundId: number, payload: ContributionCreate) =>
  http.post<Contribution>(`/funds/${fundId}/contributions/`, payload)
