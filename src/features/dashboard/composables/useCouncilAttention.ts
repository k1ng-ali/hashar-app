import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AttentionItem } from '../components/AttentionCard.vue'
import { useDashboardStore } from '../store.ts'
import { useFundsStore } from '@/features/funds/store.ts'

// Тариф платформы скоро закончится — предупреждаем совет заранее
const PLAN_WARNING_DAYS = 7
const DAY_MS = 24 * 60 * 60 * 1000

/** «Требует внимания» у совета: чеки, заявки, скорое окончание тарифа. Главная и колокольчик. */
export function useCouncilAttention() {
  const { t } = useI18n()
  const store = useDashboardStore()
  const fundsStore = useFundsStore()

  return computed<AttentionItem[]>(() => {
    const summary = store.summary
    const fund = fundsStore.current
    if (!fundsStore.permissions.isCouncil || !summary || !fund) return []

    const items: AttentionItem[] = []
    if (summary.pending_count) {
      items.push({ key: 'receipts', label: t('attention.receipts'), count: summary.pending_count, to: '/fund/receipts' })
    }
    if (summary.pending_members_count) {
      items.push({
        key: 'members',
        label: t('attention.members'),
        count: summary.pending_members_count,
        to: '/fund/members',
      })
    }
    // После окончания тарифа вместо этого пункта — плашка на главной (PlanStatusBanner)
    const expiresAt = fund.plan.expires_at ? new Date(fund.plan.expires_at).getTime() : null
    if (
      fund.plan.lapse === 'none' &&
      fund.plan.effective_plan !== 'free' &&
      expiresAt &&
      expiresAt - Date.now() < PLAN_WARNING_DAYS * DAY_MS
    ) {
      const days = Math.max(0, Math.ceil((expiresAt - Date.now()) / DAY_MS))
      items.push({ key: 'plan', label: t('attention.plan', { n: days }), to: '/fund/settings' })
    }
    return items
  })
}
