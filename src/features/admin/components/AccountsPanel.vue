<script setup lang="ts">
import { computed } from 'vue'
import { LuArrowLeftRight, LuPlus } from '@kalimahapps/vue-icons/lu'
import type { AccountTransfer } from '@/features/announcements/types.ts'
import type { Account } from '@/features/funds/types.ts'
import { CURRENCIES, type Currency } from '@/shared/lib/currency.ts'
import { formatDateTime, formatMoney } from '@/shared/lib/format.ts'

const props = defineProps<{
  accounts: Account[]
  baseCurrency: Currency
  transfers: AccountTransfer[]
  canManageAccounts: boolean
}>()

const emit = defineEmits<{
  (e: 'enable', currency: Currency): void
  (e: 'disable', currency: Currency): void
  (e: 'transfer'): void
}>()

const activeAccounts = computed(() => props.accounts.filter((a) => a.is_active))
const missingCurrencies = computed(() =>
  CURRENCIES.filter((c) => !props.accounts.some((a) => a.currency === c && a.is_active)),
)
</script>

<template>
  <div class="accounts-panel">
    <!-- 1. Остатки по каждому валютному счёту -->
    <div class="accounts">
      <div v-for="account in activeAccounts" :key="account.currency" class="account">
        <div class="account-top">
          <span class="code">{{ account.currency.toUpperCase() }}</span>
          <span v-if="account.currency === baseCurrency" class="base">{{ $t('admin.accounts.base') }}</span>
        </div>
        <div class="balance">{{ formatMoney(account.balance, account.currency) }}</div>
        <button
          v-if="canManageAccounts && account.currency !== baseCurrency"
          class="link-btn"
          @click="emit('disable', account.currency)"
        >
          {{ $t('admin.accounts.disable') }}
        </button>
      </div>
    </div>

    <!-- Подключить валюту -->
    <div v-if="canManageAccounts && missingCurrencies.length" class="enable-row">
      <span>{{ $t('admin.accounts.enableHint') }}</span>
      <button
        v-for="currency in missingCurrencies"
        :key="currency"
        class="ghost-btn"
        @click="emit('enable', currency)"
      >
        <LuPlus /> {{ currency.toUpperCase() }}
      </button>
    </div>

    <!-- 2. Переводы и корректировки -->
    <div class="card">
      <div class="card-header">
        <div>
          <h3 class="card-title">{{ $t('admin.accounts.transfersTitle') }}</h3>
          <p class="card-sub">{{ $t('admin.accounts.transfersHint') }}</p>
        </div>
        <button class="cta-btn" @click="emit('transfer')"><LuArrowLeftRight /> {{ $t('admin.accounts.newTransfer') }}</button>
      </div>

      <div v-if="transfers.length" class="transfers">
        <div v-for="transfer in transfers" :key="transfer.id" class="transfer">
          <div class="amounts">
            <span v-if="transfer.from_currency" class="out">
              −{{ formatMoney(transfer.from_amount ?? 0, transfer.from_currency) }}
            </span>
            <span v-if="transfer.from_currency && transfer.to_currency" class="arrow">→</span>
            <span v-if="transfer.to_currency" class="in">+{{ formatMoney(transfer.to_amount ?? 0, transfer.to_currency) }}</span>
          </div>
          <p class="comment">{{ transfer.comment }}</p>
          <span class="meta">{{ transfer.created_by_name }} · {{ formatDateTime(transfer.created_at) }}</span>
        </div>
      </div>
      <p v-else class="empty">{{ $t('admin.accounts.noTransfers') }}</p>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.accounts-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.accounts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.account {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px;
}

.account-top {
  display: flex;
  align-items: center;
  gap: 6px;
}

.code {
  font-size: 13px;
  font-weight: 700;
  color: $text-secondary;
}

.base {
  padding: 1px 8px;
  border-radius: 10px;
  background: $gradient;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
}

.balance {
  font-size: 20px;
  font-weight: 700;
  color: $navy;
}

.link-btn {
  align-self: flex-start;
  padding: 0;
  border: none;
  background: none;
  color: $text-muted;
  font-size: 12px;
  text-decoration: underline;
}

.enable-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 13px;
  color: $text-secondary;
}

.ghost-btn {
  @include ghost-button;
  padding: 7px 12px;
}

/* ── Переводы ─────────────────────────────────────────────────────────────── */
.card {
  @include glass-card;
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.card-sub {
  margin: 2px 0 0;
  font-size: 12px;
  color: $text-muted;
}

.cta-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 9px 14px;
  font-size: 13px;
}

.transfers {
  display: flex;
  flex-direction: column;
}

.transfer {
  padding: 10px 0;

  & + & {
    border-top: 1px solid rgba(17, 24, 39, 0.06);
  }
}

.amounts {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 15px;
  font-weight: 700;

  .out {
    color: $danger;
  }

  .in {
    color: $success;
  }

  .arrow {
    color: $text-muted;
  }
}

.comment {
  margin: 2px 0;
  font-size: 13px;
  color: #374151;
}

.meta,
.empty {
  font-size: 12px;
  color: $text-muted;
}

.empty {
  margin: 0;
}
</style>
