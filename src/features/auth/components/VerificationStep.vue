<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { errorDetail } from '@/shared/api/http.ts'
import { isGoogleEnabled } from '../google.ts'
import { useAuthStore } from '../store.ts'
import type { ChallengeResponse } from '../types.ts'
import GoogleButton from './GoogleButton.vue'

/**
 * Подтверждение личности: код из SMS (номера +992) или Google.
 * purpose=password — сначала новый пароль, он уходит вместе с подтверждением.
 */
const props = defineProps<{
  challenge: ChallengeResponse
}>()

const emit = defineEmits<{
  // Сессия уже выдана; challenge сбрасывает родитель (authStore.cancelChallenge)
  (e: 'done', purpose: ChallengeResponse['purpose']): void
  (e: 'cancel'): void
}>()

const { t, locale } = useI18n()
const authStore = useAuthStore()

const ERRORS: Record<string, string> = {
  'Invalid code': 'auth.verify.invalidCode',
  'Code expired': 'auth.verify.codeExpired',
  'Invalid challenge': 'auth.verify.expired',
  'Too many attempts, try later': 'auth.tooManyAttempts',
  'SMS is unavailable': 'auth.verify.smsUnavailable',
  'SMS is unavailable for this phone': 'auth.verify.smsUnavailable',
  'Phone is rejected': 'auth.verify.phoneRejected',
  'Google account does not match': 'auth.verify.googleMismatch',
  'Google account is linked to another user': 'auth.verify.googleTaken',
  'Google verification is unavailable': 'auth.verify.unavailable',
  'Invalid Google token': 'auth.googleFailed',
}

const hasSms = computed(() => props.challenge.methods.includes('sms'))
const hasGoogle = computed(() => isGoogleEnabled && props.challenge.methods.includes('google'))
const isPassword = computed(() => props.challenge.purpose === 'password')
// Шаг пересоздаётся на каждый новый challenge (key), поэтому purpose можно запомнить
const purpose = props.challenge.purpose

const newPassword = ref('')
const code = ref('')
const phoneHint = ref(props.challenge.phone_hint ?? '')
const codeSent = ref(false)
const isSending = ref(false)
const resendIn = ref(0)
const error = ref('')
let timer: ReturnType<typeof setInterval> | null = null

function showError(err: unknown, fallback = 'errors.generic') {
  const detail = errorDetail(err)
  error.value = t((detail && ERRORS[detail]) || fallback)
}

/** Новый пароль для purpose=password (null — не нужен); false — пароль короткий, ошибка уже показана. */
function passwordOrNull(): string | null | false {
  if (!isPassword.value) return null
  if (newPassword.value.length < 6) {
    error.value = t('auth.validation.password')
    return false
  }
  return newPassword.value
}

function startCountdown(seconds: number) {
  resendIn.value = seconds
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    resendIn.value -= 1
    if (resendIn.value <= 0 && timer) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

async function sendCode() {
  if (passwordOrNull() === false) return
  error.value = ''
  isSending.value = true
  try {
    const sent = await authStore.sendSmsCode(locale.value)
    phoneHint.value = sent.phone_hint
    codeSent.value = true
    startCountdown(sent.resend_after)
  } catch (err) {
    showError(err, 'auth.verify.smsUnavailable')
  } finally {
    isSending.value = false
  }
}

async function submitCode() {
  const password = passwordOrNull()
  if (password === false) return
  error.value = ''
  try {
    await authStore.verifySms(code.value, password)
    emit('done', purpose)
  } catch (err) {
    code.value = ''
    showError(err)
  }
}

async function submitGoogle(idToken: string) {
  const password = passwordOrNull()
  if (password === false) return
  error.value = ''
  try {
    await authStore.verifyGoogle(idToken, password)
    emit('done', purpose)
  } catch (err) {
    showError(err, 'auth.googleFailed')
  }
}

function onCodeInput(event: Event) {
  const input = event.target as HTMLInputElement
  code.value = input.value.replace(/\D/g, '').slice(0, 6)
  input.value = code.value
  // Код подставился из SMS (или введён целиком) — проверяем сразу
  if (code.value.length === 6 && !authStore.isSubmitting) void submitCode()
}

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="verify">
    <button type="button" class="back-btn" @click="emit('cancel')">← {{ $t('auth.verify.back') }}</button>

    <div class="head">
      <h2>{{ isPassword ? $t('auth.verify.passwordTitle') : $t('auth.verify.title') }}</h2>
      <p>{{ isPassword ? $t('auth.verify.passwordHint') : $t('auth.verify.hint') }}</p>
    </div>

    <label v-if="isPassword">
      <span class="label">{{ $t('auth.verify.newPassword') }}</span>
      <input v-model="newPassword" type="password" autocomplete="new-password" />
    </label>

    <template v-if="hasSms">
      <template v-if="!codeSent">
        <button type="button" class="submit-btn" :disabled="isSending" @click="sendCode">
          {{ $t('auth.verify.sendSms') }}
        </button>
        <p class="hint">{{ $t('auth.verify.smsTo', { phone: phoneHint }) }}</p>
      </template>

      <form v-else class="code-form" @submit.prevent="submitCode">
        <p class="hint">{{ $t('auth.verify.codeSent', { phone: phoneHint }) }}</p>
        <label>
          <span class="label">{{ $t('auth.verify.code') }}</span>
          <input
            :value="code"
            class="code-input"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            placeholder="••••••"
            @input="onCodeInput"
          />
        </label>
        <button type="submit" class="submit-btn" :disabled="authStore.isSubmitting || code.length !== 6">
          {{ $t('auth.verify.submit') }}
        </button>
        <button type="button" class="link-btn" :disabled="resendIn > 0 || isSending" @click="sendCode">
          {{ resendIn > 0 ? $t('auth.verify.resendIn', { n: resendIn }) : $t('auth.verify.resend') }}
        </button>
      </form>
    </template>

    <div v-if="hasSms && hasGoogle" class="divider">
      <span>{{ $t('auth.or') }}</span>
    </div>
    <GoogleButton
      v-if="hasGoogle"
      :disabled="authStore.isSubmitting"
      @token="submitGoogle"
      @error="error = $t('auth.googleFailed')"
    />

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.verify {
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

.code-form {
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

.code-input {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 8px;
  text-align: center;
}

.hint {
  margin: -6px 0 0;
  font-size: 12px;
  color: $text-muted;
  text-align: center;

  .code-form & {
    margin: 0;
  }
}

.submit-btn {
  @include cta-button;
}

.link-btn {
  padding: 4px;
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 600;
  color: $navy;
  cursor: pointer;

  &:disabled {
    color: $text-muted;
    cursor: default;
  }
}

.divider {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: $text-muted;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(17, 24, 39, 0.1);
  }
}

.error {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: $danger;
}
</style>
