<script setup lang="ts">
import { computed, ref } from 'vue'
import { formatPeriod } from '@/shared/lib/format.ts'

/**
 * Столбцы по месяцам, одна или две серии рядом (без второй оси).
 * Наведение, фокус или тап по месяцу показывает значения всех серий в строке над графиком.
 */
export interface BarSeries {
  key: string
  label: string
  values: number[]
  tone: 'ink' | 'muted'
}

const props = withDefaults(
  defineProps<{
    periods: string[]
    series: BarSeries[]
    format?: (value: number) => string
  }>(),
  { format: (value: number) => value.toLocaleString('ru-RU') },
)

const active = ref<number | null>(null)
const shown = computed(() => active.value ?? props.periods.length - 1)

const peak = computed(() => Math.max(0, ...props.series.flatMap((s) => s.values)))
const max = computed(() => peak.value || 1)
const height = (value: number) => (value > 0 ? `max(${(value / max.value) * 100}%, 3px)` : '0')
</script>

<template>
  <div class="chart">
    <!-- Значения выбранного месяца (по умолчанию — текущего) -->
    <div class="readout" aria-live="polite">
      <span class="readout-period">{{ formatPeriod(periods[shown]) }}</span>
      <span v-for="s in series" :key="s.key" class="readout-item">
        <i class="key" :class="`key--${s.tone}`" />
        <b>{{ format(s.values[shown] ?? 0) }}</b>
        <span v-if="series.length > 1" class="readout-label">{{ s.label }}</span>
      </span>
    </div>

    <div class="plot">
      <span v-if="peak" class="max">{{ format(peak) }}</span>
      <div class="columns" @mouseleave="active = null">
        <button
          v-for="(period, i) in periods"
          :key="period"
          type="button"
          class="column"
          :class="{ 'column--active': i === shown }"
          :aria-label="`${formatPeriod(period)}: ${series.map((s) => `${s.label} ${format(s.values[i] ?? 0)}`).join(', ')}`"
          @mouseenter="active = i"
          @focus="active = i"
          @click="active = i"
        >
          <span class="bars">
            <span
              v-for="s in series"
              :key="s.key"
              class="bar"
              :class="`bar--${s.tone}`"
              :style="{ height: height(s.values[i] ?? 0) }"
            />
          </span>
          <span class="label">{{ formatPeriod(period, true) }}</span>
        </button>
      </div>
    </div>

    <div v-if="series.length > 1" class="legend">
      <span v-for="s in series" :key="s.key" class="legend-item">
        <i class="swatch" :class="`key--${s.tone}`" />{{ s.label }}
      </span>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

$ink: #111827;
$muted: #8b8b94;

.chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ── Строка значений ──────────────────────────────────────────────────── */
.readout {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 14px;
  min-height: 22px;
  font-size: 13px;
  color: $text-secondary;

  b {
    font-size: 15px;
    color: $navy;
  }
}

.readout-period {
  font-weight: 600;
  color: $text-muted;
}

.readout-item {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
}

.key {
  display: inline-block;
  width: 10px;
  height: 2px;
  border-radius: 1px;
  transform: translateY(-3px);

  &--ink {
    background: $ink;
  }

  &--muted {
    background: $muted;
  }
}

/* ── Поле графика ─────────────────────────────────────────────────────── */
.plot {
  position: relative;
  padding-top: 16px;
}

.max {
  position: absolute;
  top: 0;
  left: 0;
  font-size: 10px;
  color: $text-muted;
}

.columns {
  display: flex;
  align-items: stretch;
  gap: 2px;
  height: 150px;
  border-top: 1px dashed $hairline;
}

.column {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;

  &--active {
    background: $surface-muted;
  }

  &:focus-visible {
    outline: 2px solid $ink;
    outline-offset: 1px;
  }
}

.bars {
  display: flex;
  flex: 1;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.16);
}

.bar {
  width: min(12px, 40%);
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;

  &--ink {
    background: $ink;
  }

  &--muted {
    background: $muted;
  }
}

.label {
  padding-top: 4px;
  overflow: hidden;
  font-size: 10px;
  color: $text-muted;
  text-align: center;
  white-space: nowrap;
}

/* ── Легенда ──────────────────────────────────────────────────────────── */
.legend {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: $text-secondary;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
}
</style>
