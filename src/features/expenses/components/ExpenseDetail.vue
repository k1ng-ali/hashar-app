<script setup lang="ts">
import { formatDateTime, formatMoney } from '@/shared/lib/format.ts'
import { EXPENSE_CATEGORY_ICONS, type Expense } from '../types.ts'

defineProps<{
  expense: Expense
}>()

const emit = defineEmits<{
  (e: 'open-receipt', expense: Expense, index: number): void
  (e: 'open-fund', id: number): void
}>()
</script>

<template>
  <div class="expense-detail">
    <div class="hero">
      <span class="icon">{{ EXPENSE_CATEGORY_ICONS[expense.category] }}</span>
      <div>
        <h2 class="title">{{ expense.title }}</h2>
        <span class="amount">−{{ formatMoney(expense.amount, expense.currency) }}</span>
      </div>
    </div>

    <div class="info">
      <div class="row">
        <span class="label">{{ $t('expenses.category') }}</span>
        <span class="value">{{ $t(`expenseCategory.${expense.category}`) }}</span>
      </div>
      <div class="row">
        <span class="label">{{ $t('expenses.account') }}</span>
        <span class="value">{{ expense.currency.toUpperCase() }}</span>
      </div>
      <div v-if="expense.target_fund_id && expense.target_fund_title" class="row">
        <span class="label">{{ $t('expenses.targetFund') }}</span>
        <button class="link" @click="emit('open-fund', expense.target_fund_id)">🎯 {{ expense.target_fund_title }}</button>
      </div>
      <div class="row">
        <span class="label">{{ $t('expenses.recordedBy') }}</span>
        <span class="value">{{ expense.created_by_name ?? '—' }}</span>
      </div>
      <div class="row">
        <span class="label">{{ $t('expenses.date') }}</span>
        <span class="value">{{ formatDateTime(expense.created_at) }}</span>
      </div>
    </div>

    <section>
      <h3 class="section-title">{{ $t('expenses.justification') }}</h3>
      <p class="description">{{ expense.description }}</p>
    </section>

    <section>
      <h3 class="section-title">{{ $t('expenses.documentsTitle') }}</h3>
      <div v-if="expense.receipt_images.length" class="gallery">
        <button
          v-for="(image, index) in expense.receipt_images"
          :key="index"
          class="doc"
          :aria-label="$t('receipt.view')"
          @click="emit('open-receipt', expense, index)"
        >
          <img :src="image" alt="" />
          <span class="zoom">🔍</span>
        </button>
      </div>
      <p v-else class="empty">{{ $t('expenses.noDocumentsHint') }}</p>
    </section>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.expense-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero {
  display: flex;
  align-items: center;
  gap: 14px;
}

.icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: rgba(239, 68, 68, 0.08);
  font-size: 26px;
}

.title {
  margin: 0 0 2px;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.3;
  color: $navy;
}

.amount {
  font-size: 22px;
  font-weight: 700;
  color: $danger;
}

.info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(17, 24, 39, 0.04);
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.label {
  color: $text-muted;
}

.value {
  font-weight: 600;
  text-align: right;
  color: $navy;
}

.link {
  padding: 0;
  border: none;
  background: none;
  font-weight: 700;
  text-align: right;
  color: $teal;
  cursor: pointer;
}

.section-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.description {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: $text-secondary;
  white-space: pre-line;
}

.gallery {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.doc {
  @include pressable;
  position: relative;
  aspect-ratio: 3 / 4;
  padding: 0;
  overflow: hidden;
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 14px;
  background: #fff;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.zoom {
  position: absolute;
  right: 8px;
  bottom: 8px;
  padding: 3px 8px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.6);
  font-size: 12px;
}

.empty {
  margin: 0;
  font-size: 13px;
  color: $text-muted;
}

@media (min-width: 768px) {
  .gallery {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
