<script setup lang="ts">
import { ref } from 'vue'
import {
  LuArrowUpRight,
  LuEye,
  LuEyeOff,
  LuFlame,
  LuPlus,
  LuReceipt,
} from '@kalimahapps/vue-icons/lu'
import { formatMoney } from '@/shared/lib/format.ts'
import type { AccountSummary } from '../types.ts'

defineProps<{
  baseAccount: AccountSummary
  otherAccounts: AccountSummary[]
  caption: string
}>()

const emit = defineEmits<{
  (e: 'contribute'): void
  (e: 'expenses'): void
  (e: 'receipts'): void
  (e: 'funds'): void
}>()

const isVisible = ref(true)
const HIDDEN = '••••••'
</script>

<template>
  <div class="balance-card">
    <div class="glow" />

    <div class="top-row">
      <span class="caption-pill">
        <span class="live-dot" />
        {{ caption }}
      </span>
      <button class="eye-btn" :aria-label="$t('dashboard.toggleBalance')" @click="isVisible = !isVisible">
        <LuEye v-if="isVisible" />
        <LuEyeOff v-else />
      </button>
    </div>

    <!-- Базовый счёт — крупно -->
    <div class="label">
      {{ $t('dashboard.balanceLabel') }} · {{ baseAccount.currency.toUpperCase() }}
    </div>
    <div class="value">{{ isVisible ? formatMoney(baseAccount.balance, baseAccount.currency) : HIDDEN }}</div>

    <!-- Остальные валютные счета -->
    <div v-if="otherAccounts.length" class="accounts">
      <span v-for="account in otherAccounts" :key="account.currency" class="account-chip">
        {{ isVisible ? formatMoney(account.balance, account.currency) : HIDDEN }}
      </span>
    </div>
    <div v-else class="sub">{{ $t('dashboard.balanceCaption') }}</div>

    <!-- Быстрые действия -->
    <div class="actions">
      <button class="action" @click="emit('contribute')">
        <span class="action-circle action-circle--primary"><LuPlus /></span>
        <span>{{ $t('dashboard.actions.contribute') }}</span>
      </button>
      <button class="action" @click="emit('expenses')">
        <span class="action-circle"><LuArrowUpRight /></span>
        <span>{{ $t('dashboard.actions.expense') }}</span>
      </button>
      <button class="action" @click="emit('receipts')">
        <span class="action-circle"><LuReceipt /></span>
        <span>{{ $t('dashboard.actions.receipts') }}</span>
      </button>
      <button class="action" @click="emit('funds')">
        <span class="action-circle"><LuFlame /></span>
        <span>{{ $t('dashboard.actions.funds') }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.balance-card {
  position: relative;
  overflow: hidden;
  padding: 20px;
  border-radius: 28px;
  background: $gradient;
  color: #fff;
  box-shadow: 0 14px 36px rgba(35, 73, 112, 0.3);
}

.glow {
  position: absolute;
  top: -60px;
  right: -40px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.28), transparent 70%);
  pointer-events: none;
}

/* ── Top ──────────────────────────────────────────────────────────────────── */
.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 18px;
}

.caption-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 6px 12px;
  overflow: hidden;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.live-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6EE7B7;
  box-shadow: 0 0 0 3px rgba(110, 231, 183, 0.3);
}

.eye-btn {
  @include pressable;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  font-size: 18px;
}

/* ── Balance ──────────────────────────────────────────────────────────────── */
.label {
  font-size: 13px;
  opacity: 0.85;
}

.value {
  margin: 4px 0 8px;
  font-size: var(--fs-hero);
  font-weight: 800;
  letter-spacing: -0.5px;
}

.sub {
  font-size: 12px;
  opacity: 0.75;
}

.accounts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.account-chip {
  padding: 5px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 13px;
  font-weight: 700;
}

/* ── Actions ──────────────────────────────────────────────────────────────── */
.actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 22px;
}

.action {
  @include pressable;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: none;
  background: none;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.action-circle {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  font-size: 20px;

  &--primary {
    background: #fff;
    color: $navy;
  }
}
</style>
