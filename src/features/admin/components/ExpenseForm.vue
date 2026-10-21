<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import PhotosPicker from '@/shared/components/PhotosPicker.vue'
import { generateReceiptSvg } from '@/shared/lib/receiptGenerator.ts'
import type { TargetFund } from '@/features/targetFunds/types.ts'
import { type Currency } from '@/shared/lib/currency.ts'
import { EXPENSE_CATEGORIES, type ExpenseCategory } from '@/features/expenses/types.ts'
import type { ExpenseCreate } from '../types.ts'
import OverdraftNotice from './OverdraftNotice.vue'

const props = defineProps<{
  funds: TargetFund[]
  fundName: string
  currencies: Currency[]
  baseCurrency: Currency
  /** Остатки счетов — чтобы предупредить о списании в минус. */
  balances: Partial<Record<Currency, number>>
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: ExpenseCreate): void
}>()

const { t } = useI18n()

const form = reactive({
  title: '',
  category: 'household' as ExpenseCategory,
  amount: null as number | null,
  currency: props.baseCurrency as Currency,
  description: '',
  // Ключи загруженных фото: чек, фото проблемы, результат — до трёх
  photos: [] as string[],
  // 0 — общий баланс дома (a-select не принимает null)
  targetFundId: 0,
  allowOverdraft: false,
})
const error = ref('')

const available = computed(() => props.balances[form.currency] ?? 0)
const needsConfirm = computed(() => (form.amount ?? 0) > available.value && !form.allowOverdraft)

// Списать за счёт сбора можно только в его валюте
const fundsInCurrency = computed(() => props.funds.filter((f) => f.currency === form.currency))
watch(
  () => form.currency,
  () => {
    if (!fundsInCurrency.value.some((f) => f.id === form.targetFundId)) form.targetFundId = 0
  },
)

function generateReceipt() {
  form.amount ||= 8500
  const receipt = generateReceiptSvg({
    bankName: 'ООО «Стройторг»',
    amount: form.amount,
    currency: form.currency,
    senderName: props.fundName,
    recipientName: 'ООО «Стройторг»',
    purpose: (form.title || t(`expenseCategory.${form.category}`)).slice(0, 32),
  })
  form.photos = [...form.photos, receipt]
}

function handleSubmit() {
  if (form.title.trim().length < 3 || !form.amount || form.amount <= 0 || form.description.trim().length < 3) {
    error.value = t('admin.expenses.validation')
    return
  }
  if (needsConfirm.value) {
    error.value = t('overdraft.required')
    return
  }
  error.value = ''
  emit('submit', {
    title: form.title.trim(),
    category: form.category,
    amount: form.amount,
    currency: form.currency,
    description: form.description.trim(),
    receipt_images: form.photos,
    target_fund_id: form.targetFundId || null,
    allow_overdraft: form.allowOverdraft,
  })
}
</script>

<template>
  <form class="form" @submit.prevent="handleSubmit">
    <label>
      <span class="label">{{ $t('admin.expenses.titleLabel') }}</span>
      <input v-model="form.title" maxlength="200" :placeholder="$t('admin.expenses.titlePlaceholder')" />
    </label>

    <div class="two">
      <div>
        <span class="label">{{ $t('admin.expenses.category') }}</span>
        <a-select
          v-model:value="form.category"
          size="large"
          class="select"
          :options="EXPENSE_CATEGORIES.map((c) => ({ value: c, label: $t(`expenseCategory.${c}`) }))"
        />
      </div>
      <label>
        <span class="label">{{ $t('admin.expenses.amount', { currency: form.currency.toUpperCase() }) }}</span>
        <input v-model.number="form.amount" type="number" min="1" inputmode="numeric" placeholder="0" />
      </label>
    </div>

    <div>
      <span class="label">{{ $t('admin.expenses.account') }}</span>
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

    <OverdraftNotice
      v-model="form.allowOverdraft"
      :available="available"
      :amount="form.amount"
      :currency="form.currency"
    />

    <div>
      <span class="label">{{ $t('admin.expenses.fromFund') }}</span>
      <a-select
        v-model:value="form.targetFundId"
        size="large"
        class="select"
        :options="[
          { value: 0, label: $t('admin.expenses.generalBalance') },
          ...fundsInCurrency.map((fund) => ({ value: fund.id, label: fund.title })),
        ]"
      />
    </div>

    <label>
      <span class="label">{{ $t('admin.expenses.description') }}</span>
      <textarea v-model="form.description" rows="3" :placeholder="$t('admin.expenses.descriptionPlaceholder')" />
    </label>

    <div>
      <span class="label">{{ $t('admin.expenses.receipt') }}</span>
      <PhotosPicker
        v-model="form.photos"
        :max="3"
        :hint="$t('admin.expenses.photosHint')"
        demo
        @generate="generateReceipt"
      />
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">{{ $t('admin.expenses.save') }}</button>
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

.select {
  width: 100%;
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

.two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
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
