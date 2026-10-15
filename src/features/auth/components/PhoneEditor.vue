<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { errorDetail } from '@/shared/api/http.ts'
import { formatPhone, formatPhoneInput, isValidPhone } from '@/shared/lib/formatters.ts'
import { useAuthStore } from '../store.ts'

// Телефон в профиле: после входа через Google его нет — добавляется здесь же, как и смена номера

const { t } = useI18n()
const authStore = useAuthStore()

const isEditing = ref(false)
const isSaving = ref(false)
const phone = ref('')
const error = ref('')

const current = computed(() => authStore.user?.phone ?? null)

// Ошибки backend (AuthService.update_profile) → понятный текст
const ERRORS: Record<string, string> = {
  'Phone is already registered': 'profile.phoneTaken',
  'Phone is the only way to sign in': 'profile.phoneOnlyLogin',
}

function startEdit() {
  phone.value = current.value ? formatPhone(current.value) : ''
  error.value = ''
  isEditing.value = true
}

function onPhoneInput(event: Event) {
  const input = event.target as HTMLInputElement
  phone.value = formatPhoneInput(input.value)
  input.value = phone.value
}

async function save(value: string | null) {
  if (value && !isValidPhone(value)) {
    error.value = t('requisites.phoneInvalid')
    return
  }
  error.value = ''
  isSaving.value = true
  try {
    await authStore.updateProfile({ phone: value })
    isEditing.value = false
    message.success(t('profile.phoneSaved'))
  } catch (err) {
    error.value = t(ERRORS[errorDetail(err) ?? ''] ?? 'errors.generic')
  } finally {
    isSaving.value = false
  }
}
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
      <p v-if="error" class="error">{{ error }}</p>
      <div class="actions">
        <button type="button" class="cancel-btn" :disabled="isSaving" @click="isEditing = false">
          {{ $t('common.cancel') }}
        </button>
        <button type="submit" class="save-btn" :disabled="isSaving || !phone.trim()">{{ $t('common.save') }}</button>
      </div>
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

.remove-btn {
  padding: 4px;
  border: none;
  background: none;
  color: $danger;
  font-size: 12px;
  cursor: pointer;
}
</style>
