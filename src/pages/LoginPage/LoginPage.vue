<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/features/auth/store.ts'
import { IS_DEV_MODE } from '@/shared/lib/env.ts'
import DemoUserList from '@/features/auth/components/DemoUserList.vue'
import LoginForm from '@/features/auth/components/LoginForm.vue'
import ProviderButtons from '@/features/auth/components/ProviderButtons.vue'
import RegisterForm from '@/features/auth/components/RegisterForm.vue'
import type { DemoUser, LoginPayload, RegisterPayload } from '@/features/auth/types.ts'
import AppLogo from '@/shared/components/AppLogo.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { errorDetail } from '@/shared/api/http.ts'

type AuthMode = 'login' | 'register'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const mode = ref<AuthMode>(route.query.mode === 'register' ? 'register' : 'login')
const errorMessage = ref('')

onMounted(() => {
  void authStore.fetchDemoUsers().catch(() => undefined)
})

// После входа возвращаемся туда, куда шли (например, ссылка-приглашение /join/CODE)
function afterAuth() {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  return router.replace(redirect.startsWith('/') ? redirect : '/')
}

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleLogin(payload: LoginPayload) {
  errorMessage.value = ''
  try {
    await authStore.login(payload)
    await afterAuth()
  } catch (error) {
    errorMessage.value =
      errorDetail(error) === 'Too many attempts, try later' ? t('auth.tooManyAttempts') : t('auth.invalid')
  }
}

async function handleRegister(payload: RegisterPayload) {
  errorMessage.value = ''
  try {
    await authStore.register(payload)
    await afterAuth()
  } catch (error) {
    errorMessage.value =
      errorDetail(error) === 'Phone or email is already registered' ? t('auth.alreadyRegistered') : t('errors.generic')
  }
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
        v-model="mode"
        class="tabs"
        :options="[
          { value: 'login' as AuthMode, label: $t('auth.tabLogin') },
          { value: 'register' as AuthMode, label: $t('auth.tabRegister') },
        ]"
        @update:model-value="errorMessage = ''"
      />

      <Transition name="fade" mode="out-in">
        <LoginForm
          v-if="mode === 'login'"
          key="login"
          :is-submitting="authStore.isSubmitting"
          :error-message="errorMessage"
          @submit="handleLogin"
        />
        <RegisterForm
          v-else
          key="register"
          :is-submitting="authStore.isSubmitting"
          :error-message="errorMessage"
          @submit="handleRegister"
        />
      </Transition>

      <ProviderButtons />
    </div>

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
