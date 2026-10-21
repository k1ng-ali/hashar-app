<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SegmentedControl from '@/shared/components/SegmentedControl.vue'
import { formatMoney } from '@/shared/lib/format.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import type { PlatformOverview, PlatformTab } from '../types.ts'
import BarChart, { type BarSeries } from './BarChart.vue'

const props = defineProps<{
  overview: PlatformOverview
}>()

const emit = defineEmits<{
  (e: 'go', tab: PlatformTab): void
}>()

const { t } = useI18n()

const totals = computed(() => props.overview.totals)
const periods = computed(() => props.overview.growth.map((p) => p.period))

// ── Рост ────────────────────────────────────────────────────────────────
type GrowthKind = 'users' | 'funds'
const growthKind = ref<GrowthKind>('users')
const growthOptions = computed(() => [
  { value: 'users' as GrowthKind, label: t('platform.overview.users') },
  { value: 'funds' as GrowthKind, label: t('platform.overview.funds') },
])
const growthSeries = computed<BarSeries[]>(() => [
  {
    key: growthKind.value,
    label: t('platform.overview.newPerMonth'),
    values: props.overview.growth.map((p) => p[growthKind.value]),
    tone: 'ink',
  },
])
const growthTotal = computed(() => {
  const last = props.overview.growth[props.overview.growth.length - 1]
  return last ? last[growthKind.value === 'users' ? 'users_total' : 'funds_total'] : 0
})

// ── Деньги по валютам ───────────────────────────────────────────────────
const currencies = computed(() => props.overview.currencies.map((c) => c.currency))
const currency = ref<Currency>('tjs')
watch(
  currencies,
  (list) => {
    if (list.length && !list.includes(currency.value)) currency.value = list[0]!
  },
  { immediate: true },
)
const currencyOptions = computed(() => currencies.value.map((c) => ({ value: c, label: c.toUpperCase() })))
const moneySeries = computed<BarSeries[]>(() => {
  const byPeriod = new Map(
    props.overview.money.filter((m) => m.currency === currency.value).map((m) => [m.period, m]),
  )
  return [
    {
      key: 'in',
      label: t('platform.overview.contributions'),
      values: periods.value.map((p) => byPeriod.get(p)?.contributions ?? 0),
      tone: 'ink',
    },
    {
      key: 'out',
      label: t('platform.overview.expenses'),
      values: periods.value.map((p) => byPeriod.get(p)?.expenses ?? 0),
      tone: 'muted',
    },
  ]
})
const formatCurrency = (value: number) => formatMoney(value, currency.value)

// ── Подтверждение личности ──────────────────────────────────────────────
const verification = computed(() => props.overview.verification)
const verifiedShare = computed(() => {
  const all = verification.value.verified + verification.value.unverified
  return all ? Math.round((verification.value.verified / all) * 100) : 0
})

const attention = computed(() => totals.value.pending_contributions + totals.value.pending_members)
</script>

