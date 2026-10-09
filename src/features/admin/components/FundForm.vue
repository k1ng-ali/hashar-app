<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatMoney } from '@/shared/lib/format.ts'
import { TARGET_FUND_CATEGORIES, type TargetFundCategory } from '@/features/targetFunds/types.ts'
import { type Currency } from '@/shared/lib/currency.ts'
import type { TargetFundCreate } from '../types.ts'

const PRESETS = [5000, 10000, 50000, 100000, 280000]

const props = defineProps<{
  currencies: Currency[]
  baseCurrency: Currency
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: TargetFundCreate): void
}>()

const { t } = useI18n()

const form = reactive({
  title: '',
  category: 'landscaping' as TargetFundCategory,
  target_amount: 10000 as number | null,
  currency: props.baseCurrency as Currency,
  description: '',
})
const error = ref('')

function handleSubmit() {
  if (form.title.trim().length < 3 || !form.target_amount || form.target_amount < 1 || form.description.trim().length < 3) {
    error.value = t('admin.funds.validation')
    return
  }
  error.value = ''
  emit('submit', {
    title: form.title.trim(),
    category: form.category,
    target_amount: form.target_amount,
    currency: form.currency,
    description: form.description.trim(),
  })
}
</script>

<template>
  <form class="form" @submit.prevent="handleSubmit">
    <label>
      <span class="label">{{ $t('admin.funds.titleLabel') }}</span>
      <input v-model="form.title" maxlength="200" :placeholder="$t('admin.funds.titlePlaceholder')" />
    </label>

    <div>
      <span class="label">{{ $t('admin.funds.category') }}</span>
      <div class="chips">
        <button
          v-for="category in TARGET_FUND_CATEGORIES"
          :key="category"
          type="button"
          class="chip"
          :class="{ 'chip--active': form.category === category }"
          @click="form.category = category"
        >
          {{ $t(`targetFundCategory.${category}`) }}
        </button>
      </div>
    </div>

    <div>
      <span class="label">{{ $t('admin.funds.currency') }}</span>
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
      <span class="label">{{ $t('admin.funds.target', { currency: form.currency.toUpperCase() }) }}</span>
      <input v-model.number="form.target_amount" type="number" min="1" inputmode="numeric" />
    </label>
    <div class="chips">
      <button
        v-for="preset in PRESETS"
        :key="preset"
        type="button"
        class="chip"
        :class="{ 'chip--active': form.target_amount === preset }"
        @click="form.target_amount = preset"
      >
        {{ formatMoney(preset, form.currency) }}
      </button>
    </div>

    <label>
      <span class="label">{{ $t('admin.funds.description') }}</span>
      <textarea v-model="form.description" rows="4" :placeholder="$t('admin.funds.descriptionPlaceholder')" />
    </label>

    <p v-if="error" class="error">{{ error }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">🚀 {{ $t('admin.funds.save') }}</button>
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
  padding: 7px 12px;
  font-size: 12px;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
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
