import { i18n } from '@/shared/i18n/index.ts'
import { CURRENCY_SYMBOLS, type Currency } from './currency.ts'

const LOCALE_TAGS: Record<string, string> = {
  ru: 'ru-RU',
  tg: 'ru-RU', // у Intl нет нормальной tg-локали для дат — числа и даты как в ru
  en: 'en-GB',
}

function localeTag() {
  return LOCALE_TAGS[i18n.global.locale.value] ?? 'ru-RU'
}

/** (1500, 'rub') → «1 500 ₽»; withSign — «+» для положительных сумм */
export function formatMoney(amount: number, currency: Currency, withSign = false): string {
  const sign = withSign && amount > 0 ? '+' : ''
  return `${sign}${amount.toLocaleString('ru-RU')} ${CURRENCY_SYMBOLS[currency]}`
}

/** ISO → «05.09.2026, 14:22» */
export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString(localeTag(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** ISO → «05.09.2026» */
export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(localeTag(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** «2026-09» → «Сентябрь 2026» (short: «Сен») */
export function formatPeriod(period: string | null | undefined, short = false): string {
  if (!period) return '—'
  const [year, month] = period.split('-')
  const key = `${short ? 'monthsShort' : 'months'}.m${Number(month)}`
  return short ? i18n.global.t(key) : `${i18n.global.t(key)} ${year}`
}

/** Имя для приветствия: «Иван Петров» → «Иван» */
export function firstName(fullName: string): string {
  return fullName.split(' ')[0] ?? fullName
}