<template>
  <div class="overview">
    <!-- 1. Ключевые цифры -->
    <div class="tiles">
      <div class="tile">
        <span class="tile-label">{{ $t('platform.overview.users') }}</span>
        <b class="tile-value">{{ totals.users_total }}</b>
        <span class="tile-hint">{{ $t('platform.overview.new30', { n: totals.users_new_30d }) }}</span>
      </div>
      <div class="tile">
        <span class="tile-label">{{ $t('platform.overview.activeUsers') }}</span>
        <b class="tile-value">{{ totals.users_active_7d }}</b>
        <span class="tile-hint">{{ $t('platform.overview.active30', { n: totals.users_active_30d }) }}</span>
      </div>
      <div class="tile">
        <span class="tile-label">{{ $t('platform.overview.funds') }}</span>
        <b class="tile-value">{{ totals.funds_total }}</b>
        <span class="tile-hint">{{ $t('platform.overview.new30', { n: totals.funds_new_30d }) }}</span>
      </div>
      <div class="tile">
        <span class="tile-label">{{ $t('platform.overview.activeFunds') }}</span>
        <b class="tile-value">{{ totals.funds_active_30d }}</b>
        <span class="tile-hint">{{ $t('platform.overview.members', { n: totals.members_active }) }}</span>
      </div>
    </div>

    <!-- 2. Что ждёт решения -->
    <div class="pending">
      <button type="button" class="pending-item" @click="emit('go', 'requests')">
        <b>{{ totals.pending_plan_requests }}</b>
        <span>{{ $t('platform.overview.pendingPlans') }}</span>
      </button>
      <button type="button" class="pending-item" @click="emit('go', 'funds')">
        <b>{{ totals.pending_contributions }}</b>
        <span>{{ $t('platform.overview.pendingReceipts') }}</span>
      </button>
      <button type="button" class="pending-item" @click="emit('go', 'funds')">
        <b>{{ totals.pending_members }}</b>
        <span>{{ $t('platform.overview.pendingMembers') }}</span>
      </button>
    </div>
    <p v-if="attention" class="note">{{ $t('platform.overview.councilQueue') }}</p>

    <!-- 3. Рост -->
    <section class="card">
      <div class="card-head">
        <h2 class="card-title">{{ $t('platform.overview.growth') }}</h2>
        <span class="card-meta">{{ $t('platform.overview.totalNow', { n: growthTotal }) }}</span>
      </div>
      <SegmentedControl v-model="growthKind" :options="growthOptions" />
      <BarChart :periods="periods" :series="growthSeries" />
    </section>

    <!-- 4. Деньги в фондах -->
    <section class="card">
      <div class="card-head">
        <h2 class="card-title">{{ $t('platform.overview.money') }}</h2>
      </div>
      <template v-if="currencies.length">
        <SegmentedControl v-if="currencies.length > 1" v-model="currency" :options="currencyOptions" />
        <BarChart :periods="periods" :series="moneySeries" :format="formatCurrency" />
        <div class="currency-totals">
          <span class="card-meta">{{ $t('platform.overview.allTime') }}</span>
          <div v-for="c in overview.currencies" :key="c.currency" class="currency-row">
            <span class="currency-code">{{ c.currency.toUpperCase() }}</span>
            <span>{{ $t('platform.overview.contributions') }} <b>{{ formatMoney(c.contributions, c.currency) }}</b></span>
            <span>{{ $t('platform.overview.expenses') }} <b>{{ formatMoney(c.expenses, c.currency) }}</b></span>
          </div>
        </div>
      </template>
      <p v-else class="note">{{ $t('platform.overview.noMoney') }}</p>
    </section>

    <!-- 5. Подтверждение личности -->
    <section class="card">
      <div class="card-head">
        <h2 class="card-title">{{ $t('platform.overview.verification') }}</h2>
        <span class="card-meta">{{ verifiedShare }}%</span>
      </div>
      <div
        class="meter"
        role="img"
        :aria-label="$t('platform.overview.verifiedOf', { n: verification.verified, total: verification.verified + verification.unverified })"
      >
        <span class="meter-fill" :style="{ width: `${verifiedShare}%` }" />
      </div>
      <div class="chips">
        <span class="chip">{{ $t('platform.overview.verified') }} <b>{{ verification.verified }}</b></span>
        <span class="chip">{{ $t('platform.overview.unverified') }} <b>{{ verification.unverified }}</b></span>
        <span class="chip">SMS <b>{{ verification.sms }}</b></span>
        <span class="chip">Google <b>{{ verification.google }}</b></span>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.overview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Плитки ───────────────────────────────────────────────────────────── */
.tiles {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;

  @media (min-width: 640px) {
    grid-template-columns: repeat(4, 1fr);
  }
}

.tile {
  @include glass-card(16px);
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 14px;
}

.tile-label,
.tile-hint {
  font-size: 12px;
  color: $text-muted;
}

.tile-value {
  font-size: 24px;
  font-weight: 700;
  color: $navy;
}

/* ── Ждут решения ─────────────────────────────────────────────────────── */
.pending {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.pending-item {
  @include glass-card(14px);
  @include pressable;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 10px 12px;
  cursor: pointer;
  text-align: left;

  b {
    font-size: 18px;
    color: $navy;
  }

  span {
    font-size: 11px;
    line-height: 1.3;
    color: $text-secondary;
  }
}

.note {
  margin: 0;
  font-size: 12px;
  color: $text-muted;
}

/* ── Карточки с графиками ─────────────────────────────────────────────── */
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

.card-meta {
  font-size: 12px;
  color: $text-muted;
}

.currency-totals {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 10px;
  border-top: 1px solid $hairline;
}

.currency-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  font-size: 13px;
  color: $text-secondary;

  b {
    color: $navy;
  }
}

.currency-code {
  min-width: 36px;
  font-weight: 700;
  color: $navy;
}

/* ── Подтверждение ────────────────────────────────────────────────────── */
.meter {
  height: 8px;
  overflow: hidden;
  border-radius: 4px;
  background: $surface-muted;
}

.meter-fill {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: #111827;
}

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
</style>
