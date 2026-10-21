import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Contribution } from '@/features/contributions/types.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import type { FundRole, MemberStatus, Plan } from '@/features/funds/types.ts'
import { errorMessage } from '@/shared/api/errors.ts'
import { copyText } from '@/shared/lib/browser.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useAdminStore } from '../store.ts'
import type {
  VerificationView,
  ExpenseCreate,
  FundSettingsUpdate,
  Member,
  RequisiteCreate,
  TargetFundCreate,
  TransferCreate,
} from '../types.ts'

export type AdminSheet = 'verify' | 'expense' | 'fund' | 'requisite' | 'transfer' | 'plan' | 'absence' | null

/** Действия совета для экранов раздела «Фонд» и «Финансы»: шторки и обработчики с уведомлениями. */
export function useAdminFlow() {
  const { t } = useI18n()
  const store = useAdminStore()
  const fundsStore = useFundsStore()
  const headerStore = useHeaderStore()

  // ── Sheets ────────────────────────────────────────────────────────────
  const sheet = ref<AdminSheet>(null)
  const selectedContribution = ref<Contribution | null>(null)
  const selectedPlan = ref<Plan | null>(null)
  // Участник, по которому совет решает о начислениях за период отсутствия
  const selectedMember = ref<Member | null>(null)
  // Продление текущего тарифа, а не переход на новый
  const isRenewal = ref(false)

  // ── Чеки: очередь или история ─────────────────────────────────────────
  const verificationView = ref<VerificationView>('pending')
  const verificationTabs = computed(() => [
    { value: 'pending' as VerificationView, label: t('admin.verification.queue'), badge: store.pending.length },
    { value: 'history' as VerificationView, label: t('admin.history.title') },
  ])

  watch(verificationView, (value) => {
    if (value === 'history' && !store.history.length) void store.fetchHistory()
  })

  function openSheet(name: Exclude<AdminSheet, null>) {
    sheet.value = name
  }

  function closeSheet() {
    sheet.value = null
    selectedContribution.value = null
    selectedPlan.value = null
    selectedMember.value = null
    isRenewal.value = false
  }

  function openVerify(contribution: Contribution) {
    selectedContribution.value = contribution
    sheet.value = 'verify'
  }

  function openPlanRequest(plan: Plan, renewal = false) {
    selectedPlan.value = plan
    isRenewal.value = renewal
    sheet.value = 'plan'
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

  function confirmDelete() {
    return window.confirm(t('common.confirmDelete'))
  }

  // ── Handlers: проверка чеков ──────────────────────────────────────────
  async function handleApprove(creditedAmount: number | null) {
    const contribution = selectedContribution.value
    if (!contribution) return
    const ok = await run(() => store.approve(contribution.id, creditedAmount), 'admin.verification.approved', true)
    if (ok && store.history.length) void store.fetchHistory()
  }

  async function handleReject(reason: string) {
    const contribution = selectedContribution.value
    if (!contribution) return
    const ok = await run(() => store.reject(contribution.id, reason), 'admin.verification.rejected', true)
    if (ok && store.history.length) void store.fetchHistory()
  }

  const handleHistoryFilter = () => run(() => store.fetchHistory())
  const handleHistoryMore = () => run(() => store.fetchHistory(true))

  // ── Handlers: участники ───────────────────────────────────────────────
  // Возвращающийся участник — сначала решение о периоде отсутствия
  function handleApproveMember(member: Member) {
    if (member.absence) {
      selectedMember.value = member
      sheet.value = 'absence'
      return Promise.resolve(false)
    }
    return run(() => store.approveMember(member.id), 'admin.members.approved')
  }

  // Разблокировка: если не выходил — решение о периоде блокировки; если вышел — просто снимаем блок
  function handleUnblock(member: Member) {
    if (member.absence) {
      selectedMember.value = member
      sheet.value = 'absence'
      return Promise.resolve(false)
    }
    return run(() => store.setMemberStatus(member.id, 'active'), 'admin.members.updated')
  }

  /** Подтверждение из шторки выбора: возвращение или разблокировка. */
  function handleAbsenceDecision(accrue: boolean) {
    const member = selectedMember.value
    if (!member?.absence) return Promise.resolve(false)
    const action =
      member.absence.reason === 'left'
        ? () => store.approveMember(member.id, accrue)
        : () => store.setMemberStatus(member.id, 'active', accrue)
    return run(action, accrue ? 'absence.doneAccrued' : 'absence.doneSkipped', true)
  }
  const handleRejectMember = (member: Member) => run(() => store.rejectMember(member.id), 'admin.members.rejected')
  const handleMemberStatus = (member: Member, status: MemberStatus) =>
    status === 'active' ? handleUnblock(member) : run(() => store.setMemberStatus(member.id, status), 'admin.members.updated')
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
    run(
      () => store.saveSettings(payload),
      // Новый тариф вступает в силу не сразу — говорим об этом прямо
      payload.monthly_rate !== undefined ? 'admin.settings.rateScheduled' : 'admin.settings.saved',
    )

  // ── Handlers: реквизиты ───────────────────────────────────────────────
  const handleAddRequisite = (payload: RequisiteCreate) =>
    run(() => store.addRequisite(payload), 'admin.settings.added', true)
  const handleToggleRequisite = (id: number) => run(() => store.toggleRequisite(id))

  async function handleDeleteRequisite(id: number) {
    if (confirmDelete()) await run(() => store.removeRequisite(id), 'admin.settings.deleted')
  }

  async function handleCopy(value: string) {
    if (await copyText(value)) headerStore.showNotification(t('common.copied'))
  }

  const handlePlanRequest = (months: number, contact: string, comment: string | null) => {
    const plan = selectedPlan.value
    if (!plan) return Promise.resolve(false)
    return run(
      () => store.requestPlan({ plan, months, contact, comment }),
      isRenewal.value ? 'plans.renewRequested' : 'plans.requested',
      true,
    )
  }

  return {
    sheet,
    selectedContribution,
    selectedPlan,
    selectedMember,
    isRenewal,
    verificationView,
    verificationTabs,
    permissions: computed(() => fundsStore.permissions),
    openSheet,
    closeSheet,
    openVerify,
    openPlanRequest,
    handleApprove,
    handleReject,
    handleHistoryFilter,
    handleHistoryMore,
    handleApproveMember,
    handleAbsenceDecision,
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
