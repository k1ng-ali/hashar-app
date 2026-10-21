// src/features/admin/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { AccountTransfer } from '@/features/announcements/types.ts'
import type { Contribution } from '@/features/contributions/types.ts'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import type { Requisite } from '@/features/dashboard/types.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import type { FundRole, MemberStatus } from '@/features/funds/types.ts'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import * as api from './api.ts'
import type {
  CurrencyTotal,
  ExpenseCreate,
  FundSettingsUpdate,
  HistoryFilters,
  Member,
  PlanRequest,
  PlanRequestCreate,
  RequisiteCreate,
  TargetFundCreate,
  TargetFundUpdate,
  TransferCreate,
} from './types.ts'

// Чеков в истории за одну подгрузку
const HISTORY_PAGE = 30

/** Управление фондом для совета: чеки, участники, расходы, сборы, счета, настройки, тариф. */
export const useAdminStore = defineStore('admin', () => {
  const funds = useFundsStore()
  const dashboardStore = useDashboardStore()
  const targetFundsStore = useTargetFundsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const pending = ref<Contribution[]>([])
  const members = ref<Member[]>([])
  const requisites = ref<Requisite[]>([])
  const transfers = ref<AccountTransfer[]>([])
  const planRequests = ref<PlanRequest[]>([])
  // История чеков: страница + итоги по всем подходящим чекам
  const history = ref<Contribution[]>([])
  const historyTotal = ref(0)
  const historyTotals = ref<CurrencyTotal[]>([])
  const historyFilters = ref<HistoryFilters>({ status: 'approved', currency: null, requisite_id: null, q: '' })
  const isHistoryLoading = ref(false)
  const onlyDebtors = ref(false)
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const errorMessage = ref('')

  // ── Getters ───────────────────────────────────────────────────────────
  const joinRequests = computed(() => members.value.filter((m) => m.status === 'pending'))
  const registry = computed(() => members.value.filter((m) => m.status === 'active' || m.status === 'blocked'))
  const formerMembers = computed(() => members.value.filter((m) => m.status === 'left'))
  const debtorsCount = computed(() => registry.value.filter((m) => m.balance?.status === 'debt').length)
  const visibleMembers = computed(() =>
    onlyDebtors.value ? registry.value.filter((m) => m.balance?.status === 'debt') : registry.value,
  )
  const activeCurrencies = computed<Currency[]>(
    () => funds.current?.accounts.filter((a) => a.is_active).map((a) => a.currency) ?? [],
  )
  const hasPendingPlanRequest = computed(() => planRequests.value.some((r) => r.status === 'pending'))
  const hasMoreHistory = computed(() => history.value.length < historyTotal.value)

  // ── Helpers ───────────────────────────────────────────────────────────
  async function withSubmitting<T>(action: () => Promise<T>): Promise<T> {
    isSubmitting.value = true
    try {
      return await action()
    } finally {
      isSubmitting.value = false
    }
  }

  /** Деньги изменились — обновляем остатки в карточке фонда и сводку. */
  async function refreshBalances() {
    await Promise.all([funds.fetchCurrent(), dashboardStore.fetchSummary()])
  }

  // ── Actions: загрузка ─────────────────────────────────────────────────
  /** Обёртка загрузки экрана: индикатор и понятная ошибка. */
  async function load(action: () => Promise<unknown>) {
    isLoading.value = true
    errorMessage.value = ''
    try {
      await action()
    } catch {
      errorMessage.value = 'errors.loadFailed'
    } finally {
      isLoading.value = false
    }
  }

  /** Чеки на проверке. */
  const fetchPending = () =>
    load(async () => {
      pending.value = (await api.listContributions(funds.fundId, 'pending')).data
      // Реквизиты нужны фильтру истории чеков
      requisites.value = (await api.listRequisites(funds.fundId)).data
    })

  /** Заявки и реестр участников. */
  const fetchMembers = () =>
    load(async () => {
      const [membersRes] = await Promise.all([api.listMembers(funds.fundId), funds.fetchCurrent()])
      members.value = membersRes.data
    })

  /** Счета, переводы и реквизиты. */
  const fetchAccounts = () =>
    load(async () => {
      const [requisitesRes, transfersRes] = await Promise.all([
        api.listRequisites(funds.fundId),
        api.listTransfers(funds.fundId),
        funds.fetchCurrent(),
      ])
      requisites.value = requisitesRes.data
      transfers.value = transfersRes.data
    })

  /** Настройки фонда и тариф платформы. */
  const fetchSettings = () =>
    load(async () => {
      const [plansRes] = await Promise.all([
        api.listPlanRequests(funds.fundId),
        funds.fetchCurrent(),
        funds.fetchPlans(),
      ])
      planRequests.value = plansRes.data
    })

  async function refreshMembers() {
    const { data } = await api.listMembers(funds.fundId)
    members.value = data
  }

  // ── Actions: чеки ─────────────────────────────────────────────────────
  /** Первая страница истории по текущим фильтрам (или следующая при append). */
  async function fetchHistory(append = false) {
    isHistoryLoading.value = true
    const skip = append ? history.value.length : 0
    try {
      const { data } = await api.contributionsHistory(funds.fundId, historyFilters.value, skip, HISTORY_PAGE)
      history.value = append ? [...history.value, ...data.items] : data.items
      historyTotal.value = data.total_count
      historyTotals.value = data.totals
    } finally {
      isHistoryLoading.value = false
    }
  }

  function approve(id: number, creditedAmount: number | null = null) {
    return withSubmitting(async () => {
      await api.approveContribution(funds.fundId, id, creditedAmount)
      pending.value = pending.value.filter((item) => item.id !== id)
      // Одобренный взнос меняет сальдо участников, сборы и остатки
      await Promise.all([refreshMembers(), targetFundsStore.fetchList(), refreshBalances()])
    })
  }

  function reject(id: number, reason: string) {
    return withSubmitting(async () => {
      await api.rejectContribution(funds.fundId, id, reason)
      pending.value = pending.value.filter((item) => item.id !== id)
      await dashboardStore.fetchSummary()
    })
  }

  // ── Actions: участники ────────────────────────────────────────────────
  function approveMember(id: number, accrueAbsence: boolean | null = null) {
    return withSubmitting(async () => {
      await api.approveMember(funds.fundId, id, accrueAbsence)
      await Promise.all([refreshMembers(), funds.fetchCurrent(), dashboardStore.fetchSummary()])
    })
  }

  async function rejectMember(id: number) {
    await api.rejectMember(funds.fundId, id)
    await Promise.all([refreshMembers(), dashboardStore.fetchSummary()])
  }

  function setMemberStatus(id: number, status: MemberStatus, accrueAbsence: boolean | null = null) {
    return withSubmitting(async () => {
      await api.updateMemberStatus(funds.fundId, id, status, accrueAbsence)
      await Promise.all([refreshMembers(), funds.fetchCurrent()])
    })
  }

  async function setMemberRole(id: number, role: FundRole) {
    await api.updateMemberRole(funds.fundId, id, role)
    await refreshMembers()
  }

  async function transferChairman(memberId: number) {
    await api.transferChairman(funds.fundId, memberId)
    // Наша роль поменялась на admin — перечитываем фонд и членства
    await Promise.all([refreshMembers(), funds.fetchCurrent(), funds.fetchMy()])
  }

  // ── Actions: расходы ──────────────────────────────────────────────────
  function addExpense(payload: ExpenseCreate) {
    return withSubmitting(async () => {
      await api.createExpense(funds.fundId, payload)
      await refreshBalances()
    })
  }

  async function removeExpense(id: number) {
    await api.deleteExpense(funds.fundId, id)
    await refreshBalances()
  }

  // ── Actions: целевые сборы ────────────────────────────────────────────
  function addTargetFund(payload: TargetFundCreate) {
    return withSubmitting(async () => {
      const { data } = await api.createTargetFund(funds.fundId, payload)
      targetFundsStore.upsert(data)
    })
  }

  function updateTargetFund(id: number, payload: TargetFundUpdate) {
    return withSubmitting(async () => {
      const { data } = await api.updateTargetFund(funds.fundId, id, payload)
      targetFundsStore.upsert(data)
    })
  }

  async function toggleTargetFund(id: number) {
    const { data } = await api.toggleTargetFund(funds.fundId, id)
    targetFundsStore.upsert(data)
  }

  async function removeTargetFund(id: number) {
    await api.deleteTargetFund(funds.fundId, id)
    targetFundsStore.remove(id)
  }

  // ── Actions: счета и переводы ─────────────────────────────────────────
  async function enableCurrency(currency: Currency) {
    await api.enableAccount(funds.fundId, currency)
    await refreshBalances()
  }

  async function disableCurrency(currency: Currency) {
    await api.disableAccount(funds.fundId, currency)
    await refreshBalances()
  }

  function addTransfer(payload: TransferCreate) {
    return withSubmitting(async () => {
      const { data } = await api.createTransfer(funds.fundId, payload)
      transfers.value = [data, ...transfers.value]
      await refreshBalances()
    })
  }

  // ── Actions: реквизиты ────────────────────────────────────────────────
  function addRequisite(payload: RequisiteCreate) {
    return withSubmitting(async () => {
      const { data } = await api.createRequisite(funds.fundId, payload)
      requisites.value = [...requisites.value, data]
    })
  }

  async function toggleRequisite(id: number) {
    const { data } = await api.toggleRequisite(funds.fundId, id)
    requisites.value = requisites.value.map((item) => (item.id === id ? data : item))
  }

  async function removeRequisite(id: number) {
    await api.deleteRequisite(funds.fundId, id)
    requisites.value = requisites.value.filter((item) => item.id !== id)
  }

  // ── Actions: настройки и тариф ────────────────────────────────────────
  function saveSettings(payload: FundSettingsUpdate) {
    return withSubmitting(async () => {
      const { data } = await api.updateSettings(funds.fundId, payload)
      funds.current = data
      // Ставка или базовая валюта влияют на долги
      await refreshMembers()
    })
  }

  function requestPlan(payload: PlanRequestCreate) {
    return withSubmitting(async () => {
      const { data } = await api.createPlanRequest(funds.fundId, payload)
      planRequests.value = [data, ...planRequests.value]
    })
  }

  return {
    pending,
    members,
    requisites,
    transfers,
    planRequests,
    history,
    historyTotal,
    historyTotals,
    historyFilters,
    isHistoryLoading,
    hasMoreHistory,
    onlyDebtors,
    isLoading,
    isSubmitting,
    errorMessage,
    joinRequests,
    registry,
    formerMembers,
    debtorsCount,
    visibleMembers,
    activeCurrencies,
    hasPendingPlanRequest,
    fetchPending,
    fetchMembers,
    fetchAccounts,
    fetchSettings,
    fetchHistory,
    approve,
    reject,
    approveMember,
    rejectMember,
    setMemberStatus,
    setMemberRole,
    transferChairman,
    addExpense,
    removeExpense,
    addTargetFund,
    updateTargetFund,
    toggleTargetFund,
    removeTargetFund,
    enableCurrency,
    disableCurrency,
    addTransfer,
    addRequisite,
    toggleRequisite,
    removeRequisite,
    saveSettings,
    requestPlan,
  }
})
