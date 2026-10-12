// src/shared/api/http.ts
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { message } from 'ant-design-vue'
import { i18n } from '@/shared/i18n/index.ts'

// Адрес API без /api/v1: в проде https://api.hashar.app (из сборки), локально — :8000. Пустая строка — тот же домен
export const API_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? 'http://localhost:8000' : '')

// ── Токен ───────────────────────────────────────────────────────────────────
// Access-токен живёт только в памяти, refresh — в httpOnly cookie.
// Стор авторизации регистрирует колбэки, чтобы http не импортировал стор напрямую.
let accessToken: string | null = null
let onTokenRefreshed: ((token: string) => void) | null = null
let onAuthFailed: (() => void) | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export function registerAuthHandlers(handlers: { onRefreshed: (token: string) => void; onFailed: () => void }) {
  onTokenRefreshed = handlers.onRefreshed
  onAuthFailed = handlers.onFailed
}

// ── Инстансы ────────────────────────────────────────────────────────────────
export const http = axios.create({
  baseURL: `${API_URL}/api/v1`,
  withCredentials: true,
  timeout: 15000,
})

// Чистый клиент для /auth/* — без интерсепторов, чтобы не зациклить refresh
export const authHttp = axios.create({
  baseURL: `${API_URL}/api/v1`,
  withCredentials: true,
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// ── Refresh с очередью параллельных запросов ────────────────────────────────
let isRefreshing = false
let failedQueue: { resolve: (token: string) => void; reject: (error: unknown) => void }[] = []

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach(({ resolve, reject }) => (token ? resolve(token) : reject(error)))
  failedQueue = []
}

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean }

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail?: unknown }>) => {
    const original = error.config as RetryConfig | undefined

    // Сеть недоступна / таймаут
    if (!error.response) {
      message.error(i18n.global.t('errors.network'))
      return Promise.reject(error)
    }

    if (error.response.status === 401 && original && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token) => {
              original.headers.Authorization = `Bearer ${token}`
              resolve(http(original))
            },
            reject,
          })
        })
      }

      original._retry = true
      isRefreshing = true
      try {
        const { data } = await authHttp.post<{ access_token: string }>('/auth/refresh')
        setAccessToken(data.access_token)
        onTokenRefreshed?.(data.access_token)
        processQueue(null, data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return http(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        onAuthFailed?.()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    if (error.response.status >= 500) {
      message.error(i18n.global.t('errors.server'))
    }
    return Promise.reject(error)
  },
)

/** Текст ошибки из ответа FastAPI (`detail`) или общий fallback. */
export function errorDetail(error: unknown): string | null {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return null
}
