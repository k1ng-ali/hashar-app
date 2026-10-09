<script setup lang="ts">
import { formatMoney } from '@/shared/lib/format.ts'
import type { Debtor } from '../types.ts'

defineProps<{
  debtors: Debtor[]
}>()
</script>

<template>
  <div class="debtors">
    <div v-for="debtor in debtors" :key="debtor.user_id" class="debtor">
      <div class="main">
        <span class="unit">{{ debtor.address_unit }}</span>
        <span class="name">{{ debtor.full_name }}</span>
      </div>
      <div class="sum">
        <span class="amount">{{ formatMoney(debtor.debt_amount, debtor.currency) }}</span>
        <span class="months">{{ $t('reports.monthsDebt', { n: debtor.debt_months_count }) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.debtors {
  display: flex;
  flex-direction: column;
}

.debtor {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;

  & + & {
    border-top: 1px solid rgba(35, 73, 112, 0.06);
  }
}

.main,
.sum {
  display: flex;
  flex-direction: column;
}

.sum {
  align-items: flex-end;
}

.unit {
  font-size: 12px;
  font-weight: 700;
  color: $teal;
}

.name {
  font-size: 14px;
  font-weight: 600;
  color: $navy;
}

.amount {
  font-size: 14px;
  font-weight: 800;
  color: $danger;
}

.months {
  font-size: 11px;
  color: $text-muted;
}
</style>
