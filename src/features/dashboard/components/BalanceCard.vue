<script setup lang="ts">
import { ref } from 'vue'
import { LuEye, LuEyeOff } from '@kalimahapps/vue-icons/lu'
import { CURRENCY_SYMBOLS } from '@/shared/lib/currency.ts'
import { formatMoney } from '@/shared/lib/format.ts'
import type { AccountSummary } from '../types.ts'

/** Остаток фонда: тёмная акцентная карточка, базовый счёт крупно, остальные счета ниже. */
defineProps<{
  baseAccount: AccountSummary
  otherAccounts: AccountSummary[]
  caption: string
  fundName: string
  unit: string | null
}>()

const isVisible = ref(true)
const HIDDEN = '••••••'
</script>

<template>
  <section class="balance-card">
    <div class="top">
      <span class="caption">{{ caption }} · {{ baseAccount.currency.toUpperCase() }}</span>
      <button class="eye-btn" :aria-label="$t('dashboard.toggleBalance')" @click="isVisible = !isVisible">
        <LuEye v-if="isVisible" />
        <LuEyeOff v-else />
      </button>
    </div>

    <div class="amount">
      <template v-if="isVisible">
        {{ baseAccount.balance.toLocaleString('ru-RU') }}<span class="symbol">{{ CURRENCY_SYMBOLS[baseAccount.currency] }}</span>
      </template>
      <template v-else>{{ HIDDEN }}</template>
    </div>

    <div v-if="otherAccounts.length" class="others">
      <span v-for="account in otherAccounts" :key="account.currency" class="other">
        {{ isVisible ? formatMoney(account.balance, account.currency) : HIDDEN }}
      </span>
    </div>

    <!-- Низ карточки — как «держатель» и «срок» у банковской карты -->
    <div class="bottom">
      <div class="meta">
        <span class="meta-label">{{ $t('dashboard.card.fund') }}</span>
        <span class="meta-value">{{ fundName }}</span>
      </div>
      <div v-if="unit" class="meta meta--right">
        <span class="meta-label">{{ $t('dashboard.card.unit') }}</span>
        <span class="meta-value">{{ unit }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.balance-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 24px;
  // Тёмная «карта»: зелёный отсвет сверху слева, синий — снизу справа
  background:
    radial-gradient(120% 90% at 0% 0%, rgba(52, 98, 74, 0.85) 0%, rgba(52, 98, 74, 0) 55%),
    radial-gradient(110% 90% at 100% 100%, rgba(37, 66, 110, 0.9) 0%, rgba(37, 66, 110, 0) 55%),
    linear-gradient(160deg, #1d2420 0%, #12161c 100%);
  box-shadow: 0 12px 30px rgba(17, 24, 39, 0.22);
  color: #fff;
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.caption {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.72);
}

.eye-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 16px;
}

.amount {
  font-size: clamp(34px, 10vw, 42px);
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.symbol {
  margin-left: 6px;
  font-size: 0.45em;
  font-weight: 500;
  letter-spacing: 0;
  color: rgba(255, 255, 255, 0.6);
}

.others {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.other {
  padding: 4px 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 13px;
  font-weight: 500;
}

.bottom {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 8px;
}

.meta {
  display: flex;
  flex-direction: column;
  min-width: 0;

  &--right {
    flex-shrink: 0;
    text-align: right;
  }
}

.meta-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
}

.meta-value {
  overflow: hidden;
  font-size: 14px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
