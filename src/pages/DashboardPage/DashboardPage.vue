<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LuCreditCard, LuReceiptText, LuTarget, LuWallet } from '@kalimahapps/vue-icons/lu'
import { useAuthStore } from '@/features/auth/store.ts'
import BalanceBanner from '@/features/contributions/components/BalanceBanner.vue'
import { useContributionsStore } from '@/features/contributions/store.ts'
import AttentionCard, { type AttentionItem } from '@/features/dashboard/components/AttentionCard.vue'
import BalanceCard from '@/features/dashboard/components/BalanceCard.vue'
import MetricsRow from '@/features/dashboard/components/MetricsRow.vue'
import OperationsList from '@/features/dashboard/components/OperationsList.vue'
import QuickTiles, { type QuickTile } from '@/features/dashboard/components/QuickTiles.vue'
import RequisitesSheet from '@/features/dashboard/components/RequisitesSheet.vue'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import type { Operation, OperationsFilter } from '@/features/dashboard/types.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { firstName } from '@/shared/lib/format.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useReceiptStore } from '@/shared/stores/useReceiptStore.ts'

// Тариф платформы скоро закончится — предупреждаем председателя заранее
const PLAN_WARNING_DAYS = 7
const DAY_MS = 24 * 60 * 60 * 1000

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

onMounted(async () => {
  headerStore.setTitle(t('dashboard.greeting', { name: firstName(authStore.user?.full_name ?? '') }))
  await Promise.all([store.fetchDashboard(), contributionsStore.fetchBalance(), targetFundsStore.fetchList()])
})

onUnmounted(() => {
  headerStore.reset()
})

// ── Быстрые действия ─────────────────────────────────────────────────────
const tiles = computed<QuickTile[]>(() => [
  { key: 'contribute', icon: LuWallet, title: t('dashboard.tiles.contribute'), hint: t('dashboard.tiles.contributeHint') },
  { key: 'requisites', icon: LuCreditCard, title: t('dashboard.tiles.requisites'), hint: t('dashboard.tiles.requisitesHint') },
  { key: 'expenses', icon: LuReceiptText, title: t('dashboard.tiles.expenses'), hint: t('dashboard.tiles.expensesHint') },
  {
    key: 'funds',
    icon: LuTarget,
    title: t('dashboard.tiles.funds'),
    hint: t('dashboard.tiles.fundsHint', { n: targetFundsStore.activeItems.length }),
  },
])

function handleTile(key: string) {
  if (key === 'requisites') isRequisitesOpen.value = true
  else if (key === 'contribute') void router.push('/contribute')
  else void router.push(`/finance/${key}`)
}

// ── Требует внимания (совет) ─────────────────────────────────────────────
const attention = computed<AttentionItem[]>(() => {
  const summary = store.summary
  const fund = fundsStore.current
  if (!fundsStore.permissions.isCouncil || !summary || !fund) return []

  const items: AttentionItem[] = []
  if (summary.pending_count) {
    items.push({ key: 'receipts', label: t('attention.receipts'), count: summary.pending_count, to: '/fund/receipts' })
  }
  if (summary.pending_members_count) {
    items.push({ key: 'members', label: t('attention.members'), count: summary.pending_members_count, to: '/fund/members' })
  }
  const expiresAt = fund.plan.expires_at ? new Date(fund.plan.expires_at).getTime() : null
  if (fund.plan.effective_plan !== 'free' && expiresAt && expiresAt - Date.now() < PLAN_WARNING_DAYS * DAY_MS) {
    const days = Math.max(0, Math.ceil((expiresAt - Date.now()) / DAY_MS))
    items.push({ key: 'plan', label: t('attention.plan', { n: days }), to: '/fund/settings' })
  }
  return items
})

// ── Операции ─────────────────────────────────────────────────────────────
function changeFilter(filter: OperationsFilter) {
  void store.fetchOperations(filter)
}

function openReceipt(operation: Operation) {
  if (operation.receipt_image) receiptStore.open(operation.title, operation.receipt_image)
}

// Строка расхода в ленте операций ведёт на его карточку («e-<id>»)
function openExpense(operation: Operation) {
  void router.push({ path: '/finance/expenses', query: { id: operation.id.replace('e-', '') } })
}
</script>

<template>
  <div class="dashboard-page">
    <!-- 1. Остаток фонда -->
    <CardSkeleton v-if="store.isLoading && !store.summary" :lines="3" :height="120" />
    <BalanceCard
      v-else-if="store.baseAccount"
      :base-account="store.baseAccount"
      :other-accounts="store.otherAccounts"
      :caption="$t('dashboard.balanceLabel')"
      :fund-name="fundsStore.current?.name ?? ''"
      :unit="fundsStore.currentMembership?.address_unit ?? null"
    />
    <EmptyState v-else-if="store.errorMessage" icon="📡" :title="$t(store.errorMessage)">
      <button class="ghost-btn" @click="store.fetchDashboard()">{{ $t('common.retry') }}</button>
    </EmptyState>

    <!-- 2. Дела совета -->
    <AttentionCard v-if="attention.length" :items="attention" @open="(to) => router.push(to)" />

    <!-- 3. Моё сальдо -->
    <BalanceBanner
      v-if="contributionsStore.balance && contributionsStore.balance.rate > 0"
      :balance="contributionsStore.balance"
      @pay="router.push('/contribute')"
    />

    <!-- 4. Быстрые действия -->
    <section class="section">
      <h2 class="section-title">{{ $t('dashboard.quickActions') }}</h2>
      <QuickTiles :tiles="tiles" @select="handleTile" />
    </section>

    <!-- 5. Месяц по базовому счёту -->
    <MetricsRow
      v-if="store.summary && store.baseAccount"
      :account="store.baseAccount"
      :period="store.summary.current_period"
      :paying-count="store.payingMembersCount"
      :members-count="store.summary.active_members_count"
    />

    <!-- 6. Последние операции -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">{{ $t('dashboard.operationsTitle') }}</h2>
        <router-link to="/finance/reports" class="see-all">{{ $t('dashboard.seeAll') }}</router-link>
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

      <OperationsList
        v-if="store.operations.length"
        :operations="store.operations"
        @open-receipt="openReceipt"
        @open-expense="openExpense"
      />
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
  gap: 18px;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 12px 16px 16px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  @include section-title;
  font-size: 15px;
  font-weight: 500;
  color: $text-secondary;
}

.see-all {
  font-size: 14px;
  font-weight: 600;
  color: $navy;
  text-decoration: none;
}

.ghost-btn {
  @include ghost-button;
}

@media (min-width: 768px) {
  .dashboard-page {
    padding: 24px;
  }
}
</style>
