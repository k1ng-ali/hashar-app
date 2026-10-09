<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { type Currency } from '@/shared/lib/currency.ts'
import type { RequisiteCreate } from '../types.ts'

const props = defineProps<{
  currencies: Currency[]
  baseCurrency: Currency
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: RequisiteCreate): void
}>()

const { t } = useI18n()

const form = reactive({
  currency: props.baseCurrency as Currency,
  bank_name: '', card_or_account_number: '', recipient_name: '', phone_number: '', note: '' })
const error = ref('')

function handleSubmit() {
  if (form.bank_name.trim().length < 2 || form.card_or_account_number.trim().length < 4 || form.recipient_name.trim().length < 2) {
    error.value = t('admin.settings.validation')
    return
  }
  error.value = ''
  emit('submit', {
    currency: form.currency,
    bank_name: form.bank_name.trim(),
    card_or_account_number: form.card_or_account_number.trim(),
    recipient_name: form.recipient_name.trim(),
    phone_number: form.phone_number.trim() || null,
    note: form.note.trim() || null,
  })
}
</script>

<template>
  <form class="form" @submit.prevent="handleSubmit">
    <div>
      <span class="label">{{ $t('admin.settings.requisiteCurrency') }}</span>
      <div class="chips">
        <button
          v-for="currency in currencies"
          :key="currency"
          type="button"
          class="chip"
          :class="{ 'chip--active': form.currency === currency }"
          @click="form.currency = currency"
        >
          {{ currency.toUpperCase() }}
        </button>
      </div>
    </div>

    <label>
      <span class="label">{{ $t('admin.settings.bank') }}</span>
      <input v-model="form.bank_name" :placeholder="$t('admin.settings.bankPlaceholder')" />
    </label>

    <label>
      <span class="label">{{ $t('admin.settings.number') }}</span>
      <input v-model="form.card_or_account_number" class="mono" placeholder="2202 2034 5678 9101" />
    </label>

    <label>
      <span class="label">{{ $t('admin.settings.recipient') }}</span>
      <input v-model="form.recipient_name" :placeholder="$t('admin.settings.recipientPlaceholder')" />
    </label>

    <label>
      <span class="label">{{ $t('admin.settings.sbpPhone') }} · {{ $t('common.optional') }}</span>
      <input v-model="form.phone_number" type="tel" :placeholder="$t('auth.phonePlaceholder')" />
    </label>

    <label>
      <span class="label">{{ $t('admin.settings.note') }} · {{ $t('common.optional') }}</span>
      <textarea v-model="form.note" rows="2" :placeholder="$t('admin.settings.notePlaceholder')" />
    </label>

    <p v-if="error" class="error">{{ error }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">{{ $t('admin.settings.save') }}</button>
  </form>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.label {
  @include field-label;
}

input,
textarea {
  @include field-input;
}

textarea {
  resize: vertical;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  @include ghost-button;
  padding: 8px 12px;
  font-size: 12px;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}

.mono {
  font-family: 'SF Mono', 'Consolas', monospace;
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
