<script setup lang="ts">
import { computed } from 'vue'
import { LuChevronRight, LuPaperclip, LuTrash2 } from '@kalimahapps/vue-icons/lu'
import { formatDateTime, formatMoney } from '@/shared/lib/format.ts'
import { EXPENSE_CATEGORY_ICONS, type Expense } from '../types.ts'

const props = defineProps<{
  expense: Expense
  canDelete?: boolean
}>()

const emit = defineEmits<{
  (e: 'open', expense: Expense): void
  (e: 'open-receipt', expense: Expense, index: number): void
  (e: 'delete', id: number): void
}>()

// В ленте — до трёх миниатюр, остальные числом
const MAX_THUMBS = 3
const thumbs = computed(() => props.expense.receipt_images.slice(0, MAX_THUMBS))
const moreCount = computed(() => props.expense.receipt_images.length - thumbs.value.length)
</script>

<template>
  <article class="expense" @click="emit('open', expense)">
    <div class="top">
      <span class="category" :class="`category--${expense.category}`">
        {{ EXPENSE_CATEGORY_ICONS[expense.category] }} {{ $t(`expenseCategory.${expense.category}`) }}
      </span>
      <div class="top-right">
        <span class="date">{{ formatDateTime(expense.created_at) }}</span>
        <button
          v-if="canDelete"
          class="icon-btn"
          :aria-label="$t('common.delete')"
          @click.stop="emit('delete', expense.id)"
        >
          <LuTrash2 />
        </button>
      </div>
    </div>

    <div class="headline">
      <h2 class="title">{{ expense.title }}</h2>
      <span class="amount">−{{ formatMoney(expense.amount, expense.currency) }}</span>
    </div>

    <p class="description">{{ expense.description }}</p>

    <span v-if="expense.target_fund_title" class="fund">🎯 {{ $t('expenses.fromFund', { title: expense.target_fund_title }) }}</span>

    <!-- Чеки и акты -->
    <div v-if="thumbs.length" class="thumbs">
      <button
        v-for="(image, index) in thumbs"
        :key="index"
        class="thumb"
        :aria-label="$t('receipt.view')"
        @click.stop="emit('open-receipt', expense, index)"
      >
        <img :src="image" alt="" />
        <span v-if="index === thumbs.length - 1 && moreCount > 0" class="thumb-more">+{{ moreCount }}</span>
      </button>
    </div>

    <div class="footer">
      <span class="by">{{ $t('admin.expenses.by', { name: expense.created_by_name ?? '—' }) }}</span>
      <span class="more">
        <LuPaperclip v-if="expense.receipt_images.length" />
        {{ expense.receipt_images.length ? $t('expenses.documents', { n: expense.receipt_images.length }) : $t('expenses.noDocuments') }}
        <LuChevronRight />
      </span>
    </div>
  </article>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.expense {
  @include glass-card;
  @include pressable;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  cursor: pointer;
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.category {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.08);
  color: $navy;
  font-size: 11px;
  font-weight: 700;

  &--repair {
    background: rgba(245, 158, 11, 0.14);
    color: #B45309;
  }

  &--electrical {
    background: rgba(234, 179, 8, 0.16);
    color: #A16207;
  }

  &--emergency {
    background: rgba(239, 68, 68, 0.12);
    color: #B91C1C;
  }

  &--landscaping {
    background: rgba(16, 185, 129, 0.12);
    color: #047857;
  }

  &--cctv {
    background: rgba(99, 102, 241, 0.12);
    color: #4338CA;
  }
}

.date {
  font-size: 11px;
  color: $text-muted;
}

.icon-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.08);
  color: $danger;
}

.headline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
  color: $navy;
}

.amount {
  flex-shrink: 0;
  font-size: 17px;
  font-weight: 700;
  color: $danger;
}

.description {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  font-size: 14px;
  line-height: 1.5;
  color: $text-secondary;
  white-space: pre-line;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.fund {
  align-self: flex-start;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(17, 24, 39, 0.12);
  color: #111827;
  font-size: 12px;
  font-weight: 700;
}

.thumbs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.thumb {
  @include pressable;
  position: relative;
  aspect-ratio: 4 / 3;
  padding: 0;
  overflow: hidden;
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 12px;
  background: #fff;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.thumb-more {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.55);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(17, 24, 39, 0.06);
  font-size: 12px;
  color: $text-muted;
}

.more {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  font-weight: 700;
  color: $teal;
}
</style>
