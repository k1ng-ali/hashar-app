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
 * - ежемесячный взнос — только на реквизиты базовой валюты фонда
 * - взнос в целевой сбор — только в валюте этого сбора
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
  const receipt = ref('')
  const comment = ref('')
  const validationError = ref('')

  // ── Getters ───────────────────────────────────────────────────────────
  const baseCurrency = computed(() => fundsStore.current?.base_currency ?? 'tjs')
  const rate = computed(() => fundsStore.current?.monthly_rate ?? 0)
  const targetFund = computed(() => targetFundsStore.items.find((f) => f.id === targetFundId.value) ?? null)

  /** Валюта, в которой сейчас можно заплатить. */
  const requiredCurrency = computed(() =>
    category.value === 'monthly_fee' ? baseCurrency.value : (targetFund.value?.currency ?? null),
  )

  const availableRequisites = computed(() =>
    dashboardStore.requisites.filter((r) => r.currency === requiredCurrency.value),
  )
  const selectedRequisite = computed(
    () => dashboardStore.requisites.find((r) => r.id === requisiteId.value) ?? null,
  )
  const currency = computed(() => selectedRequisite.value?.currency ?? requiredCurrency.value ?? baseCurrency.value)

  const debtAmount = computed(() =>
    contributionsStore.balance?.status === 'debt' ? contributionsStore.balance.debt_amount : 0,
  )
  const presets = computed(() => (category.value === 'monthly_fee' && rate.value ? [1, 2, 3, 6].map((n) => rate.value * n) : []))

  // Сменилась валюта — выбираем первый подходящий реквизит
  watch(requiredCurrency, () => {
    if (!availableRequisites.value.some((r) => r.id === requisiteId.value)) {
      requisiteId.value = availableRequisites.value[0]?.id ?? null
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
    requisiteId.value = availableRequisites.value[0]?.id ?? null
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
    receipt,
    comment,
    validationError,
    rate,
    baseCurrency,
    currency,
    requiredCurrency,
    availableRequisites,
    debtAmount,
    presets,
    init,
    generateDemoReceipt,
    submit,
  }
}
