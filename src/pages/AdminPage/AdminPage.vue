<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { LuPlus } from '@kalimahapps/vue-icons/lu'
import AccountsPanel from '@/features/admin/components/AccountsPanel.vue'
import ExpenseCard from '@/features/admin/components/ExpenseCard.vue'
import ExpenseForm from '@/features/admin/components/ExpenseForm.vue'
import FundAdminRow from '@/features/admin/components/FundAdminRow.vue'
import FundForm from '@/features/admin/components/FundForm.vue'
import MemberCard from '@/features/admin/components/MemberCard.vue'
import MemberRequestCard from '@/features/admin/components/MemberRequestCard.vue'
import PlanRequestForm from '@/features/admin/components/PlanRequestForm.vue'
import RequisiteForm from '@/features/admin/components/RequisiteForm.vue'
import SettingsPanel from '@/features/admin/components/SettingsPanel.vue'
import TransferForm from '@/features/admin/components/TransferForm.vue'
import VerifyCard from '@/features/admin/components/VerifyCard.vue'
import VerifyPanel from '@/features/admin/components/VerifyPanel.vue'
import { useAdminFlow } from '@/features/admin/composables/useAdminFlow.ts'
import { useAdminStore } from '@/features/admin/store.ts'
import type { Expense } from '@/features/admin/types.ts'
import { useAuthStore } from '@/features/auth/store.ts'
import type { Contribution } from '@/features/contributions/types.ts'
import FundCodeCard from '@/features/funds/components/FundCodeCard.vue'
import PlanCard from '@/features/funds/components/PlanCard.vue'
import { useFundsStore } from '@/features/funds/store.ts'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { formatMoney } from '@/shared/lib/format.ts'
import { useReceiptStore } from '@/shared/stores/useReceiptStore.ts'

const router = useRouter()
const store = useAdminStore()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const targetFundsStore = useTargetFundsStore()
const receiptStore = useReceiptStore()
const flow = useAdminFlow()

onMounted(() => {
  void flow.initView()
})

onUnmounted(() => {
  flow.dispose()
})

// ── Handlers ─────────────────────────────────────────────────────────────
function zoomReceipt(contribution: Contribution) {
  receiptStore.open(
    `${contribution.user_name} · ${formatMoney(contribution.amount, contribution.currency)}`,
    contribution.receipt_image,
  )
}

function openExpenseReceipt(expense: Expense) {
  receiptStore.open(expense.title, expense.receipt_images[0])
}
</script>

