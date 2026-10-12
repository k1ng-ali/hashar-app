<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { type Currency } from '@/shared/lib/currency.ts'
import type { TransferCreate } from '../types.ts'
import OverdraftNotice from './OverdraftNotice.vue'

type TransferMode = 'transfer' | 'income' | 'outcome'

const props = defineProps<{
  currencies: Currency[]
  /** Остатки счетов — чтобы предупредить о списании в минус. */
  balances: Partial<Record<Currency, number>>
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: TransferCreate): void
}>()

const { t } = useI18n()

const mode = ref<TransferMode>(props.currencies.length > 1 ? 'transfer' : 'income')
const form = reactive({
  from_currency: props.currencies[0] as Currency,
  from_amount: null as number | null,
  to_currency: (props.currencies[1] ?? props.currencies[0]) as Currency,
  to_amount: null as number | null,
  comment: '',
  allowOverdraft: false,
})
const error = ref('')

const showFrom = computed(() => mode.value !== 'income')
const showTo = computed(() => mode.value !== 'outcome')
const available = computed(() => props.balances[form.from_currency] ?? 0)
const needsConfirm = computed(
  () => showFrom.value && (form.from_amount ?? 0) > available.value && !form.allowOverdraft,
)

function handleSubmit() {
  const fromOk = !showFrom.value || (form.from_amount ?? 0) > 0
  const toOk = !showTo.value || (form.to_amount ?? 0) > 0
  if (!fromOk || !toOk || form.comment.trim().length < 3) {
    error.value = t('admin.accounts.validation')
    return
  }
  if (mode.value === 'transfer' && form.from_currency === form.to_currency) {
    error.value = t('admin.accounts.sameCurrency')
    return
  }
  if (needsConfirm.value) {
    error.value = t('overdraft.required')
    return
  }
  error.value = ''
  emit('submit', {
    from_currency: showFrom.value ? form.from_currency : null,
    from_amount: showFrom.value ? form.from_amount : null,
    to_currency: showTo.value ? form.to_currency : null,
    to_amount: showTo.value ? form.to_amount : null,
    comment: form.comment.trim(),
    allow_overdraft: showFrom.value && form.allowOverdraft,
  })
}
</script>

<template>
  <form class="form" @submit.prevent="handleSubmit">
    <div class="modes">
      <button
        v-for="item in ['transfer', 'income', 'outcome'] as TransferMode[]"
        :key="item"
        type="button"
        class="mode"
        :class="{ 'mode--active': mode === item }"
        :disabled="item === 'transfer' && currencies.length < 2"
        @click="mode = item"
      >
        {{ $t(`admin.accounts.modes.${item}`) }}
      </button>
    </div>
    <p class="hint">{{ $t(`admin.accounts.modeHints.${mode}`) }}</p>

    <!-- Списание -->
    <div v-if="showFrom" class="side side--out">
      <span class="label">{{ $t('admin.accounts.from') }}</span>
      <div class="row">
        <div class="currencies" role="radiogroup">
          <button
            v-for="c in currencies"
            :key="c"
            type="button"
            role="radio"
            class="currency"
            :class="{ 'currency--active': form.from_currency === c }"
            :aria-checked="form.from_currency === c"
            @click="form.from_currency = c"
          >
            {{ c.toUpperCase() }}
          </button>
        </div>
        <div class="amount">
          <input v-model.number="form.from_amount" type="number" min="1" inputmode="numeric" placeholder="0" />
          <span class="amount-currency">{{ form.from_currency.toUpperCase() }}</span>
        </div>
      </div>
      <OverdraftNotice
        v-model="form.allowOverdraft"
        :available="available"
        :amount="form.from_amount"
        :currency="form.from_currency"
      />
    </div>

    <!-- Зачисление -->
    <div v-if="showTo" class="side side--in">
      <span class="label">{{ $t('admin.accounts.to') }}</span>
      <div class="row">
        <div class="currencies" role="radiogroup">
          <button
            v-for="c in currencies"
            :key="c"
            type="button"
            role="radio"
            class="currency"
            :class="{ 'currency--active': form.to_currency === c }"
            :aria-checked="form.to_currency === c"
            @click="form.to_currency = c"
          >
            {{ c.toUpperCase() }}
          </button>
        </div>
        <div class="amount">
          <input v-model.number="form.to_amount" type="number" min="1" inputmode="numeric" placeholder="0" />
          <span class="amount-currency">{{ form.to_currency.toUpperCase() }}</span>
        </div>
      </div>
    </div>
    <p v-if="mode === 'transfer'" class="hint">💱 {{ $t('admin.accounts.noRates') }}</p>

    <label>
      <span class="label">{{ $t('admin.accounts.comment') }}</span>
      <textarea v-model="form.comment" rows="2" :placeholder="$t('admin.accounts.commentPlaceholder')" />
    </label>

    <p class="hint">📢 {{ $t('admin.accounts.publicNote') }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">{{ $t('admin.accounts.submit') }}</button>
  </form>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modes {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  padding: 4px;
  border-radius: 16px;
  background: rgba(17, 24, 39, 0.06);
}

.mode {
  @include pressable;
  padding: 9px 6px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: $text-secondary;
  font-size: 12px;
  font-weight: 700;

  &--active {
    background: #fff;
    color: $navy;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  &:disabled {
    opacity: 0.4;
  }
}

.side {
  padding: 12px;
  border-radius: 16px;

  &--out {
    background: rgba(239, 68, 68, 0.06);
  }

  &--in {
    background: rgba(16, 185, 129, 0.07);
  }
}

.row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.currencies {
  display: flex;
  gap: 6px;
}

.currency {
  @include pressable;
  flex: 1;
  padding: 8px 0;
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 12px;
  background: $surface;
  color: $text-secondary;
  font-size: 13px;
  font-weight: 600;

  &--active {
    border-color: transparent;
    background: #111827;
    color: #fff;
  }
}

.amount {
  position: relative;

  input {
    padding-right: 56px;
  }
}

.amount-currency {
  position: absolute;
  top: 50%;
  right: 14px;
  transform: translateY(-50%);
  font-size: 13px;
  font-weight: 600;
  color: $text-muted;
}

.label {
  @include field-label;
}

input,
textarea {
  @include field-input;
}

input {
  font-size: 18px;
  font-weight: 700;
}

textarea {
  resize: vertical;
}

.hint {
  margin: -6px 0 0;
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
}
</style>
