<script setup lang="ts">
import { computed, onUnmounted } from 'vue'
import { LuSearch } from '@kalimahapps/vue-icons/lu'
import type { Contribution, ContributionStatus } from '@/features/contributions/types.ts'
import type { Requisite } from '@/features/dashboard/types.ts'
import EmptyState from '@/shared/components/EmptyState.vue'
import type { Currency } from '@/shared/lib/currency.ts'
import { formatMoney } from '@/shared/lib/format.ts'
import type { CurrencyTotal, HistoryFilters } from '../types.ts'
import VerifyCard from './VerifyCard.vue'

const props = defineProps<{
  items: Contribution[]
  totals: CurrencyTotal[]
  totalCount: number
  currencies: Currency[]
  requisites: Requisite[]
  isLoading: boolean
  hasMore: boolean
}>()

const filters = defineModel<HistoryFilters>('filters', { required: true })

const emit = defineEmits<{
  (e: 'change'): void
  (e: 'more'): void
  (e: 'open', contribution: Contribution): void
}>()

const STATUSES: (ContributionStatus | null)[] = ['approved', 'pending', 'rejected', null]
const SEARCH_DELAY = 350

// Реквизиты выбранной валюты (или все)
const requisiteOptions = computed(() =>
  props.requisites
    .filter((r) => !filters.value.currency || r.currency === filters.value.currency)
    .map((r) => ({
      value: r.id,
      label: `${r.bank_name} · ${r.card_or_account_number} · ${r.currency.toUpperCase()}`,
    })),
)

function update(patch: Partial<HistoryFilters>) {
  filters.value = { ...filters.value, ...patch }
  emit('change')
}

function setCurrency(value: unknown) {
  const currency = typeof value === 'string' ? (value as Currency) : null
  const requisite = props.requisites.find((r) => r.id === filters.value.requisite_id)
  // Реквизит другой валюты больше не подходит под фильтр
  const keepRequisite = requisite && (!currency || requisite.currency === currency)
  update({ currency, requisite_id: keepRequisite ? filters.value.requisite_id : null })
}

// Поиск по участнику — с задержкой, чтобы не дёргать API на каждую букву
let searchTimer: ReturnType<typeof setTimeout> | undefined
function onSearch(event: Event) {
  const q = (event.target as HTMLInputElement).value
  filters.value = { ...filters.value, q }
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => emit('change'), SEARCH_DELAY)
}

onUnmounted(() => clearTimeout(searchTimer))
</script>

<template>
  <div class="receipts-history">
    <div class="filters">
      <div class="chips">
        <button
          v-for="status in STATUSES"
          :key="status ?? 'all'"
          type="button"
          class="chip"
          :class="{ 'chip--active': filters.status === status }"
          @click="update({ status })"
        >
          {{ $t(`history.filters.${status ?? 'all'}`) }}
        </button>
      </div>

      <label class="search">
        <LuSearch />
        <input :value="filters.q" type="search" :placeholder="$t('admin.history.search')" @input="onSearch" />
      </label>

      <div class="selects">
        <a-select
          :value="filters.currency ?? undefined"
          allow-clear
          class="select"
          :placeholder="$t('admin.history.allCurrencies')"
          :options="currencies.map((c) => ({ value: c, label: c.toUpperCase() }))"
          @update:value="setCurrency"
        />
        <a-select
          :value="filters.requisite_id ?? undefined"
          allow-clear
          class="select select--wide"
          :placeholder="$t('admin.history.allRequisites')"
          :options="requisiteOptions"
          @update:value="(value: unknown) => update({ requisite_id: typeof value === 'number' ? value : null })"
        />
      </div>
    </div>

    <!-- Итоги по всем найденным чекам, а не только по загруженной странице -->
    <div class="totals">
      <span class="found">{{ $t('admin.history.found', { n: totalCount }) }}</span>
      <span v-for="total in totals" :key="total.currency" class="total">
        {{ formatMoney(total.amount, total.currency) }} · {{ total.count }}
      </span>
    </div>

    <div v-if="items.length" class="list">
      <VerifyCard v-for="item in items" :key="item.id" :contribution="item" @check="emit('open', $event)" />
      <button v-if="hasMore" class="more-btn" :disabled="isLoading" @click="emit('more')">
        {{ $t('admin.history.more') }}
      </button>
    </div>
    <EmptyState v-else-if="!isLoading" icon="🧾" :title="$t('admin.history.empty')" />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.receipts-history {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filters {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  @include ghost-button;
  padding: 6px 12px;
  font-size: 12px;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border: 1px solid $field-border;
  border-radius: 12px;
  background: #fff;
  color: $text-muted;

  input {
    flex: 1;
    min-width: 0;
    padding: 10px 0;
    border: none;
    outline: none;
    background: transparent;
    font-size: 14px;
    color: $navy;
  }
}

.selects {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 8px;
}

.select {
  width: 100%;
  min-width: 0;
}

.totals {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.found {
  margin-right: 4px;
  font-size: 13px;
  font-weight: 700;
  color: $navy;
}

.total {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
  font-size: 12px;
  font-weight: 700;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.more-btn {
  @include ghost-button;
  align-self: center;
}
</style>
