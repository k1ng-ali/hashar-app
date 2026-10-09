// src/features/targetFunds/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useFundsStore } from '@/features/funds/store.ts'
import * as api from './api.ts'
import type { TargetFund, TargetFundDetail } from './types.ts'

export const useTargetFundsStore = defineStore('targetFunds', () => {
  const funds = useFundsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const items = ref<TargetFund[]>([])
  const detail = ref<TargetFundDetail | null>(null)
  const isLoading = ref(false)
  const isDetailLoading = ref(false)
  const errorMessage = ref('')

  // ── Getters ───────────────────────────────────────────────────────────
  const activeItems = computed(() => items.value.filter((item) => item.is_active))

  // ── Actions ───────────────────────────────────────────────────────────
  async function fetchList() {
    isLoading.value = true
    try {
      const { data } = await api.listTargetFunds(funds.fundId)
      items.value = data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchDetail(id: number) {
    isDetailLoading.value = true
    errorMessage.value = ''
    // Не показываем данные предыдущего сбора, пока грузится новый
    if (detail.value?.id !== id) detail.value = null
    try {
      const { data } = await api.getTargetFund(funds.fundId, id)
      detail.value = data
    } catch {
      errorMessage.value = 'targetFunds.notFound'
    } finally {
      isDetailLoading.value = false
    }
  }

  /** Подменяет сбор в списке и карточке после действий в админке. */
  function upsert(fund: TargetFund) {
    const index = items.value.findIndex((item) => item.id === fund.id)
    if (index === -1) items.value = [fund, ...items.value]
    else items.value[index] = fund
    if (detail.value?.id === fund.id) detail.value = { ...detail.value, ...fund }
  }

  function remove(id: number) {
    items.value = items.value.filter((item) => item.id !== id)
    if (detail.value?.id === id) detail.value = null
  }

  return {
    items,
    detail,
    isLoading,
    isDetailLoading,
    errorMessage,
    activeItems,
    fetchList,
    fetchDetail,
    upsert,
    remove,
  }
})
