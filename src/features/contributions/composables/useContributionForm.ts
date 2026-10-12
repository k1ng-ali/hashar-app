import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/features/auth/store.ts'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import { generateReceiptSvg } from '@/shared/lib/receiptGenerator.ts'
import { useContributionsStore } from '../store.ts'
import type { ContributionCategory } from '../types.ts'

/**
 * Форма взноса: предзаполнение, выбор реквизита (= валюты), валидация, демо-чек, отправка.
 *
 * Правила валют (как на бэкенде):
 * - платить можно на любой активный реквизит фонда — валюта взноса = валюта реквизита
 * - ежемесячный взнос засчитывается в базовой валюте, целевой — в валюте сбора
 * - если валюта реквизита другая, участник сам указывает, сколько зачесть (курс не считаем)
 */
export function useContributionForm() {
  const { t } = useI18n()
  const authStore = useAuthStore()
  const fundsStore = useFundsStore()
  const dashboardStore = useDashboardStore()
  const targetFundsStore = useTargetFundsStore()
  const contributionsStore = useContributionsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const category = ref<ContributionCategory>('monthly_fee')
  const targetFundId = ref<number | null>(null)
  const requisiteId = ref<number | null>(null)
  const amount = ref<number | null>(null)
  const creditedAmount = ref<number | null>(null)
  const receipt = ref('')
  const comment = ref('')
  const validationError = ref('')

  // ── Getters ───────────────────────────────────────────────────────────
  const baseCurrency = computed(() => fundsStore.current?.base_currency ?? 'tjs')
  const rate = computed(() => fundsStore.current?.monthly_rate ?? 0)
  const targetFund = computed(() => targetFundsStore.items.find((f) => f.id === targetFundId.value) ?? null)

  /** Валюта назначения: в ней взнос засчитывается (базовая или валюта сбора). */
  const requiredCurrency = computed(() =>
    category.value === 'monthly_fee' ? baseCurrency.value : (targetFund.value?.currency ?? null),
  )

  // Все реквизиты фонда; сначала — в валюте назначения
  const availableRequisites = computed(() =>
    [...dashboardStore.requisites].sort(
      (a, b) => Number(b.currency === requiredCurrency.value) - Number(a.currency === requiredCurrency.value),
    ),
  )
  const selectedRequisite = computed(
    () => dashboardStore.requisites.find((r) => r.id === requisiteId.value) ?? null,
  )
  const currency = computed(() => selectedRequisite.value?.currency ?? requiredCurrency.value ?? baseCurrency.value)
  /** Платим в другой валюте — нужно указать, сколько зачесть. */
  const needsCredit = computed(
    () => !!selectedRequisite.value && !!requiredCurrency.value && currency.value !== requiredCurrency.value,
  )

  function defaultRequisiteId(): number | null {
    const preferred = availableRequisites.value.find((r) => r.currency === requiredCurrency.value)
    return (preferred ?? availableRequisites.value[0])?.id ?? null
  }

  const debtAmount = computed(() =>
    contributionsStore.balance?.status === 'debt' ? contributionsStore.balance.debt_amount : 0,
  )
  /** Быстрые суммы тарифа — в базовой валюте, поэтому для поля зачёта или суммы в базовой. */
  const presets = computed(() => (category.value === 'monthly_fee' && rate.value ? [1, 2, 3, 6].map((n) => rate.value * n) : []))

  // Сменилось назначение — предлагаем реквизит в его валюте
  watch(requiredCurrency, () => {
    requisiteId.value = defaultRequisiteId()
  })

  // Сумма в валюте назначения (долг, тариф) переезжает в поле зачёта, а сумму перевода
  // в другой валюте участник вводит сам; при возврате к валюте назначения — обратно
  watch(needsCredit, (value) => {
    if (value) {
      creditedAmount.value = amount.value
      amount.value = null
    } else {
      amount.value = creditedAmount.value ?? amount.value
      creditedAmount.value = null
    }
  })

  // ── Actions ───────────────────────────────────────────────────────────
  /** Предзаполнение: из ссылки на сбор или суммой долга / тарифа. */
  function init(presetFundId: number | null) {
    receipt.value = ''
    comment.value = ''
    validationError.value = ''

    if (presetFundId) {
      category.value = 'target_fund'
      targetFundId.value = presetFundId
      amount.value = null
    } else {
      category.value = 'monthly_fee'
      targetFundId.value = null
      amount.value = debtAmount.value || rate.value || null
    }
    creditedAmount.value = null
    requisiteId.value = defaultRequisiteId()
  }

  function generateDemoReceipt() {
    const requisite = selectedRequisite.value
    receipt.value = generateReceiptSvg({
      bankName: requisite?.bank_name ?? 'Bank',
      amount: amount.value ?? 0,
      currency: currency.value,
      senderName: authStore.user?.full_name ?? '—',
      recipientName: requisite?.recipient_name ?? t('app.name'),
      purpose:
        category.value === 'target_fund' && targetFund.value
          ? targetFund.value.title.slice(0, 32)
          : `${t('contributionCategory.monthly_fee')} (${fundsStore.currentMembership?.address_unit ?? ''})`,
    })
  }

  function validate(): boolean {
    validationError.value = ''
    if (category.value === 'target_fund' && !targetFundId.value) {
      validationError.value = t('contribution.validation.fund')
    } else if (!requisiteId.value) {
      validationError.value = t('contribution.validation.requisite')
    } else if (!amount.value || amount.value < 1) {
      validationError.value = t('contribution.validation.amount')
    } else if (needsCredit.value && (!creditedAmount.value || creditedAmount.value < 1)) {
      validationError.value = t('contribution.validation.credited')
    } else if (!receipt.value) {
      validationError.value = t('contribution.validation.receipt')
    }
    return !validationError.value
  }

  async function submit() {
    if (!validate()) return null
    return contributionsStore.submit({
      requisite_id: requisiteId.value!,
      amount: amount.value!,
      credited_amount: needsCredit.value ? creditedAmount.value : null,
      category: category.value,
      target_fund_id: category.value === 'target_fund' ? targetFundId.value : null,
      receipt_image: receipt.value,
      comment_user: comment.value.trim() || null,
    })
  }

  return {
    category,
    targetFundId,
    requisiteId,
    amount,
    creditedAmount,
    receipt,
    comment,
    validationError,
    rate,
    baseCurrency,
    currency,
    requiredCurrency,
    needsCredit,
    availableRequisites,
    debtAmount,
    presets,
    init,
    generateDemoReceipt,
    submit,
  }
}
