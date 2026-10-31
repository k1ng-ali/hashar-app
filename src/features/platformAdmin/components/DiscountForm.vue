<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DiscountKind, DiscountPlan, PlanDiscount, PlanDiscountPayload } from '../types.ts'

const props = defineProps<{
  /** null — новая скидка. */
  discount: PlanDiscount | null
  isPromo: boolean
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: PlanDiscountPayload): void
}>()

const PLANS: DiscountPlan[] = ['pro', 'max']
const MAX_PERCENT = 99

/** Дата поля ввода (местное время) из ISO. */
function toDateInput(iso: string | null | undefined): string {
  if (!iso) return ''
  const date = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

const title = ref(props.discount?.title ?? '')
const code = ref(props.discount?.code ?? '')
const kind = ref<DiscountKind>(props.discount?.kind ?? 'percent')
const value = ref<number | null>(props.discount?.value ?? null)
const plans = ref<DiscountPlan[]>((props.discount?.plans as DiscountPlan[] | undefined) ?? [...PLANS])
const startsOn = ref(toDateInput(props.discount?.starts_at))
const endsOn = ref(toDateInput(props.discount?.ends_at))
const maxUses = ref<number | null>(props.discount?.max_uses ?? null)

function togglePlan(plan: DiscountPlan) {
  plans.value = plans.value.includes(plan) ? plans.value.filter((p) => p !== plan) : [...plans.value, plan]
}

const isValid = computed(() => {
  const amount = value.value ?? 0
  if (title.value.trim().length < 2 || amount < 1 || !plans.value.length) return false
  if (kind.value === 'percent' && amount > MAX_PERCENT) return false
  if (startsOn.value && endsOn.value && endsOn.value < startsOn.value) return false
  return !props.isPromo || code.value.trim().length >= 3
})

function submit() {
  if (!isValid.value) return
  emit('submit', {
    title: title.value.trim(),
    code: props.isPromo ? code.value.trim() : null,
    kind: kind.value,
    value: value.value as number,
    plans: plans.value,
    // Срок — полные дни по местному времени: с начала первого до конца последнего
    starts_at: startsOn.value ? new Date(`${startsOn.value}T00:00:00`).toISOString() : null,
    ends_at: endsOn.value ? new Date(`${endsOn.value}T23:59:59`).toISOString() : null,
    max_uses: props.isPromo ? maxUses.value || null : null,
    is_active: props.discount?.is_active ?? true,
  })
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <label v-if="isPromo">
      <span class="label">{{ $t('platform.pricing.code') }} *</span>
      <input v-model="code" class="code-input" maxlength="30" required placeholder="SPRING26" />
      <span class="field-hint">{{ $t('platform.pricing.codeHint') }}</span>
    </label>

    <label>
      <span class="label">{{ isPromo ? $t('platform.pricing.note') : $t('platform.pricing.saleName') }} *</span>
      <input v-model="title" maxlength="100" required />
      <span v-if="!isPromo" class="field-hint">{{ $t('platform.pricing.saleNameHint') }}</span>
    </label>

    <div>
      <span class="label">{{ $t('platform.pricing.kind') }}</span>
      <div class="chips">
        <button
          v-for="option in ['percent', 'fixed'] as DiscountKind[]"
          :key="option"
          type="button"
          class="chip"
          :class="{ 'chip--active': kind === option }"
          @click="kind = option"
        >
          {{ $t(`platform.pricing.kinds.${option}`) }}
        </button>
      </div>
    </div>

    <label>
      <span class="label">{{ kind === 'percent' ? $t('platform.pricing.valuePercent') : $t('platform.pricing.valueFixed') }} *</span>
      <input v-model.number="value" type="number" min="1" :max="kind === 'percent' ? MAX_PERCENT : undefined" required />
      <span class="field-hint">{{ $t('platform.pricing.valueHint') }}</span>
    </label>

    <div>
      <span class="label">{{ $t('platform.pricing.plans') }}</span>
      <div class="chips">
        <button
          v-for="plan in PLANS"
          :key="plan"
          type="button"
          class="chip"
          :class="{ 'chip--active': plans.includes(plan) }"
          @click="togglePlan(plan)"
        >
          {{ $t(`plans.${plan}`) }}
        </button>
      </div>
    </div>

    <div class="dates">
      <label>
        <span class="label">{{ $t('platform.pricing.startsOn') }}</span>
        <input v-model="startsOn" type="date" />
      </label>
      <label>
        <span class="label">{{ $t('platform.pricing.endsOn') }}</span>
        <input v-model="endsOn" type="date" />
      </label>
    </div>

    <label v-if="isPromo">
      <span class="label">{{ $t('platform.pricing.maxUses') }} · {{ $t('common.optional') }}</span>
      <input v-model.number="maxUses" type="number" min="1" />
      <span class="field-hint">{{ $t('platform.pricing.maxUsesHint') }}</span>
    </label>

    <button type="submit" class="submit-btn" :disabled="isSubmitting || !isValid">
      {{ $t('common.save') }}
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

.label {
  @include field-label;
}

input {
  @include field-input;
}

.code-input {
  text-transform: uppercase;
}

.field-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: $text-muted;
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

.dates {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;

  label {
    min-width: 0;
  }
}

.submit-btn {
  @include cta-button;
}
</style>
