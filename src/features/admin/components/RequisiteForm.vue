<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SegmentedControl from '@/shared/components/SegmentedControl.vue'
import { type Currency } from '@/shared/lib/currency.ts'
import {
  CARD_DIGITS,
  cardDigits,
  formatAccountInput,
  formatCardInput,
  formatPhoneInput,
  isValidAccount,
  isValidCard,
  isValidPhone,
} from '@/shared/lib/formatters.ts'
import type { RequisiteCreate, RequisiteKind } from '../types.ts'

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
  kind: 'card' as RequisiteKind,
  bank_name: '',
  card_or_account_number: '',
  recipient_name: '',
  phone_number: '',
  note: '',
})
const error = ref('')

const kindOptions = computed(() => [
  { value: 'card' as RequisiteKind, label: t('requisites.kind.card') },
  { value: 'account' as RequisiteKind, label: t('requisites.kind.account') },
])

// Сменили тип — номер другого формата больше не подходит
watch(
  () => form.kind,
  () => {
    form.card_or_account_number = ''
  },
)

const isNumberValid = computed(() =>
  form.kind === 'card' ? isValidCard(form.card_or_account_number) : isValidAccount(form.card_or_account_number),
)
const isPhoneValid = computed(() => !form.phone_number.trim() || isValidPhone(form.phone_number))
const numberHint = computed(() =>
  form.kind === 'card'
    ? t('requisites.cardDigits', { n: cardDigits(form.card_or_account_number), total: CARD_DIGITS })
    : t('requisites.accountHint'),
)

// Форматирование на лету — пользователь сразу видит, как номер увидят участники
function onNumberInput(event: Event) {
  const input = event.target as HTMLInputElement
  form.card_or_account_number = form.kind === 'card' ? formatCardInput(input.value) : formatAccountInput(input.value)
  input.value = form.card_or_account_number
}

function onPhoneInput(event: Event) {
  const input = event.target as HTMLInputElement
  form.phone_number = formatPhoneInput(input.value)
  input.value = form.phone_number
}

function handleSubmit() {
  if (form.bank_name.trim().length < 2 || form.recipient_name.trim().length < 2) {
    error.value = t('admin.settings.validation')
    return
  }
  if (!isNumberValid.value) {
    error.value = form.kind === 'card' ? t('requisites.cardInvalid') : t('requisites.accountInvalid')
    return
  }
  if (!isPhoneValid.value) {
    error.value = t('requisites.phoneInvalid')
    return
  }
  error.value = ''
  emit('submit', {
    currency: form.currency,
    kind: form.kind,
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

    <SegmentedControl v-model="form.kind" :options="kindOptions" />

    <label>
      <span class="label">{{ form.kind === 'card' ? $t('requisites.cardNumber') : $t('requisites.accountNumber') }}</span>
      <input
        :value="form.card_or_account_number"
        class="mono"
        :class="{ 'is-valid': isNumberValid }"
        :inputmode="form.kind === 'card' ? 'numeric' : 'text'"
        autocomplete="off"
        :placeholder="form.kind === 'card' ? '0000 0000 0000 0000' : 'TJ00 0000 0000 0000 0000'"
        @input="onNumberInput"
      />
      <span class="field-hint" :class="{ 'field-hint--ok': isNumberValid }">{{ numberHint }}</span>
    </label>

    <label>
      <span class="label">{{ $t('admin.settings.recipient') }}</span>
      <input v-model="form.recipient_name" :placeholder="$t('admin.settings.recipientPlaceholder')" />
    </label>

    <label>
      <span class="label">{{ $t('admin.settings.sbpPhone') }} · {{ $t('common.optional') }}</span>
      <input
        :value="form.phone_number"
        type="tel"
        inputmode="tel"
        placeholder="+992 90 123 45 67"
        :class="{ 'is-invalid': !isPhoneValid && form.phone_number.length > 4 }"
        @input="onPhoneInput"
      />
      <span class="field-hint">{{ $t('requisites.phoneHint') }}</span>
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

.field-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: $text-muted;

  &--ok {
    color: $success;
  }
}

.is-valid {
  border-color: rgba(22, 163, 74, 0.4);
}

.is-invalid {
  border-color: rgba(229, 72, 77, 0.5);
}
</style>
