// src/features/platformAdmin/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as api from './api.ts'
import type {
  DiscountPlan,
  FundAdmin,
  PlanApprove,
  PlanDiscount,
  PlanDiscountPayload,
  PlanRequest,
  Pricing,
} from './types.ts'

/** Админ платформы: подтверждение тарифов после оплаты и список фондов. */
export const usePlatformAdminStore = defineStore('platformAdmin', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const requests = ref<PlanRequest[]>([])
  const funds = ref<FundAdmin[]>([])
  const pricing = ref<Pricing | null>(null)
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

  // ── Actions: цены и скидки ────────────────────────────────────────────
  async function fetchPricing() {
    pricing.value = (await api.getPricing()).data
  }

  /** Изменение цены и скидки затрагивает сразу несколько строк (состояния, лимиты) — перечитываем всё. */
  async function changePricing(action: () => Promise<unknown>) {
    isSubmitting.value = true
    try {
      await action()
      await fetchPricing()
    } finally {
      isSubmitting.value = false
    }
  }

  const setPrice = (plan: DiscountPlan, price: number) => changePricing(() => api.setPlanPrice(plan, price))
  const saveDiscount = (discount: PlanDiscount | null, payload: PlanDiscountPayload) =>
    changePricing(() => (discount ? api.updateDiscount(discount.id, payload) : api.createDiscount(payload)))
  const removeDiscount = (id: number) => changePricing(() => api.deleteDiscount(id))

  return {
    requests,
    funds,
    pricing,
    isLoading,
    isSubmitting,
    pendingRequests,
    reviewedRequests,
    fetchAll,
    fetchPricing,
    setPrice,
    saveDiscount,
    removeDiscount,
    approve,
    reject,
  }
})
