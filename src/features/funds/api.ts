import { http } from '@/shared/api/http.ts'
import type { FundCreate, FundInfo, FundPublic, JoinPayload, MyFund, PlanOption } from './types.ts'

export const listMyFunds = () => http.get<MyFund[]>('/funds/my')

export const searchFunds = (q: string) => http.get<FundPublic[]>('/funds/search', { params: { q } })

export const getFundByCode = (code: string) => http.get<FundPublic>(`/funds/by-code/${encodeURIComponent(code)}`)

export const createFund = (payload: FundCreate) => http.post<FundInfo>('/funds/', payload)

export const joinFund = (fundId: number, payload: JoinPayload) => http.post<void>(`/funds/${fundId}/join`, payload)

export const cancelJoin = (fundId: number) => http.delete<void>(`/funds/${fundId}/join`)

export const getFund = (fundId: number) => http.get<FundInfo>(`/funds/${fundId}`)

export const leaveFund = (fundId: number) => http.post<void>(`/funds/${fundId}/leave`)

export const listPlans = () => http.get<PlanOption[]>('/funds/plans')
