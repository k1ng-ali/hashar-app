<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LuPlus } from '@kalimahapps/vue-icons/lu'
import { useAuthStore } from '@/features/auth/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import AccountSummary from '@/features/contributions/components/AccountSummary.vue'
import BalanceBanner from '@/features/contributions/components/BalanceBanner.vue'
import ContributionCard from '@/features/contributions/components/ContributionCard.vue'
import { useContributionsStore, type HistoryFilter } from '@/features/contributions/store.ts'
import type { Contribution } from '@/features/contributions/types.ts'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { formatMoney } from '@/shared/lib/format.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useReceiptStore } from '@/shared/stores/useReceiptStore.ts'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const store = useContributionsStore()
const headerStore = useHeaderStore()
const receiptStore = useReceiptStore()

onMounted(async () => {
  headerStore.setTitle(t('history.title'))
  store.filter = 'all'
  await store.fetchMy()
})

onUnmounted(() => {
  headerStore.reset()
})

// ── Handlers ─────────────────────────────────────────────────────────────
function openReceipt(contribution: Contribution) {
  receiptStore.open(formatMoney(contribution.amount, contribution.currency), contribution.receipt_image)
}
</script>

<template>
  <div class="history-page">
    <!-- 1. Лицевой счёт -->
    <div class="account-card">
      <div class="account-top">
        <div>
          <span class="account-label">{{ $t('balance.account') }}</span>
          <div class="account-unit">{{ fundsStore.currentMembership?.address_unit ?? '—' }}</div>
          <div class="account-owner">{{ $t('history.owner', { name: authStore.user?.full_name }) }}</div>
        </div>
        <button class="pay-btn" @click="router.push('/contribute')">
          <LuPlus /> {{ $t('history.pay') }}
        </button>
      </div>

      <AccountSummary v-if="store.balance" :balance="store.balance" />
    </div>

    <BalanceBanner
      v-if="store.balance && store.balance.status === 'debt'"
      :balance="store.balance"
      @pay="router.push('/contribute')"
    />

    <!-- 2. Платежи -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">{{ $t('history.listTitle') }}</h2>
        <span class="counter">{{ $t('history.count', { n: store.items.length }) }}</span>
      </div>

      <PillTabs
        v-model="store.filter"
        :options="[
          { value: 'all' as HistoryFilter, label: $t('history.filters.all') },
          { value: 'approved' as HistoryFilter, label: $t('history.filters.approved') },
          { value: 'pending' as HistoryFilter, label: $t('history.filters.pending'), badge: store.countByStatus.pending },
          { value: 'rejected' as HistoryFilter, label: $t('history.filters.rejected') },
        ]"
      />

      <div v-if="store.isLoading" class="list">
        <CardSkeleton v-for="i in 3" :key="i" />
      </div>

      <div v-else-if="store.filteredItems.length" class="list">
        <ContributionCard
          v-for="contribution in store.filteredItems"
          :key="contribution.id"
          :contribution="contribution"
          @open-receipt="openReceipt"
        />
      </div>

      <EmptyState v-else icon="🧾" :title="$t('history.emptyTitle')" :hint="$t('history.emptyHint')">
        <button class="pay-btn" @click="router.push('/contribute')">{{ $t('history.pay') }}</button>
      </EmptyState>
    </section>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.history-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 16px;
}

/* ── Лицевой счёт ─────────────────────────────────────────────────────────── */
.account-card {
  @include glass-card(24px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
}

.account-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.account-label {
  font-size: 12px;
  color: $text-muted;
}

.account-unit {
  font-size: 22px;
  font-weight: 800;
  color: $navy;
}

.account-owner {
  font-size: 13px;
  color: $text-secondary;
}

.pay-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 10px 16px;
  font-size: 13px;
}

/* ── Платежи ──────────────────────────────────────────────────────────────── */
.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.section-title {
  @include section-title;
}

.counter {
  font-size: 12px;
  color: $text-muted;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (min-width: 768px) {
  .history-page {
    padding: 24px;
  }
}
</style>
