<script setup lang="ts">
import AbsenceDecision from '@/features/admin/components/AbsenceDecision.vue'
import MemberCard from '@/features/admin/components/MemberCard.vue'
import MemberRequestCard from '@/features/admin/components/MemberRequestCard.vue'
import { useAdminFlow } from '@/features/admin/composables/useAdminFlow.ts'
import { useFundSubpage } from '@/features/admin/composables/useFundSubpage.ts'
import { useAdminStore } from '@/features/admin/store.ts'
import { useAuthStore } from '@/features/auth/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { formatDate, formatMoney } from '@/shared/lib/format.ts'

const store = useAdminStore()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const flow = useAdminFlow()

useFundSubpage('fundMenu.members', store.fetchMembers)
</script>

<template>
  <div class="subpage">
    <template v-if="store.isLoading && !store.members.length">
      <CardSkeleton v-for="i in 3" :key="i" />
    </template>

    <EmptyState v-else-if="store.errorMessage" icon="📡" :title="$t(store.errorMessage)">
      <button class="ghost-btn" @click="store.fetchMembers()">{{ $t('common.retry') }}</button>
    </EmptyState>

    <template v-else>
      <!-- Заявки на вступление -->
      <section v-if="store.joinRequests.length" class="section">
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
      </section>

      <!-- Реестр -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">{{ $t('admin.members.title') }}</h2>
          <span class="limit">
            {{ $t('admin.members.limit', {
              n: fundsStore.current?.plan.members_count ?? 0,
              limit: fundsStore.current?.plan.member_limit ?? '∞',
            }) }}
          </span>
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

      <!-- Вышедшие: долг за время участия сохраняется -->
      <section v-if="store.formerMembers.length" class="section">
        <div class="section-header">
          <h2 class="section-title">{{ $t('absence.formerTitle') }} · {{ store.formerMembers.length }}</h2>
        </div>
        <p class="section-hint">{{ $t('absence.formerHint') }}</p>
        <div class="former">
          <div v-for="member in store.formerMembers" :key="member.id" class="former-row">
            <div class="former-info">
              <span class="former-name">{{ member.full_name }}</span>
              <span class="former-meta">
                {{ member.address_unit ?? '—' }}
                <template v-if="member.left_at"> · {{ $t('absence.leftAt', { date: formatDate(member.left_at) }) }}</template>
              </span>
            </div>
            <span v-if="member.balance?.debt_amount" class="former-debt">
              {{ $t('absence.debtShort', { amount: formatMoney(member.balance.debt_amount, member.balance.currency) }) }}
            </span>
            <span v-else class="former-ok">{{ $t('absence.noDebtShort') }}</span>
          </div>
        </div>
      </section>
    </template>

    <BottomSheet
      :open="flow.sheet.value === 'absence' && !!flow.selectedMember.value"
      :title="flow.selectedMember.value?.absence?.reason === 'left' ? $t('absence.titleReturn') : $t('absence.titleUnblock')"
      @close="flow.closeSheet"
    >
      <AbsenceDecision
        v-if="flow.selectedMember.value?.absence"
        :key="flow.selectedMember.value.id"
        :member="flow.selectedMember.value"
        :is-submitting="store.isSubmitting"
        @confirm="flow.handleAbsenceDecision"
      />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.subpage {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 960px;
  margin: 0 auto;
  padding: 16px;
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
}

.limit {
  font-size: 12px;
  color: $text-muted;
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
  font-weight: 500;
  color: $navy;
}

.ghost-btn {
  @include ghost-button;
}

@media (min-width: 768px) {
  .subpage {
    padding: 24px;
  }

  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.section-hint {
  margin: -6px 0 0;
  font-size: 12px;
  color: $text-muted;
}

.former {
  @include glass-card(18px);
  overflow: hidden;
}

.former-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;

  & + & {
    border-top: 1px solid $hairline;
  }
}

.former-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.former-name {
  font-size: 14px;
  font-weight: 500;
  color: $navy;
}

.former-meta {
  font-size: 12px;
  color: $text-muted;
}

.former-debt {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
  color: $danger;
}

.former-ok {
  flex-shrink: 0;
  font-size: 12px;
  color: $text-muted;
}
</style>
