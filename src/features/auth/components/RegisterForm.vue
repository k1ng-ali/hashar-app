<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { RegisterPayload } from '../types.ts'

defineProps<{
  isSubmitting: boolean
  errorMessage: string
}>()

const emit = defineEmits<{
  (e: 'submit', payload: RegisterPayload): void
}>()

const { t } = useI18n()

const form = reactive({ full_name: '', phone: '', email: '', password: '' })
const localError = ref('')

function handleSubmit() {
  if (form.full_name.trim().length < 2) {
    localError.value = t('auth.validation.name')
  } else if (!form.phone.trim() && !form.email.trim()) {
    localError.value = t('auth.validation.contact')
  } else if (form.password.length < 6) {
    localError.value = t('auth.validation.password')
  } else {
    localError.value = ''
    emit('submit', {
      full_name: form.full_name.trim(),
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      password: form.password,
    })
  }
}
</script>

<template>
  <form class="auth-form" @submit.prevent="handleSubmit">
    <label>
      <span class="label">{{ $t('auth.fullName') }}</span>
      <input v-model="form.full_name" autocomplete="name" :placeholder="$t('auth.fullNamePlaceholder')" />
    </label>

    <div class="two">
      <label>
        <span class="label">{{ $t('auth.phone') }}</span>
        <input v-model="form.phone" type="tel" autocomplete="tel" :placeholder="$t('auth.phonePlaceholder')" />
      </label>
      <label>
        <span class="label">Email</span>
        <input v-model="form.email" type="email" autocomplete="email" placeholder="name@mail.com" />
      </label>
    </div>
    <p class="hint">{{ $t('auth.contactHint') }}</p>

    <label>
      <span class="label">{{ $t('auth.password') }}</span>
      <input v-model="form.password" type="password" autocomplete="new-password" />
    </label>

    <p v-if="localError || errorMessage" class="error">{{ localError || errorMessage }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">{{ $t('auth.register') }}</button>
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

.two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.hint {
  margin: -8px 0 0;
  font-size: 12px;
  color: $text-muted;
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
