<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/features/auth/store.ts'
import { IS_DEV_MODE } from '@/shared/lib/env.ts'
import { message } from 'ant-design-vue'
import DemoUserList from '@/features/auth/components/DemoUserList.vue'
import ForgotPasswordForm from '@/features/auth/components/ForgotPasswordForm.vue'
import LoginForm from '@/features/auth/components/LoginForm.vue'
import ProviderButtons from '@/features/auth/components/ProviderButtons.vue'
import RegisterForm from '@/features/auth/components/RegisterForm.vue'
import VerificationStep from '@/features/auth/components/VerificationStep.vue'
import type { DemoUser, LoginPayload, RegisterPayload } from '@/features/auth/types.ts'
import AppLogo from '@/shared/components/AppLogo.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { errorDetail } from '@/shared/api/http.ts'

type AuthMode = 'login' | 'register'
// forgot — восстановление пароля, verify — подтверждение личности (SMS или Google)
type AuthView = AuthMode | 'forgot' | 'verify'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const mode = ref<AuthMode>(route.query.mode === 'register' ? 'register' : 'login')
const isForgot = ref(false)
const errorMessage = ref('')
const view = computed<AuthView>(() => (authStore.challenge ? 'verify' : isForgot.value ? 'forgot' : mode.value))

onMounted(() => {
  void authStore.fetchDemoUsers().catch(() => undefined)
})
// Незавершённое подтверждение не переживает уход со страницы
onBeforeUnmount(() => authStore.cancelChallenge())

// Подтвердить личность нечем: SMS не настроены или номер не +992, а Google выключен
const UNAVAILABLE = 'Verification is unavailable'

// После входа возвращаемся туда, куда шли (например, ссылка-приглашение /join/CODE)
function afterAuth() {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  return router.replace(redirect.startsWith('/') ? redirect : '/')
}

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleLogin(payload: LoginPayload) {
  errorMessage.value = ''
  try {
    if (await authStore.login(payload)) await afterAuth()
  } catch (error) {
    const detail = errorDetail(error)
    errorMessage.value =
      detail === 'Too many attempts, try later'
        ? t('auth.tooManyAttempts')
        : detail === UNAVAILABLE
          ? t('auth.verify.unavailable')
          : t('auth.invalid')
  }
}

async function handleRegister(payload: RegisterPayload) {
  errorMessage.value = ''
  try {
    // Регистрация всегда ведёт к подтверждению личности
    await authStore.register(payload)
  } catch (error) {
    const detail = errorDetail(error)
    errorMessage.value =
      detail === 'Phone or email is already registered'
        ? t('auth.alreadyRegistered')
        : detail === UNAVAILABLE
          ? t('auth.verify.unavailable')
          : t('errors.generic')
  }
}

async function handleForgot(login: string) {
  errorMessage.value = ''
  try {
    await authStore.forgotPassword(login)
    isForgot.value = false
  } catch (error) {
    const detail = errorDetail(error)
    errorMessage.value =
      detail === 'User not found'
        ? t('auth.forgot.notFound')
        : detail === 'Too many attempts, try later'
          ? t('auth.tooManyAttempts')
          : detail === UNAVAILABLE
            ? t('auth.verify.unavailable')
            : t('errors.generic')
  }
}

async function handleVerified(purpose: 'login' | 'password') {
  if (purpose === 'password') message.success(t('auth.verify.passwordChanged'))
  await afterAuth()
}

function handleVerifyCancel() {
  authStore.cancelChallenge()
  errorMessage.value = ''
}

async function handleGoogle(idToken: string) {
  errorMessage.value = ''
  try {
    await authStore.googleLogin(idToken)
    await afterAuth()
  } catch (error) {
    errorMessage.value =
      errorDetail(error) === 'Too many attempts, try later' ? t('auth.tooManyAttempts') : t('auth.googleFailed')
  }
}

function handleGoogleError() {
  errorMessage.value = t('auth.googleFailed')
}

async function handleDemo(user: DemoUser) {
  errorMessage.value = ''
  try {
    await authStore.devLogin(user.id)
    await afterAuth()
  } catch {
    errorMessage.value = t('errors.generic')
  }
}
</script>

