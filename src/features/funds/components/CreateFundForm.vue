<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { CURRENCIES, type Currency } from '@/shared/lib/currency.ts'
import type { FundCreate } from '../types.ts'

defineProps<{
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: FundCreate): void
}>()

const { t } = useI18n()

const form = reactive({
  name: '',
  address: '',
  description: '',
  base_currency: 'tjs' as Currency,
  extra: [] as Currency[],
  monthly_rate: 150 as number | null,
  address_unit: '',
})
const error = ref('')

function toggleExtra(currency: Currency) {
  form.extra = form.extra.includes(currency) ? form.extra.filter((c) => c !== currency) : [...form.extra, currency]
}

function handleSubmit() {
  if (form.name.trim().length < 3) {
    error.value = t('funds.create.validation')
    return
  }
  error.value = ''
  emit('submit', {
    name: form.name.trim(),
    address: form.address.trim() || null,
    description: form.description.trim() || null,
    base_currency: form.base_currency,
    currencies: form.extra.filter((c) => c !== form.base_currency),
    monthly_rate: form.monthly_rate ?? 0,
    address_unit: form.address_unit.trim() || null,
  })
}
</script>

<template>
  <form class="form" @submit.prevent="handleSubmit">
    <label>
      <span class="label">{{ $t('funds.create.name') }}</span>
      <input v-model="form.name" maxlength="150" :placeholder="$t('funds.create.namePlaceholder')" />
    </label>

    <label>
      <span class="label">{{ $t('funds.create.address') }} · {{ $t('common.optional') }}</span>
      <input v-model="form.address" maxlength="255" :placeholder="$t('funds.create.addressPlaceholder')" />
    </label>

    <!-- Базовая валюта: в ней тариф и долги -->
    <div>
      <span class="label">{{ $t('funds.create.baseCurrency') }}</span>
      <div class="chips">
        <button
          v-for="currency in CURRENCIES"
          :key="currency"
          type="button"
          class="chip"
          :class="{ 'chip--active': form.base_currency === currency }"
          @click="form.base_currency = currency"
        >
          {{ $t(`currency.${currency}`) }}
        </button>
      </div>
      <p class="hint">{{ $t('funds.create.baseCurrencyHint') }}</p>
    </div>

    <!-- Дополнительные счета -->
    <div>
      <span class="label">{{ $t('funds.create.extraCurrencies') }}</span>
      <div class="chips">
        <button
          v-for="currency in CURRENCIES.filter((c) => c !== form.base_currency)"
          :key="currency"
          type="button"
          class="chip"
          :class="{ 'chip--active': form.extra.includes(currency) }"
          @click="toggleExtra(currency)"
        >
          {{ form.extra.includes(currency) ? '✓' : '+' }} {{ currency.toUpperCase() }}
        </button>
      </div>
    </div>

    <div class="two">
      <label>
        <span class="label">{{ $t('funds.create.rate', { currency: form.base_currency.toUpperCase() }) }}</span>
        <input v-model.number="form.monthly_rate" type="number" min="0" inputmode="numeric" />
      </label>
      <label>
        <span class="label">{{ $t('funds.create.myUnit') }}</span>
        <input v-model="form.address_unit" maxlength="50" :placeholder="$t('funds.join.unitPlaceholder')" />
      </label>
    </div>

    <label>
      <span class="label">{{ $t('funds.create.description') }} · {{ $t('common.optional') }}</span>
      <textarea v-model="form.description" rows="2" />
    </label>

    <p v-if="error" class="error">{{ error }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">🚀 {{ $t('funds.create.submit') }}</button>
    <p class="hint hint--center">{{ $t('funds.create.chairmanNote') }}</p>
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

.two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
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

.hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: $text-muted;

  &--center {
    margin-top: -6px;
    text-align: center;
  }
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
