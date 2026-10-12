import { http } from '@/shared/api/http.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import type { Debtor, ExportKind, FinancialReport } from './types.ts'

export const getFinancialReport = (fundId: number, currency?: Currency, months = 6) =>
  http.get<FinancialReport>(`/funds/${fundId}/reports/financial`, { params: { currency, months } })

export const listDebtors = (fundId: number) => http.get<Debtor[]>(`/funds/${fundId}/reports/debtors`)

// Реестры с именами и телефонами участников выгружает только совет
export const exportCsv = (fundId: number, kind: ExportKind) =>
  http.get<Blob>(`/council/funds/${fundId}/reports/export/${kind}`, { responseType: 'blob' })
