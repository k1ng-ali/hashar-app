<script setup lang="ts">
import { computed } from 'vue'
import ProgressBar from '@/shared/components/ProgressBar.vue'
import { formatDate } from '@/shared/lib/format.ts'
import { discountValueLabel } from '../planSale.ts'
import type { Plan, PlanInfo, PlanOption } from '../types.ts'

const props = defineProps<{
  info: PlanInfo
  options: PlanOption[]
  canRequest: boolean
  hasPendingRequest: boolean
}>()

const emit = defineEmits<{
  (e: 'request', plan: Plan, renewal: boolean): void
}>()

const usage = computed(() =>
  props.info.member_limit ? Math.round((props.info.members_count / props.info.member_limit) * 100) : 0,
)

// Апгрейд — только на тарифы выше текущего
const ORDER: Plan[] = ['free', 'pro', 'max', 'individual']
// Продлить можно действующий платный тариф (срок добавится к дате окончания)
const canRenew = computed(() => props.info.effective_plan !== 'free')

const upgrades = computed(() =>
  props.options.filter((o) => ORDER.indexOf(o.plan) > ORDER.indexOf(props.info.effective_plan)),
)
// Распродажа на текущий тариф — повод продлить
const currentSale = computed(() => props.options.find((o) => o.plan === props.info.effective_plan)?.sale ?? null)
</script>

<template>
  <div class="plan-card">
    <div class="top">
      <div>
        <span class="label">{{ $t('plans.current') }}</span>
        <div class="plan-name">{{ $t(`plans.${info.effective_plan}`) }}</div>
      </div>
      <span v-if="info.expires_at && info.effective_plan !== 'free'" class="expires">
        {{ $t('plans.until', { date: formatDate(info.expires_at) }) }}
      </span>
    </div>

    <div class="usage">
      <span>{{ $t('plans.members') }}</span>
      <b>
        {{ info.members_count }} / {{ info.member_limit ?? '∞' }}
      </b>
    </div>
    <ProgressBar v-if="info.member_limit" :percent="usage" tone="brand" />

    <p v-if="info.plan !== info.effective_plan" class="warning">⚠️ {{ $t('plans.expired') }}</p>

    <button
      v-if="canRequest && canRenew"
      class="renew-btn"
      :disabled="hasPendingRequest"
      @click="emit('request', info.effective_plan, true)"
    >
      🔄 {{ $t('plans.renew') }}
    </button>

    <p v-if="canRenew && currentSale" class="sale">
      🏷 {{ currentSale.title }} · {{ discountValueLabel(currentSale, $t) }}
      <template v-if="currentSale.ends_at"> · {{ $t('plans.until', { date: formatDate(currentSale.ends_at) }) }}</template>
    </p>

    <!-- Тарифы для повышения -->
    <div v-if="upgrades.length" class="options">
      <div v-for="option in upgrades" :key="option.plan" class="option">
        <div>
          <b>{{ $t(`plans.${option.plan}`) }}</b>
          <span>
            {{ option.member_limit ? $t('plans.upTo', { n: option.member_limit }) : $t('plans.unlimited') }}
          </span>
          <span v-if="option.sale" class="sale">
            🏷 {{ option.sale.title }} · {{ discountValueLabel(option.sale, $t) }}
            <template v-if="option.sale.ends_at"> · {{ $t('plans.until', { date: formatDate(option.sale.ends_at) }) }}</template>
          </span>
        </div>
        <div class="option-right">
          <span class="price">
            <s v-if="option.sale && option.list_price_tjs" class="old-price">{{ option.list_price_tjs }}</s>
            {{ option.price_tjs ? $t('plans.price', { price: option.price_tjs }) : $t('plans.byAgreement') }}
          </span>
          <button
            v-if="canRequest"
            class="request-btn"
            :disabled="hasPendingRequest"
            @click="emit('request', option.plan, false)"
          >
            {{ $t('plans.request') }}
          </button>
        </div>
      </div>
    </div>
    <p v-if="hasPendingRequest" class="hint">⏱ {{ $t('plans.pending') }}</p>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.plan-card {
  @include glass-card;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}

.top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.label {
  font-size: 12px;
  color: $text-muted;
}

.plan-name {
  font-size: 22px;
  font-weight: 700;
  background: $gradient;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.expires {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.14);
  color: #111827;
  font-size: 11px;
  font-weight: 700;
}

.usage {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: $text-secondary;

  b {
    color: $navy;
  }
}

.warning {
  margin: 0;
  font-size: 12px;
  color: #B45309;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.option {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);

  > div:first-child {
    display: flex;
    flex-direction: column;

    b {
      color: $navy;
    }

    span {
      font-size: 12px;
      color: $text-muted;
    }
  }
}

.option-right {
  display: flex;
  align-items: center;
  margin-left: auto;
  gap: 8px;
}

.price {
  font-size: 13px;
  font-weight: 700;
  color: $navy;
}

.old-price {
  font-weight: 500;
  color: $text-muted;
}

.sale {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: $success !important;
}

.request-btn {
  @include cta-button;
  padding: 7px 12px;
  font-size: 12px;
}

.hint {
  margin: 0;
  font-size: 12px;
  color: #B45309;
}

.renew-btn {
  @include cta-button;
  align-self: flex-start;
  padding: 9px 16px;
  font-size: 13px;
}
</style>
