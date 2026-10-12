<script setup lang="ts">
import { formatMoney } from '@/shared/lib/format.ts'
import type { ResidentBalance } from '../types.ts'

defineProps<{
  balance: ResidentBalance
}>()
</script>

<template>
  <div class="account-grid">
    <div class="cell">
      <span class="label">{{ $t('balance.status') }}</span>
      <span class="chip" :class="`chip--${balance.status}`">
        <span class="dot" />
        {{ $t(`balance.status_${balance.status}`) }}
      </span>
    </div>

    <div class="cell">
      <span class="label">{{ $t('balance.saldo') }}</span>
      <span class="value" :class="{ 'value--neg': balance.balance < 0, 'value--pos': balance.balance > 0 }">
        {{ formatMoney(balance.balance, balance.currency, true) }}
      </span>
    </div>

    <div class="cell">
      <span class="label">{{ $t('balance.totalDue') }}</span>
      <span class="value">{{ formatMoney(balance.total_due, balance.currency) }}</span>
    </div>

    <div class="cell">
      <span class="label">{{ $t('balance.totalPaid') }}</span>
      <span class="value">{{ formatMoney(balance.total_paid, balance.currency) }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
}

.label {
  font-size: 12px;
  color: $text-muted;
}

.value {
  font-size: 16px;
  font-weight: 700;
  color: $navy;

  &--neg {
    color: $danger;
  }

  &--pos {
    color: $success;
  }
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  &--debt {
    color: $danger;

    .dot {
      background: $danger;
    }
  }

  &--advance {
    color: $success;

    .dot {
      background: $success;
    }
  }

  &--ok {
    color: $teal;

    .dot {
      background: $teal;
    }
  }
}

@media (min-width: 768px) {
  .account-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
