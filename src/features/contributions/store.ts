// src/features/contributions/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useFundsStore } from '@/features/funds/store.ts'
import * as api from './api.ts'
import type { Contribution, ContributionCreate, ContributionStatus, ResidentBalance } from './types.ts'

export type HistoryFilter = 'all' | ContributionStatus

export const useContributionsStore = defineStore('contributions', () => {
  const funds = useFundsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const items = ref<Contribution[]>([])
  const balance = ref<ResidentBalance | null>(null)
  const filter = ref<HistoryFilter>('all')
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const errorMessage = ref('')

  // ── Getters ───────────────────────────────────────────────────────────
  const filteredItems = computed(() =>
    filter.value === 'all' ? items.value : items.value.filter((item) => item.status === filter.value),
  )
  const hasDebt = computed(() => balance.value?.status === 'debt')
  const countByStatus = computed(() => ({
    pending: items.value.filter((item) => item.status === 'pending').length,
    rejected: items.value.filter((item) => item.status === 'rejected').length,
  }))

  // ── Actions ───────────────────────────────────────────────────────────
  async function fetchBalance() {
    const { data } = await api.getMyBalance(funds.fundId)
    balance.value = data
  }

  async function fetchMy() {
    isLoading.value = true
    errorMessage.value = ''
    try {
      const [contributions] = await Promise.all([api.listMyContributions(funds.fundId), fetchBalance()])
      items.value = contributions.data
    } catch {
      errorMessage.value = 'errors.loadFailed'
    } finally {
      isLoading.value = false
    }
  }

  async function submit(payload: ContributionCreate) {
    isSubmitting.value = true
    try {
      const { data } = await api.createContribution(funds.fundId, payload)
      items.value = [data, ...items.value]
      await fetchBalance()
      return data
    } finally {
      isSubmitting.value = false
    }
  }

  return {
    items,
    balance,
    filter,
    isLoading,
    isSubmitting,
    errorMessage,
    filteredItems,
    hasDebt,
    countByStatus,
    fetchBalance,
    fetchMy,
    submit,
  }
})
