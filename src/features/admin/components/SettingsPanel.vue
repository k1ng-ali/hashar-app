<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { FundInfo } from '@/features/funds/types.ts'
import { type Currency } from '@/shared/lib/currency.ts'
import { formatDate, formatMoney } from '@/shared/lib/format.ts'
import type { FundSettingsUpdate } from '../types.ts'

const props = defineProps<{
  fund: FundInfo
  currencies: Currency[]
  isChairman: boolean
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'save', payload: FundSettingsUpdate): void
}>()

const info = reactive({ name: '', address: '', description: '' })
const finance = reactive({ base_currency: 'tjs' as Currency, monthly_rate: 0 as number | null })

// Форма всегда отражает актуальную карточку фонда
watch(
  () => props.fund,
  (fund) => {
    Object.assign(info, { name: fund.name, address: fund.address ?? '', description: fund.description ?? '' })
    // В поле — тариф, который будет действовать с ближайшего месяца
    Object.assign(finance, {
      base_currency: fund.base_currency,
      monthly_rate: fund.next_monthly_rate ?? fund.monthly_rate,
    })
  },
  { immediate: true },
)

// Действующий тариф = запланированный, если он есть, иначе текущий
const plannedRate = computed(() => props.fund.next_monthly_rate ?? props.fund.monthly_rate)
const history = computed(() => [...props.fund.rate_history].reverse())

/** «2026-11» → «01.11.2026»: тариф действует с 1-го числа месяца. */
const firstDay = (period: string) => formatDate(`${period}-01T00:00:00`)

function saveInfo() {
  emit('save', {
    name: info.name.trim(),
    address: info.address.trim() || null,
    description: info.description.trim() || null,
  })
}

function saveFinance() {
  const payload: FundSettingsUpdate = {}
  if (finance.base_currency !== props.fund.base_currency) payload.base_currency = finance.base_currency
  // Тариф отправляем, только если он правда меняется — иначе не планируем лишнее изменение
  const rate = finance.monthly_rate ?? 0
  if (rate !== plannedRate.value) payload.monthly_rate = rate
  if (Object.keys(payload).length) emit('save', payload)
}
</script>

<template>
  <div class="settings">
    <!-- 1. Информация о фонде -->
    <section class="card">
      <h3 class="card-title">{{ $t('admin.settings.infoTitle') }}</h3>
      <label>
        <span class="label">{{ $t('funds.create.name') }}</span>
        <input v-model="info.name" maxlength="150" />
      </label>
      <label>
        <span class="label">{{ $t('funds.create.address') }}</span>
        <input v-model="info.address" maxlength="255" />
      </label>
      <label>
        <span class="label">{{ $t('funds.create.description') }}</span>
        <textarea v-model="info.description" rows="2" />
      </label>
      <button class="cta-btn" :disabled="isSubmitting || info.name.trim().length < 3" @click="saveInfo">
        {{ $t('admin.settings.save') }}
      </button>
    </section>

    <!-- 2. Тариф взноса и базовая валюта -->
    <section class="card">
      <h3 class="card-title">{{ $t('admin.settings.rateTitle') }}</h3>
      <p class="card-sub">{{ $t('admin.settings.rateSubtitle') }}</p>

      <span class="label">{{ $t('funds.create.baseCurrency') }}</span>
      <div class="chips">
        <button
          v-for="currency in currencies"
          :key="currency"
          type="button"
          class="chip"
          :class="{ 'chip--active': finance.base_currency === currency }"
          :disabled="!isChairman || fund.setup_locked"
          @click="finance.base_currency = currency"
        >
          {{ currency.toUpperCase() }}
        </button>
      </div>
      <p class="hint">{{ $t('funds.create.baseCurrencyHint') }}</p>
      <p v-if="fund.setup_locked" class="hint">🔒 {{ $t('admin.settings.currencyLocked') }}</p>

      <div class="rate-now">
        <span>{{ $t('admin.settings.rateCurrent') }}</span>
        <b>{{ formatMoney(fund.monthly_rate, fund.base_currency) }}</b>
      </div>
      <div v-if="fund.next_monthly_rate !== null && fund.next_rate_period" class="rate-planned">
        📅 {{ $t('admin.settings.ratePlanned', {
          amount: formatMoney(fund.next_monthly_rate, fund.base_currency),
          date: firstDay(fund.next_rate_period),
        }) }}
      </div>

      <label>
        <span class="label">{{ $t('admin.settings.rateUnit', { currency: finance.base_currency.toUpperCase() }) }}</span>
        <input v-model.number="finance.monthly_rate" type="number" min="0" :disabled="!isChairman" />
      </label>
      <p class="rate-note">ℹ️ {{ $t('admin.settings.rateNote') }}</p>

      <details v-if="history.length > 1" class="rate-history">
        <summary>{{ $t('admin.settings.rateHistory') }}</summary>
        <div v-for="rate in history" :key="rate.period" class="rate-row">
          <span>{{ $t('admin.settings.rateFrom', { date: firstDay(rate.period) }) }}</span>
          <b>{{ formatMoney(rate.amount, fund.base_currency) }}</b>
        </div>
      </details>

      <button v-if="isChairman" class="cta-btn" :disabled="isSubmitting" @click="saveFinance">
        {{ $t('admin.settings.rateSave') }}
      </button>
      <p v-else class="hint">🔒 {{ $t('admin.settings.onlyChairman') }}</p>
    </section>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.settings {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card {
  @include glass-card;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}


.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.card-sub {
  margin: -6px 0 0;
  font-size: 12px;
  color: $text-muted;
}

.label {
  @include field-label;
}

input,
textarea {
  @include field-input;

  &:disabled {
    opacity: 0.6;
  }
}

textarea {
  resize: vertical;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  @include ghost-button;
  padding: 8px 12px;
  font-size: 12px;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}

.hint {
  margin: 0;
  font-size: 12px;
  color: $text-muted;
}

.cta-btn {
  @include cta-button;
  align-self: flex-start;
  padding: 11px 18px;
  font-size: 13px;
}


/* ── Тариф ────────────────────────────────────────────────────────────────── */
.rate-now {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  font-size: 13px;
  color: $text-secondary;

  b {
    font-size: 18px;
    color: $navy;
  }
}

.rate-planned {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(17, 24, 39, 0.12);
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.rate-note {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(245, 158, 11, 0.1);
  color: #92400E;
  font-size: 12px;
  line-height: 1.45;
}

.rate-history {
  font-size: 13px;
  color: $text-secondary;

  summary {
    cursor: pointer;
    font-weight: 700;
    color: $navy;
  }
}

.rate-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(17, 24, 39, 0.06);

  b {
    color: $navy;
  }
}
</style>
