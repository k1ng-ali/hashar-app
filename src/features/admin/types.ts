import type { ResidentBalance } from '@/features/contributions/types.ts'
import type { FundRole, MemberStatus, Plan } from '@/features/funds/types.ts'
import type { TargetFundCategory } from '@/features/targetFunds/types.ts'
import type { Currency } from '@/shared/lib/currency.ts'

export type AdminTab = 'verification' | 'members' | 'expenses' | 'funds' | 'accounts' | 'settings'

// ── Expenses ──
export type ExpenseCategory = 'repair' | 'electrical' | 'emergency' | 'household' | 'landscaping' | 'cctv'

export const EXPENSE_CATEGORIES: ExpenseCategory[] = [
  'household',
  'repair',
  'electrical',
  'emergency',
  'landscaping',
  'cctv',
]

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

export interface ExpenseCreate {
  title: string
  category: ExpenseCategory
  amount: number
  currency: Currency
  description: string
  receipt_images: string[]
  target_fund_id: number | null
}

// ── Members ──
export interface Member {
  id: number
  user_id: number
  full_name: string
  phone: string | null
  email: string | null
  avatar_url: string | null
  role: FundRole
  status: MemberStatus
  address_unit: string | null
  message: string | null
  joined_at: string | null
  created_at: string
  balance: ResidentBalance | null
}

// ── Target funds ──
export interface TargetFundCreate {
  title: string
  description: string
  target_amount: number
  currency: Currency
  category: TargetFundCategory
}

// ── Accounts ──
export interface RequisiteCreate {
  currency: Currency
  bank_name: string
  card_or_account_number: string
  recipient_name: string
  phone_number?: string | null
  note?: string | null
}

export interface TransferCreate {
  from_currency: Currency | null
  from_amount: number | null
  to_currency: Currency | null
  to_amount: number | null
  comment: string
}

// ── Settings ──
export interface FundSettingsUpdate {
  name?: string
  description?: string | null
  address?: string | null
  base_currency?: Currency
  monthly_rate?: number
}

// ── Plan ──
export interface PlanRequest {
  id: number
  fund_id: number
  fund_name: string
  plan: Plan
  months: number
  status: 'pending' | 'approved' | 'rejected'
  comment: string | null
  admin_comment: string | null
  requested_by_name: string | null
  reviewed_at: string | null
  created_at: string
}
