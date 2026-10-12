<script setup lang="ts">
import { LuEye, LuShieldCheck } from '@kalimahapps/vue-icons/lu'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { formatDateTime, formatMoney } from '@/shared/lib/format.ts'
import type { Contribution } from '@/features/contributions/types.ts'

// В очереди — кнопка «Проверить», в истории — статус и просмотр чека

defineProps<{
  contribution: Contribution
}>()

const emit = defineEmits<{
  (e: 'check', contribution: Contribution): void
}>()
</script>

<template>
  <div class="verify-card">
    <button class="thumb" :aria-label="$t('admin.verification.check')" @click="emit('check', contribution)">
      <img :src="contribution.receipt_image" alt="" />
    </button>

    <div class="details">
      <div class="name">
        {{ contribution.user_name }}
        <span class="unit">{{ contribution.user_unit }}</span>
      </div>
      <span class="purpose">
        {{ contribution.target_fund_title ?? $t(`contributionCategory.${contribution.category}`) }}
      </span>
      <span v-if="contribution.requisite_label" class="requisite">💳 {{ contribution.requisite_label }}</span>
      <span class="date">{{ formatDateTime(contribution.created_at) }}</span>
      <span v-if="contribution.comment_user" class="comment">«{{ contribution.comment_user }}»</span>
    </div>

    <div class="right">
      <div class="sums">
        <span class="amount">{{ formatMoney(contribution.amount, contribution.currency, true) }}</span>
        <span v-if="contribution.currency !== contribution.credited_currency" class="credited">
          {{ $t('contribution.creditedShort', { amount: formatMoney(contribution.credited_amount, contribution.credited_currency) }) }}
        </span>
      </div>
      <button v-if="contribution.status === 'pending'" class="check-btn" @click="emit('check', contribution)">
        <LuShieldCheck /> {{ $t('admin.verification.check') }}
      </button>
      <template v-else>
        <StatusBadge :status="contribution.status" />
        <button class="view-btn" @click="emit('check', contribution)"><LuEye /> {{ $t('receipt.view') }}</button>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.verify-card {
  @include glass-card(18px);
  display: flex;
  gap: 12px;
  padding: 12px;
}

.thumb {
  @include pressable;
  flex-shrink: 0;
  width: 56px;
  height: 74px;
  padding: 0;
  overflow: hidden;
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 10px;
  background: #fff;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.unit {
  margin-left: 4px;
  font-size: 12px;
  font-weight: 600;
  color: $teal;
}

.purpose {
  font-size: 12px;
  font-weight: 600;
  color: $text-secondary;
}

.date {
  font-size: 11px;
  color: $text-muted;
}

.requisite {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: $text-secondary;
}

.comment {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-style: italic;
  color: $text-secondary;
}

.right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  gap: 6px;
  flex-shrink: 0;
}

.sums {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.credited {
  font-size: 11px;
  font-weight: 600;
  color: $text-muted;
}

.view-btn {
  @include ghost-button;
  padding: 5px 10px;
  font-size: 12px;
}

.amount {
  font-size: 15px;
  font-weight: 700;
  color: $success;
}

.check-btn {
  @include cta-button;
  padding: 7px 12px;
  font-size: 12px;
}
</style>
