<script setup lang="ts">
import { LuEye, LuTrash2 } from '@kalimahapps/vue-icons/lu'
import { formatDateTime, formatMoney } from '@/shared/lib/format.ts'
import type { Expense } from '../types.ts'

defineProps<{
  expense: Expense
  canDelete: boolean
}>()

const emit = defineEmits<{
  (e: 'open-receipt', expense: Expense): void
  (e: 'delete', id: number): void
}>()
</script>

<template>
  <div class="expense-card">
    <div class="top">
      <span class="category">{{ $t(`expenseCategory.${expense.category}`) }}</span>
      <span class="amount">−{{ formatMoney(expense.amount, expense.currency) }}</span>
    </div>

    <div class="title">{{ expense.title }}</div>
    <p class="description">{{ expense.description }}</p>
    <span v-if="expense.target_fund_title" class="fund">🎯 {{ expense.target_fund_title }}</span>

    <div class="footer">
      <span class="by">
        {{ $t('admin.expenses.by', { name: expense.created_by_name ?? '—' }) }} · {{ formatDateTime(expense.created_at) }}
      </span>
      <div class="actions">
        <button v-if="expense.receipt_images.length" class="ghost-btn" @click="emit('open-receipt', expense)">
          <LuEye /> {{ $t('receipt.view') }}
        </button>
        <button v-if="canDelete" class="icon-btn" :aria-label="$t('common.delete')" @click="emit('delete', expense.id)">
          <LuTrash2 />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.expense-card {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.category {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(35, 73, 112, 0.08);
  color: $navy;
  font-size: 11px;
  font-weight: 700;
}

.amount {
  font-size: 15px;
  font-weight: 800;
  color: $danger;
}

.title {
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.description {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
}

.fund {
  font-size: 12px;
  font-weight: 600;
  color: $teal;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.by {
  font-size: 11px;
  color: $text-muted;
}

.actions {
  display: flex;
  gap: 6px;
}

.ghost-btn {
  @include ghost-button;
  padding: 6px 12px;
  font-size: 12px;
}

.icon-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.08);
  color: $danger;
}
</style>
