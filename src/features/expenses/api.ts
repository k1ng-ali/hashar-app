import { http } from '@/shared/api/http.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import type { Expense, ExpenseCategory } from './types.ts'

const base = (fundId: number) => `/funds/${fundId}/expenses`

export const listExpenses = (
  fundId: number,
  params: { category?: ExpenseCategory; currency?: Currency; skip?: number; limit?: number },
) => http.get<Expense[]>(`${base(fundId)}/`, { params })

export const getExpense = (fundId: number, id: number) => http.get<Expense>(`${base(fundId)}/${id}`)
