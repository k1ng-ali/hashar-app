# Ҳашар — платформа общих фондов

<p><img src="public/logo.svg" alt="Ҳашар" height="64" /></p>

Платформа прозрачных фондов для домов, ТСЖ и посёлков. Пользователь регистрируется, **создаёт свой фонд** (и становится председателем) или **находит фонд** по коду, ссылке-приглашению или названию и подаёт заявку — фонд становится доступен после одобрения советом. Внутри фонда: взносы с чеками, проверка советом, расходы, целевые сборы, **мультивалютные счета (TJS / RUB / USD)** с переводами между ними, доска объявлений и отчётность. Тарифы Free / Pro / Max / Individual ограничивают число участников и подтверждаются админом платформы.

```
Fund-system/
├── backend/      # FastAPI + async SQLAlchemy + PostgreSQL + Alembic   → backend/README.md
├── src/          # Vue 3 + TypeScript + Pinia + vue-router + vue-i18n
├── deploy/       # прод API: docker-compose.prod.yml, Caddyfile, update.sh, backup.sh
└── .github/workflows/
    ├── frontend.yml  # release → сборка → GitHub Pages (hashar.app)
    └── backend.yml   # release → тесты → образ в Docker Hub (api.hashar.app)
```

## Быстрый старт

```bash
# 1. База и API
cd backend
cp .env.example .env
docker compose up -d db
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload

# 2. Фронтенд (из корня проекта)
cp .env.example .env
npm install
npm run dev
```

- Приложение: http://localhost:5173 — в `VITE_DEV_MODE` на экране входа есть быстрый вход демо-пользователями
- Ссылка-приглашение: http://localhost:5173/join/STAR2026
- API: http://localhost:8000/api/v1, Swagger: http://localhost:8000/docs
- Пароль демо-пользователей: `password123`

## Продакшен

Ветки: `main` — разработка, `release` — деплой. Push в `release` запускает GitHub Actions:

```
release ─┬─ frontend.yml: npm run build ──────────────▶ GitHub Pages ── hashar.app
         └─ backend.yml:  pytest → docker build ──────▶ Docker Hub
                                                            │  ./update.sh на сервере
браузер ──HTTPS──▶ Cloudflare ──HTTPS (Origin CA)──▶ Caddy ─┴▶ backend ── api.hashar.app
```

Каждый workflow срабатывает только на свои файлы (`backend/**` или всё остальное); вручную — Actions → Run workflow.

### 1. GitHub (один раз)

- **Settings → Secrets and variables → Actions:** секреты `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN` (Docker Hub → Account settings → Personal access tokens, права Read & Write)
- **Settings → Pages:** Source — **GitHub Actions**, Custom domain — `hashar.app`, Enforce HTTPS — вкл. (галочка станет доступна, когда GitHub выпустит сертификат, обычно до часа). Pages для приватного репозитория — только на платном тарифе GitHub

### 2. Cloudflare (один раз)

- **DNS для фронтенда (GitHub Pages)** — **без проксирования** (серое облако, DNS only), иначе GitHub не сможет выпустить и продлевать сертификат:
  - `hashar.app` — четыре A-записи: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
  - `www` — CNAME на `<github-логин>.github.io` (GitHub сам перенаправит www → hashar.app)
- **DNS для API:** `api.hashar.app` — A-запись на IP сервера, **проксирование включено** (оранжевое облако)
- **SSL/TLS → Overview:** режим **Full (strict)**. Не Flexible: с ним Cloudflare ходит на сервер по http, а Caddy отправляет обратно на https — бесконечный редирект
- **SSL/TLS → Origin Server → Create Certificate:** RSA, хосты `hashar.app, *.hashar.app`, срок 15 лет. Сертификат сохранить на сервере в `deploy/certs/origin.pem`, ключ — в `deploy/certs/origin.key` (ключ показывается один раз; папка в `.gitignore`)
- **SSL/TLS → Edge Certificates:** Always Use HTTPS — вкл., Minimum TLS — 1.2