<template>
  <div class="login-page">
    <div class="hero">
      <AppLogo class="logo" :size="76" />
      <h1>{{ $t('app.name') }}</h1>
      <p>{{ $t('auth.subtitle') }}</p>
    </div>

    <div class="card">
      <PillTabs
        v-if="view === 'login' || view === 'register'"
        v-model="mode"
        class="tabs"
        :options="[
          { value: 'login' as AuthMode, label: $t('auth.tabLogin') },
          { value: 'register' as AuthMode, label: $t('auth.tabRegister') },
        ]"
        @update:model-value="errorMessage = ''"
      />

      <Transition name="fade" mode="out-in">
        <VerificationStep
          v-if="view === 'verify' && authStore.challenge"
          :key="authStore.challenge.challenge"
          :challenge="authStore.challenge"
          @done="handleVerified"
          @cancel="handleVerifyCancel"
        />
        <ForgotPasswordForm
          v-else-if="view === 'forgot'"
          key="forgot"
          :is-submitting="authStore.isSubmitting"
          :error-message="errorMessage"
          @submit="handleForgot"
          @cancel="isForgot = false; errorMessage = ''"
        />
        <LoginForm
          v-else-if="view === 'login'"
          key="login"
          :is-submitting="authStore.isSubmitting"
          :error-message="errorMessage"
          @submit="handleLogin"
          @forgot="isForgot = true; errorMessage = ''"
        />
        <RegisterForm
          v-else
          key="register"
          :is-submitting="authStore.isSubmitting"
          :error-message="errorMessage"
          @submit="handleRegister"
        />
      </Transition>

      <ProviderButtons
        v-if="view === 'login' || view === 'register'"
        :disabled="authStore.isSubmitting"
        @google="handleGoogle"
        @error="handleGoogleError"
      />

      <!-- Касается и регистрации, и входа через Google (там аккаунт создаётся сразу) -->
      <i18n-t keypath="legal.consent" tag="p" class="consent">
        <template #terms>
          <router-link to="/terms">{{ $t('legal.termsLink') }}</router-link>
        </template>
        <template #link>
          <router-link to="/privacy">{{ $t('legal.consentLink') }}</router-link>
        </template>
      </i18n-t>
    </div>

    <nav class="legal-links">
      <router-link to="/about">{{ $t('legal.about') }}</router-link>
      <router-link to="/terms">{{ $t('legal.terms') }}</router-link>
      <router-link to="/privacy">{{ $t('legal.privacy') }}</router-link>
    </nav>

    <!-- Быстрый вход для демо -->
    <section v-if="IS_DEV_MODE && authStore.demoUsers.length" class="demo">
      <h2>{{ $t('auth.demoTitle') }}</h2>
      <p>{{ $t('auth.demoHint') }}</p>
      <DemoUserList :users="authStore.demoUsers" :disabled="authStore.isSubmitting" @select="handleDemo" />
    </section>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.login-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 460px;
  margin: 0 auto;
  padding: calc(32px + var(--sat)) 16px calc(32px + var(--sab));
}

.hero {
  text-align: center;

  .logo {
    margin: 0 auto 14px;
  }

  h1 {
    margin: 0 0 6px;
    font-size: 24px;
    font-weight: 700;
    color: $navy;
  }

  p {
    margin: 0;
    font-size: 14px;
    color: $text-secondary;
  }
}

.card {
  @include glass-card(24px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
}

.consent {
  margin: 0;
  font-size: 12px;
  text-align: center;
  color: $text-secondary;

  a {
    color: $navy;
    text-decoration: underline;
  }
}

.legal-links {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px 18px;

  a {
    font-size: 13px;
    color: $text-secondary;
    text-decoration: underline;
  }
}

/* ── Demo ─────────────────────────────────────────────────────────────────── */
.demo {
  h2 {
    @include section-title;
    font-size: 16px;
  }

  p {
    margin: 4px 0 12px;
    font-size: 13px;
    color: $text-secondary;
  }
}
</style>
