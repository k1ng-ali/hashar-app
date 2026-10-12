# Фонд дома — платформа

Платформа прозрачных фондов для домов, ТСЖ и посёлков. Пользователь регистрируется, **создаёт свой фонд** (и становится председателем) или **находит фонд** по коду, ссылке-приглашению или названию и подаёт заявку — фонд становится доступен после одобрения советом. Внутри фонда: взносы с чеками, проверка советом, расходы, целевые сборы, **мультивалютные счета (TJS / RUB / USD)** с переводами между ними, доска объявлений и отчётность. Тарифы Free / Pro / Max / Individual ограничивают число участников и подтверждаются админом платформы.

```
Fund-system/
├── backend/      # FastAPI + async SQLAlchemy + PostgreSQL + Alembic   → backend/README.md
└── src/          # Vue 3 + TypeScript + Pinia + vue-router + vue-i18n
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
npm run deploy    # сборка + gh-pages
```
