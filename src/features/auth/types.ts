import type { FundRole } from '@/features/funds/types.ts'

export interface User {
  id: number
  full_name: string
  phone: string | null
  email: string | null
  avatar_url: string | null
  is_platform_admin: boolean
  // Без пароля — аккаунт только с входом через Google
  has_password: boolean
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
  phone: string // по нему подтверждается личность
  email: string | null
  password: string
}

// ── Подтверждение личности ──
export type VerificationMethod = 'sms' | 'google'

/** Сессии ещё нет: нужно подтвердить личность (новое устройство, новый аккаунт, смена пароля). */
export interface ChallengeResponse {
  challenge: string
  purpose: 'login' | 'password' // password — вместе с подтверждением задаётся новый пароль
  methods: VerificationMethod[]
  phone_hint: string | null // «+992 ••• •• 67» — куда уйдёт SMS
}

export interface SmsSentResponse {
  phone_hint: string
  resend_after: number // секунд до повторной отправки
  expires_in: number
}

export interface UpdateProfilePayload {
  phone: string | null // null — убрать телефон
  code?: string // код из SMS — обязателен для нового номера +992
}
