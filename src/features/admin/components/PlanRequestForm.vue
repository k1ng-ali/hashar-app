<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Plan, PlanOption } from '@/features/funds/types.ts'

const props = defineProps<{
  plan: Plan
  options: PlanOption[]
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', months: number, comment: string | null): void
}>()

const MONTHS = [1, 3, 6, 12]

const months = ref(1)
const comment = ref('')

const option = computed(() => props.options.find((o) => o.plan === props.plan) ?? null)
const total = computed(() => (option.value?.price_tjs ? option.value.price_tjs * months.value : null))
</script>

<template>
  <form class="form" @submit.prevent="emit('submit', months, comment.trim() || null)">
    <div class="plan">
      <b>{{ $t(`plans.${plan}`) }}</b>
      <span>
        {{ option?.member_limit ? $t('plans.upTo', { n: option.member_limit }) : $t('plans.unlimited') }}
      </span>
    </div>

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
      <span class="label">{{ $t('plans.comment') }} · {{ $t('common.optional') }}</span>
      <textarea v-model="comment" rows="2" :placeholder="$t('plans.commentPlaceholder')" />
    </label>

    <p class="hint">{{ $t('plans.paymentNote') }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">{{ $t('plans.request') }}</button>
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
  font-weight: 800;
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
</style>
