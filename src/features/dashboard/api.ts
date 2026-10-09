import { http } from '@/shared/api/http.ts'
import type { FundSummary, Operation, OperationsFilter, Requisite } from './types.ts'

export const getSummary = (fundId: number) => http.get<FundSummary>(`/funds/${fundId}/summary`)

export const getOperations = (fundId: number, type: OperationsFilter = 'all', limit = 10) =>
  http.get<Operation[]>(`/funds/${fundId}/operations`, { params: { type, limit } })

export const getRequisites = (fundId: number) => http.get<Requisite[]>(`/funds/${fundId}/requisites`)
