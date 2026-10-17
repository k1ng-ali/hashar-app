<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { errorDetail } from '@/shared/api/http.ts'
import { formatPhone, formatPhoneInput, isValidPhone } from '@/shared/lib/formatters.ts'
import { useAuthStore } from '../store.ts'

// Телефон в профиле: после входа через Google его нет — добавляется здесь же, как и смена номера.
// Новый номер +992 подтверждается кодом из SMS: по телефону подтверждается личность при входе

const { t, locale } = useI18n()
const authStore = useAuthStore()

const isEditing = ref(false)
const isSaving = ref(false)
const phone = ref('')
const error = ref('')
// Шаг с кодом: на какой номер ушёл код (скрытый) и сколько ждать повторной отправки
const codePhone = ref<string | null>(null)
const phoneHint = ref('')
const code = ref('')
const resendIn = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const current = computed(() => authStore.user?.phone ?? null)

// Ошибки backend (AuthService.update_profile / send_phone_code) → понятный текст
const ERRORS: Record<string, string> = {
  'Phone is already registered': 'profile.phoneTaken',
  'Phone is the only way to sign in': 'profile.phoneOnlyLogin',
  'Invalid code': 'auth.verify.invalidCode',
  'Code expired': 'auth.verify.codeExpired',
  'Too many attempts, try later': 'auth.tooManyAttempts',
  'SMS is unavailable': 'auth.verify.smsUnavailable',
  'Phone is rejected': 'auth.verify.phoneRejected',
}

const digitsOf = (value: string) => value.replace(/\D/g, '')
// Только на таджикские номера уходят SMS (Payomchi)
const isTjPhone = (value: string) => /^992\d{9}$/.test(digitsOf(value))

function showError(err: unknown) {
  error.value = t(ERRORS[errorDetail(err) ?? ''] ?? 'errors.generic')
}

function startEdit() {
  phone.value = current.value ? formatPhone(current.value) : ''
  error.value = ''
  resetCode()
  isEditing.value = true
}

function resetCode() {
  codePhone.value = null
  code.value = ''
  resendIn.value = 0
  if (timer) clearInterval(timer)
  timer = null
}

function onPhoneInput(event: Event) {
  const input = event.target as HTMLInputElement
  phone.value = formatPhoneInput(input.value)
  input.value = phone.value
  // Номер изменился — старый код к нему не подходит
  if (codePhone.value && digitsOf(phone.value) !== digitsOf(codePhone.value)) resetCode()
}

function onCodeInput(event: Event) {
  const input = event.target as HTMLInputElement
  code.value = input.value.replace(/\D/g, '').slice(0, 6)
  input.value = code.value
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

/** true — код отправлен, ждём ввода; false — номер сохраняется без кода. */
async function sendCode(value: string): Promise<boolean> {
  try {
    const sent = await authStore.sendPhoneCode(value, locale.value)
    codePhone.value = value
    phoneHint.value = sent.phone_hint
    startCountdown(sent.resend_after)
    return true
  } catch (err) {
    // SMS на сервере выключены — номер подтверждать нечем, сохраняем как раньше
    if (errorDetail(err) === 'SMS is unavailable for this phone') return false
    throw err
  }
}

async function save(value: string | null) {
  if (value && !isValidPhone(value)) {
    error.value = t('requisites.phoneInvalid')
    return
  }
  error.value = ''
  isSaving.value = true
  try {
    const isNew = !!value && digitsOf(value) !== digitsOf(current.value ?? '')
    if (isNew && isTjPhone(value) && !codePhone.value && (await sendCode(value))) return
    await authStore.updateProfile({ phone: value, code: codePhone.value && value ? code.value : undefined })
    isEditing.value = false
    resetCode()
    message.success(t('profile.phoneSaved'))
  } catch (err) {
    code.value = ''
    showError(err)
  } finally {
    isSaving.value = false
  }
}

async function resend() {
  if (!codePhone.value) return
  error.value = ''
  isSaving.value = true
  try {
    await sendCode(codePhone.value)
  } catch (err) {
    showError(err)
  } finally {
    isSaving.value = false
  }
}

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="phone-editor">
    <template v-if="!isEditing">
      <div class="row">
        <div>
          <div class="label">{{ $t('auth.phone') }}</div>
          <div v-if="current" class="value">{{ formatPhone(current) }}</div>
          <div v-else class="value value--empty">{{ $t('profile.noPhone') }}</div>
        </div>
        <button type="button" class="edit-btn" @click="startEdit">
          {{ current ? $t('profile.change') : $t('profile.add') }}
        </button>
      </div>
      <p v-if="!current" class="hint">{{ $t('profile.phoneHint') }}</p>
    </template>

    <form v-else @submit.prevent="save(phone.trim() || null)">
      <label>
        <span class="label">{{ $t('auth.phone') }}</span>
        <input
          :value="phone"
          type="tel"
          inputmode="tel"
          autocomplete="tel"
          :placeholder="$t('auth.phonePlaceholder')"
          @input="onPhoneInput"
        />
      </label>
      <template v-if="codePhone">
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
      </template>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="actions">
        <button type="button" class="cancel-btn" :disabled="isSaving" @click="isEditing = false">
          {{ $t('common.cancel') }}
        </button>
        <button
          type="submit"
          class="save-btn"
          :disabled="isSaving || !phone.trim() || (!!codePhone && code.length !== 6)"
        >
          {{ codePhone ? $t('auth.verify.submit') : $t('common.save') }}
        </button>
      </div>
      <button v-if="codePhone" type="button" class="resend-btn" :disabled="isSaving || resendIn > 0" @click="resend">
        {{ resendIn > 0 ? $t('auth.verify.resendIn', { n: resendIn }) : $t('auth.verify.resend') }}
      </button>
      <button v-if="current" type="button" class="remove-btn" :disabled="isSaving" @click="save(null)">
        {{ $t('profile.removePhone') }}
      </button>
    </form>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.phone-editor {
  @include glass-card;
  padding: 14px 18px;
  margin-bottom: 14px;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.label {
  @include field-label;
}

.value {
  font-size: 15px;
  font-weight: 600;
  color: $navy;

  &--empty {
    font-weight: 500;
    color: $text-muted;
  }
}

.hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: $text-secondary;
}

.edit-btn {
  @include ghost-button;
  padding: 8px 14px;
  font-size: 13px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 10px;
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

.actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.cancel-btn {
  @include ghost-button;
  padding: 11px;
}

.save-btn {
  @include cta-button;
  padding: 11px;
}

.code-input {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 8px;
  text-align: center;
}

.resend-btn {
  padding: 4px;
  border: none;
  background: none;
  font-size: 12px;
  font-weight: 600;
  color: $navy;
  cursor: pointer;

  &:disabled {
    color: $text-muted;
    cursor: default;
  }
}

.remove-btn {
  padding: 4px;
  border: none;
  background: none;
  color: $danger;
  font-size: 12px;
  cursor: pointer;
}
</style>
