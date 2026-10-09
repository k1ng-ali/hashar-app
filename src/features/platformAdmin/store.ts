// src/features/platformAdmin/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as api from './api.ts'
import type { FundAdmin, PlanApprove, PlanRequest } from './types.ts'

/** Админ платформы: подтверждение тарифов после оплаты и список фондов. */
export const usePlatformAdminStore = defineStore('platformAdmin', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const requests = ref<PlanRequest[]>([])
  const funds = ref<FundAdmin[]>([])
  const isLoading = ref(false)
  const isSubmitting = ref(false)

  // ── Getters ───────────────────────────────────────────────────────────
  const pendingRequests = computed(() => requests.value.filter((r) => r.status === 'pending'))
  const reviewedRequests = computed(() => requests.value.filter((r) => r.status !== 'pending'))

  // ── Actions ───────────────────────────────────────────────────────────
  async function fetchAll() {
    isLoading.value = true
    try {
      const [requestsRes, fundsRes] = await Promise.all([api.listPlanRequests(), api.listFunds()])
      requests.value = requestsRes.data
      funds.value = fundsRes.data
    } finally {
      isLoading.value = false
    }
  }

  async function review(action: () => Promise<{ data: PlanRequest }>) {
    isSubmitting.value = true
    try {
      const { data } = await action()
      requests.value = requests.value.map((r) => (r.id === data.id ? data : r))
      const { data: fundsData } = await api.listFunds()
      funds.value = fundsData
    } finally {
      isSubmitting.value = false
    }
  }

  const approve = (id: number, payload: PlanApprove) => review(() => api.approvePlanRequest(id, payload))
  const reject = (id: number, comment: string) => review(() => api.rejectPlanRequest(id, comment))

  return {
    requests,
    funds,
    isLoading,
    isSubmitting,
    pendingRequests,
    reviewedRequests,
    fetchAll,
    approve,
    reject,
  }
})
