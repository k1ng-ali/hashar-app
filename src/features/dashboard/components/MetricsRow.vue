<script setup lang="ts">
import { LuArrowDownLeft, LuArrowUpRight, LuUsers } from '@kalimahapps/vue-icons/lu'
import { formatMoney, formatPeriod } from '@/shared/lib/format.ts'
import type { AccountSummary } from '../types.ts'

// Метрики месяца — по базовому счёту фонда
defineProps<{
  account: AccountSummary
  period: string
  payingCount: number
  membersCount: number
}>()
</script>

<template>
  <div class="metrics">
    <div class="metric">
      <span class="metric-icon metric-icon--in"><LuArrowDownLeft /></span>
      <span class="metric-name">{{ $t('dashboard.metrics.collected', { month: formatPeriod(period, true) }) }}</span>
      <span class="metric-value metric-value--in">{{ formatMoney(account.month_collected, account.currency, true) }}</span>
    </div>

    <div class="metric">
      <span class="metric-icon metric-icon--out"><LuArrowUpRight /></span>
      <span class="metric-name">{{ $t('dashboard.metrics.spent') }}</span>
      <span class="metric-value metric-value--out">{{ account.month_spent ? '−' : '' }}{{ formatMoney(account.month_spent, account.currency) }}</span>
    </div>

    <div class="metric">
      <span class="metric-icon"><LuUsers /></span>
      <span class="metric-name">{{ $t('dashboard.metrics.discipline') }}</span>
      <span class="metric-value">{{ payingCount }} / {{ membersCount }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.metric {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 12px;
}

.metric-icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  margin-bottom: 4px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.08);
  color: $navy;
  font-size: 16px;

  &--in {
    background: rgba(16, 185, 129, 0.12);
    color: $success;
  }

  &--out {
    background: rgba(239, 68, 68, 0.1);
    color: $danger;
  }
}

.metric-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: $text-secondary;
}

.metric-value {
  font-size: 14px;
  font-weight: 700;
  color: $navy;

  &--in {
    color: $success;
  }

  &--out {
    color: $danger;
  }
}
</style>
