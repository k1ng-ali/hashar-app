<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LuPlus } from '@kalimahapps/vue-icons/lu'
import FundForm from '@/features/admin/components/FundForm.vue'
import { useAdminFlow } from '@/features/admin/composables/useAdminFlow.ts'
import { useAdminStore } from '@/features/admin/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import TargetFundCard from '@/features/targetFunds/components/TargetFundCard.vue'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import type { TargetFund } from '@/features/targetFunds/types.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import type { Currency } from '@/shared/lib/currency.ts'

type FundsView = 'active' | 'closed'

const route = useRoute()
const router = useRouter()
const store = useTargetFundsStore()
const fundsStore = useFundsStore()
const adminStore = useAdminStore()
const flow = useAdminFlow()

const view = ref<FundsView>('active')
const visible = computed(() => store.items.filter((item) => item.is_active === (view.value === 'active')))
const closedCount = computed(() => store.items.filter((item) => !item.is_active).length)
const currencies = computed<Currency[]>(
  () => fundsStore.current?.accounts.filter((a) => a.is_active).map((a) => a.currency) ?? [],
)

onMounted(async () => {
  await store.fetchList()
  // «+» → «Открыть сбор» ведёт сюда с ?create=1
  if (route.query.create && fundsStore.permissions.canManageFinance) {
    flow.openSheet('fund')
    void router.replace({ query: {} })
  }
})

function contribute(fund: TargetFund) {
  void router.push({ path: '/contribute', query: { fund: fund.id } })
}
</script>

<template>
  <div class="funds-page">
    <div class="toolbar">
      <PillTabs
        v-model="view"
        :options="[
          { value: 'active', label: $t('targetFunds.tabActive') },
          { value: 'closed', label: $t('targetFunds.tabClosed'), badge: closedCount || undefined },
        ]"
      />
      <button v-if="fundsStore.permissions.canManageFinance" class="add-btn" @click="flow.openSheet('fund')">
        <LuPlus /> {{ $t('admin.funds.create') }}
      </button>
    </div>

    <div v-if="store.isLoading && !store.items.length" class="grid">
      <CardSkeleton v-for="i in 2" :key="i" />
    </div>
    <div v-else-if="visible.length" class="grid">
      <TargetFundCard
        v-for="fund in visible"
        :key="fund.id"
        :fund="fund"
        @open="(f) => router.push(`/target-funds/${f.id}`)"
        @contribute="contribute"
      />
    </div>
    <EmptyState v-else icon="🎯" :title="$t('targetFunds.emptyTitle')" :hint="$t('targetFunds.emptyHint')" />

    <BottomSheet :open="flow.sheet.value === 'fund'" :title="$t('admin.funds.sheetTitle')" @close="flow.closeSheet">
      <FundForm
        v-if="fundsStore.current"
        :currencies="currencies"
        :base-currency="fundsStore.current.base_currency"
        :is-submitting="adminStore.isSubmitting"
        @submit="flow.handleAddFund"
      />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.funds-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.add-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 9px 14px;
  font-size: 13px;
}

.grid {
  display: grid;
  gap: 12px;
}

@media (min-width: 768px) {
  .funds-page {
    padding: 16px 24px 24px;
  }

  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