### 3. Сервер (один раз)

Нужны Docker и папка `deploy/` — проще всего клон репозитория (тогда `update.sh` сам подтягивает изменения compose и Caddyfile):

```bash
git clone <repo> /opt/hashar && cd /opt/hashar/deploy
cp .env.example .env        # BACKEND_IMAGE, SECRET_KEY (openssl rand -hex 32), DB_PASSWORD (openssl rand -hex 24)
mkdir certs                 # сюда origin.pem и origin.key из Cloudflare
chmod +x update.sh backup.sh
./update.sh
```

Если репозиторий образа в Docker Hub приватный — перед этим `docker login`.

Проверка: `https://api.hashar.app/health` → `{"db":1}`, `https://hashar.app` — экран входа.

### Выпуск версии

```bash
git checkout release && git merge main && git push    # Actions собирают фронт и образ
ssh <сервер> /opt/hashar/deploy/update.sh             # когда backend.yml закончился
```

`update.sh`: `git pull` конфигов → `docker compose pull` → `up -d` → ждёт, пока backend станет healthy. Миграции backend применяет сам при старте. Откат: `BACKEND_TAG=sha-<коммит> ./update.sh` (теги — в Docker Hub). Фронтенд откатывается повторным запуском старого успешного Frontend-workflow в Actions.

### Как устроено

- Caddy отвечает **только адресам Cloudflare** — прямой заход на IP сервера обрывается (иначе можно обойти защиту Cloudflare). Если выключить проксирование в Cloudflare, убрать `import cloudflare_only` в `deploy/Caddyfile`, иначе API перестанет отвечать
- реальный IP посетителя Caddy берёт из `CF-Connecting-IP` (только от Cloudflare) и передаёт backend — на нём держится лимит попыток входа и регистрации. Список адресов Cloudflare в `deploy/Caddyfile` сверять с https://www.cloudflare.com/ips раз в год
- фронтенд и API — поддомены одного сайта: refresh-cookie `SameSite=Lax; Secure` ставит `api.hashar.app`, CORS разрешён только `https://hashar.app`. Адрес API задан в `frontend.yml` и вшивается в сборку и в CSP — при смене поддомена API поменять его там
- GitHub Pages не даёт ставить заголовки, поэтому CSP — `<meta>` в `index.html`, его добавляет плагин в `vite.config.ts` при сборке. Через `<meta>` нельзя запретить встраивание сайта во фрейм (`frame-ancestors`)
- SPA на Pages: workflow копирует `index.html` в `404.html`, поэтому прямые ссылки вида `/join/CODE` открываются (со статусом 404 — для приложения это не важно)
- backend при старте применяет миграции; `DEV_MODE=false`: нет `/docs`, демо-входа, демо-чеков и seed, а со слабым `SECRET_KEY` backend не запустится
- логи контейнеров ротируются (5 × 10 МБ на сервис): `docker compose -f docker-compose.prod.yml logs -f backend`
- первый админ платформы назначается вручную после регистрации:
  `docker compose -f docker-compose.prod.yml exec db psql -U <DB_USER> <DB_NAME> -c "update users set is_platform_admin = true where phone = '+992...'"`
- бэкап БД — `deploy/backup.sh` по cron (хранит 14 дней на этом же сервере — копии стоит регулярно уносить в другое место)
- проверить прод-сборку фронта локально: `VITE_API_URL=https://api.hashar.app npm run build && npm run preview`

## Сценарии

