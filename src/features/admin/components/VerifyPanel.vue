<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { LuCircleCheck, LuCircleX } from '@kalimahapps/vue-icons/lu'
import { formatDateTime, formatMoney, formatPeriod } from '@/shared/lib/format.ts'
import type { Contribution } from '@/features/contributions/types.ts'

const props = defineProps<{
  contribution: Contribution
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'zoom', contribution: Contribution): void
  (e: 'approve', creditedAmount: number | null): void
  (e: 'reject', reason: string): void
}>()

const isRejecting = ref(false)
const reason = ref('')
// Оплата в другой валюте: совет сверяет и при необходимости правит зачтённую сумму
const isOtherCurrency = computed(() => props.contribution.currency !== props.contribution.credited_currency)
const credited = ref<number | null>(props.contribution.credited_amount)

// Новая заявка — сбрасываем форму
watch(
  () => props.contribution.id,
  () => {
    isRejecting.value = false
    reason.value = ''
    credited.value = props.contribution.credited_amount
  },
)

function approve() {
  emit('approve', isOtherCurrency.value && credited.value ? credited.value : null)
}
</script>

<template>
  <div class="verify-panel">
    <div class="info">
      <div class="row">
        <span class="label">{{ $t('admin.verification.sender') }}</span>
        <span class="value"><b>{{ contribution.user_name }}</b> · {{ contribution.user_unit }}</span>
      </div>
      <div class="row">
        <span class="label">{{ $t('admin.verification.amount') }}</span>
        <span class="value value--amount">{{ formatMoney(contribution.amount, contribution.currency) }}</span>
      </div>
      <div class="row">
        <span class="label">{{ $t('admin.verification.requisite') }}</span>
        <span class="value">{{ contribution.requisite_label ?? '—' }}</span>
      </div>
      <div class="row">
        <span class="label">{{ $t('admin.verification.purpose') }}</span>
        <span class="value">
          {{
            contribution.category === 'target_fund'
              ? contribution.target_fund_title
              : `${$t('contributionCategory.monthly_fee')} · ${formatPeriod(contribution.billing_period)}`
          }}
        </span>
      </div>
      <div class="row">
        <span class="label">{{ $t('admin.verification.sentAt') }}</span>
        <span class="value">{{ formatDateTime(contribution.created_at) }}</span>
      </div>
      <div v-if="contribution.comment_user" class="comment">
        <span class="label">{{ $t('admin.verification.residentComment') }}</span>
        <p>«{{ contribution.comment_user }}»</p>
      </div>
    </div>

    <!-- Зачёт при оплате в другой валюте -->
    <label v-if="isOtherCurrency" class="credited-box">
      <span class="label">
        {{ $t('admin.verification.credited', { currency: contribution.credited_currency.toUpperCase() }) }}
      </span>
      <input v-model.number="credited" type="number" min="1" inputmode="numeric" />
      <span class="hint">{{ $t('admin.verification.creditedHint') }}</span>
    </label>

    <button class="receipt" @click="emit('zoom', contribution)">
      <img :src="contribution.receipt_image" alt="" />
      <span class="zoom-hint">🔍 {{ $t('admin.verification.zoom') }}</span>
    </button>

    <!-- Отклонение с причиной -->
    <div v-if="isRejecting" class="reject-box">
      <span class="label">{{ $t('admin.verification.rejectReason') }}</span>
      <textarea v-model="reason" rows="3" :placeholder="$t('admin.verification.rejectPlaceholder')" />
      <div class="actions">
        <button class="ghost-btn" @click="isRejecting = false">{{ $t('common.back') }}</button>
        <button
          class="danger-btn"
          :disabled="isSubmitting || reason.trim().length < 3"
          @click="emit('reject', reason.trim())"
        >
          {{ $t('admin.verification.confirmReject') }}
        </button>
      </div>
    </div>

    <div v-else class="actions">
      <button class="ghost-btn ghost-btn--danger" :disabled="isSubmitting" @click="isRejecting = true">
        <LuCircleX /> {{ $t('admin.verification.reject') }}
      </button>
      <button class="approve-btn" :disabled="isSubmitting || (isOtherCurrency && !credited)" @click="approve">
        <LuCircleCheck /> {{ $t('admin.verification.approve') }}
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.verify-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.label {
  font-size: 12px;
  color: $text-muted;
}

.value {
  text-align: right;
  color: #111827;

  &--amount {
    font-size: 18px;
    font-weight: 700;
    color: $success;
  }
}

.comment p {
  margin: 4px 0 0;
  font-size: 13px;
  font-style: italic;
  color: $text-secondary;
}

.receipt {
  @include pressable;
  position: relative;
  padding: 8px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 18px;
  background: #fff;

  img {
    display: block;
    width: 100%;
    max-height: 320px;
    object-fit: contain;
  }
}

.zoom-hint {
  position: absolute;
  right: 14px;
  bottom: 14px;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(15, 23, 42, 0.7);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.reject-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(254, 242, 242, 0.9);

  textarea {
    @include field-input;
    resize: vertical;
  }
}

.actions {
  display: flex;
  gap: 10px;

  > * {
    flex: 1;
  }
}

.ghost-btn {
  @include ghost-button;

  &--danger {
    color: $danger;
    border-color: rgba(239, 68, 68, 0.25);
  }
}

.approve-btn {
  @include cta-button;
  background: linear-gradient(135deg, #34D399, #10B981);
  box-shadow: none;
}

.danger-btn {
  @include cta-button;
  background: linear-gradient(135deg, #F87171, #EF4444);
  box-shadow: none;
}

.credited-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 14px;
  background: rgba(255, 251, 235, 0.9);

  input {
    @include field-input;
  }

  .hint {
    font-size: 12px;
    color: #B45309;
  }
}
</style>
