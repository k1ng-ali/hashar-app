import { authHttp, http } from '@/shared/api/http.ts'
import type {
  ChallengeResponse,
  DemoUser,
  LoginPayload,
  RegisterPayload,
  SmsSentResponse,
  TokenResponse,
  UpdateProfilePayload,
  User,
} from './types.ts'

// Регистрация всегда, а вход с нового устройства — с подтверждением личности (ChallengeResponse)
export const register = (payload: RegisterPayload) => authHttp.post<ChallengeResponse>('/auth/register', payload)

export const login = (payload: LoginPayload) => authHttp.post<TokenResponse | ChallengeResponse>('/auth/login', payload)

export const googleLogin = (idToken: string) => authHttp.post<TokenResponse>('/auth/google', { id_token: idToken })

// ── Подтверждение личности ──
export const sendSmsCode = (challenge: string, locale: string) =>
  authHttp.post<SmsSentResponse>('/auth/verify/sms/send', { challenge, locale })

export const verifySms = (challenge: string, code: string, newPassword: string | null) =>
  authHttp.post<TokenResponse>('/auth/verify/sms', { challenge, code, new_password: newPassword })

export const verifyGoogle = (challenge: string, idToken: string, newPassword: string | null) =>
  authHttp.post<TokenResponse>('/auth/verify/google', { challenge, id_token: idToken, new_password: newPassword })

export const forgotPassword = (login: string) => authHttp.post<ChallengeResponse>('/auth/password/forgot', { login })

export const startPasswordChange = () => http.post<ChallengeResponse>('/auth/password/change')

export const refresh = () => authHttp.post<TokenResponse>('/auth/refresh')

export const logout = () => authHttp.post<void>('/auth/logout')

export const getMe = () => http.get<User>('/auth/me')

export const updateProfile = (payload: UpdateProfilePayload) => http.patch<User>('/auth/me', payload)

// Код из SMS на новый номер +992 перед сменой телефона
export const sendPhoneCode = (phone: string, locale: string) =>
  http.post<SmsSentResponse>('/auth/me/phone/code', { phone, locale })

export const deleteAccount = (password: string | null) => http.post<void>('/auth/delete-account', { password })

// ── DEV_MODE ──
export const getDemoUsers = () => authHttp.get<DemoUser[]>('/auth/dev-users')

export const devLogin = (userId: number) => authHttp.post<TokenResponse>('/auth/dev-login', { user_id: userId })
