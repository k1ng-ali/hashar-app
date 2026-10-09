<script setup lang="ts">
import { reactive } from 'vue'
import type { LoginPayload } from '../types.ts'

defineProps<{
  isSubmitting: boolean
  errorMessage: string
}>()

const emit = defineEmits<{
  (e: 'submit', payload: LoginPayload): void
}>()

const form = reactive({ login: '', password: '' })
</script>

<template>
  <form class="auth-form" @submit.prevent="emit('submit', { login: form.login.trim(), password: form.password })">
    <label>
      <span class="label">{{ $t('auth.login') }}</span>
      <input v-model="form.login" autocomplete="username" required :placeholder="$t('auth.loginPlaceholder')" />
    </label>

    <label>
      <span class="label">{{ $t('auth.password') }}</span>
      <input v-model="form.password" type="password" autocomplete="current-password" required />
    </label>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting || !form.login || !form.password">
      {{ $t('auth.submit') }}
    </button>
  </form>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.label {
  @include field-label;
}

input {
  @include field-input;
}

.error {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: $danger;
}

.submit-btn {
  @include cta-button;
  margin-top: 4px;
}
</style>
