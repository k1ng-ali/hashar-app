<script setup lang="ts">
import { computed } from 'vue'
import { LuEye } from '@kalimahapps/vue-icons/lu'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { formatDateTime, formatMoney, formatPeriod } from '@/shared/lib/format.ts'
import type { Contribution } from '../types.ts'

const props = defineProps<{
  contribution: Contribution
}>()

const emit = defineEmits<{
  (e: 'open-receipt', contribution: Contribution): void
}>()

const purpose = computed(() =>
  props.contribution.category === 'monthly_fee'
    ? formatPeriod(props.contribution.billing_period)
    : props.contribution.target_fund_title ?? '—',
)
</script>

<template>
  <div class="contribution-card">
    <div class="top">
      <span class="date">{{ formatDateTime(contribution.created_at) }}</span>
      <StatusBadge :status="contribution.status" />
    </div>

    <div class="body">
      <div class="info">
        <span class="category">{{ $t(`contributionCategory.${contribution.category}`) }}</span>
        <span class="purpose">{{ purpose }}</span>
        <span v-if="contribution.requisite_label" class="requisite">💳 {{ contribution.requisite_label }}</span>
        <span v-if="contribution.comment_user" class="comment">«{{ contribution.comment_user }}»</span>
      </div>
      <div class="sums">
        <span class="amount">{{ formatMoney(contribution.amount, contribution.currency, true) }}</span>
        <span v-if="contribution.currency !== contribution.credited_currency" class="credited">
          {{ $t('contribution.creditedShort', { amount: formatMoney(contribution.credited_amount, contribution.credited_currency) }) }}
        </span>
      </div>
    </div>

    <div class="footer">
      <button v-if="contribution.receipt_image" class="receipt-btn" @click="emit('open-receipt', contribution)">
        <LuEye /> {{ $t('receipt.view') }}
      </button>
      <span v-if="contribution.reviewed_at" class="reviewed">
        {{
          $t('history.reviewed', {
            name: contribution.reviewed_by_name ?? '—',
            date: formatDateTime(contribution.reviewed_at),
          })
        }}
      </span>
    </div>

    <div v-if="contribution.status === 'rejected' && contribution.comment_admin" class="reject-reason">
      {{ $t('history.rejectReason', { reason: contribution.comment_admin }) }}
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.contribution-card {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.date {
  font-size: 12px;
  color: $text-muted;
}

.body {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.category {
  font-size: 11px;
  font-weight: 700;
  color: $teal;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.purpose {
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.comment {
  font-size: 12px;
  font-style: italic;
  color: $text-secondary;
}

.amount {
  flex-shrink: 0;
  font-size: 16px;
  font-weight: 700;
  color: $success;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.receipt-btn {
  @include ghost-button;
  padding: 6px 12px;
  font-size: 12px;
}

.reviewed {
  font-size: 11px;
  color: $text-muted;
}

.reject-reason {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.08);
  color: #B91C1C;
  font-size: 12px;
  font-weight: 600;
}

.requisite {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: $text-secondary;
}

.sums {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
}

.credited {
  font-size: 11px;
  font-weight: 600;
  color: $text-muted;
}
</style>
