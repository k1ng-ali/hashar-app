<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDate, formatMoney } from '@/shared/lib/format.ts'
import type { PlatformPlans, PlatformTab } from '../types.ts'
import BarChart, { type BarSeries } from './BarChart.vue'

const props = defineProps<{
  plans: PlatformPlans
}>()

const emit = defineEmits<{
  (e: 'go', tab: PlatformTab): void
}>()

const { t } = useI18n()

const tjs = (value: number) => formatMoney(value, 'tjs')
const periods = computed(() => props.plans.revenue.map((r) => r.period))
const revenueSeries = computed<BarSeries[]>(() => [
  { key: 'revenue', label: t('platform.plans.revenue'), values: props.plans.revenue.map((r) => r.amount_tjs), tone: 'ink' },
])

const fundsTotal = computed(() => props.plans.distribution.reduce((sum, d) => sum + d.funds, 0))
const share = (n: number) => (fundsTotal.value ? Math.round((n / fundsTotal.value) * 100) : 0)

const daysLeft = (iso: string) => Math.max(0, Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000))
</script>

<template>
  <div class="plans">
    <!-- 1. Выручка -->
    <div class="tiles">
      <div class="tile">
        <span class="tile-label">{{ $t('platform.plans.mrr') }}</span>
        <b class="tile-value">{{ tjs(plans.mrr_tjs) }}</b>
      </div>
      <div class="tile">
        <span class="tile-label">{{ $t('platform.plans.revenue30') }}</span>
        <b class="tile-value">{{ tjs(plans.revenue_30d_tjs) }}</b>
      </div>
      <div class="tile">
        <span class="tile-label">{{ $t('platform.plans.revenueTotal') }}</span>
        <b class="tile-value">{{ tjs(plans.revenue_total_tjs) }}</b>
      </div>
    </div>

    <section class="card">
      <h2 class="card-title">{{ $t('platform.plans.revenueByMonth') }}</h2>
      <BarChart :periods="periods" :series="revenueSeries" :format="tjs" />
      <p class="note">{{ $t('platform.plans.revenueHint') }}</p>
    </section>

    <!-- 2. Распределение по тарифам -->
    <section class="card">
      <h2 class="card-title">{{ $t('platform.plans.distribution') }}</h2>
      <div class="rows">
        <div v-for="d in plans.distribution" :key="d.plan" class="row">
          <span class="row-name">{{ $t(`plans.${d.plan}`) }}</span>
          <span class="track"><span class="fill" :style="{ width: `${share(d.funds)}%` }" /></span>
          <b class="row-value">{{ d.funds }}</b>
        </div>
      </div>
    </section>

    <!-- 3. Заявки -->
    <section class="card">
      <div class="card-head">
        <h2 class="card-title">{{ $t('platform.plans.requests') }}</h2>
        <button type="button" class="link" @click="emit('go', 'requests')">{{ $t('platform.plans.openRequests') }}</button>
      </div>
      <div class="chips">
        <span class="chip">{{ $t('platform.plans.pending') }} <b>{{ plans.requests.pending }}</b></span>
        <span class="chip">{{ $t('platform.plans.approved') }} <b>{{ plans.requests.approved }}</b></span>
        <span class="chip">{{ $t('platform.plans.rejected') }} <b>{{ plans.requests.rejected }}</b></span>
      </div>
    </section>

    <!-- 4. Скоро истекают -->
    <section class="card">
      <h2 class="card-title">{{ $t('platform.plans.expiring') }}</h2>
      <div v-if="plans.expiring.length" class="rows">
        <div v-for="fund in plans.expiring" :key="fund.id" class="expiring">
          <div>
            <b>{{ fund.name }}</b>
            <span class="meta">{{ fund.code }} · {{ $t(`plans.${fund.plan}`) }}</span>
          </div>
          <div class="expiring-date">
            <b>{{ $t('platform.plans.daysLeft', { n: daysLeft(fund.plan_expires_at) }) }}</b>
            <span class="meta">{{ formatDate(fund.plan_expires_at) }}</span>
          </div>
        </div>
      </div>
      <p v-else class="note">{{ $t('platform.plans.noExpiring') }}</p>
    </section>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.plans {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tiles {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.tile {
  @include glass-card(16px);
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  padding: 12px;
}

.tile-label {
  font-size: 11px;
  line-height: 1.3;
  color: $text-muted;
}

.tile-value {
  font-size: 17px;
  font-weight: 700;
  color: $navy;
  overflow-wrap: anywhere;
}

.card {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
}

.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.card-title {
  @include section-title;
  font-size: 15px;
}

.note {
  margin: 0;
  font-size: 12px;
  color: $text-muted;
}

.link {
  padding: 0;
  border: none;
  background: none;
  color: $navy;
  font-size: 13px;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
}

/* ── Распределение ────────────────────────────────────────────────────── */
.rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

// Строки распределения делят одну сетку — колонка названий по самому длинному
.rows:has(.row) {
  display: grid;
  grid-template-columns: max-content 1fr auto;
  align-items: center;
  gap: 8px 10px;
}

.row {
  display: contents;
  font-size: 13px;
  color: $text-secondary;
}

.track {
  height: 8px;
  overflow: hidden;
  border-radius: 4px;
  background: $surface-muted;
}

.fill {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: #111827;
}

.row-name {
  font-size: 13px;
  color: $text-secondary;
}

.row-value {
  font-size: 13px;
  text-align: right;
  color: $navy;
}

/* ── Заявки ───────────────────────────────────────────────────────────── */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  padding: 4px 10px;
  border-radius: 20px;
  background: $surface-muted;
  font-size: 12px;
  color: $text-secondary;

  b {
    color: $navy;
  }
}

/* ── Истекающие ───────────────────────────────────────────────────────── */
.expiring {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  font-size: 14px;
  color: $navy;

  b,
  .meta {
    display: block;
  }
}

.expiring-date {
  text-align: right;
}

.meta {
  font-size: 12px;
  color: $text-muted;
}
</style>
