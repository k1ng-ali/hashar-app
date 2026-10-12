// src/features/auth/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { registerAuthHandlers, setAccessToken } from '@/shared/api/http.ts'
import { IS_DEV_MODE } from '@/shared/lib/env.ts'
import { router } from '@/app/router.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import * as api from './api.ts'
import type { DemoUser, LoginPayload, RegisterPayload, TokenResponse, User } from './types.ts'

export const useAuthStore = defineStore('auth', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const demoUsers = ref<DemoUser[]>([])
  const isSubmitting = ref(false)
  let bootstrapPromise: Promise<void> | null = null

  // ── Getters ───────────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!user.value && !!accessToken.value)
  const isPlatformAdmin = computed(() => !!user.value?.is_platform_admin)

  // ── Actions ───────────────────────────────────────────────────────────
  function applyToken(data: TokenResponse) {
    // Другой пользователь — фонды предыдущего не должны «протечь»
    if (user.value?.id !== data.user.id) useFundsStore().reset()
    accessToken.value = data.access_token
    user.value = data.user
    setAccessToken(data.access_token)
  }

  function clear() {
    useFundsStore().reset()
    accessToken.value = null
    user.value = null
    setAccessToken(null)
  }

  /** Восстанавливает сессию по refresh-cookie. Вызывается один раз при старте. */
  function bootstrap(): Promise<void> {
    if (!bootstrapPromise) {
      bootstrapPromise = api
        .refresh()
        .then(({ data }) => applyToken(data))
        .catch(() => clear())
    }
    return bootstrapPromise
  }

  async function withSubmitting(action: () => Promise<{ data: TokenResponse }>) {
    isSubmitting.value = true
    try {
      const { data } = await action()
      applyToken(data)
    } finally {
      isSubmitting.value = false
    }
  }

  const login = (payload: LoginPayload) => withSubmitting(() => api.login(payload))
  const register = (payload: RegisterPayload) => withSubmitting(() => api.register(payload))
  const devLogin = (userId: number) => withSubmitting(() => api.devLogin(userId))

  async function fetchDemoUsers() {
    if (!IS_DEV_MODE) return
    const { data } = await api.getDemoUsers()
    demoUsers.value = data
  }

  async function logout() {
    try {
      await api.logout()
    } finally {
      clear()
      await router.replace('/login')
    }
  }

  // http-интерсептор сообщает о новом токене или о провале refresh
  registerAuthHandlers({
    onRefreshed: (token) => {
      accessToken.value = token
    },
    onFailed: () => {
      clear()
      void router.replace('/login')
    },
  })

  return {
    user,
    accessToken,
    demoUsers,
    isSubmitting,
    isAuthenticated,
    isPlatformAdmin,
    bootstrap,
    login,
    register,
    fetchDemoUsers,
    devLogin,
    logout,
  }
})
