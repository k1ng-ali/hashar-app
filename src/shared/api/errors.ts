import { i18n } from '@/shared/i18n/index.ts'
import { errorDetail } from './http.ts'

/**
 * Ошибки бэкенда (`detail` на английском) → ключи переводов.
 * Пользователь не должен видеть английский текст сервера в русском или таджикском интерфейсе.
 * Ошибки входа и подтверждения разбираются на своих экранах (LoginPage, VerificationStep).
 */
const API_ERRORS: Record<string, string> = {
  // ── Доступ ──
  'Not enough rights': 'apiErrors.noRights',
  'Not a member of this fund': 'apiErrors.notMember',
  'Only the chairman can do this': 'apiErrors.chairmanOnly',
  // ── Не найдено ──
  'Fund not found': 'apiErrors.fundNotFound',
  'Member not found': 'apiErrors.notFound',
  'Announcement not found': 'apiErrors.notFound',
  'Contribution not found': 'apiErrors.notFound',
  'Expense not found': 'apiErrors.notFound',
  'Target fund not found': 'apiErrors.notFound',
  'Requisite not found': 'apiErrors.requisiteNotFound',
  'Request not found': 'apiErrors.notFound',
  'Plan request not found': 'apiErrors.notFound',
  'User not found': 'apiErrors.notFound',
  'Contact not found': 'apiErrors.notFound',
  'Account not found': 'apiErrors.notFound',
  // ── Фонды и участники ──
  'Already a member': 'apiErrors.alreadyMember',
  'Request is already pending': 'apiErrors.requestPending',
  'Blocked in this fund': 'apiErrors.blocked',
  'Member limit reached for the plan': 'admin.errors.memberLimit',
  'Transfer chairman rights first': 'apiErrors.transferChairman',
  'Request is not pending': 'apiErrors.alreadyReviewed',
  'Member is not active': 'apiErrors.memberInactive',
  'Member is not active or blocked': 'apiErrors.memberInactive',
  'Cannot change yourself': 'apiErrors.cannotChangeYourself',
  'Cannot change the chairman': 'apiErrors.cannotChangeChairman',
  'Already the chairman': 'apiErrors.alreadyChairman',
  'Absence decision required': 'absence.chooseFirst',
  'Could not generate fund code': 'errors.generic',
  // ── Деньги ──
  'Fund plan expired: contributions are blocked': 'planStatus.blockedResident',
  'Target fund is closed': 'apiErrors.targetFundClosed',
  'Currency must match the target fund': 'apiErrors.currencyMismatch',
  'credited_amount is required when paying in another currency': 'apiErrors.creditedRequired',
  'Contribution already reviewed': 'apiErrors.alreadyReviewed',
  'Cannot approve your own contribution': 'admin.errors.ownContribution',
  'Insufficient funds': 'overdraft.rejected',
  'Account balance must be zero': 'admin.errors.balanceNotZero',
  'Cannot disable the base currency': 'admin.errors.baseCurrency',
  'Currency account is not enabled': 'admin.errors.currencyDisabled',
  'Financial setup is locked': 'admin.errors.setupLocked',
  'Target fund has operations, close it': 'admin.errors.targetFundHasOperations',
  'Finance announcements cannot be deleted': 'apiErrors.financeAnnouncement',
  'Too many contacts': 'apiErrors.tooManyContacts',
  // ── Чеки ──
  'Receipt must be a PNG, JPEG or WebP image': 'apiErrors.receiptFormat',
  'Receipt image is too large': 'receipt.tooLarge',
  'Request body is too large': 'receipt.tooLarge',
  'Receipt upload not found, upload it again': 'apiErrors.receiptExpired',
  'Too many uploads, try later': 'apiErrors.tooManyUploads',
  'Receipt storage is not configured': 'errors.server',
  // ── Тарифы ──
  'Plan request is already pending': 'plans.pending',
  'Plan request already reviewed': 'apiErrors.alreadyReviewed',
  'monthly_price is required for this plan': 'apiErrors.priceRequired',
  'Too many attempts, try later': 'auth.tooManyAttempts',
}

/** Понятный текст ошибки запроса на языке интерфейса; неизвестная ошибка — fallbackKey. */
export function errorMessage(error: unknown, fallbackKey = 'errors.generic'): string {
  const detail = errorDetail(error)
  const key = detail ? API_ERRORS[detail] : undefined
  return i18n.global.t(key ?? fallbackKey)
}
