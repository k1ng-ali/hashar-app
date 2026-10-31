<script setup lang="ts">
import { computed } from 'vue'
import PlanRequestForm from '@/features/admin/components/PlanRequestForm.vue'
import SettingsPanel from '@/features/admin/components/SettingsPanel.vue'
import { useAdminFlow } from '@/features/admin/composables/useAdminFlow.ts'
import { useFundSubpage } from '@/features/admin/composables/useFundSubpage.ts'
import { useAdminStore } from '@/features/admin/store.ts'
import { useAuthStore } from '@/features/auth/store.ts'
import FundCodeCard from '@/features/funds/components/FundCodeCard.vue'
import PlanCard from '@/features/funds/components/PlanCard.vue'
import { useFundsStore } from '@/features/funds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import { formatPhone } from '@/shared/lib/formatters.ts'

const store = useAdminStore()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const flow = useAdminFlow()

useFundSubpage('fundMenu.settings', store.fetchSettings)

// Контакт по умолчанию для заявки на тариф
const myContact = computed(() =>
  authStore.user?.phone ? formatPhone(authStore.user.phone) : (authStore.user?.email ?? ''),
)
</script>

<template>
  <div class="subpage">
    <CardSkeleton v-if="!fundsStore.current" :lines="4" />

    <template v-else>
      <PlanCard
        :info="fundsStore.current.plan"
        :options="fundsStore.plans"
        :can-request="flow.permissions.value.isChairman"
        :has-pending-request="store.hasPendingPlanRequest"
        @request="flow.openPlanRequest"
      />
      <FundCodeCard :code="fundsStore.current.code" @copy="flow.handleCopy" />
      <SettingsPanel
        :fund="fundsStore.current"
        :currencies="store.activeCurrencies"
        :is-chairman="flow.permissions.value.isChairman"
        :is-submitting="store.isSubmitting"
        @save="flow.handleSaveSettings"
      />
    </template>

    <BottomSheet
      :open="flow.sheet.value === 'plan'"
      :title="flow.isRenewal.value ? $t('plans.renewTitle') : $t('plans.requestTitle')"
      @close="flow.closeSheet"
    >
      <PlanRequestForm
        v-if="flow.selectedPlan.value"
        :key="`${flow.selectedPlan.value}-${flow.isRenewal.value}`"
        :plan="flow.selectedPlan.value"
        :options="fundsStore.plans"
        :is-renewal="flow.isRenewal.value"
        :expires-at="fundsStore.current?.plan.expires_at ?? null"
        :quote="flow.planQuote.value"
        :promo-code="flow.promoCode.value"
        :promo-error="flow.promoError.value"
        :default-contact="myContact"
        :is-submitting="store.isSubmitting"
        @submit="flow.handlePlanRequest"
        @apply-promo="flow.loadQuote"
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
