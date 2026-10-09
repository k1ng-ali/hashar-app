import type { ExpenseCategory } from '@/features/admin/types.ts'
import type { Currency } from '@/shared/lib/currency.ts'

export interface MonthlyLedgerRow {
  period: string
  income: number
  expense: number
  delta: number
  is_current: boolean
}

export interface CategoryStat {
  category: ExpenseCategory
  total: number
  percent: number
}

export interface FinancialReport {
  currency: Currency
  currencies: Currency[]
  base_currency: Currency
  monthly_rows: MonthlyLedgerRow[]
  category_stats: CategoryStat[]
  total_income: number
  total_expense: number
  net_balance: number
  rate: number
}

export interface Debtor {
  member_id: number
  user_id: number
  full_name: string
  address_unit: string | null
  phone: string | null
  debt_amount: number
  currency: Currency
  debt_months_count: number
  unpaid_periods: string[]
}

export type ExportKind = 'contributions' | 'expenses' | 'debtors'
