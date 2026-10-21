# monitoring — Cloudflare Worker: бэкапы и API

Работает на стороне Cloudflare, независимо от сервера: если сервер упал или cron не запустился,
мониторинг всё равно это заметит и напишет в Telegram. Код — [`worker.js`](worker.js), один файл без зависимостей.

Запускается каждые 5 минут (один Cron Trigger `*/5 * * * *`):

| Что | Когда проверяет | Когда пишет |
|---|---|---|
| API: `GET https://api.hashar.app/health` отвечает `{"db": 1}` | каждый запуск | API не отвечает две проверки подряд; API снова работает |
| Бэкап: последний файл в `hashar-backups/db/` | раз в сутки, в 05:00 UTC (10:00 Душанбе) | бэкапа нет дольше 26 ч или он вдвое меньше предыдущего; иначе — «✅ Бэкап в порядке» |

Отметка «сегодня бэкап проверен» хранится в R2 (`monitor/backup.json`), поэтому отчёт приходит один раз в сутки, сколько бы триггеров ни было.

Ежедневное «✅» — нарочно: если оно перестало приходить, сломался сам мониторинг. Выключить — `DAILY_REPORT=false`.

## 1. Telegram-бот

1. В Telegram написать [@BotFather](https://t.me/BotFather) → `/newbot` → имя и логин бота. Он пришлёт **токен** вида `123456:ABC...`
2. Открыть своего бота и отправить ему любое сообщение (иначе бот не может писать первым)
3. В браузере открыть `https://api.telegram.org/bot<ТОКЕН>/getUpdates` — в ответе `"chat":{"id":123456789,...}`. Это **chat id**.
   Для группы: добавить бота в группу, написать в ней сообщение — id группы начинается с минуса

## 2. Worker

Дашборд Cloudflare → **Compute (Workers) → Workers & Pages → Create → Worker → Start with Hello World**,
имя `hashar-monitor` → **Deploy**. Затем:

1. **Edit code** — заменить весь код содержимым `worker.js` → **Deploy**
2. **Settings → Bindings → Add → R2 bucket:** variable name `BACKUPS`, бакет `hashar-backups`.
   Worker читает бакет без ключей; удалить бэкапы не может — их держит блокировка бакета (`db/`).
   Своё состояние (упал ли API) он хранит там же, в `monitor/health.json`
3. **Settings → Variables and Secrets:**

   | Имя | Тип | Значение |
   |---|---|---|
   | `TELEGRAM_BOT_TOKEN` | **Secret** | токен от BotFather |
   | `TELEGRAM_CHAT_ID` | Text | chat id |
   | `API_HEALTH_URL` | Text | `https://api.hashar.app/health` |
   | `BACKUP_CHECK_HOUR_UTC` | Text | необязательно, по умолчанию `5` — час проверки бэкапа по UTC (бэкап на сервере — в 03:30 UTC) |
   | `BACKUP_MAX_AGE_HOURS` | Text | необязательно, по умолчанию `26` |
   | `DAILY_REPORT` | Text | необязательно; `false` — не присылать ежедневное «✅» |
   | `TIMEZONE` | Text | необязательно, по умолчанию `Asia/Dushanbe` — время в сообщениях |

4. **Settings → Trigger events → Add → Cron Triggers:** одно расписание — `*/5 * * * *`. Других не нужно: час проверки бэкапа задаёт `BACKUP_CHECK_HOUR_UTC`

## 3. Проверка

- **Бэкап:** временно поставить `BACKUP_CHECK_HOUR_UTC` равным текущему часу по UTC — в ближайшие 5 минут придёт «✅ Бэкап БД в порядке» (или 🔴 с причиной), один раз. Затем вернуть `5`. Если сегодня проверка уже была — удалить в бакете объект `monitor/backup.json`
- **API:** проверяется сам каждые 5 минут; сообщение придёт только при сбое. Убедиться, что проверка идёт, — **Observability → Logs** Worker'а
- Ничего не пришло — в **Observability → Logs** будет `Telegram 401` (неверный токен) или `400 chat not found` (неверный chat id или боту не написали первым)

Код обновляется так же: **Edit code** → вставить новый `worker.js` → **Deploy**. Бесплатного тарифа Workers и R2 хватает с большим запасом.