<template>
  <div class="admin-page">
    <div class="intro">
      <span class="role-badge">
        {{ flow.permissions.value.isChairman ? '👑' : '🛡️' }}
        {{ $t(`roles.${fundsStore.current?.my_role ?? 'admin'}`) }}
      </span>
      <span class="access">{{ fundsStore.current?.name }}</span>
    </div>

    <PillTabs v-model="flow.view.value" :options="flow.tabs.value" />

    <template v-if="store.isLoading && !store.members.length">
      <CardSkeleton v-for="i in 3" :key="i" />
    </template>

    <EmptyState v-else-if="store.errorMessage" icon="📡" :title="$t(store.errorMessage)">
      <button class="ghost-btn" @click="store.fetchAll()">{{ $t('common.retry') }}</button>
    </EmptyState>

    <Transition v-else name="slide" mode="out-in">
      <!-- 1. Проверка чеков -->
      <section v-if="flow.view.value === 'verification'" key="verification" class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">{{ $t('admin.verification.title') }}</h2>
            <span class="section-sub">{{ $t('admin.verification.subtitle') }}</span>
          </div>
          <span class="count-pill">{{ $t('admin.verification.count', { n: store.pending.length }) }}</span>
        </div>

        <div v-if="store.pending.length" class="list">
          <VerifyCard
            v-for="contribution in store.pending"
            :key="contribution.id"
            :contribution="contribution"
            @check="flow.openVerify"
          />
        </div>
        <EmptyState v-else icon="✅" :title="$t('admin.verification.emptyTitle')" :hint="$t('admin.verification.emptyHint')" />
      </section>

      <!-- 2. Участники: заявки и реестр -->
      <section v-else-if="flow.view.value === 'members'" key="members" class="section">
        <template v-if="store.joinRequests.length">
          <h2 class="section-title">{{ $t('admin.members.requestsTitle') }} · {{ store.joinRequests.length }}</h2>
          <div class="list">
            <MemberRequestCard
              v-for="member in store.joinRequests"
              :key="member.id"
              :member="member"
              @approve="flow.handleApproveMember"
              @reject="flow.handleRejectMember"
            />
          </div>
        </template>

        <div class="section-header">
          <div>
            <h2 class="section-title">{{ $t('admin.members.title') }}</h2>
            <span class="section-sub">
              {{ $t('admin.members.limit', {
                n: fundsStore.current?.plan.members_count ?? 0,
                limit: fundsStore.current?.plan.member_limit ?? '∞',
              }) }}
            </span>
          </div>
        </div>

        <label class="switch-row">
          <a-switch v-model:checked="store.onlyDebtors" />
          <span>{{ $t('admin.members.onlyDebtors') }} ({{ store.debtorsCount }})</span>
        </label>

        <div v-if="store.visibleMembers.length" class="grid">
          <MemberCard
            v-for="member in store.visibleMembers"
            :key="member.id"
            :member="member"
            :is-me="member.user_id === authStore.user?.id"
            :can-change-roles="flow.permissions.value.canChangeRoles"
            @status="flow.handleMemberStatus"
            @role="flow.handleMemberRole"
            @make-chairman="flow.handleTransferChairman"
          />
        </div>
        <EmptyState v-else icon="🏠" :title="$t('admin.members.empty')" :hint="$t('admin.members.inviteHint')" />
      </section>

      <!-- 3. Расходы -->
      <section v-else-if="flow.view.value === 'expenses'" key="expenses" class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">{{ $t('admin.expenses.title') }}</h2>
            <span class="section-sub">{{ $t('admin.expenses.subtitle') }}</span>
          </div>
          <button class="cta-btn" @click="flow.openSheet('expense')"><LuPlus /> {{ $t('admin.expenses.add') }}</button>
        </div>

        <div v-if="store.expenses.length" class="list">
          <ExpenseCard
            v-for="expense in store.expenses"
            :key="expense.id"
            :expense="expense"
            :can-delete="flow.permissions.value.canDeleteRecords"
            @open-receipt="openExpenseReceipt"
            @delete="flow.handleDeleteExpense"
          />
        </div>
        <EmptyState v-else icon="🧾" :title="$t('admin.expenses.empty')" />
      </section>

      <!-- 4. Целевые сборы -->
      <section v-else-if="flow.view.value === 'funds'" key="funds" class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">{{ $t('admin.funds.title') }}</h2>
            <span class="section-sub">{{ $t('admin.funds.subtitle') }}</span>
          </div>
          <button class="cta-btn" @click="flow.openSheet('fund')"><LuPlus /> {{ $t('admin.funds.create') }}</button>
        </div>

        <div v-if="targetFundsStore.items.length" class="list">
          <FundAdminRow
            v-for="fund in targetFundsStore.items"
            :key="fund.id"
            :fund="fund"
            :can-delete="flow.permissions.value.canDeleteRecords"
            @open="(id) => router.push(`/target-funds/${id}`)"
            @toggle="flow.handleToggleFund"
            @delete="flow.handleDeleteFund"
          />
        </div>
        <EmptyState v-else icon="🎯" :title="$t('targetFunds.emptyTitle')" />
      </section>

      <!-- 5. Счета и переводы -->
      <section v-else-if="flow.view.value === 'accounts' && fundsStore.current" key="accounts" class="section">
        <AccountsPanel
          :accounts="fundsStore.current.accounts"
          :base-currency="fundsStore.current.base_currency"
          :transfers="store.transfers"
          :can-manage-accounts="flow.permissions.value.canManageSettings"
          @enable="flow.handleEnableCurrency"
          @disable="flow.handleDisableCurrency"
          @transfer="flow.openSheet('transfer')"
        />
      </section>

      <!-- 6. Настройки, код фонда и тариф -->
      <section v-else-if="fundsStore.current" key="settings" class="section">
        <FundCodeCard :code="fundsStore.current.code" @copy="flow.handleCopy" />
        <PlanCard
          :info="fundsStore.current.plan"
          :options="fundsStore.plans"
          :can-request="flow.permissions.value.isChairman"
          :has-pending-request="store.hasPendingPlanRequest"
          @request="flow.openPlanRequest"
        />
        <SettingsPanel
          :fund="fundsStore.current"
          :currencies="store.activeCurrencies"
          :requisites="store.requisites"
          :is-chairman="flow.permissions.value.isChairman"
          :is-submitting="store.isSubmitting"
          @save="flow.handleSaveSettings"
          @add-requisite="flow.openSheet('requisite')"
          @toggle-requisite="flow.handleToggleRequisite"
          @delete-requisite="flow.handleDeleteRequisite"
        />
      </section>
    </Transition>

    <!-- ═══ Шторки ═══ -->
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

    <BottomSheet :open="flow.sheet.value === 'expense'" :title="$t('admin.expenses.sheetTitle')" @close="flow.closeSheet">
      <ExpenseForm
        v-if="fundsStore.current"
        :funds="targetFundsStore.items"
        :fund-name="fundsStore.current.name"
        :currencies="store.activeCurrencies"
        :base-currency="fundsStore.current.base_currency"
        :is-submitting="store.isSubmitting"
        @submit="flow.handleAddExpense"
      />
    </BottomSheet>

    <BottomSheet :open="flow.sheet.value === 'fund'" :title="$t('admin.funds.sheetTitle')" @close="flow.closeSheet">
      <FundForm
        v-if="fundsStore.current"
        :currencies="store.activeCurrencies"
        :base-currency="fundsStore.current.base_currency"
        :is-submitting="store.isSubmitting"
        @submit="flow.handleAddFund"
      />
    </BottomSheet>

    <BottomSheet :open="flow.sheet.value === 'transfer'" :title="$t('admin.accounts.newTransfer')" @close="flow.closeSheet">
      <TransferForm :currencies="store.activeCurrencies" :is-submitting="store.isSubmitting" @submit="flow.handleAddTransfer" />
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

    <BottomSheet :open="flow.sheet.value === 'plan'" :title="$t('plans.requestTitle')" @close="flow.closeSheet">
      <PlanRequestForm
        v-if="flow.selectedPlan.value"
        :plan="flow.selectedPlan.value"
        :options="fundsStore.plans"
        :is-submitting="store.isSubmitting"
        @submit="flow.handlePlanRequest"
      />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.admin-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 16px;
}

.intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.role-badge {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 20px;
  background: $gradient;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.access {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: $text-muted;
}

/* ── Sections ─────────────────────────────────────────────────────────────── */
.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  @include section-title;
  font-size: 17px;
}

.section-sub {
  font-size: 12px;
  color: $text-muted;
}

.count-pill {
  flex-shrink: 0;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(245, 158, 11, 0.14);
  color: #B45309;
  font-size: 12px;
  font-weight: 700;
}

.cta-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 9px 14px;
  font-size: 13px;
}

.ghost-btn {
  @include ghost-button;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.grid {
  display: grid;
  gap: 10px;
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 600;
  color: $navy;
}

@media (min-width: 768px) {
  .admin-page {
    padding: 24px;
  }

  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
