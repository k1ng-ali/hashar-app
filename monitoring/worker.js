/**
 * Мониторинг Ҳашар — Cloudflare Worker по расписанию, независимый от сервера.
 *
 * Одно расписание — каждые 5 минут (Cron Trigger "*\/5 * * * *"). При каждом запуске:
 *   API     — GET API_HEALTH_URL. Сообщение в Telegram, когда API упал (две проверки подряд —
 *             разовый сбой сети не в счёт) и когда поднялся
 *   бэкап   — раз в сутки, в час BACKUP_CHECK_HOUR_UTC: свежий файл в бакете бэкапов (db/)
 *             не старше BACKUP_MAX_AGE_HOURS и не меньше половины предыдущего (пустой или обрезанный дамп).
 *             Если всё хорошо — короткий отчёт: молчание самого мониторинга тоже заметно.
 *             Отметка «сегодня проверено» — в R2, поэтому отчёт один, сколько бы раз Worker ни запустился
 *
 * Привязки и переменные — monitoring/README.md.
 */

// Состояние между запусками. Лежит в том же бакете, но не в db/ — блокировка бэкапов его не держит
const HEALTH_STATE_KEY = 'monitor/health.json'
const BACKUP_STATE_KEY = 'monitor/backup.json'
const FAILURES_BEFORE_ALERT = 2
const HEALTH_TIMEOUT_MS = 10_000

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(Promise.all([checkHealth(env), dailyBackupCheck(env, new Date(event.scheduledTime))]))
  },

  // Снаружи Worker ничего не делает: проверка — README → «Проверка»
  async fetch() {
    return new Response('Not found', { status: 404 })
  },
}

// ── Бэкапы ──────────────────────────────────────────────────────────────────

async function dailyBackupCheck(env, now) {
  if (now.getUTCHours() !== Number(env.BACKUP_CHECK_HOUR_UTC ?? 5)) return
  const today = now.toISOString().slice(0, 10)
  if ((await readJson(env.BACKUPS, BACKUP_STATE_KEY))?.checked === today) return
  await checkBackups(env)
  // Отметка — после отправки: не дошло сообщение (Telegram недоступен) — повтор через 5 минут
  await env.BACKUPS.put(BACKUP_STATE_KEY, JSON.stringify({ checked: today }))
}

async function checkBackups(env) {
  const backups = await listBackups(env.BACKUPS)
  const maxAgeHours = Number(env.BACKUP_MAX_AGE_HOURS || 26)

  if (backups.length === 0) {
    await notify(env, '🔴 Бэкапов в R2 нет совсем (hashar-backups/db/)')
    return
  }

  const [latest, previous] = backups
  const ageHours = (Date.now() - latest.uploaded.getTime()) / 3_600_000
  const problems = []
  if (ageHours > maxAgeHours) {
    problems.push(`последний бэкап ${Math.floor(ageHours)} ч назад (норма — до ${maxAgeHours} ч)`)
  }
  if (previous && latest.size < previous.size / 2) {
    problems.push(`последний бэкап ${formatSize(latest.size)} — вдвое меньше предыдущего (${formatSize(previous.size)})`)
  }

  const summary = `${latest.key.replace('db/', '')}, ${formatSize(latest.size)}, ${formatTime(latest.uploaded, env)}`
  if (problems.length) {
    await notify(env, `🔴 Бэкап БД: ${problems.join('; ')}\nПоследний: ${summary}\nЛог на сервере: deploy/backups/backup.log`)
  } else if (env.DAILY_REPORT !== 'false') {
    await notify(env, `✅ Бэкап БД в порядке: ${summary} (копий в R2: ${backups.length})`)
  }
}

/** Все копии из db/, новые первыми. */
async function listBackups(bucket) {
  const objects = []
  let cursor
  do {
    const page = await bucket.list({ prefix: 'db/', cursor })
    objects.push(...page.objects)
    cursor = page.truncated ? page.cursor : undefined
  } while (cursor)
  return objects.sort((a, b) => b.uploaded - a.uploaded)
}

// ── API ─────────────────────────────────────────────────────────────────────

async function checkHealth(env) {
  const error = await probe(env.API_HEALTH_URL)
  const state = (await readJson(env.BACKUPS, HEALTH_STATE_KEY)) ?? { failures: 0, alerted: false }
  const before = JSON.stringify(state)

  if (error) {
    state.failures += 1
    state.since ??= new Date().toISOString()
    if (state.failures >= FAILURES_BEFORE_ALERT && !state.alerted) {
      await notify(env, `🔴 API не отвечает: ${error}\n${env.API_HEALTH_URL}`)
      state.alerted = true
    }
  } else {
    if (state.alerted) {
      const minutes = Math.round((Date.now() - Date.parse(state.since)) / 60_000)
      await notify(env, `✅ API снова работает (был недоступен ~${minutes} мин)`)
    }
    state.failures = 0
    state.alerted = false
    delete state.since
  }
  // Пишем только при изменении: пока API здоров, запусков каждые 5 минут — ноль записей в R2
  if (JSON.stringify(state) !== before) await env.BACKUPS.put(HEALTH_STATE_KEY, JSON.stringify(state))
}

/** null — API здоров, иначе текст ошибки. /health отвечает {"db": 1}, если и backend, и база живы. */
async function probe(url) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS) })
    if (!response.ok) return `HTTP ${response.status}`
    const body = await response.json().catch(() => null)
    return body?.db === 1 ? null : `неожиданный ответ ${JSON.stringify(body)}`
  } catch (error) {
    return error.name === 'TimeoutError' ? `нет ответа за ${HEALTH_TIMEOUT_MS / 1000} с` : String(error)
  }
}

async function readJson(bucket, key) {
  const object = await bucket.get(key)
  return object ? object.json() : null
}

// ── Telegram ────────────────────────────────────────────────────────────────

async function notify(env, text) {
  const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text, disable_web_page_preview: true }),
  })
  // Ошибку видно в логах Worker'а (Observability): неверный токен или chat id
  if (!response.ok) throw new Error(`Telegram ${response.status}: ${await response.text()}`)
}

function formatSize(bytes) {
  return bytes < 1024 * 1024 ? `${Math.round(bytes / 1024)} КБ` : `${(bytes / 1024 / 1024).toFixed(1)} МБ`
}

function formatTime(date, env) {
  return date.toLocaleString('ru-RU', { timeZone: env.TIMEZONE || 'Asia/Dushanbe', dateStyle: 'short', timeStyle: 'short' })
}
