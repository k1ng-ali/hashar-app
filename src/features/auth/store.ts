// src/features/auth/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { registerAuthHandlers, setAccessToken } from '@/shared/api/http.ts'
import { IS_DEV_MODE } from '@/shared/lib/env.ts'
import { router } from '@/app/router.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import * as api from './api.ts'
import type {
  ChallengeResponse,
  DemoUser,
  LoginPayload,
  RegisterPayload,
  TokenResponse,
  UpdateProfilePayload,
  User,
} from './types.ts'

export const useAuthStore = defineStore('auth', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const demoUsers = ref<DemoUser[]>([])
  const isSubmitting = ref(false)
  // Ждёт подтверждения личности: вход с нового устройства, новый аккаунт или смена пароля
  const challenge = ref<ChallengeResponse | null>(null)
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

  // challenge не трогаем: «сессия кончилась» (например, 401 у фонового запроса) не должна
  // сбивать начатое подтверждение — его сбрасывают страницы входа и смены пароля
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

  /** true — вошли; false — сервер ждёт подтверждения личности (challenge). */
  async function startAuth(action: () => Promise<{ data: TokenResponse | ChallengeResponse }>) {
    isSubmitting.value = true
    try {
      const { data } = await action()
      if ('challenge' in data) {
        challenge.value = data
        return false
      }
      applyToken(data)
      return true
    } finally {
      isSubmitting.value = false
    }
  }

  const login = (payload: LoginPayload) => startAuth(() => api.login(payload))
  const register = (payload: RegisterPayload) => startAuth(() => api.register(payload))
  const forgotPassword = (loginValue: string) => startAuth(() => api.forgotPassword(loginValue))
  const startPasswordChange = () => startAuth(() => api.startPasswordChange())

  // ── Подтверждение личности ──
  function requireChallenge(): string {
    if (!challenge.value) throw new Error('No verification in progress')
    return challenge.value.challenge
  }

  async function sendSmsCode(locale: string) {
    const { data } = await api.sendSmsCode(requireChallenge(), locale)
    return data
  }

  // challenge после успеха сбрасывает страница (cancelChallenge): иначе шаг подтверждения
  // размонтируется раньше, чем успеет сообщить об успехе
  const verifySms = (code: string, newPassword: string | null) =>
    withSubmitting(() => api.verifySms(requireChallenge(), code, newPassword))
  const verifyGoogle = (idToken: string, newPassword: string | null) =>
    withSubmitting(() => api.verifyGoogle(requireChallenge(), idToken, newPassword))

  function cancelChallenge() {
    challenge.value = null
  }

  const googleLogin = (idToken: string) => withSubmitting(() => api.googleLogin(idToken))
  const devLogin = (userId: number) => withSubmitting(() => api.devLogin(userId))

  async function updateProfile(payload: UpdateProfilePayload) {
    const { data } = await api.updateProfile(payload)
    user.value = data
  }

  async function sendPhoneCode(phone: string, locale: string) {
    const { data } = await api.sendPhoneCode(phone, locale)
    return data
  }

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

  /** Удаление аккаунта с обезличиванием (подтверждение паролем, если он есть). Сессия на сервере уже удалена. */
  async function deleteAccount(password: string | null) {
    await api.deleteAccount(password)
    clear()
    await router.replace('/login')
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
    challenge,
    isAuthenticated,
    isPlatformAdmin,
    bootstrap,
    login,
    register,
    forgotPassword,
    startPasswordChange,
    sendSmsCode,
    verifySms,
    verifyGoogle,
    cancelChallenge,
    googleLogin,
    updateProfile,
    sendPhoneCode,
    fetchDemoUsers,
    devLogin,
    logout,
    deleteAccount,
  }
})
