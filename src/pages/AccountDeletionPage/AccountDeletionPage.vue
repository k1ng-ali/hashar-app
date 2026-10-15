<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/features/auth/store.ts'
import { errorDetail } from '@/shared/api/http.ts'
import LegalDocument from '@/shared/components/LegalDocument.vue'
import { ACCOUNT_DELETION } from './content.ts'

const { t } = useI18n()
const authStore = useAuthStore()

const password = ref('')
const confirmed = ref(false)
const isDeleting = ref(false)
const errorMessage = ref('')
// Аккаунт только с Google — пароля нет, подтверждение одной галочкой
const needsPassword = computed(() => !!authStore.user?.has_password)

// Ошибки backend (AuthService.delete_account) → понятный текст
const ERRORS: Record<string, string> = {
  'Invalid password': 'legal.deletion.errors.password',
  'Transfer chairman rights first': 'legal.deletion.errors.chairman',
  'Too many attempts, try later': 'auth.tooManyAttempts',
}

async function handleDelete() {
  errorMessage.value = ''
  isDeleting.value = true
  try {
    await authStore.deleteAccount(needsPassword.value ? password.value : null)
    message.success(t('legal.deletion.done'))
  } catch (error) {
    const key = ERRORS[errorDetail(error) ?? '']
    errorMessage.value = t(key ?? 'errors.generic')
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <LegalDocument :documents="ACCOUNT_DELETION">
    <section class="delete-card">
      <template v-if="authStore.isAuthenticated && authStore.user">
        <h2>{{ $t('legal.deletion.formTitle') }}</h2>
        <p class="who">{{ $t('legal.deletion.signedInAs', { name: authStore.user.full_name }) }}</p>

        <form @submit.prevent="handleDelete">
          <label v-if="needsPassword">
            <span class="label">{{ $t('legal.deletion.password') }}</span>
            <input v-model="password" type="password" autocomplete="current-password" />
          </label>
          <label class="check">
            <input v-model="confirmed" type="checkbox" />
            <span>{{ $t('legal.deletion.confirm') }}</span>
          </label>

          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

          <button type="submit" class="danger-btn" :disabled="!confirmed || (needsPassword && !password) || isDeleting">
            {{ $t('legal.deletion.submit') }}
          </button>
        </form>
      </template>

      <template v-else>
        <h2>{{ $t('legal.deletion.formTitle') }}</h2>
        <p class="who">{{ $t('legal.deletion.signInHint') }}</p>
        <router-link class="signin-btn" :to="{ path: '/login', query: { redirect: '/account-deletion' } }">
          {{ $t('legal.deletion.signIn') }}
        </router-link>
      </template>
    </section>
  </LegalDocument>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.delete-card {
  @include glass-card(20px);
  margin-top: 32px;
  padding: 20px;
  border-color: rgba(229, 72, 77, 0.25);

  h2 {
    @include section-title;
  }

  .who {
    margin: 4px 0 16px;
    font-size: 14px;
    color: $text-secondary;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .label {
    @include field-label;
  }

  input[type='password'] {
    @include field-input;
  }

  .check {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 14px;
    cursor: pointer;

    input {
      width: 18px;
      height: 18px;
      margin-top: 2px;
      flex-shrink: 0;
      accent-color: $danger;
    }
  }

  .error {
    margin: 0;
    font-size: 13px;
    color: $danger;
  }
}

.danger-btn {
  @include cta-button;
  background: $danger;
}

.signin-btn {
  @include cta-button;
  width: 100%;
  text-decoration: none;
}
</style>
