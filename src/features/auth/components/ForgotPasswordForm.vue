<script setup lang="ts">
import { ref } from 'vue'
import { formatLoginInput } from '@/shared/lib/formatters.ts'

defineProps<{
  isSubmitting: boolean
  errorMessage: string
}>()

const emit = defineEmits<{
  (e: 'submit', login: string): void
  (e: 'cancel'): void
}>()

const login = ref('')

function onLoginInput(event: Event) {
  const input = event.target as HTMLInputElement
  login.value = formatLoginInput(input.value)
  input.value = login.value
}
</script>

<template>
  <form class="auth-form" @submit.prevent="emit('submit', login.trim())">
    <button type="button" class="back-btn" @click="emit('cancel')">← {{ $t('auth.verify.back') }}</button>

    <div class="head">
      <h2>{{ $t('auth.forgot.title') }}</h2>
      <p>{{ $t('auth.forgot.hint') }}</p>
    </div>

    <label>
      <span class="label">{{ $t('auth.login') }}</span>
      <input
        :value="login"
        autocomplete="username"
        required
        :placeholder="$t('auth.loginPlaceholder')"
        @input="onLoginInput"
      />
    </label>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting || login.trim().length < 3">
      {{ $t('auth.forgot.submit') }}
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

.back-btn {
  align-self: flex-start;
  padding: 0;
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 600;
  color: $text-secondary;
  cursor: pointer;
}

.head {
  h2 {
    margin: 0 0 6px;
    font-size: 18px;
    font-weight: 700;
    color: $navy;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: $text-secondary;
  }
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
}
</style>
