<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PlanQuote } from '@/features/admin/types.ts'
import type { Plan, PlanOption } from '@/features/funds/types.ts'
import { formatDate } from '@/shared/lib/format.ts'

const props = defineProps<{
  plan: Plan
  options: PlanOption[]
  isRenewal: boolean
  expiresAt: string | null
  /** Расчёт сервера: цена со скидкой, продление или перенос остатка. null — ещё считается. */
  quote: PlanQuote | null
  promoCode: string | null
  promoError: string
  defaultContact: string
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', months: number, contact: string, comment: string | null): void
  (e: 'apply-promo', code: string | null): void
}>()

const MONTHS = [1, 3, 6, 12]
const MIN_CONTACT = 3

const months = ref(1)
// Контакт для связи по оплате — по умолчанию телефон или email председателя
const contact = ref(props.defaultContact)
const comment = ref('')
const isValid = computed(() => contact.value.trim().length >= MIN_CONTACT)

const option = computed(() => props.options.find((o) => o.plan === props.plan) ?? null)
const total = computed(() => (props.quote?.price_tjs ? props.quote.price_tjs * months.value : null))
const listTotal = computed(() => (props.quote?.list_price_tjs ? props.quote.list_price_tjs * months.value : null))
const hasDiscount = computed(() => !!total.value && !!listTotal.value && total.value < listTotal.value)

const promoInput = ref('')
const hasPromo = computed(() => props.plan !== 'individual')
function applyPromo() {
  const code = promoInput.value.trim().toUpperCase()
  if (code) emit('apply-promo', code)
}
function clearPromo() {
  promoInput.value = ''
  emit('apply-promo', null)
}
</script>

<template>
  <form class="form" @submit.prevent="isValid && emit('submit', months, contact.trim(), comment.trim() || null)">
    <div class="plan">
      <b>{{ $t(`plans.${plan}`) }}</b>
      <span>
        {{ option?.member_limit ? $t('plans.upTo', { n: option.member_limit }) : $t('plans.unlimited') }}
      </span>
    </div>

    <p v-if="quote?.is_extension" class="renewal">
      🔄 {{ expiresAt ? $t('plans.renewHint', { date: formatDate(expiresAt) }) : $t('plans.renewHintNoDate') }}
    </p>

    <p v-if="quote?.carryover_tjs" class="renewal">
      🔁
      {{
        quote.carryover_days !== null
          ? $t('plans.carryoverHint', { amount: quote.carryover_tjs, n: quote.carryover_days })
          : $t('plans.carryoverHintIndividual', { amount: quote.carryover_tjs })
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
      <p v-if="total" class="total">
        {{ $t('plans.total', { price: total }) }}
        <s v-if="hasDiscount" class="old-price">{{ listTotal }}</s>
      </p>
      <p v-if="hasDiscount && quote?.discount_label" class="discount">
        🏷 {{ $t('plans.discountApplied', { name: quote.discount_label, price: quote.price_tjs }) }}
      </p>
    </div>

    <div v-if="hasPromo">
      <span class="label">{{ $t('plans.promo') }} · {{ $t('common.optional') }}</span>
      <div v-if="promoCode && quote?.promo_status === 'applied'" class="promo-applied">
        <span>✅ {{ promoCode }}</span>
        <button type="button" class="link-btn" @click="clearPromo">{{ $t('plans.promoRemove') }}</button>
      </div>
      <div v-else class="promo-row">
        <input
          v-model="promoInput"
          class="promo-input"
          maxlength="30"
          :placeholder="$t('plans.promoPlaceholder')"
          @keydown.enter.prevent="applyPromo"
        />
        <button type="button" class="promo-btn" :disabled="!promoInput.trim()" @click="applyPromo">
          {{ $t('plans.promoApply') }}
        </button>
      </div>
      <p v-if="promoError" class="promo-error">{{ promoError }}</p>
      <p v-else-if="quote?.promo_status === 'not_better'" class="field-hint">{{ $t('plans.promoNotBetter') }}</p>
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

    <button type="submit" class="submit-btn" :disabled="isSubmitting || !isValid || !quote">
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

.old-price {
  margin-left: 6px;
  font-weight: 500;
  color: $text-muted;
}

.discount {
  margin: 4px 0 0;
  font-size: 13px;
  font-weight: 600;
  color: $success;
}

.promo-row {
  display: flex;
  gap: 8px;
}

.promo-input {
  flex: 1;
  min-width: 0;
  text-transform: uppercase;
}

.promo-btn {
  @include ghost-button;
  flex-shrink: 0;
}

.promo-applied {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(22, 163, 74, 0.1);
  color: $success;
  font-size: 14px;
  font-weight: 700;
}

.link-btn {
  border: none;
  background: none;
  color: $text-secondary;
  font-size: 13px;
  text-decoration: underline;
  cursor: pointer;
}

.promo-error {
  margin: 6px 0 0;
  font-size: 13px;
  color: $danger;
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
