import type { Currency } from '@/shared/lib/currency.ts'

export type ExpenseCategory = 'repair' | 'electrical' | 'emergency' | 'household' | 'landscaping' | 'cctv'

export const EXPENSE_CATEGORIES: ExpenseCategory[] = [
  'household',
  'repair',
  'electrical',
  'emergency',
  'landscaping',
  'cctv',
]

/** Иконка категории в ленте расходов. */
export const EXPENSE_CATEGORY_ICONS: Record<ExpenseCategory, string> = {
  household: '🧹',
  repair: '🛠️',
  electrical: '💡',
  emergency: '🚨',
  landscaping: '🌳',
  cctv: '📹',
}

/** Расход фонда — зеркало ExpenseOut. */
export interface Expense {
  id: number
  title: string
  category: ExpenseCategory
  amount: number
  currency: Currency
  description: string
  receipt_images: string[]
  target_fund_id: number | null
  target_fund_title: string | null
  created_by_name: string | null
  created_at: string
}

export type ExpensesFilter = 'all' | ExpenseCategory
