import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { Contribution } from '@/features/contributions/types.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import type { FundRole, MemberStatus, Plan } from '@/features/funds/types.ts'
import { errorDetail } from '@/shared/api/http.ts'
import { copyText } from '@/shared/lib/browser.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useAdminStore } from '../store.ts'
import type {
  AdminTab,
  ExpenseCreate,
  FundSettingsUpdate,
  Member,
  RequisiteCreate,
  TargetFundCreate,
  TransferCreate,
} from '../types.ts'

const TABS: AdminTab[] = ['verification', 'members', 'expenses', 'funds', 'accounts', 'settings']

export type AdminSheet = 'verify' | 'expense' | 'fund' | 'requisite' | 'transfer' | 'plan' | null

/** Оркестрация экрана управления фондом: вкладка из URL, шторки, обработчики с уведомлениями. */
export function useAdminFlow() {
  const { t } = useI18n()
  const route = useRoute()
  const router = useRouter()
  const store = useAdminStore()
  const fundsStore = useFundsStore()
  const headerStore = useHeaderStore()

  // ── View ──────────────────────────────────────────────────────────────
  const view = computed<AdminTab>({
    get: () => {
      const tab = route.query.tab as AdminTab
      return TABS.includes(tab) ? tab : 'verification'
    },
    set: (tab) => {
      void router.replace({ query: { ...route.query, tab } })
    },
  })

  const tabs = computed(() =>
    TABS.map((tab) => ({
      value: tab,
      label: t(`admin.tabs.${tab}`),
      badge: tab === 'verification' ? store.pending.length : tab === 'members' ? store.joinRequests.length : 0,
    })),
  )

  // ── Sheets ────────────────────────────────────────────────────────────
  const sheet = ref<AdminSheet>(null)
  const selectedContribution = ref<Contribution | null>(null)
  const selectedPlan = ref<Plan | null>(null)

  function openSheet(name: Exclude<AdminSheet, null>) {
    sheet.value = name
  }

  function closeSheet() {
    sheet.value = null
    selectedContribution.value = null
    selectedPlan.value = null
  }

  function openVerify(contribution: Contribution) {
    selectedContribution.value = contribution
    sheet.value = 'verify'
  }

  function openPlanRequest(plan: Plan) {
    selectedPlan.value = plan
    sheet.value = 'plan'
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────
  async function initView() {
    headerStore.setTitle(t('admin.title'))
    await store.fetchAll()
  }

  function dispose() {
    headerStore.reset()
  }

  // ── Helpers ───────────────────────────────────────────────────────────
  async function run(action: () => Promise<unknown>, successKey?: string, close = false) {
    try {
      await action()
      if (successKey) headerStore.showNotification(t(successKey))
      if (close) closeSheet()
      return true
    } catch (error) {
      headerStore.showNotification(errorMessage(error), 'error', 3500)
      return false
    }
  }

  // Известные ошибки бэкенда — понятным текстом
  function errorMessage(error: unknown): string {
    const detail = errorDetail(error)
    const known: Record<string, string> = {
      'Member limit reached for the plan': 'admin.errors.memberLimit',
      'Account balance must be zero': 'admin.errors.balanceNotZero',
      'Cannot disable the base currency': 'admin.errors.baseCurrency',
      'Currency account is not enabled': 'admin.errors.currencyDisabled',
      'Currency must match the target fund': 'admin.errors.currencyMismatch',
      'Plan request is already pending': 'plans.pending',
    }
    return detail && known[detail] ? t(known[detail]) : (detail ?? t('errors.generic'))
  }

  function confirmDelete() {
    return window.confirm(t('common.confirmDelete'))
  }

  // ── Handlers: проверка чеков ──────────────────────────────────────────
  async function handleApprove() {
    const contribution = selectedContribution.value
    if (contribution) await run(() => store.approve(contribution.id), 'admin.verification.approved', true)
  }

  async function handleReject(reason: string) {
    const contribution = selectedContribution.value
    if (contribution) await run(() => store.reject(contribution.id, reason), 'admin.verification.rejected', true)
  }

  // ── Handlers: участники ───────────────────────────────────────────────
  const handleApproveMember = (member: Member) => run(() => store.approveMember(member.id), 'admin.members.approved')
  const handleRejectMember = (member: Member) => run(() => store.rejectMember(member.id), 'admin.members.rejected')
  const handleMemberStatus = (member: Member, status: MemberStatus) =>
    run(() => store.setMemberStatus(member.id, status), 'admin.members.updated')
  const handleMemberRole = (member: Member, role: FundRole) =>
    run(() => store.setMemberRole(member.id, role), 'admin.members.updated')

  async function handleTransferChairman(member: Member) {
    if (!window.confirm(t('admin.members.transferConfirm', { name: member.full_name }))) return
    await run(() => store.transferChairman(member.id), 'admin.members.chairmanTransferred')
  }

  // ── Handlers: расходы и сборы ─────────────────────────────────────────
  const handleAddExpense = (payload: ExpenseCreate) => run(() => store.addExpense(payload), 'admin.expenses.added', true)

  async function handleDeleteExpense(id: number) {
    if (confirmDelete()) await run(() => store.removeExpense(id), 'admin.expenses.deleted')
  }

  const handleAddFund = (payload: TargetFundCreate) => run(() => store.addTargetFund(payload), 'admin.funds.created', true)
  const handleToggleFund = (id: number) => run(() => store.toggleTargetFund(id), 'targetFunds.toggled')

  async function handleDeleteFund(id: number) {
    if (confirmDelete()) await run(() => store.removeTargetFund(id), 'targetFunds.deleted')
  }

  // ── Handlers: счета ───────────────────────────────────────────────────
  const handleEnableCurrency = (currency: Currency) =>
    run(() => store.enableCurrency(currency), 'admin.accounts.enabled')
  const handleDisableCurrency = (currency: Currency) =>
    run(() => store.disableCurrency(currency), 'admin.accounts.disabled')
  const handleAddTransfer = (payload: TransferCreate) =>
    run(() => store.addTransfer(payload), 'admin.accounts.transferDone', true)

  // ── Handlers: настройки ───────────────────────────────────────────────
  const handleSaveSettings = (payload: FundSettingsUpdate) =>
    run(() => store.saveSettings(payload), 'admin.settings.saved')
  const handleAddRequisite = (payload: RequisiteCreate) =>
    run(() => store.addRequisite(payload), 'admin.settings.added', true)
  const handleToggleRequisite = (id: number) => run(() => store.toggleRequisite(id))

  async function handleDeleteRequisite(id: number) {
    if (confirmDelete()) await run(() => store.removeRequisite(id), 'admin.settings.deleted')
  }

  async function handleCopy(value: string) {
    if (await copyText(value)) headerStore.showNotification(t('common.copied'))
  }

  const handlePlanRequest = (months: number, comment: string | null) => {
    const plan = selectedPlan.value
    if (!plan) return Promise.resolve(false)
    return run(() => store.requestPlan(plan, months, comment), 'plans.requested', true)
  }

  return {
    view,
    tabs,
    sheet,
    selectedContribution,
    selectedPlan,
    permissions: computed(() => fundsStore.permissions),
    initView,
    dispose,
    openSheet,
    closeSheet,
    openVerify,
    openPlanRequest,
    handleApprove,
    handleReject,
    handleApproveMember,
    handleRejectMember,
    handleMemberStatus,
    handleMemberRole,
    handleTransferChairman,
    handleAddExpense,
    handleDeleteExpense,
    handleAddFund,
    handleToggleFund,
    handleDeleteFund,
    handleEnableCurrency,
    handleDisableCurrency,
    handleAddTransfer,
    handleSaveSettings,
    handleAddRequisite,
    handleToggleRequisite,
    handleDeleteRequisite,
    handleCopy,
    handlePlanRequest,
  }
}
