<script setup lang="ts">
import { formatPhone } from '@/shared/lib/formatters.ts'
import { computed } from 'vue'
import type { FundRole, MemberStatus } from '@/features/funds/types.ts'
import { formatDate, formatMoney } from '@/shared/lib/format.ts'
import type { Member } from '../types.ts'

const props = defineProps<{
  member: Member
  isMe: boolean
  canChangeRoles: boolean
}>()

const emit = defineEmits<{
  (e: 'status', member: Member, status: MemberStatus): void
  (e: 'role', member: Member, role: FundRole): void
  (e: 'make-chairman', member: Member): void
}>()

const balanceLabel = computed(() => {
  const balance = props.member.balance
  if (!balance) return null
  if (balance.status === 'debt') return { key: 'admin.members.debt', amount: formatMoney(balance.debt_amount, balance.currency) }
  if (balance.status === 'advance') {
    return { key: 'admin.members.advance', amount: formatMoney(balance.advance_amount, balance.currency) }
  }
  return { key: 'admin.members.paid', amount: '' }
})

// Председателя и себя менять нельзя — бэкенд тоже это запрещает
const isEditable = computed(() => !props.isMe && props.member.role !== 'chairman')
</script>

<template>
  <div class="member-card" :class="{ 'member-card--blocked': member.status === 'blocked' }">
    <div class="top">
      <span class="unit">{{ member.address_unit ?? '—' }}</span>
      <span class="role" :class="`role--${member.role}`">{{ $t(`roles.${member.role}`) }}</span>
    </div>

    <div class="name">
      {{ member.full_name }}
      <span v-if="isMe" class="me">{{ $t('admin.members.you') }}</span>
    </div>
    <span class="contact">{{ member.phone ? formatPhone(member.phone) : member.email }}</span>

    <div v-if="balanceLabel && member.balance" class="row">
      <span>{{ $t('admin.members.totalPaid') }}: {{ formatMoney(member.balance.total_paid, member.balance.currency) }}</span>
      <b :class="`balance--${member.balance.status}`">{{ $t(balanceLabel.key, { amount: balanceLabel.amount }) }}</b>
    </div>
    <span v-if="member.status === 'blocked'" class="status">
      {{ member.blocked_at ? $t('absence.blockedAt', { date: formatDate(member.blocked_at) }) : $t('memberStatus.blocked') }}
      <template v-if="member.left_at"> · {{ $t('absence.leftWhileBlocked') }}</template>
    </span>
    <span v-if="member.status === 'blocked' && member.balance" class="frozen">{{ $t('absence.balanceFrozen') }}</span>

    <div v-if="isEditable" class="actions">
      <button v-if="member.status === 'active'" class="ghost-btn ghost-btn--danger" @click="emit('status', member, 'blocked')">
        {{ $t('admin.members.block') }}
      </button>
      <button v-else class="ghost-btn" @click="emit('status', member, 'active')">{{ $t('admin.members.unblock') }}</button>

      <template v-if="canChangeRoles && member.status === 'active'">
        <button v-if="member.role === 'resident'" class="ghost-btn" @click="emit('role', member, 'admin')">
          {{ $t('admin.members.makeAdmin') }}
        </button>
        <button v-else class="ghost-btn" @click="emit('role', member, 'resident')">
          {{ $t('admin.members.makeResident') }}
        </button>
        <button class="ghost-btn" @click="emit('make-chairman', member)">👑 {{ $t('admin.members.makeChairman') }}</button>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.member-card {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;

  &--blocked {
    opacity: 0.7;
  }
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.unit {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.14);
  color: #111827;
  font-size: 12px;
  font-weight: 700;
}

.role {
  font-size: 11px;
  font-weight: 700;
  color: $text-muted;

  &--chairman {
    color: #B45309;
  }

  &--admin {
    color: $navy;
  }
}

.name {
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.me {
  margin-left: 6px;
  padding: 1px 8px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.08);
  font-size: 11px;
}

.contact {
  font-size: 13px;
  color: $text-secondary;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: $text-muted;
}

.balance--debt {
  color: $danger;
}

.balance--advance {
  color: $success;
}

.balance--ok {
  color: $teal;
}

.status {
  align-self: flex-start;
  padding: 2px 10px;
  border-radius: 20px;
  background: rgba(239, 68, 68, 0.1);
  color: #B91C1C;
  font-size: 11px;
  font-weight: 700;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.ghost-btn {
  @include ghost-button;
  padding: 6px 12px;
  font-size: 12px;

  &--danger {
    color: $danger;
  }
}

.frozen {
  font-size: 11px;
  color: $text-muted;
}
</style>
