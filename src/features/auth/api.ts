import { authHttp, http } from '@/shared/api/http.ts'
import type { DemoUser, LoginPayload, RegisterPayload, TokenResponse, UpdateProfilePayload, User } from './types.ts'

export const register = (payload: RegisterPayload) => authHttp.post<TokenResponse>('/auth/register', payload)

export const login = (payload: LoginPayload) => authHttp.post<TokenResponse>('/auth/login', payload)

export const googleLogin = (idToken: string) => authHttp.post<TokenResponse>('/auth/google', { id_token: idToken })

export const refresh = () => authHttp.post<TokenResponse>('/auth/refresh')

export const logout = () => authHttp.post<void>('/auth/logout')

export const getMe = () => http.get<User>('/auth/me')

export const updateProfile = (payload: UpdateProfilePayload) => http.patch<User>('/auth/me', payload)

export const deleteAccount = (password: string | null) => http.post<void>('/auth/delete-account', { password })

// ── DEV_MODE ──
export const getDemoUsers = () => authHttp.get<DemoUser[]>('/auth/dev-users')

export const devLogin = (userId: number) => authHttp.post<TokenResponse>('/auth/dev-login', { user_id: userId })
