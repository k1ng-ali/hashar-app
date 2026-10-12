<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AccountsPanel from '@/features/admin/components/AccountsPanel.vue'
import RequisiteForm from '@/features/admin/components/RequisiteForm.vue'
import RequisitesPanel from '@/features/admin/components/RequisitesPanel.vue'
import TransferForm from '@/features/admin/components/TransferForm.vue'
import { useAdminFlow } from '@/features/admin/composables/useAdminFlow.ts'
import { useFundSubpage } from '@/features/admin/composables/useFundSubpage.ts'
import { useAdminStore } from '@/features/admin/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'

const route = useRoute()
const router = useRouter()
const store = useAdminStore()
const fundsStore = useFundsStore()
const flow = useAdminFlow()

useFundSubpage('fundMenu.accounts', store.fetchAccounts)

// Остатки счетов — для предупреждения о минусе в форме перевода
const balances = computed(() =>
  Object.fromEntries(fundsStore.current?.accounts.map((a) => [a.currency, a.balance]) ?? []),
)

onMounted(() => {
  // «+» → «Перевод между счетами» ведёт сюда с ?create=1
  if (route.query.create) {
    flow.openSheet('transfer')
    void router.replace({ query: {} })
  }
})
</script>

<template>
  <div class="subpage">
    <CardSkeleton v-if="!fundsStore.current" :lines="4" />

    <template v-else>
      <AccountsPanel
        :accounts="fundsStore.current.accounts"
        :base-currency="fundsStore.current.base_currency"
        :transfers="store.transfers"
        :can-manage-accounts="flow.permissions.value.canManageSettings"
        @enable="flow.handleEnableCurrency"
        @disable="flow.handleDisableCurrency"
        @transfer="flow.openSheet('transfer')"
      />
      <RequisitesPanel
        :requisites="store.requisites"
        :can-manage="flow.permissions.value.canManageSettings"
        @add="flow.openSheet('requisite')"
        @toggle="flow.handleToggleRequisite"
        @delete="flow.handleDeleteRequisite"
      />
    </template>

    <BottomSheet :open="flow.sheet.value === 'transfer'" :title="$t('admin.accounts.newTransfer')" @close="flow.closeSheet">
      <TransferForm
        :currencies="store.activeCurrencies"
        :balances="balances"
        :is-submitting="store.isSubmitting"
        @submit="flow.handleAddTransfer"
      />
    </BottomSheet>

    <BottomSheet :open="flow.sheet.value === 'requisite'" :title="$t('admin.settings.sheetTitle')" @close="flow.closeSheet">
      <RequisiteForm
        v-if="fundsStore.current"
        :currencies="store.activeCurrencies"
        :base-currency="fundsStore.current.base_currency"
        :is-submitting="store.isSubmitting"
        @submit="flow.handleAddRequisite"
      />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
.subpage {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 820px;
  margin: 0 auto;
  padding: 16px;
}

@media (min-width: 768px) {
  .subpage {
    padding: 24px;
  }
}
</style>
