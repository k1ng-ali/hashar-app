// src/features/admin/store.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { AccountTransfer } from '@/features/announcements/types.ts'
import type { Contribution } from '@/features/contributions/types.ts'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import type { Requisite } from '@/features/dashboard/types.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import type { FundRole, MemberStatus, Plan } from '@/features/funds/types.ts'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import * as api from './api.ts'
import type {
  Expense,
  ExpenseCreate,
  FundSettingsUpdate,
  Member,
  PlanRequest,
  RequisiteCreate,
  TargetFundCreate,
  TransferCreate,
} from './types.ts'

/** Управление фондом для совета: чеки, участники, расходы, сборы, счета, настройки, тариф. */
export const useAdminStore = defineStore('admin', () => {
  const funds = useFundsStore()
  const dashboardStore = useDashboardStore()
  const targetFundsStore = useTargetFundsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const pending = ref<Contribution[]>([])
  const members = ref<Member[]>([])
  const expenses = ref<Expense[]>([])
  const requisites = ref<Requisite[]>([])
  const transfers = ref<AccountTransfer[]>([])
  const planRequests = ref<PlanRequest[]>([])
  const onlyDebtors = ref(false)
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const errorMessage = ref('')

  // ── Getters ───────────────────────────────────────────────────────────
  const joinRequests = computed(() => members.value.filter((m) => m.status === 'pending'))
  const registry = computed(() => members.value.filter((m) => m.status === 'active' || m.status === 'blocked'))
  const debtorsCount = computed(() => registry.value.filter((m) => m.balance?.status === 'debt').length)
  const visibleMembers = computed(() =>
    onlyDebtors.value ? registry.value.filter((m) => m.balance?.status === 'debt') : registry.value,
  )
  const activeCurrencies = computed<Currency[]>(
    () => funds.current?.accounts.filter((a) => a.is_active).map((a) => a.currency) ?? [],
  )
  const hasPendingPlanRequest = computed(() => planRequests.value.some((r) => r.status === 'pending'))

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
  async function fetchAll() {
    isLoading.value = true
    errorMessage.value = ''
    const fundId = funds.fundId
    try {
      const [pendingRes, membersRes, expensesRes, requisitesRes, transfersRes, plansRes] = await Promise.all([
        api.listContributions(fundId, 'pending'),
        api.listMembers(fundId),
        api.listExpenses(fundId),
        api.listRequisites(fundId),
        api.listTransfers(fundId),
        api.listPlanRequests(fundId),
        targetFundsStore.fetchList(),
        funds.fetchCurrent(),
        funds.fetchPlans(),
      ])
      pending.value = pendingRes.data
      members.value = membersRes.data
      expenses.value = expensesRes.data
      requisites.value = requisitesRes.data
      transfers.value = transfersRes.data
      planRequests.value = plansRes.data
    } catch {
      errorMessage.value = 'errors.loadFailed'
    } finally {
      isLoading.value = false
    }
  }

  async function refreshMembers() {
    const { data } = await api.listMembers(funds.fundId)
    members.value = data
  }

  // ── Actions: чеки ─────────────────────────────────────────────────────
  function approve(id: number) {
    return withSubmitting(async () => {
      await api.approveContribution(funds.fundId, id)
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
  async function approveMember(id: number) {
    await api.approveMember(funds.fundId, id)
    await Promise.all([refreshMembers(), funds.fetchCurrent()])
  }

  async function rejectMember(id: number) {
    await api.rejectMember(funds.fundId, id)
    await refreshMembers()
  }

  async function setMemberStatus(id: number, status: MemberStatus) {
    await api.updateMemberStatus(funds.fundId, id, status)
    await Promise.all([refreshMembers(), funds.fetchCurrent()])
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
      const { data } = await api.createExpense(funds.fundId, payload)
      expenses.value = [data, ...expenses.value]
      await refreshBalances()
    })
  }

  async function removeExpense(id: number) {
    await api.deleteExpense(funds.fundId, id)
    expenses.value = expenses.value.filter((item) => item.id !== id)
    await refreshBalances()
  }

  // ── Actions: целевые сборы ────────────────────────────────────────────
  function addTargetFund(payload: TargetFundCreate) {
    return withSubmitting(async () => {
      const { data } = await api.createTargetFund(funds.fundId, payload)
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

  function requestPlan(plan: Plan, months: number, comment: string | null) {
    return withSubmitting(async () => {
      const { data } = await api.createPlanRequest(funds.fundId, plan, months, comment)
      planRequests.value = [data, ...planRequests.value]
    })
  }

  return {
    pending,
    members,
    expenses,
    requisites,
    transfers,
    planRequests,
    onlyDebtors,
    isLoading,
    isSubmitting,
    errorMessage,
    joinRequests,
    registry,
    debtorsCount,
    visibleMembers,
    activeCurrencies,
    hasPendingPlanRequest,
    fetchAll,
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
