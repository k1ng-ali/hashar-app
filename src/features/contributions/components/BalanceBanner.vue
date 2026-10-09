<script setup lang="ts">
import { computed } from 'vue'
import { formatMoney, formatPeriod } from '@/shared/lib/format.ts'
import type { ResidentBalance } from '../types.ts'

const props = defineProps<{
  balance: ResidentBalance
}>()

const emit = defineEmits<{
  (e: 'pay'): void
}>()

const unpaidLabel = computed(() => props.balance.unpaid_periods.map((p) => formatPeriod(p, true)).join(', '))
</script>

<template>
  <!-- Долг -->
  <div v-if="balance.status === 'debt'" class="banner banner--debt">
    <span class="banner-icon">⚠️</span>
    <div class="banner-text">
      <div class="banner-title">{{ $t('balance.debtTitle', { amount: formatMoney(balance.debt_amount, balance.currency) }) }}</div>
      <div class="banner-sub">
        {{ $t('balance.debtSub', { count: balance.debt_months_count, periods: unpaidLabel }) }}
      </div>
    </div>
    <button class="pay-btn" @click="emit('pay')">{{ $t('balance.payDebt') }}</button>
  </div>

  <!-- Аванс -->
  <div v-else-if="balance.status === 'advance'" class="banner banner--advance">
    <span class="banner-icon">🎉</span>
    <div class="banner-text">
      <div class="banner-title">{{ $t('balance.advanceTitle') }}</div>
      <div class="banner-sub">
        {{
          $t('balance.advanceSub', {
            amount: formatMoney(balance.advance_amount, balance.currency),
            period: formatPeriod(balance.paid_until_period),
          })
        }}
      </div>
    </div>
  </div>

  <!-- Всё оплачено -->
  <div v-else class="banner banner--ok">
    <span class="banner-icon">✅</span>
    <div class="banner-text">
      <div class="banner-title">{{ $t('balance.okTitle') }}</div>
      <div class="banner-sub">{{ $t('balance.okSub', { period: formatPeriod(balance.next_billing_period) }) }}</div>
    </div>
  </div>

  <p v-if="balance.has_pending" class="pending-note">
    ⏱ {{ $t('balance.pendingNote', { amount: formatMoney(balance.pending_amount, balance.currency) }) }}
  </p>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.banner {
  @include glass-card(18px);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;

  &--debt {
    border-color: rgba(239, 68, 68, 0.25);
    background: rgba(254, 242, 242, 0.85);
  }

  &--advance {
    border-color: rgba(16, 185, 129, 0.25);
    background: rgba(236, 253, 245, 0.85);
  }
}

.banner-icon {
  font-size: 24px;
}

.banner-text {
  flex: 1;
  min-width: 0;
}

.banner-title {
  font-size: 14px;
  font-weight: 800;
  color: $navy;

  .banner--debt & {
    color: #B91C1C;
  }

  .banner--advance & {
    color: #047857;
  }
}

.banner-sub {
  margin-top: 2px;
  font-size: 12px;
  color: $text-secondary;
}

.pay-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 9px 16px;
  font-size: 13px;
  background: linear-gradient(135deg, #F87171, #EF4444);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.pending-note {
  margin: 8px 4px 0;
  font-size: 12px;
  color: #B45309;
}
</style>
