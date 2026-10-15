// Проверка перед `cap copy` / `cap sync` (npm-хук capacitor:copy:before):
// в Android-приложение должна попасть сборка с продовым API (npm run build:android).
// Обычный `npm run build` берёт адрес из .env — http://localhost:8000, и запросы
// с телефона уходят «в себя»: приложение открывается, но до сервера ничего не доходит.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const webDir = process.env.CAPACITOR_WEB_DIR ?? 'dist'
const html = readFileSync(join(webDir, 'index.html'), 'utf8').replaceAll('&#39;', "'")
// Адрес API вшивается в CSP (vite.config.ts) — по нему и проверяем
const connectSrc = html.match(/connect-src ([^;"]*)/)?.[1] ?? ''
const apiUrl = connectSrc.replace("'self'", '').trim()

if (!apiUrl.startsWith('https://') || apiUrl.includes('localhost')) {
  console.error(
    `\n✖ В ${webDir}/ сборка с API "${apiUrl || 'не задан'}" — в Android-приложении он недоступен.\n` +
      '  Соберите через: npm run build:android\n',
  )
  process.exit(1)
}
console.log(`✓ API в сборке для Android: ${apiUrl}`)
