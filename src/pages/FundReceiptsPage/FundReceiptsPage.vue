<script setup lang="ts">
import ReceiptsHistory from '@/features/admin/components/ReceiptsHistory.vue'
import VerifyCard from '@/features/admin/components/VerifyCard.vue'
import VerifyPanel from '@/features/admin/components/VerifyPanel.vue'
import { useAdminFlow } from '@/features/admin/composables/useAdminFlow.ts'
import { useFundSubpage } from '@/features/admin/composables/useFundSubpage.ts'
import { useAdminStore } from '@/features/admin/store.ts'
import type { Contribution } from '@/features/contributions/types.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import SegmentedControl from '@/shared/components/SegmentedControl.vue'
import { formatMoney } from '@/shared/lib/format.ts'
import { useReceiptStore } from '@/shared/stores/useReceiptStore.ts'

const store = useAdminStore()
const receiptStore = useReceiptStore()
const flow = useAdminFlow()

useFundSubpage('fundMenu.receipts', store.fetchPending)

// ── Handlers ─────────────────────────────────────────────────────────────
function zoomReceipt(contribution: Contribution) {
  receiptStore.open(
    `${contribution.user_name} · ${formatMoney(contribution.amount, contribution.currency)}`,
    contribution.receipt_image,
  )
}

// Из истории: чек на проверке открываем на проверку, остальные — просто показываем
function openHistoryReceipt(contribution: Contribution) {
  if (contribution.status === 'pending') flow.openVerify(contribution)
  else zoomReceipt(contribution)
}
</script>

<template>
  <div class="subpage">
    <SegmentedControl v-model="flow.verificationView.value" :options="flow.verificationTabs.value" />

    <template v-if="flow.verificationView.value === 'pending'">
      <template v-if="store.isLoading && !store.pending.length">
        <CardSkeleton v-for="i in 2" :key="i" />
      </template>
      <EmptyState v-else-if="store.errorMessage" icon="📡" :title="$t(store.errorMessage)">
        <button class="ghost-btn" @click="store.fetchPending()">{{ $t('common.retry') }}</button>
      </EmptyState>
      <div v-else-if="store.pending.length" class="list">
        <p class="hint">{{ $t('admin.verification.subtitle') }}</p>
        <VerifyCard
          v-for="contribution in store.pending"
          :key="contribution.id"
          :contribution="contribution"
          @check="flow.openVerify"
        />
      </div>
      <EmptyState
        v-else
        icon="✅"
        :title="$t('admin.verification.emptyTitle')"
        :hint="$t('admin.verification.emptyHint')"
      />
    </template>

    <ReceiptsHistory
      v-else
      v-model:filters="store.historyFilters"
      :items="store.history"
      :totals="store.historyTotals"
      :total-count="store.historyTotal"
      :currencies="store.activeCurrencies"
      :requisites="store.requisites"
      :is-loading="store.isHistoryLoading"
      :has-more="store.hasMoreHistory"
      @change="flow.handleHistoryFilter"
      @more="flow.handleHistoryMore"
      @open="openHistoryReceipt"
    />

    <BottomSheet
      :open="flow.sheet.value === 'verify' && !!flow.selectedContribution.value"
      :title="$t('admin.verification.sheetTitle')"
      @close="flow.closeSheet"
    >
      <VerifyPanel
        v-if="flow.selectedContribution.value"
        :contribution="flow.selectedContribution.value"
        :is-submitting="store.isSubmitting"
        @zoom="zoomReceipt"
        @approve="flow.handleApprove"
        @reject="flow.handleReject"
      />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.subpage {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 820px;
  margin: 0 auto;
  padding: 16px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hint {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
}

.ghost-btn {
  @include ghost-button;
}

@media (min-width: 768px) {
  .subpage {
    padding: 24px;
  }
}
</style>
