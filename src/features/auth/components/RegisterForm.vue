<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatPhoneInput, isValidPhone } from '@/shared/lib/formatters.ts'
import type { RegisterPayload } from '../types.ts'

defineProps<{
  isSubmitting: boolean
  errorMessage: string
}>()

const emit = defineEmits<{
  (e: 'submit', payload: RegisterPayload): void
}>()

const { t } = useI18n()

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

const form = reactive({ full_name: '', phone: '', email: '', password: '' })
const localError = ref('')

// Номер форматируется на лету — как у реквизитов
function onPhoneInput(event: Event) {
  const input = event.target as HTMLInputElement
  form.phone = formatPhoneInput(input.value)
  input.value = form.phone
}

function handleSubmit() {
  if (form.full_name.trim().length < 2) {
    localError.value = t('auth.validation.name')
  } else if (!form.phone.trim() && !form.email.trim()) {
    localError.value = t('auth.validation.contact')
  } else if (form.phone.trim() && !isValidPhone(form.phone)) {
    localError.value = t('requisites.phoneInvalid')
  } else if (form.email.trim() && !EMAIL_PATTERN.test(form.email.trim())) {
    localError.value = t('auth.validation.email')
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

    <label>
      <span class="label">{{ $t('auth.phone') }}</span>
      <input
        :value="form.phone"
        type="tel"
        inputmode="tel"
        autocomplete="tel"
        placeholder="+992 90 123 45 67"
        @input="onPhoneInput"
      />
    </label>
    <label>
      <span class="label">Email</span>
      <input v-model="form.email" type="email" autocomplete="email" placeholder="name@mail.com" />
    </label>
    <p class="hint">{{ $t('auth.contactHint') }}</p>

    <label>
      <span class="label">{{ $t('auth.password') }}</span>
      <input v-model="form.password" type="password" autocomplete="new-password" />
    </label>

    <p v-if="localError || errorMessage" class="error">{{ localError || errorMessage }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">{{ $t('auth.register') }}</button>

    <i18n-t keypath="legal.consent" tag="p" class="consent">
      <template #link>
        <router-link to="/privacy">{{ $t('legal.consentLink') }}</router-link>
      </template>
    </i18n-t>
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
</style>
