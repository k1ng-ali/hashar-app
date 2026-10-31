<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { formatDate, formatDateTime } from '@/shared/lib/format.ts'
import { discountValueLabel } from '@/features/funds/planSale.ts'
import type { PlanDiscount, Pricing } from '../types.ts'

const props = defineProps<{
  pricing: Pricing
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'save-price', plan: PlanPriceKey, price: number): void
  (e: 'create', isPromo: boolean): void
  (e: 'edit', discount: PlanDiscount): void
  (e: 'toggle', discount: PlanDiscount): void
  (e: 'delete', discount: PlanDiscount): void
}>()

type PlanPriceKey = Pricing['prices'][number]['plan']

// Черновики цен: кнопка «Сохранить» появляется, только когда цена отличается
const drafts = ref<Record<string, number>>({})
watch(
  () => props.pricing.prices,
  (prices) => {
    drafts.value = Object.fromEntries(prices.map((p) => [p.plan, p.price_tjs]))
  },
  { immediate: true },
)
const isDirty = (plan: string, price: number) => drafts.value[plan] !== price && drafts.value[plan] >= 1

const sales = computed(() => props.pricing.discounts.filter((d) => !d.code))
const promos = computed(() => props.pricing.discounts.filter((d) => d.code))
const groups = computed(() => [
  { key: 'sales', isPromo: false, items: sales.value },
  { key: 'promos', isPromo: true, items: promos.value },
])
</script>

<template>
  <div class="pricing">
    <!-- 1. Прайс -->
    <section class="card">
      <h2 class="card-title">{{ $t('platform.pricing.pricesTitle') }}</h2>
      <p class="hint">{{ $t('platform.pricing.pricesHint') }}</p>
      <div v-for="row in pricing.prices" :key="row.plan" class="price-row">
        <div class="price-name">
          <b>{{ $t(`plans.${row.plan}`) }}</b>
          <span>{{ $t('platform.pricing.updatedAt', { date: formatDateTime(row.updated_at) }) }}</span>
        </div>
        <input v-model.number="drafts[row.plan]" type="number" min="1" :aria-label="$t(`plans.${row.plan}`)" />
        <button
          v-if="isDirty(row.plan, row.price_tjs)"
          class="save-btn"
          :disabled="isSubmitting"
          @click="emit('save-price', row.plan, drafts[row.plan])"
        >
          {{ $t('common.save') }}
        </button>
      </div>
    </section>

    <!-- 2. Распродажи и промокоды -->
    <section v-for="group in groups" :key="group.key" class="card">
      <div class="card-head">
        <div>
          <h2 class="card-title">{{ $t(`platform.pricing.${group.key}Title`) }}</h2>
          <p class="hint">{{ $t(`platform.pricing.${group.key}Hint`) }}</p>
        </div>
        <button class="add-btn" @click="emit('create', group.isPromo)">+ {{ $t('platform.pricing.add') }}</button>
      </div>

      <p v-if="!group.items.length" class="empty">{{ $t('platform.pricing.empty') }}</p>

      <article v-for="item in group.items" :key="item.id" class="discount">
        <div class="discount-top">
          <div>
            <b class="discount-name">{{ item.code ?? item.title }}</b>
            <span v-if="item.code" class="discount-note">{{ item.title }}</span>
          </div>
          <span class="state" :class="`state--${item.state}`">{{ $t(`platform.pricing.state.${item.state}`) }}</span>
        </div>
        <p class="discount-meta">
          <b>{{ discountValueLabel(item, $t) }}</b>
          · {{ item.plans.map((plan) => $t(`plans.${plan}`)).join(', ') }}
          <template v-if="item.starts_at"> · {{ $t('platform.pricing.from', { date: formatDate(item.starts_at) }) }}</template>
          <template v-if="item.ends_at"> · {{ $t('plans.until', { date: formatDate(item.ends_at) }) }}</template>
          <template v-if="item.max_months"> · {{ $t('platform.pricing.forMonths', { n: item.max_months }) }}</template>
          <template v-if="item.code">
            · {{ $t('platform.pricing.uses', { n: item.uses }) }}<template v-if="item.max_uses"> / {{ item.max_uses }}</template>
          </template>
        </p>
        <div class="discount-actions">
          <button class="ghost-btn" :disabled="isSubmitting" @click="emit('edit', item)">{{ $t('platform.pricing.edit') }}</button>
          <button class="ghost-btn" :disabled="isSubmitting" @click="emit('toggle', item)">
            {{ item.is_active ? $t('platform.pricing.disable') : $t('platform.pricing.enable') }}
          </button>
          <button
            v-if="!item.uses"
            class="ghost-btn ghost-btn--danger"
            :disabled="isSubmitting"
            @click="emit('delete', item)"
          >
            {{ $t('common.delete') }}
          </button>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.pricing {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.hint {
  margin: 2px 0 0;
  font-size: 12px;
  color: $text-muted;
}

.empty {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
}

.add-btn {
  @include ghost-button;
  flex-shrink: 0;
  white-space: nowrap;
}

/* ── Прайс ──────────────────────────────────────────────────────────────── */
.price-row {
  display: flex;
  align-items: center;
  gap: 10px;

  input {
    @include field-input;
    width: 96px;
    flex-shrink: 0;
    padding: 9px 12px;
  }
}

.price-name {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;

  b {
    color: $navy;
  }

  span {
    font-size: 11px;
    color: $text-muted;
  }
}

.save-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 9px 14px;
  font-size: 13px;
}

/* ── Скидки ─────────────────────────────────────────────────────────────── */
.discount {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: 14px;
  background: $surface-muted;
}

.discount-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.discount-name {
  display: block;
  color: $navy;
  overflow-wrap: anywhere;
}

.discount-note {
  font-size: 12px;
  color: $text-muted;
}

.discount-meta {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;

  b {
    color: $navy;
  }
}

.discount-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ghost-btn {
  @include ghost-button;
  padding: 7px 12px;
  font-size: 12px;

  &--danger {
    color: $danger;
  }
}

.state {
  flex-shrink: 0;
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.08);
  color: $text-secondary;
  font-size: 11px;
  font-weight: 700;

  &--active {
    background: rgba(22, 163, 74, 0.12);
    color: $success;
  }

  &--scheduled {
    background: rgba(245, 158, 11, 0.14);
    color: #b45309;
  }
}
</style>
