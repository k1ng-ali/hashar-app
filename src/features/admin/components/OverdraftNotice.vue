<script setup lang="ts">
import { computed, watch } from 'vue'
import type { Currency } from '@/shared/lib/currency.ts'
import { formatMoney } from '@/shared/lib/format.ts'

const props = defineProps<{
  available: number
  amount: number | null
  currency: Currency
}>()

/** Совет явно подтвердил списание сверх остатка. */
const confirmed = defineModel<boolean>({ required: true })

const isOverdraft = computed(() => (props.amount ?? 0) > props.available)
const after = computed(() => props.available - (props.amount ?? 0))

// Сумма снова в пределах остатка — подтверждение больше не нужно
watch(isOverdraft, (value) => {
  if (!value) confirmed.value = false
})
</script>

<template>
  <div class="overdraft" :class="{ 'overdraft--warn': isOverdraft }">
    <span class="available">
      {{ $t('overdraft.available', { amount: formatMoney(available, currency) }) }}
    </span>

    <template v-if="isOverdraft">
      <p class="warning">
        ⚠️ {{ $t('overdraft.warning', { amount: formatMoney(after, currency) }) }}
      </p>
      <label class="confirm">
        <input v-model="confirmed" type="checkbox" />
        <span>{{ $t('overdraft.confirm') }}</span>
      </label>
    </template>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.overdraft {
  display: flex;
  flex-direction: column;
  gap: 6px;

  &--warn {
    padding: 12px;
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 14px;
    background: rgba(254, 242, 242, 0.9);
  }
}

.available {
  font-size: 12px;
  font-weight: 600;
  color: $text-muted;
}

.warning {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.45;
  color: #B91C1C;
}

.confirm {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.4;
  color: $navy;
  cursor: pointer;

  input {
    flex-shrink: 0;
    width: 18px;
    height: 18px;
    margin-top: 1px;
    accent-color: $danger;
  }
}
</style>