1. **Вступление.** Регистрация → «Мои фонды» → «Найти» по коду / названию (или ссылка `/join/<код>`) → заявка с помещением → совет принимает во вкладке «Участники» (с учётом лимита тарифа) → фонд появляется в переключателе.
2. **Создание фонда.** «Мои фонды» → «Создать»: название, адрес, базовая валюта, дополнительные счета, ежемесячный взнос → создатель становится председателем, код и ссылка — в «Админ → Настройки». Права председателя можно передать.
3. **Валюты.** У фонда счёт на каждую включённую валюту, остатки показываются отдельно. Реквизит для оплаты привязан к валюте; при взносе участник выбирает любой реквизит — от него берётся валюта. Ежемесячный взнос и долги считаются в базовой валюте, целевой сбор — в своей: при оплате в другой валюте участник указывает, сколько зачесть, совет сверяет при проверке. Тариф взноса хранится по месяцам — изменение действует с 1-го числа следующего месяца и не пересчитывает прошлое. Перевод между счетами (или корректировка) вводится вручную с обеими суммами и автоматически публикуется в объявлениях.
4. **Тарифы.** Председатель отправляет заявку или продление с контактом для связи → админ платформы (`/platform`) видит совет фонда с контактами и включает тариф на N месяцев после оплаты.
5. **Чеки.** Совет проверяет очередь и ведёт историю чеков: фильтры по статусу, валюте, реквизиту и поиск по участнику, итоги по валютам. Реквизиты фонда — во вкладке «Счета».

## Frontend

**Стек:** Vue 3.5 (`<script setup lang="ts">`) · Vite · TypeScript strict · Pinia (setup-сторы) · vue-router (lazy-маршруты) · vue-i18n (ru / tg / en) · axios · ant-design-vue · SCSS scoped · иконки `@kalimahapps/vue-icons`

```
src/
├── main.ts                    # createApp → pinia → i18n → router → mount
├── App.vue                    # splash, auth-гейт, <Header/> <router-view :key=fundId/> <Navigator/>
├── app/router.ts              # маршруты + guard: вход, выбранный фонд, совет, админ платформы
├── pages/<Name>Page/
│   ├── LoginPage              # вход / регистрация / провайдеры (скоро)
│   ├── FundsPage, JoinPage    # мои фонды, создать, найти, вступление по ссылке
│   ├── DashboardPage          # остаток, «Требует внимания», быстрые действия, операции
│   ├── FinancePage            # /finance/*: HistoryPage (мои), ExpensesPage, TargetFundsPage, ReportsPage
│   ├── ContributePage, TargetFundPage, AnnouncementsPage
│   ├── FundPage               # /fund: карточка фонда, меню управления и общее
│   ├── FundReceiptsPage, FundMembersPage, FundAccountsPage, FundSettingsPage  # /fund/* — совет
│   └── PlatformAdminPage      # админ платформы: заявки на тарифы, фонды
├── features/
│   ├── auth/                  # регистрация, вход, refresh-cookie
│   ├── funds/                 # мои фонды, текущий фонд, права в фонде, создание/поиск/вступление, тариф
│   ├── dashboard/             # сводка по валютам, лента операций, реквизиты
│   ├── contributions/         # взносы, сальдо, форма (composables/useContributionForm)
│   ├── targetFunds/, announcements/, reports/
│   ├── expenses/              # лента расходов, карточка расхода
│   ├── admin/                 # действия совета (composables/useAdminFlow, useFundSubpage)
│   ├── platformAdmin/         # админ платформы
│   ├── header/                # шапка, переключатель фондов, профиль
│   └── navigator/             # таб-бар: Главная · Финансы · «+» · Новости · Фонд; сайдбар с подразделами
└── shared/
    ├── api/http.ts            # axios + Bearer + refresh с очередью запросов
    ├── i18n/                  # ru.ts, tg.ts, en.ts
    ├── stores/                # useHeaderStore, useNavStore, useReceiptStore
    ├── components/            # BottomSheet, PillTabs, ReceiptPicker, ReceiptViewer, ...
    └── lib/                   # format (деньги с валютой), currency, browser, receiptGenerator
```

Все запросы фонда идут через `useFundsStore().fundId`; при переключении фонда страница пересоздаётся и загружает данные заново.

```bash
npm run build     # vue-tsc -b && vite build
npm run preview   # посмотреть сборку локально (деплой — push в release)
```
