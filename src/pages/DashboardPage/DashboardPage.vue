<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LuLandmark, LuPlus } from '@kalimahapps/vue-icons/lu'
import { useAuthStore } from '@/features/auth/store.ts'
import BalanceBanner from '@/features/contributions/components/BalanceBanner.vue'
import { useContributionsStore } from '@/features/contributions/store.ts'
import BalanceCard from '@/features/dashboard/components/BalanceCard.vue'
import MetricsRow from '@/features/dashboard/components/MetricsRow.vue'
import OperationsList from '@/features/dashboard/components/OperationsList.vue'
import RequisitesSheet from '@/features/dashboard/components/RequisitesSheet.vue'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import type { Operation, OperationsFilter } from '@/features/dashboard/types.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import TargetFundCard from '@/features/targetFunds/components/TargetFundCard.vue'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import type { TargetFund } from '@/features/targetFunds/types.ts'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { firstName } from '@/shared/lib/format.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useReceiptStore } from '@/shared/stores/useReceiptStore.ts'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const store = useDashboardStore()
const contributionsStore = useContributionsStore()
const targetFundsStore = useTargetFundsStore()
const headerStore = useHeaderStore()
const receiptStore = useReceiptStore()

const isRequisitesOpen = ref(false)
const fundsSection = ref<HTMLElement | null>(null)
const operationsSection = ref<HTMLElement | null>(null)

onMounted(async () => {
  headerStore.setTitle(t('dashboard.greeting', { name: firstName(authStore.user?.full_name ?? '') }))
  await Promise.all([store.fetchDashboard(), contributionsStore.fetchBalance(), targetFundsStore.fetchList()])
})

onUnmounted(() => {
  headerStore.reset()
})

// ── Handlers ─────────────────────────────────────────────────────────────
function goContribute(fund?: TargetFund) {
  void router.push({ path: '/contribute', query: fund ? { fund: fund.id } : undefined })
}

function showExpenses() {
  void store.fetchOperations('expense')
  operationsSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function changeFilter(filter: OperationsFilter) {
  void store.fetchOperations(filter)
}

function openReceipt(operation: Operation) {
  if (operation.receipt_image) receiptStore.open(operation.title, operation.receipt_image)
}
</script>

<template>
  <div class="dashboard-page">
    <!-- 1. Балансы фонда по валютам -->
    <CardSkeleton v-if="store.isLoading && !store.summary" :lines="4" :height="250" />
    <BalanceCard
      v-else-if="store.baseAccount"
      :base-account="store.baseAccount"
      :other-accounts="store.otherAccounts"
      :caption="`${fundsStore.current?.name} · ${fundsStore.currentMembership?.address_unit ?? ''}`"
      @contribute="goContribute()"
      @expenses="showExpenses"
      @receipts="router.push('/history')"
      @funds="fundsSection?.scrollIntoView({ behavior: 'smooth', block: 'start' })"
    />
    <EmptyState v-else-if="store.errorMessage" icon="📡" :title="$t(store.errorMessage)">
      <button class="ghost-btn" @click="store.fetchDashboard()">{{ $t('common.retry') }}</button>
    </EmptyState>

    <!-- 2. Сальдо участника -->
    <BalanceBanner
      v-if="contributionsStore.balance && contributionsStore.balance.rate > 0"
      :balance="contributionsStore.balance"
      @pay="goContribute()"
    />

    <!-- 3. Метрики месяца (базовая валюта) -->
    <MetricsRow
      v-if="store.summary && store.baseAccount"
      :account="store.baseAccount"
      :period="store.summary.current_period"
      :paying-count="store.payingMembersCount"
      :members-count="store.summary.active_members_count"
    />

    <button class="requisites-btn" @click="isRequisitesOpen = true">
      <LuLandmark /> {{ $t('requisites.title') }}
    </button>

    <!-- 4. Целевые сборы -->
    <section ref="fundsSection" class="section">
      <div class="section-header">
        <div>
          <h2 class="section-title">{{ $t('dashboard.fundsTitle') }}</h2>
          <span class="section-sub">{{ $t('dashboard.fundsSubtitle') }}</span>
        </div>
        <button
          v-if="fundsStore.permissions.canManageFinance"
          class="ghost-btn"
          @click="router.push({ path: '/admin', query: { tab: 'funds' } })"
        >
          <LuPlus /> {{ $t('dashboard.createFund') }}
        </button>
      </div>

      <div v-if="targetFundsStore.isLoading && !targetFundsStore.items.length" class="grid">
        <CardSkeleton v-for="i in 2" :key="i" />
      </div>
      <div v-else-if="targetFundsStore.items.length" class="grid">
        <TargetFundCard
          v-for="fund in targetFundsStore.items"
          :key="fund.id"
          :fund="fund"
          @open="(f) => router.push(`/target-funds/${f.id}`)"
          @contribute="goContribute"
        />
      </div>
      <EmptyState v-else icon="🎯" :title="$t('targetFunds.emptyTitle')" :hint="$t('targetFunds.emptyHint')" />
    </section>

    <!-- 5. Операции -->
    <section ref="operationsSection" class="section">
      <div class="section-header">
        <div>
          <h2 class="section-title">{{ $t('dashboard.operationsTitle') }}</h2>
          <span class="section-sub">{{ $t('dashboard.operationsSubtitle') }}</span>
        </div>
      </div>

      <PillTabs
        :model-value="store.operationsFilter"
        :options="[
          { value: 'all', label: $t('dashboard.filters.all') },
          { value: 'income', label: $t('dashboard.filters.income') },
          { value: 'expense', label: $t('dashboard.filters.expense') },
          { value: 'transfer', label: $t('dashboard.filters.transfer') },
        ]"
        @update:model-value="changeFilter"
      />

      <OperationsList v-if="store.operations.length" :operations="store.operations" @open-receipt="openReceipt" />
      <EmptyState v-else-if="!store.isOperationsLoading" icon="🧾" :title="$t('dashboard.noOperations')" />
    </section>

    <RequisitesSheet :open="isRequisitesOpen" :requisites="store.requisites" @close="isRequisitesOpen = false" />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 16px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-margin-top: calc(var(--header-height) + var(--sat) + 12px);
}

.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  @include section-title;
}

.section-sub {
  font-size: 12px;
  color: $text-muted;
}

.grid {
  display: grid;
  gap: 12px;
}

.ghost-btn {
  @include ghost-button;
}

.requisites-btn {
  @include ghost-button;
  padding: 12px;
}

@media (min-width: 768px) {
  .dashboard-page {
    padding: 24px;
  }

  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
