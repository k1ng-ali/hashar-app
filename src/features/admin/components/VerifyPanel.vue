<script setup lang="ts">
import { ref, watch } from 'vue'
import { LuCircleCheck, LuCircleX } from '@kalimahapps/vue-icons/lu'
import { formatDateTime, formatMoney, formatPeriod } from '@/shared/lib/format.ts'
import type { Contribution } from '@/features/contributions/types.ts'

const props = defineProps<{
  contribution: Contribution
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'zoom', contribution: Contribution): void
  (e: 'approve'): void
  (e: 'reject', reason: string): void
}>()

const isRejecting = ref(false)
const reason = ref('')

// Новая заявка — сбрасываем форму отклонения
watch(
  () => props.contribution.id,
  () => {
    isRejecting.value = false
    reason.value = ''
  },
)
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
      <button class="approve-btn" :disabled="isSubmitting" @click="emit('approve')">
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
  color: #1F2937;

  &--amount {
    font-size: 18px;
    font-weight: 800;
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
  border: 1px solid rgba(35, 73, 112, 0.08);
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
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.35);
}

.danger-btn {
  @include cta-button;
  background: linear-gradient(135deg, #F87171, #EF4444);
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
}
</style>
