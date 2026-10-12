// src/features/expenses/store.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useFundsStore } from '@/features/funds/store.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import * as api from './api.ts'
import type { Expense, ExpensesFilter } from './types.ts'

// Расходов за одну подгрузку
const PAGE_SIZE = 20

/** Лента расходов фонда для всех участников: фильтры, подгрузка, открытый расход. */
export const useExpensesStore = defineStore('expenses', () => {
  const funds = useFundsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const items = ref<Expense[]>([])
  const filter = ref<ExpensesFilter>('all')
  const currency = ref<Currency | null>(null)
  const hasMore = ref(false)
  const selected = ref<Expense | null>(null)
  const isLoading = ref(false)
  const errorMessage = ref('')

  // ── Actions ───────────────────────────────────────────────────────────
  /** Первая страница по фильтрам (или следующая при append). */
  async function fetchItems(append = false) {
    isLoading.value = true
    errorMessage.value = ''
    try {
      const { data } = await api.listExpenses(funds.fundId, {
        category: filter.value === 'all' ? undefined : filter.value,
        currency: currency.value ?? undefined,
        skip: append ? items.value.length : 0,
        limit: PAGE_SIZE,
      })
      items.value = append ? [...items.value, ...data] : data
      hasMore.value = data.length === PAGE_SIZE
    } catch {
      errorMessage.value = 'errors.loadFailed'
    } finally {
      isLoading.value = false
    }
  }

  function setFilter(next: ExpensesFilter) {
    filter.value = next
    return fetchItems()
  }

  function setCurrency(next: Currency | null) {
    currency.value = next
    return fetchItems()
  }

  /** Открыть расход: из ленты — сразу, по ссылке (?id=) — с загрузкой. */
  async function open(id: number) {
    selected.value = items.value.find((item) => item.id === id) ?? (await api.getExpense(funds.fundId, id)).data
  }

  function close() {
    selected.value = null
  }

  return {
    items,
    filter,
    currency,
    hasMore,
    selected,
    isLoading,
    errorMessage,
    fetchItems,
    setFilter,
    setCurrency,
    open,
    close,
  }
})
