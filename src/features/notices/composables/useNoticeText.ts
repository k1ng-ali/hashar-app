import { useI18n } from 'vue-i18n'
import { formatDate } from '@/shared/lib/format.ts'
import type { Notice } from '../types.ts'

export interface NoticeText {
  title: string
  body: string | null
  /** Уведомление про тариф — к нему кнопка «Продлить тариф». */
  aboutPlan: boolean
}

/** Заголовок и текст уведомления: у системных — по kind и details, у сообщений админа — его текст. */
export function useNoticeText() {
  const { t } = useI18n()

  return (notice: Notice): NoticeText => {
    const d = notice.details
    const plan = d.plan ? t(`plans.${d.plan}`) : ''
    const date = d.expires_at ? formatDate(d.expires_at) : ''
    const blockDate = d.blocks_at ? formatDate(d.blocks_at) : ''

    switch (notice.kind) {
      case 'admin_message':
        return { title: t('notices.fromAdmin'), body: notice.text, aboutPlan: false }
      case 'plan_rejected':
        return {
          title: t('notices.planRejected', { plan }),
          body: d.reason ? t('notices.reason', { reason: d.reason }) : null,
          aboutPlan: true,
        }
      case 'plan_approved':
        return {
          title: t('notices.planApproved', { plan }),
          body: [t('notices.activeUntil', { date }), d.comment].filter(Boolean).join(' · '),
          aboutPlan: false,
        }
      case 'plan_expiring':
        return {
          title: t('notices.planExpiring', { plan, date }),
          body: t('notices.planExpiringBody', { date: blockDate }),
          aboutPlan: true,
        }
      case 'plan_expired':
        return {
          title: t('notices.planExpired', { plan, date }),
          body: d.will_block ? t('notices.planExpiredBlock', { date: blockDate }) : t('notices.planExpiredFree'),
          aboutPlan: true,
        }
      case 'plan_lapsed':
        return { title: t('notices.planLapsed'), body: t('notices.planLapsedBody'), aboutPlan: true }
    }
  }
}
