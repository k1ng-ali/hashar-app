// src/features/funds/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as api from './api.ts'
import type { FundCreate, FundInfo, FundPermissions, FundPublic, JoinPayload, MyFund, PlanOption } from './types.ts'

const CURRENT_FUND_KEY = 'fund.current'

function savedFundId(): number | null {
  try {
    return Number(localStorage.getItem(CURRENT_FUND_KEY)) || null
  } catch {
    return null
  }
}

/** Фонды пользователя и текущий (активный) фонд — контекст для всех остальных фич. */
export const useFundsStore = defineStore('funds', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const myFunds = ref<MyFund[]>([])
  const currentFundId = ref<number | null>(savedFundId())
  const current = ref<FundInfo | null>(null)
  const searchResults = ref<FundPublic[]>([])
  const plans = ref<PlanOption[]>([])
  const isLoaded = ref(false)
  const isLoading = ref(false)
  const isSubmitting = ref(false)

  // ── Getters ───────────────────────────────────────────────────────────
  const activeFunds = computed(() => myFunds.value.filter((f) => f.status === 'active'))
  const requests = computed(() => myFunds.value.filter((f) => f.status !== 'active'))
  const hasActiveFund = computed(() => activeFunds.value.length > 0)

  const currentMembership = computed(() => myFunds.value.find((f) => f.id === current.value?.id) ?? null)

  /** id фонда для запросов; страницы фонда открываются только когда он выбран. */
  const fundId = computed(() => current.value?.id ?? 0)

  const permissions = computed<FundPermissions>(() => {
    const role = current.value?.my_role
    const isChairman = role === 'chairman'
    const isCouncil = isChairman || role === 'admin'
    return {
      isCouncil,
      isChairman,
      canManageMembers: isCouncil,
      canChangeRoles: isChairman,
      canManageFinance: isCouncil,
      canDeleteRecords: isChairman,
      canManageSettings: isChairman,
      canPinAnnouncements: isCouncil,
    }
  })

  // ── Actions ───────────────────────────────────────────────────────────
  function rememberFund(id: number | null) {
    currentFundId.value = id
    try {
      if (id) localStorage.setItem(CURRENT_FUND_KEY, String(id))
      else localStorage.removeItem(CURRENT_FUND_KEY)
    } catch {
      // не критично
    }
  }

  async function fetchMy() {
    isLoading.value = true
    try {
      const { data } = await api.listMyFunds()
      myFunds.value = data
      isLoaded.value = true
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCurrent() {
    if (!current.value) return
    const { data } = await api.getFund(current.value.id)
    current.value = data
  }

  /** Восстанавливает активный фонд после входа: сохранённый или первый доступный. */
  async function restore() {
    await fetchMy()
    const saved = activeFunds.value.find((f) => f.id === currentFundId.value)
    const target = saved ?? activeFunds.value[0]
    if (target) await select(target.id)
    else {
      current.value = null
      rememberFund(null)
    }
  }

  async function select(id: number) {
    const { data } = await api.getFund(id)
    current.value = data
    rememberFund(id)
  }

  async function create(payload: FundCreate) {
    isSubmitting.value = true
    try {
      const { data } = await api.createFund(payload)
      current.value = data
      rememberFund(data.id)
      await fetchMy()
      return data
    } finally {
      isSubmitting.value = false
    }
  }

  async function search(query: string) {
    if (query.trim().length < 2) {
      searchResults.value = []
      return
    }
    const { data } = await api.searchFunds(query.trim())
    searchResults.value = data
  }

  async function findByCode(code: string) {
    const { data } = await api.getFundByCode(code)
    return data
  }

  async function join(fundId: number, payload: JoinPayload) {
    isSubmitting.value = true
    try {
      await api.joinFund(fundId, payload)
      await fetchMy()
    } finally {
      isSubmitting.value = false
    }
  }

  async function cancelJoin(fundId: number) {
    await api.cancelJoin(fundId)
    await fetchMy()
  }

  /** Выход из фонда: текущего или указанного (заблокированный выходит со списка «Мои фонды»). */
  async function leave(fundId: number | null = current.value?.id ?? null) {
    if (!fundId) return
    await api.leaveFund(fundId)
    if (fundId === current.value?.id) {
      current.value = null
      rememberFund(null)
    }
    await restore()
  }

  async function fetchPlans() {
    if (plans.value.length) return
    const { data } = await api.listPlans()
    plans.value = data
  }

  function reset() {
    myFunds.value = []
    current.value = null
    isLoaded.value = false
  }

  return {
    myFunds,
    currentFundId,
    current,
    searchResults,
    plans,
    isLoaded,
    isLoading,
    isSubmitting,
    activeFunds,
    requests,
    hasActiveFund,
    currentMembership,
    fundId,
    permissions,
    fetchMy,
    fetchCurrent,
    restore,
    select,
    create,
    search,
    findByCode,
    join,
    cancelJoin,
    leave,
    fetchPlans,
    reset,
  }
})
