/**
 * Генерирует реалистичный SVG-чек (data URL) — для демо и быстрого теста проверки чеков.
 */
import { CURRENCY_SYMBOLS, type Currency } from './currency.ts'

export interface ReceiptParams {
  bankName: string
  amount: number
  currency: Currency
  senderName: string
  recipientName: string
  purpose: string
}

function escapeXml(value: string): string {
  return value.replace(/[<>&'"]/g, (char) => `&#${char.charCodeAt(0)};`)
}

export function generateReceiptSvg(params: ReceiptParams): string {
  const amount = `${params.amount.toLocaleString('ru-RU')} ${CURRENCY_SYMBOLS[params.currency]}`
  const date = new Date().toLocaleString('ru-RU')
  const transactionId = `TX-${Math.floor(100000000 + Math.random() * 900000000)}`
  const font = "font-family='Manrope, Segoe UI, Roboto, sans-serif'"

  const row = (y: number, label: string, value: string) => `
    <text x='40' y='${y}' ${font} font-size='12' fill='#6B7280'>${escapeXml(label)}</text>
    <text x='380' y='${y}' text-anchor='end' ${font} font-size='12' font-weight='600' fill='#1F2937'>${escapeXml(value)}</text>`

  const svg = `
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 420 560'>
  <defs>
    <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#4EBEC2'/>
      <stop offset='100%' stop-color='#234970'/>
    </linearGradient>
  </defs>
  <rect x='10' y='10' width='400' height='540' rx='20' fill='#ffffff' stroke='#E5E7EB'/>
  <path d='M10 30 Q10 10 30 10 L390 10 Q410 10 410 30 L410 96 L10 96 Z' fill='url(#g)'/>
  <circle cx='48' cy='53' r='18' fill='rgba(255,255,255,0.25)'/>
  <path d='M41 53 L46 58 L56 48' stroke='#fff' stroke-width='3' fill='none' stroke-linecap='round'/>
  <text x='78' y='49' ${font} font-size='15' font-weight='700' fill='#fff'>${escapeXml(params.bankName)}</text>
  <text x='78' y='68' ${font} font-size='11' fill='rgba(255,255,255,0.85)'>Чек по операции</text>
  <text x='210' y='146' text-anchor='middle' ${font} font-size='12' fill='#6B7280'>Сумма перевода</text>
  <text x='210' y='186' text-anchor='middle' ${font} font-size='32' font-weight='800' fill='#234970'>${amount}</text>
  <rect x='150' y='204' width='120' height='26' rx='13' fill='#D1FAE5'/>
  <text x='210' y='221' text-anchor='middle' ${font} font-size='11' font-weight='700' fill='#047857'>ИСПОЛНЕН</text>
  <line x1='34' y1='250' x2='386' y2='250' stroke='#E5E7EB' stroke-dasharray='6 4'/>
  ${row(284, 'Дата и время', date)}
  ${row(318, 'Отправитель', params.senderName)}
  ${row(352, 'Получатель', params.recipientName)}
  ${row(386, 'Назначение', params.purpose)}
  ${row(420, 'Документ', transactionId)}
  <text x='210' y='520' text-anchor='middle' ${font} font-size='10' fill='#9CA3AF'>Сформировано онлайн · Фонд дома</text>
</svg>`.trim()

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}
