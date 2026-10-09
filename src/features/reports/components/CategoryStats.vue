<script setup lang="ts">
import ProgressBar from '@/shared/components/ProgressBar.vue'
import { formatMoney } from '@/shared/lib/format.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import type { CategoryStat } from '../types.ts'

defineProps<{
  stats: CategoryStat[]
  currency: Currency
}>()
</script>

<template>
  <div class="stats">
    <div v-for="stat in stats" :key="stat.category" class="stat">
      <div class="row">
        <span class="name">{{ $t(`expenseCategory.${stat.category}`) }}</span>
        <span class="amount">{{ formatMoney(stat.total, currency) }} · {{ stat.percent }}%</span>
      </div>
      <ProgressBar :percent="stat.percent" tone="brand" />
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.stats {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.name {
  font-size: 13px;
  font-weight: 700;
  color: $navy;
}

.amount {
  font-size: 12px;
  color: $text-secondary;
}
</style>
