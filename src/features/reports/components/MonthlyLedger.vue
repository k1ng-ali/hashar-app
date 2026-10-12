<script setup lang="ts">
import { formatMoney, formatPeriod } from '@/shared/lib/format.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import type { MonthlyLedgerRow } from '../types.ts'

defineProps<{
  rows: MonthlyLedgerRow[]
  rate: number
  currency: Currency
  baseCurrency: Currency
}>()
</script>

<template>
  <div class="ledger">
    <div v-for="row in rows" :key="row.period" class="month" :class="{ 'month--current': row.is_current }">
      <div class="month-top">
        <span class="name">{{ formatPeriod(row.period) }}</span>
        <span class="badge" :class="{ 'badge--current': row.is_current }">
          {{ row.is_current ? $t('reports.currentMonth') : $t('reports.closedMonth') }}
        </span>
      </div>

      <div class="cells">
        <div class="cell">
          <span class="label">{{ $t('reports.income') }}</span>
          <span class="value value--in">{{ formatMoney(row.income, currency, true) }}</span>
        </div>
        <div class="cell">
          <span class="label">{{ $t('reports.expense') }}</span>
          <span class="value value--out">−{{ formatMoney(row.expense, currency) }}</span>
        </div>
        <div class="cell">
          <span class="label">{{ $t('reports.delta') }}</span>
          <span class="value" :class="row.delta >= 0 ? 'value--in' : 'value--out'">
            {{ formatMoney(row.delta, currency, true) }}
          </span>
        </div>
        <div class="cell">
          <span class="label">{{ $t('reports.rate') }}</span>
          <span class="value">{{ formatMoney(rate, baseCurrency) }} {{ $t('common.perMonth') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.ledger {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.month {
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);

  &--current {
    border: 1px solid rgba(17, 24, 39, 0.45);
  }
}

.month-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.name {
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.badge {
  padding: 2px 10px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.08);
  color: $text-secondary;
  font-size: 11px;
  font-weight: 700;

  &--current {
    background: $gradient;
    color: #fff;
  }
}

.cells {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 12px;
}

.cell {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 11px;
  color: $text-muted;
}

.value {
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

@media (min-width: 768px) {
  .cells {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
