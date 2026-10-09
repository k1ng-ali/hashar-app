<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { type Currency } from '@/shared/lib/currency.ts'
import type { TransferCreate } from '../types.ts'

type TransferMode = 'transfer' | 'income' | 'outcome'

const props = defineProps<{
  currencies: Currency[]
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
})
const error = ref('')

const showFrom = computed(() => mode.value !== 'income')
const showTo = computed(() => mode.value !== 'outcome')

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
  error.value = ''
  emit('submit', {
    from_currency: showFrom.value ? form.from_currency : null,
    from_amount: showFrom.value ? form.from_amount : null,
    to_currency: showTo.value ? form.to_currency : null,
    to_amount: showTo.value ? form.to_amount : null,
    comment: form.comment.trim(),
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
        <select v-model="form.from_currency">
          <option v-for="c in currencies" :key="c" :value="c">{{ c.toUpperCase() }}</option>
        </select>
        <input v-model.number="form.from_amount" type="number" min="1" inputmode="numeric" placeholder="0" />
      </div>
    </div>

    <!-- Зачисление -->
    <div v-if="showTo" class="side side--in">
      <span class="label">{{ $t('admin.accounts.to') }}</span>
      <div class="row">
        <select v-model="form.to_currency">
          <option v-for="c in currencies" :key="c" :value="c">{{ c.toUpperCase() }}</option>
        </select>
        <input v-model.number="form.to_amount" type="number" min="1" inputmode="numeric" placeholder="0" />
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
  background: rgba(35, 73, 112, 0.06);
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
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 8px;
}

.label {
  @include field-label;
}

input,
select,
textarea {
  @include field-input;
}

input {
  font-size: 18px;
  font-weight: 800;
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
