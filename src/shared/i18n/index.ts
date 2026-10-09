import { createI18n } from 'vue-i18n'
import ru from './locales/ru.ts'
import tg from './locales/tg.ts'
import en from './locales/en.ts'

export type AppLocale = 'ru' | 'tg' | 'en'

export const LOCALES: { code: AppLocale; label: string }[] = [
  { code: 'ru', label: 'Русский' },
  { code: 'tg', label: 'Тоҷикӣ' },
  { code: 'en', label: 'English' },
]

const STORAGE_KEY = 'fund.locale'

function savedLocale(): AppLocale {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    if (value === 'ru' || value === 'tg' || value === 'en') return value
  } catch {
    // localStorage может быть недоступен (приватный режим)
  }
  return 'ru'
}

export const i18n = createI18n({
  legacy: false,
  locale: savedLocale(),
  fallbackLocale: 'ru',
  messages: { ru, tg, en },
})

export function setLocale(locale: AppLocale) {
  i18n.global.locale.value = locale
  document.documentElement.lang = locale
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // не критично
  }
}
