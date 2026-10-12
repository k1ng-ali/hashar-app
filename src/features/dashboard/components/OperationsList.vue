<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { LuArrowDownLeft, LuArrowLeftRight, LuArrowUpRight } from '@kalimahapps/vue-icons/lu'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { formatDateTime, formatMoney } from '@/shared/lib/format.ts'
import type { Operation } from '../types.ts'

defineProps<{
  operations: Operation[]
}>()

const emit = defineEmits<{
  (e: 'open-receipt', operation: Operation): void
  (e: 'open-expense', operation: Operation): void
}>()

const { t } = useI18n()

// Подпись: для взноса — название сбора или «Ежемесячный взнос», для расхода — категория и автор
function subtitle(operation: Operation): string {
  if (operation.type === 'income') {
    return operation.subtitle || t(`contributionCategory.${operation.category}`)
  }
  if (operation.type === 'transfer') {
    return `${t(`transfers.${operation.category}`)} · ${operation.subtitle}`
  }
  const category = t(`expenseCategory.${operation.category}`)
  return operation.subtitle ? `${category} · ${operation.subtitle}` : category
}

function amountLabel(operation: Operation): string {
  if (operation.type === 'transfer' && operation.counter_amount !== null && operation.counter_currency) {
    return `${formatMoney(operation.counter_amount, operation.counter_currency)} → ${formatMoney(operation.amount, operation.currency)}`
  }
  const sign = operation.type === 'expense' || operation.amount < 0 ? '−' : '+'
  return `${sign}${formatMoney(Math.abs(operation.amount), operation.currency)}`
}
</script>

<template>
  <div class="operations">
    <div v-for="operation in operations" :key="operation.id" class="operation">
      <span class="op-icon" :class="`op-icon--${operation.type}`">
        <LuArrowDownLeft v-if="operation.type === 'income'" />
        <LuArrowLeftRight v-else-if="operation.type === 'transfer'" />
        <LuArrowUpRight v-else />
      </span>

      <div
        class="op-main"
        :class="{ 'op-main--link': operation.type === 'expense' }"
        @click="operation.type === 'expense' && emit('open-expense', operation)"
      >
        <div class="op-row">
          <span class="op-title">{{ operation.title }}</span>
          <span class="op-amount" :class="`op-amount--${operation.type}`">{{ amountLabel(operation) }}</span>
        </div>
        <div class="op-meta">
          <span class="op-subtitle">{{ subtitle(operation) }}</span>
          <span>· {{ formatDateTime(operation.created_at) }}</span>
          <StatusBadge v-if="operation.status && operation.status !== 'approved'" :status="operation.status" />
        </div>
      </div>

      <button
        v-if="operation.receipt_image"
        class="receipt-thumb"
        :aria-label="$t('receipt.view')"
        @click="emit('open-receipt', operation)"
      >
        <img :src="operation.receipt_image" alt="" />
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.operations {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.operation {
  @include glass-card(18px);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
}

.op-icon {
  @include icon-circle(40px);

  &--income {
    background: rgba(22, 163, 74, 0.1);
    color: $success;
  }

  &--expense {
    background: rgba(229, 72, 77, 0.1);
    color: $danger;
  }

  &--transfer {
    background: $surface-muted;
    color: $navy;
  }
}

.op-main {
  flex: 1;
  min-width: 0;
}

.op-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.op-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 15px;
  font-weight: 500;
  color: $navy;
}

.op-amount {
  flex-shrink: 0;
  font-size: 15px;
  font-weight: 600;

  &--income {
    color: $success;
  }

  &--expense {
    color: $danger;
  }

  &--transfer {
    color: $navy;
  }
}

.op-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 6px;
  margin-top: 3px;
  font-size: 12px;
  color: $text-muted;
}

.op-subtitle {
  overflow: hidden;
  max-width: 60%;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.receipt-thumb {
  @include pressable;
  flex-shrink: 0;
  width: 36px;
  height: 46px;
  padding: 0;
  overflow: hidden;
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 8px;
  background: #fff;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.op-main--link {
  cursor: pointer;

  .op-title {
    text-decoration: underline;
    text-decoration-color: rgba(17, 24, 39, 0.2);
    text-underline-offset: 3px;
  }
}
</style>
