<script setup lang="ts">
import { computed, ref } from 'vue'
import { formatDateTime } from '@/shared/lib/format.ts'
import type { PlanApprove, PlanRequest } from '../types.ts'

const props = defineProps<{
  request: PlanRequest
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'approve', request: PlanRequest, payload: PlanApprove): void
  (e: 'reject', request: PlanRequest, comment: string): void
}>()

const months = ref(props.request.months)
const memberLimit = ref<number | null>(null)
const monthlyPrice = ref<number | null>(null)

const isIndividual = computed(() => props.request.plan === 'individual')
// У individual дни остатка считаем по введённой договорной цене (месяц тарифа — 30 дней)
const carryoverDays = computed(() => {
  const { carryover_tjs: value, carryover_days: days } = props.request
  if (!isIndividual.value || value === null) return days
  return monthlyPrice.value ? Math.round((value / monthlyPrice.value) * 30) : null
})
const canApprove = computed(() => !isIndividual.value || !!monthlyPrice.value)
const comment = ref('')
// Цена зафиксирована при подаче заявки; срок админ может поправить — итог пересчитывается
const total = computed(() => {
  const { price_tjs: price, list_price_tjs: list, discount_months: discounted } = props.request
  if (!price || !list) return null
  const count = months.value || 0
  const withDiscount = Math.min(discounted, count)
  return price * withDiscount + list * (count - withDiscount)
})
</script>

<template>
  <div class="request" :class="`request--${request.status}`">
    <div class="top">
      <div>
        <b>{{ request.fund_name }}</b>
        <span class="meta">{{ request.requested_by_name }} · {{ formatDateTime(request.created_at) }}</span>
      </div>
      <span class="plan">{{ $t(`plans.${request.plan}`) }} · {{ $t('plans.monthsShort', { n: request.months }) }}</span>
    </div>
    <p class="contact">📞 {{ $t('platform.contact') }}: <b>{{ request.contact || '—' }}</b></p>
    <p v-if="request.comment" class="comment">«{{ request.comment }}»</p>
    <p v-if="request.price_tjs" class="price-line">
      💰 {{ $t('plans.price', { price: request.price_tjs }) }}
      <s v-if="request.discount_label">{{ request.list_price_tjs }}</s>
      <b v-if="total"> · {{ $t('plans.total', { price: total }) }}</b>
      <span v-if="request.discount_label" class="discount">
        · 🏷 {{ request.discount_label }} · {{ $t('platform.pricing.forMonths', { n: request.discount_months }) }}
      </span>
    </p>
    <p v-if="request.status === 'pending' && request.carryover_tjs" class="carryover">
      🔁 {{ $t('platform.carryover', { amount: request.carryover_tjs }) }}
      <b v-if="carryoverDays !== null">{{ $t('platform.carryoverDays', { n: carryoverDays }) }}</b>
    </p>

    <!-- Решение админа -->
    <template v-if="request.status === 'pending'">
      <div class="fields">
        <label>
          <span>{{ $t('platform.months') }}</span>
          <input v-model.number="months" type="number" min="1" max="36" />
        </label>
        <label v-if="isIndividual">
          <span>{{ $t('platform.memberLimit') }}</span>
          <input v-model.number="memberLimit" type="number" min="1" :placeholder="$t('plans.unlimited')" />
        </label>
        <label v-if="isIndividual">
          <span>{{ $t('platform.monthlyPrice') }} *</span>
          <input v-model.number="monthlyPrice" type="number" min="1" />
        </label>
      </div>
      <input v-model="comment" class="comment-input" :placeholder="$t('platform.commentPlaceholder')" />

      <div class="actions">
        <button
          class="ghost-btn ghost-btn--danger"
          :disabled="isSubmitting || comment.trim().length < 3"
          @click="emit('reject', request, comment.trim())"
        >
          {{ $t('platform.reject') }}
        </button>
        <button
          class="cta-btn"
          :disabled="isSubmitting || !canApprove"
          @click="
            emit('approve', request, {
              months,
              member_limit: memberLimit || null,
              monthly_price: monthlyPrice || null,
              admin_comment: comment.trim() || null,
            })
          "
        >
          {{ $t('platform.approve') }}
        </button>
      </div>
    </template>

    <p v-else class="result">
      {{ $t(`platform.status.${request.status}`) }}
      <template v-if="request.admin_comment"> · {{ request.admin_comment }}</template>
    </p>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.price-line {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
  overflow-wrap: anywhere;

  b {
    color: $navy;
  }

  s {
    color: $text-muted;
  }

  .discount {
    font-weight: 600;
    color: $success;
  }
}

.carryover {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f3f4f6;
  font-size: 13px;
  color: #374151;

  b {
    margin-left: 4px;
    color: #111827;
  }
}

.request {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;

  &--pending {
    border-color: rgba(245, 158, 11, 0.4);
  }
}

.top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;

  b {
    display: block;
    color: $navy;
  }
}

.meta {
  font-size: 12px;
  color: $text-muted;
}

.plan {
  flex-shrink: 0;
  padding: 4px 12px;
  border-radius: 20px;
  background: $gradient;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.comment {
  margin: 0;
  font-size: 13px;
  font-style: italic;
  color: $text-secondary;
}

.fields {
  display: flex;
  gap: 10px;

  label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    font-size: 12px;
    color: $text-secondary;
  }

  input {
    @include field-input;
    padding: 9px 12px;
  }
}

.comment-input {
  @include field-input;
  padding: 9px 12px;
}

.actions {
  display: flex;
  gap: 8px;

  > * {
    flex: 1;
  }
}

.ghost-btn {
  @include ghost-button;

  &--danger {
    color: $danger;
  }
}

.cta-btn {
  @include cta-button;
  padding: 10px;
}

.result {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
}

.contact {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
  word-break: break-word;

  b {
    color: $navy;
  }
}
</style>
