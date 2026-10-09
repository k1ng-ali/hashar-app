<script setup lang="ts">
import { reactive, watch } from 'vue'
import { LuPlus, LuTrash2 } from '@kalimahapps/vue-icons/lu'
import type { Requisite } from '@/features/dashboard/types.ts'
import type { FundInfo } from '@/features/funds/types.ts'
import { type Currency } from '@/shared/lib/currency.ts'
import type { FundSettingsUpdate } from '../types.ts'

const props = defineProps<{
  fund: FundInfo
  currencies: Currency[]
  requisites: Requisite[]
  isChairman: boolean
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'save', payload: FundSettingsUpdate): void
  (e: 'add-requisite'): void
  (e: 'toggle-requisite', id: number): void
  (e: 'delete-requisite', id: number): void
}>()

const info = reactive({ name: '', address: '', description: '' })
const finance = reactive({ base_currency: 'tjs' as Currency, monthly_rate: 0 as number | null })

// Форма всегда отражает актуальную карточку фонда
watch(
  () => props.fund,
  (fund) => {
    Object.assign(info, { name: fund.name, address: fund.address ?? '', description: fund.description ?? '' })
    Object.assign(finance, { base_currency: fund.base_currency, monthly_rate: fund.monthly_rate })
  },
  { immediate: true },
)

function saveInfo() {
  emit('save', {
    name: info.name.trim(),
    address: info.address.trim() || null,
    description: info.description.trim() || null,
  })
}

function saveFinance() {
  emit('save', { base_currency: finance.base_currency, monthly_rate: finance.monthly_rate ?? 0 })
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
          :disabled="!isChairman"
          @click="finance.base_currency = currency"
        >
          {{ currency.toUpperCase() }}
        </button>
      </div>
      <p class="hint">{{ $t('funds.create.baseCurrencyHint') }}</p>

      <label>
        <span class="label">{{ $t('admin.settings.rateUnit', { currency: finance.base_currency.toUpperCase() }) }}</span>
        <input v-model.number="finance.monthly_rate" type="number" min="0" :disabled="!isChairman" />
      </label>

      <button v-if="isChairman" class="cta-btn" :disabled="isSubmitting" @click="saveFinance">
        {{ $t('admin.settings.rateSave') }}
      </button>
      <p v-else class="hint">🔒 {{ $t('admin.settings.onlyChairman') }}</p>
    </section>

    <!-- 3. Реквизиты по валютам -->
    <section class="card">
      <div class="card-header">
        <div>
          <h3 class="card-title">{{ $t('admin.settings.requisitesTitle') }}</h3>
          <p class="card-sub">{{ $t('admin.settings.requisitesSubtitle') }}</p>
        </div>
        <button v-if="isChairman" class="ghost-btn" @click="emit('add-requisite')">
          <LuPlus /> {{ $t('admin.settings.addRequisite') }}
        </button>
      </div>

      <div class="requisites">
        <div v-for="requisite in requisites" :key="requisite.id" class="requisite">
          <div class="requisite-top">
            <b>
              {{ requisite.bank_name }}
              <span class="currency">{{ requisite.currency.toUpperCase() }}</span>
            </b>
            <div class="requisite-actions">
              <a-switch
                :checked="requisite.is_active"
                :disabled="!isChairman"
                size="small"
                @change="emit('toggle-requisite', requisite.id)"
              />
              <button
                v-if="isChairman"
                class="icon-btn"
                :aria-label="$t('common.delete')"
                @click="emit('delete-requisite', requisite.id)"
              >
                <LuTrash2 />
              </button>
            </div>
          </div>
          <span class="number">{{ requisite.card_or_account_number }}</span>
          <span class="recipient">{{ requisite.recipient_name }}</span>
        </div>
        <p v-if="!requisites.length" class="hint">{{ $t('requisites.empty') }}</p>
      </div>
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

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
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

.ghost-btn {
  @include ghost-button;
}

/* ── Реквизиты ────────────────────────────────────────────────────────────── */
.requisites {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.requisite {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
}

.requisite-top {
  display: flex;
  align-items: center;
  justify-content: space-between;

  b {
    color: $navy;
  }
}

.currency {
  margin-left: 6px;
  padding: 1px 8px;
  border-radius: 10px;
  background: rgba(78, 190, 194, 0.14);
  color: #0E7C80;
  font-size: 11px;
}

.requisite-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.number {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 14px;
  font-weight: 700;
  color: #1F2937;
}

.recipient {
  font-size: 12px;
  color: $text-secondary;
}

.icon-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.08);
  color: $danger;
}
</style>
