import type { FundRole } from '@/features/funds/types.ts'

export interface User {
  id: number
  full_name: string
  phone: string | null
  email: string | null
  avatar_url: string | null
  is_platform_admin: boolean
  created_at: string
}

export interface DemoUser {
  id: number
  full_name: string
  avatar_url: string | null
  is_platform_admin: boolean
  memberships: { fund_name: string; role: FundRole }[]
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface LoginPayload {
  login: string // телефон или email
  password: string
}

export interface RegisterPayload {
  full_name: string
  phone: string | null
  email: string | null
  password: string
}

// Провайдеры входа, которые подключим позже (бэкенд: user_auth_providers)
export type AuthProvider = 'google' | 'telegram'
