<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Plan, PlanOption } from '@/features/funds/types.ts'
import { formatDate } from '@/shared/lib/format.ts'

const props = defineProps<{
  plan: Plan
  options: PlanOption[]
  isRenewal: boolean
  expiresAt: string | null
  /** Стоимость неиспользованного остатка текущего тарифа (null — нечего переносить). */
  remainingTjs: number | null
  defaultContact: string
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', months: number, contact: string, comment: string | null): void
}>()

const MONTHS = [1, 3, 6, 12]
const MIN_CONTACT = 3

const months = ref(1)
// Контакт для связи по оплате — по умолчанию телефон или email председателя
const contact = ref(props.defaultContact)
const comment = ref('')
const isValid = computed(() => contact.value.trim().length >= MIN_CONTACT)

const option = computed(() => props.options.find((o) => o.plan === props.plan) ?? null)
const total = computed(() => (option.value?.price_tjs ? option.value.price_tjs * months.value : null))
// Месяц тарифа — 30 дней: остаток в деньгах докупает дни нового тарифа по его цене
const carryoverDays = computed(() =>
  props.remainingTjs && option.value?.price_tjs
    ? Math.round((props.remainingTjs / option.value.price_tjs) * 30)
    : null,
)
</script>

<template>
  <form class="form" @submit.prevent="isValid && emit('submit', months, contact.trim(), comment.trim() || null)">
    <div class="plan">
      <b>{{ $t(`plans.${plan}`) }}</b>
      <span>
        {{ option?.member_limit ? $t('plans.upTo', { n: option.member_limit }) : $t('plans.unlimited') }}
      </span>
    </div>

    <p v-if="isRenewal" class="renewal">
      🔄 {{ expiresAt ? $t('plans.renewHint', { date: formatDate(expiresAt) }) : $t('plans.renewHintNoDate') }}
    </p>

    <p v-if="!isRenewal && remainingTjs" class="renewal">
      🔁
      {{
        carryoverDays !== null
          ? $t('plans.carryoverHint', { amount: remainingTjs, n: carryoverDays })
          : $t('plans.carryoverHintIndividual', { amount: remainingTjs })
      }}
    </p>

    <div v-if="plan !== 'individual'">
      <span class="label">{{ $t('plans.months') }}</span>
      <div class="chips">
        <button
          v-for="value in MONTHS"
          :key="value"
          type="button"
          class="chip"
          :class="{ 'chip--active': months === value }"
          @click="months = value"
        >
          {{ value }}
        </button>
      </div>
      <p v-if="total" class="total">{{ $t('plans.total', { price: total }) }}</p>
    </div>

    <label>
      <span class="label">{{ $t('plans.contact') }} *</span>
      <input v-model="contact" maxlength="150" required :placeholder="$t('plans.contactPlaceholder')" />
      <span class="field-hint">{{ $t('plans.contactHint') }}</span>
    </label>

    <label>
      <span class="label">{{ $t('plans.comment') }} · {{ $t('common.optional') }}</span>
      <textarea v-model="comment" rows="2" :placeholder="$t('plans.commentPlaceholder')" />
    </label>

    <p class="hint">{{ $t('plans.paymentNote') }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting || !isValid">
      {{ isRenewal ? $t('plans.renew') : $t('plans.request') }}
    </button>
  </form>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.plan {
  @include glass-card(16px);
  display: flex;
  flex-direction: column;
  padding: 14px;

  b {
    font-size: 20px;
    color: $navy;
  }

  span {
    font-size: 12px;
    color: $text-muted;
  }
}

.label {
  @include field-label;
}

textarea {
  @include field-input;
  resize: vertical;
}

.chips {
  display: flex;
  gap: 8px;
}

.chip {
  @include ghost-button;
  flex: 1;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}

.total {
  margin: 8px 0 0;
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.hint {
  margin: 0;
  font-size: 12px;
  color: $text-muted;
}

.submit-btn {
  @include cta-button;
}

input {
  @include field-input;
}

.field-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: $text-muted;
}

.renewal {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(17, 24, 39, 0.12);
  color: #111827;
  font-size: 13px;
  font-weight: 600;
}
</style>
