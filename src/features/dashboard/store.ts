// src/features/dashboard/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useFundsStore } from '@/features/funds/store.ts'
import * as api from './api.ts'
import type { FundSummary, Operation, OperationsFilter, Requisite } from './types.ts'

export const useDashboardStore = defineStore('dashboard', () => {
  const funds = useFundsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const summary = ref<FundSummary | null>(null)
  const operations = ref<Operation[]>([])
  const operationsFilter = ref<OperationsFilter>('all')
  const requisites = ref<Requisite[]>([])
  const isLoading = ref(false)
  const isOperationsLoading = ref(false)
  const errorMessage = ref('')

  // ── Getters ───────────────────────────────────────────────────────────
  const baseAccount = computed(
    () => summary.value?.accounts.find((a) => a.currency === summary.value?.base_currency) ?? null,
  )
  const otherAccounts = computed(
    () => summary.value?.accounts.filter((a) => a.currency !== summary.value?.base_currency) ?? [],
  )
  const payingMembersCount = computed(() =>
    summary.value ? summary.value.active_members_count - summary.value.debtors_count : 0,
  )

  // ── Actions ───────────────────────────────────────────────────────────
  async function fetchSummary() {
    const { data } = await api.getSummary(funds.fundId)
    summary.value = data
  }

  async function fetchOperations(filter: OperationsFilter = operationsFilter.value) {
    operationsFilter.value = filter
    isOperationsLoading.value = true
    try {
      const { data } = await api.getOperations(funds.fundId, filter)
      operations.value = data
    } finally {
      isOperationsLoading.value = false
    }
  }

  async function fetchRequisites() {
    const { data } = await api.getRequisites(funds.fundId)
    requisites.value = data
  }

  /** Всё для главного экрана одним вызовом. */
  async function fetchDashboard() {
    isLoading.value = true
    errorMessage.value = ''
    try {
      await Promise.all([fetchSummary(), fetchOperations('all'), fetchRequisites()])
    } catch {
      errorMessage.value = 'errors.loadFailed'
    } finally {
      isLoading.value = false
    }
  }

  return {
    summary,
    operations,
    operationsFilter,
    requisites,
    isLoading,
    isOperationsLoading,
    errorMessage,
    baseAccount,
    otherAccounts,
    payingMembersCount,
    fetchSummary,
    fetchOperations,
    fetchRequisites,
    fetchDashboard,
  }
})
