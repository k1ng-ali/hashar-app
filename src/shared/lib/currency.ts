export type Currency = 'tjs' | 'rub' | 'usd'

export const CURRENCIES: Currency[] = ['tjs', 'rub', 'usd']

// Знак валюты рядом с суммой
export const CURRENCY_SYMBOLS: Record<Currency, string> = {
  tjs: 'смн',
  rub: '₽',
  usd: '$',
}

