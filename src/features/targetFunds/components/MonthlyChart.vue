<script setup lang="ts">
import { computed } from 'vue'
import { formatPeriod } from '@/shared/lib/format.ts'
import type { MonthAmount } from '../types.ts'

const props = defineProps<{
  months: MonthAmount[]
}>()

const max = computed(() => Math.max(...props.months.map((month) => month.amount), 1))

function shortAmount(amount: number) {
  return amount >= 1000 ? `${Math.round(amount / 1000)}k` : String(amount)
}
</script>

<template>
  <div class="chart">
    <div v-for="(month, index) in months" :key="month.period" class="column">
      <div class="bar-wrap">
        <span v-if="month.amount" class="bar-value">{{ shortAmount(month.amount) }}</span>
        <div
          class="bar"
          :class="{ 'bar--current': index === months.length - 1, 'bar--empty': !month.amount }"
          :style="{ height: `${Math.max((month.amount / max) * 100, 6)}%` }"
        />
      </div>
      <span class="label">{{ formatPeriod(month.period, true) }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.chart {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  height: 160px;
}

.column {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  height: 100%;
}

.bar-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  width: 100%;
  flex: 1;
}

.bar-value {
  margin-bottom: 4px;
  font-size: 10px;
  font-weight: 700;
  color: $navy;
}

.bar {
  width: 100%;
  max-width: 36px;
  border-radius: 10px 10px 6px 6px;
  background: rgba(17, 24, 39, 0.35);
  transition: height 0.6s ease;

  &--current {
    background: $gradient;
  }

  &--empty {
    background: rgba(17, 24, 39, 0.08);
  }
}

.label {
  font-size: 11px;
  font-weight: 600;
  color: $text-muted;
}
</style>
