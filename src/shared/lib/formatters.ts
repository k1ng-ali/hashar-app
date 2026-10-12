/**
 * Форматирование ввода реквизитов и телефонов на лету.
 * Правила совпадают с бэкендом (backend/app/core/formatting.py).
 */

export const CARD_DIGITS = 16
const ACCOUNT_MIN = 10
const ACCOUNT_MAX = 34
const PHONE_MIN = 10
const PHONE_MAX = 15

const group = (value: string, size = 4) => value.match(new RegExp(`.{1,${size}}`, 'g'))?.join(' ') ?? ''

/** «2202203456» → «2202 2034 56» (до 16 цифр). */
export function formatCardInput(raw: string): string {
  return group(raw.replace(/\D/g, '').slice(0, CARD_DIGITS))
}

export function cardDigits(value: string): number {
  return value.replace(/\D/g, '').length
}

export function isValidCard(value: string): boolean {
  return cardDigits(value) === CARD_DIGITS
}

/** Номер счёта / IBAN: латинские буквы и цифры, группами по 4. */
export function formatAccountInput(raw: string): string {
  return group(raw.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, ACCOUNT_MAX))
}

export function isValidAccount(value: string): boolean {
  const compact = value.replace(/\s/g, '')
  return compact.length >= ACCOUNT_MIN && compact.length <= ACCOUNT_MAX
}

/** Телефон: «+» и цифры; +992 и +7 — в привычном виде, остальные — группами по 3. */
export function formatPhoneInput(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, PHONE_MAX)
  if (!digits) return raw.trim().startsWith('+') ? '+' : ''

  if (digits.startsWith('992')) {
    const d = digits.slice(3, 12)
    return ['+992', d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)].filter(Boolean).join(' ')
  }
  if (digits.startsWith('7')) {
    const d = digits.slice(1, 11)
    let result = '+7'
    if (d) result += ` ${d.slice(0, 3)}`
    if (d.length > 3) result += ` ${d.slice(3, 6)}`
    if (d.length > 6) result += `-${d.slice(6, 8)}`
    if (d.length > 8) result += `-${d.slice(8, 10)}`
    return result
  }
  return `+${group(digits, 3)}`
}

export function isValidPhone(value: string): boolean {
  const digits = value.replace(/\D/g, '').length
  return digits >= PHONE_MIN && digits <= PHONE_MAX
}

/** Телефон для показа: «+79161234567» → «+7 916 123-45-67»; некорректный — как есть. */
export function formatPhone(phone: string | null | undefined): string {
  if (!phone) return ''
  return isValidPhone(phone) ? formatPhoneInput(phone) : phone
}

/** Ссылка для звонка: только «+» и цифры. */
export function phoneHref(phone: string): string {
  return `tel:${phone.replace(/[^\d+]/g, '')}`
}

/** Ввод «телефон или email»: похоже на номер — форматируем как телефон. */
export function formatLoginInput(raw: string): string {
  return /^\+?[\d\s()-]+$/.test(raw) && /\d/.test(raw) ? formatPhoneInput(raw) : raw
}
