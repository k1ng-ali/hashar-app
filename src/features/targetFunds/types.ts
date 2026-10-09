import type { Contribution } from '@/features/contributions/types.ts'
import type { Currency } from '@/shared/lib/currency.ts'

export type TargetFundCategory = 'security' | 'landscaping' | 'major_repair' | 'infrastructure'

export const TARGET_FUND_CATEGORIES: TargetFundCategory[] = ['landscaping', 'security', 'major_repair', 'infrastructure']

export interface TargetFund {
  id: number
  title: string
  description: string
  target_amount: number
  currency: Currency
  category: TargetFundCategory
  is_active: boolean
  collected_amount: number
  remaining_amount: number
  percent: number
  contributors_count: number
  created_at: string
}

export interface MonthAmount {
  period: string
  amount: number
}

export interface TargetFundDetail extends TargetFund {
  average_contribution: number
  monthly: MonthAmount[]
  contributions: Contribution[]
}
