<script setup lang="ts">
import { LuSend } from '@kalimahapps/vue-icons/lu'
import ReceiptPicker from '@/shared/components/ReceiptPicker.vue'
import type { Currency } from '@/shared/lib/currency.ts'
import { formatMoney } from '@/shared/lib/format.ts'
import type { Requisite } from '@/features/dashboard/types.ts'
import type { TargetFund } from '@/features/targetFunds/types.ts'
import RequisitePicker from './RequisitePicker.vue'
import type { ContributionCategory } from '../types.ts'

defineProps<{
  rate: number
  baseCurrency: Currency
  currency: Currency
  requiredCurrency: Currency | null
  funds: TargetFund[]
  requisites: Requisite[]
  presets: number[]
  debtAmount: number
  validationError: string
  isSubmitting: boolean
}>()

const category = defineModel<ContributionCategory>('category', { required: true })
const targetFundId = defineModel<number | null>('targetFundId', { required: true })
const requisiteId = defineModel<number | null>('requisiteId', { required: true })
const amount = defineModel<number | null>('amount', { required: true })
const receipt = defineModel<string>('receipt', { required: true })
const comment = defineModel<string>('comment', { required: true })

const emit = defineEmits<{
  (e: 'generate'): void
  (e: 'submit'): void
  (e: 'copy', value: string): void
}>()
</script>

<template>
  <form class="contribution-form" @submit.prevent="emit('submit')">
    <!-- Долг: заполнить сумму одним нажатием -->
    <button
      v-if="debtAmount && category === 'monthly_fee'"
      type="button"
      class="debt-fill"
      @click="amount = debtAmount"
    >
      ⚠️ {{ $t('contribution.fillDebt', { amount: formatMoney(debtAmount, baseCurrency) }) }}
    </button>

    <!-- 1. Назначение -->
    <div class="field">
      <span class="label">{{ $t('contribution.purpose') }}</span>
      <div class="segmented">
        <button
          type="button"
          class="segment"
          :class="{ 'segment--active': category === 'monthly_fee' }"
          @click="category = 'monthly_fee'"
        >
          {{ $t('contribution.monthlyFee', { amount: formatMoney(rate, baseCurrency) }) }}
        </button>
        <button
          type="button"
          class="segment"
          :class="{ 'segment--active': category === 'target_fund' }"
          @click="category = 'target_fund'"
        >
          {{ $t('contribution.targetFund') }}
        </button>
      </div>
    </div>

    <div v-if="category === 'target_fund'" class="field">
      <span class="label">{{ $t('contribution.selectFund') }}</span>
      <a-select
        v-if="funds.length"
        :value="targetFundId ?? undefined"
        size="large"
        class="select"
        :placeholder="$t('contribution.selectFundPlaceholder')"
        :options="funds.map((f) => ({ value: f.id, label: `${f.title} · ${f.currency.toUpperCase()} · ${f.percent}%` }))"
        @update:value="(value) => (targetFundId = typeof value === 'number' ? value : null)"
      />
      <p v-else class="hint">{{ $t('contribution.noActiveFunds') }}</p>
    </div>

    <!-- 2. Куда переводите (реквизит определяет валюту) -->
    <div v-if="requiredCurrency" class="field">
      <span class="label">{{ $t('contribution.toAccount', { currency: requiredCurrency.toUpperCase() }) }}</span>
      <RequisitePicker v-if="requisites.length" v-model="requisiteId" :requisites="requisites" @copy="emit('copy', $event)" />
      <p v-else class="hint hint--warn">{{ $t('contribution.noRequisites', { currency: requiredCurrency.toUpperCase() }) }}</p>
    </div>

    <!-- 3. Сумма в валюте счёта -->
    <div class="field">
      <span class="label">{{ $t('contribution.amount', { currency: currency.toUpperCase() }) }}</span>
      <div class="amount-box">
        <input v-model.number="amount" type="number" min="1" inputmode="numeric" placeholder="0" />
        <span class="currency">{{ currency.toUpperCase() }}</span>
      </div>
      <div v-if="presets.length" class="chips">
        <button
          v-for="value in presets"
          :key="value"
          type="button"
          class="chip"
          :class="{ 'chip--active': amount === value }"
          @click="amount = value"
        >
          {{ formatMoney(value, baseCurrency) }}
        </button>
      </div>
    </div>

    <!-- 4. Чек -->
    <div class="field">
      <span class="label">{{ $t('contribution.receipt') }}</span>
      <ReceiptPicker v-model="receipt" @generate="emit('generate')" />
    </div>

    <div class="field">
      <span class="label">{{ $t('contribution.comment') }} · {{ $t('common.optional') }}</span>
      <textarea v-model="comment" rows="2" :placeholder="$t('contribution.commentPlaceholder')" />
    </div>

    <p v-if="validationError" class="error">{{ validationError }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">
      <LuSend /> {{ $t('contribution.submit') }}
    </button>
    <p class="note">{{ $t('contribution.note') }}</p>
  </form>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.contribution-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.label {
  @include field-label;
}

textarea {
  @include field-input;
  resize: vertical;
}

.select {
  width: 100%;
}

.hint {
  margin: 0;
  font-size: 13px;
  color: $text-muted;

  &--warn {
    color: #B45309;
  }
}

/* ── Debt ─────────────────────────────────────────────────────────────────── */
.debt-fill {
  @include pressable;
  padding: 12px;
  border: 1px solid rgba(239, 68, 68, 0.25);
  border-radius: 14px;
  background: rgba(254, 242, 242, 0.9);
  color: #B91C1C;
  font-size: 13px;
  font-weight: 700;
}

/* ── Segmented ────────────────────────────────────────────────────────────── */
.segmented {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 4px;
  border-radius: 16px;
  background: rgba(35, 73, 112, 0.06);
}

.segment {
  @include pressable;
  padding: 10px 8px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: $text-secondary;
  font-size: 13px;
  font-weight: 700;

  &--active {
    background: #fff;
    color: $navy;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
}

/* ── Amount ───────────────────────────────────────────────────────────────── */
.amount-box {
  position: relative;

  input {
    @include field-input;
    padding-right: 64px;
    font-size: 24px;
    font-weight: 800;
    color: $navy;
  }
}

.currency {
  position: absolute;
  top: 50%;
  right: 16px;
  transform: translateY(-50%);
  font-size: 16px;
  font-weight: 800;
  color: $text-muted;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
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

/* ── Submit ───────────────────────────────────────────────────────────────── */
.error {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: $danger;
}

.submit-btn {
  @include cta-button;
  width: 100%;
}

.note {
  margin: -6px 0 0;
  font-size: 12px;
  text-align: center;
  color: $text-muted;
}
</style>
