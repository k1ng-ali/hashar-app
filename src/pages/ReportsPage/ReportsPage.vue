<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import CategoryStats from '@/features/reports/components/CategoryStats.vue'
import DebtorsList from '@/features/reports/components/DebtorsList.vue'
import ExportButtons from '@/features/reports/components/ExportButtons.vue'
import MonthlyLedger from '@/features/reports/components/MonthlyLedger.vue'
import { useReportsStore } from '@/features/reports/store.ts'
import type { ExportKind } from '@/features/reports/types.ts'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { type Currency } from '@/shared/lib/currency.ts'
import { formatMoney } from '@/shared/lib/format.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

const { t } = useI18n()
const store = useReportsStore()
const headerStore = useHeaderStore()

const currencyTabs = computed(() =>
  (store.report?.currencies ?? []).map((c) => ({ value: c, label: `${c.toUpperCase()}` })),
)

onMounted(async () => {
  await store.fetchAll()
})

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleExport(kind: ExportKind) {
  try {
    const filename = await store.exportCsv(kind)
    headerStore.showNotification(t('reports.exported', { name: filename }))
  } catch {
    headerStore.showNotification(t('errors.generic'), 'error')
  }
}

function changeCurrency(currency: Currency) {
  void store.fetchAll(currency)
}
</script>

<template>
  <div class="reports-page">
    <p class="subtitle">{{ $t('reports.subtitle') }}</p>

    <ExportButtons :exporting-kind="store.exportingKind" @export="handleExport" />

    <template v-if="store.isLoading && !store.report">
      <CardSkeleton :lines="2" />
      <CardSkeleton :lines="5" :height="280" />
    </template>

    <EmptyState v-else-if="store.errorMessage" icon="📡" :title="$t(store.errorMessage)">
      <button class="ghost-btn" @click="store.fetchAll()">{{ $t('common.retry') }}</button>
    </EmptyState>

    <template v-else-if="store.report">
      <!-- Отчёт по каждому валютному счёту отдельно -->
      <PillTabs
        v-if="currencyTabs.length > 1"
        :model-value="store.report.currency"
        :options="currencyTabs"
        @update:model-value="changeCurrency"
      />

      <!-- 1. Итоги -->
      <div class="totals">
        <div class="total">
          <span class="label">{{ $t('reports.totalIncome') }}</span>
          <span class="value value--in">{{ formatMoney(store.report.total_income, store.report.currency) }}</span>
        </div>
        <div class="total">
          <span class="label">{{ $t('reports.totalExpense') }}</span>
          <span class="value value--out">{{ formatMoney(store.report.total_expense, store.report.currency) }}</span>
        </div>
        <div class="total">
          <span class="label">{{ $t('reports.netBalance') }}</span>
          <span class="value">{{ formatMoney(store.report.net_balance, store.report.currency) }}</span>
        </div>
      </div>

      <!-- 2. Ведомость -->
      <section class="card">
        <h2 class="card-title">📊 {{ $t('reports.monthly') }}</h2>
        <MonthlyLedger
          :rows="store.report.monthly_rows"
          :rate="store.report.rate"
          :currency="store.report.currency"
          :base-currency="store.report.base_currency"
        />
      </section>

      <div class="grid">
        <!-- 3. Структура расходов -->
        <section class="card">
          <h2 class="card-title">🧩 {{ $t('reports.structure') }}</h2>
          <CategoryStats
            v-if="store.report.category_stats.length"
            :stats="store.report.category_stats"
            :currency="store.report.currency"
          />
          <EmptyState v-else icon="🧾" :title="$t('reports.noExpenses')" />
        </section>

        <!-- 4. Должники (в базовой валюте) -->
        <section class="card">
          <div class="card-header">
            <h2 class="card-title">⚠️ {{ $t('reports.debtors') }}</h2>
            <span class="badge">{{ $t('reports.debtorsCount', { n: store.debtors.length }) }}</span>
          </div>
          <DebtorsList v-if="store.debtors.length" :debtors="store.debtors" />
          <EmptyState v-else icon="🎉" :title="$t('reports.noDebtors')" />
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.reports-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 16px;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
}

.ghost-btn {
  @include ghost-button;
}

/* ── Итоги ────────────────────────────────────────────────────────────────── */
.totals {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.total {
  @include glass-card(16px);
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px;
}

.label {
  font-size: 11px;
  color: $text-muted;
}

.value {
  font-size: 15px;
  font-weight: 700;
  color: $navy;

  &--in {
    color: $success;
  }

  &--out {
    color: $danger;
  }
}

/* ── Cards ────────────────────────────────────────────────────────────────── */
.card {
  @include glass-card;
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;

  .card-title {
    margin: 0;
  }
}

.card-title {
  @include section-title;
  margin-bottom: 12px;
  font-size: 16px;
}

.badge {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(239, 68, 68, 0.1);
  color: #B91C1C;
  font-size: 11px;
  font-weight: 700;
}

.grid {
  display: grid;
  gap: 16px;
}

@media (min-width: 768px) {
  .reports-page {
    padding: 24px;
  }

  .grid {
    grid-template-columns: 1fr 1fr;
    align-items: start;
  }
}
</style>
