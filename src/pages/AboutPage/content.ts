// src/pages/AboutPage/content.ts
// Публичная страница «О проекте» (главная сайта для гостей; её же видит проверка бренда Google).
// Лимиты тарифов должны совпадать с backend/app/enums/plan.py, цены Pro и Max приходят с сервера, обещания о данных — с политикой конфиденциальности.
import type { Plan } from '@/features/funds/types.ts'
import type { AppLocale } from '@/shared/i18n/index.ts'

interface Card {
  icon: string
  title: string
  text: string
}

export interface AboutContent {
  nav: { login: string; open: string }
  hero: { badge: string; title: string; lead: string; start: string; login: string; open: string }
  demo: {
    caption: string
    fund: string
    balance: string
    balanceValue: string
    paid: string
    paidValue: string
    rows: { title: string; meta: string; amount: string; kind: 'in' | 'out' }[]
  }
  audience: { title: string; items: Card[] }
  steps: { title: string; items: { title: string; text: string }[] }
  features: { title: string; items: Card[] }
  trust: { title: string; lead: string; items: string[]; link: string }
  plans: {
    title: string
    lead: string
    // price пуст у Pro и Max — их цену задаёт админ платформы, она приходит с сервера
    items: { plan: Plan; name: string; limit: string; price?: string; note: string }[]
    payment: string
  }
  faq: { title: string; items: { q: string; a: string }[] }
  final: { title: string; text: string; cta: string }
  footer: { about: string; contact: string }
}

export const ABOUT: Record<AppLocale, AboutContent> = {
  ru: {
    nav: { login: 'Войти', open: 'Открыть' },
    hero: {
      badge: 'Для домов, махалли и посёлков',
      title: 'Общий фонд, в котором видно каждый сомони',
      lead:
        'Ҳашар — сервис для учёта общих денег соседей. Жители отправляют взносы с фото чека, совет фонда подтверждает их и публикует расходы с документами, а отчёты и долги каждый видит сам — без тетрадей, таблиц и споров.',
      start: 'Создать фонд бесплатно',
      login: 'Войти',
      open: 'Открыть приложение',
    },
    demo: {
      caption: 'Так выглядит фонд в приложении (пример)',
      fund: 'Дом 12, ул. Рудаки',
      balance: 'Баланс фонда',
      balanceValue: '12 450 смн',
      paid: 'Оплатили за октябрь',
      paidValue: '38 из 42',
      rows: [
        { title: 'Взнос · кв. 17', meta: 'Чек подтверждён', amount: '+150 смн', kind: 'in' },
        { title: 'Ремонт крыши', meta: 'Расход · 2 документа', amount: '−4 200 смн', kind: 'out' },
        { title: 'Сбор на детскую площадку', meta: '68% собрано', amount: '+300 смн', kind: 'in' },
      ],
    },
    audience: {
      title: 'Для кого',
      items: [
        { icon: '🏢', title: 'Многоквартирные дома', text: 'Ежемесячные взносы на уборку, лифт, освещение и ремонт подъездов.' },
        { icon: '🏘️', title: 'Махалли и посёлки', text: 'Общие дела: дороги, вода, освещение улиц, помощь соседям и общие мероприятия.' },
        { icon: '🤝', title: 'Сообщества', text: 'Землячества, родительские комитеты, любые группы с общей кассой.' },
      ],
    },
    steps: {
      title: 'Как это работает',
      items: [
        { title: 'Создайте фонд', text: 'Укажите название, адрес и ежемесячный взнос. Вы становитесь председателем, приглашение — по ссылке или коду фонда.' },
        { title: 'Соседи вступают', text: 'Жители находят фонд по коду, указывают квартиру или дом. Совет подтверждает заявки.' },
        { title: 'Взносы с чеками', text: 'Участник переводит деньги на реквизиты фонда и прикладывает чек. Совет проверяет и зачисляет — долг пересчитывается сам.' },
        { title: 'Открытые расходы', text: 'Каждый расход публикуется с суммой, категорией и документами. Отчёт за месяц видят все участники.' },
      ],
    },
    features: {
      title: 'Что умеет Ҳашар',
      items: [
        { icon: '🧾', title: 'Взносы с чеками', text: 'Фото или скриншот перевода, проверка советом, история по каждому участнику.' },
        { icon: '📉', title: 'Долги и авансы', text: 'Начисления по месяцам считаются автоматически, переплата переходит на следующие месяцы.' },
        { icon: '📢', title: 'Расходы и новости', text: 'Лента расходов с документами, объявления и экстренные контакты для всего фонда.' },
        { icon: '🎯', title: 'Целевые сборы', text: 'Сбор на конкретную цель с прогрессом: ремонт, площадка, помощь соседу.' },
        { icon: '💱', title: 'Несколько валют', text: 'Счета в TJS, RUB и USD — каждый со своим балансом, переводы между ними видны всем.' },
        { icon: '👥', title: 'Совет фонда', text: 'Председатель и ревизоры, журнал их действий, блокировка и выход участников без потери истории.' },
      ],
    },
    trust: {
      title: 'Деньги и данные',
      lead: 'Ҳашар не принимает и не хранит деньги: взносы переводятся напрямую на реквизиты фонда, сервис только ведёт учёт.',
      items: [
        'Данные фонда видят только его участники; чеки других жителей видит только совет.',
        'Без рекламы, трекеров и продажи данных.',
        'Соединение только по HTTPS, пароли хранятся в виде хеша, вход можно отозвать на всех устройствах.',
        'Аккаунт можно удалить в любой момент прямо в приложении.',
      ],
      link: 'Политика конфиденциальности',
    },
    plans: {
      title: 'Тарифы',
      lead: 'Тариф выбирается для фонда, а не для каждого жителя. Участники ничего не платят платформе.',
      items: [
        { plan: 'free', name: 'Free', limit: 'до 10 участников', price: 'Бесплатно', note: 'Все функции, без ограничения по времени' },
        { plan: 'pro', name: 'Pro', limit: 'до 100 участников', note: 'Для дома или небольшой махалли' },
        { plan: 'max', name: 'Max', limit: 'до 500 участников', note: 'Для крупных махалли и посёлков' },
        { plan: 'individual', name: 'Индивидуальный', limit: 'свой лимит', price: 'По договорённости', note: 'Для больших сообществ и объединений' },
      ],
      payment:
        'Платный тариф подключает председатель: отправляет заявку в приложении, администратор связывается для оплаты и включает тариф. При смене тарифа оплаченный остаток не сгорает.',
    },
    faq: {
      title: 'Вопросы',
      items: [
        { q: 'Ҳашар хранит деньги фонда?', a: 'Нет. Деньги переводятся на карты и счета, которые указал совет фонда. Ҳашар — это учёт: кто, сколько и за что заплатил и куда ушли деньги.' },
        { q: 'Кто подтверждает взносы?', a: 'Совет фонда — председатель и ревизоры. Они видят чек, сверяют поступление и зачисляют взнос. Пока взнос не подтверждён, долг не уменьшается.' },
        { q: 'Можно состоять в нескольких фондах?', a: 'Да. Например, в фонде дома и в фонде махалли — переключение в одно касание.' },
        { q: 'Как войти?', a: 'По телефону или email с паролем либо через Google. Есть сайт hashar.app и приложение для Android.' },
        { q: 'Что будет с записями, если житель удалит аккаунт?', a: 'Его личные данные стираются, а взносы и расходы остаются в отчётах фонда обезличенными — иначе отчётность не сойдётся.' },
      ],
    },
    final: {
      title: 'Начните с бесплатного фонда',
      text: 'До 10 участников — бесплатно и без срока. Создание фонда занимает пару минут.',
      cta: 'Создать фонд',
    },
    footer: { about: 'Прозрачный учёт общего фонда дома, махалли или посёлка.', contact: 'Поддержка' },
  },

  tg: {
    nav: { login: 'Ворид шудан', open: 'Кушодан' },
    hero: {
      badge: 'Барои биноҳо, маҳаллаҳо ва деҳаҳо',
      title: 'Фонди умумӣ, ки ҳар як сомониаш намоён аст',
      lead:
        'Ҳашар — хизматрасонӣ барои ҳисоби пули умумии ҳамсояҳо. Сокинон саҳмро бо акси чек мефиристанд, шӯрои фонд онро тасдиқ мекунад ва хароҷотро бо ҳуҷҷатҳо нашр менамояд, ҳисобот ва қарзҳоро ҳар кас худаш мебинад — бе дафтар, ҷадвал ва баҳс.',
      start: 'Фондро ройгон созед',
      login: 'Ворид шудан',
      open: 'Барномаро кушодан',
    },
    demo: {
      caption: 'Фонд дар барнома чунин менамояд (намуна)',
      fund: 'Бинои 12, кӯчаи Рӯдакӣ',
      balance: 'Тавозуни фонд',
      balanceValue: '12 450 смн',
      paid: 'Барои октябр пардохтанд',
      paidValue: '38 аз 42',
      rows: [
        { title: 'Саҳм · ҳуҷраи 17', meta: 'Чек тасдиқ шуд', amount: '+150 смн', kind: 'in' },
        { title: 'Таъмири бом', meta: 'Хароҷот · 2 ҳуҷҷат', amount: '−4 200 смн', kind: 'out' },
        { title: 'Ҷамъоварӣ барои майдончаи кӯдакон', meta: '68% ҷамъ шуд', amount: '+300 смн', kind: 'in' },
      ],
    },
    audience: {
      title: 'Барои кӣ',
      items: [
        { icon: '🏢', title: 'Биноҳои бисёрошёна', text: 'Саҳмҳои моҳона барои тозакунӣ, лифт, равшанӣ ва таъмири даромадгоҳҳо.' },
        { icon: '🏘️', title: 'Маҳаллаҳо ва деҳаҳо', text: 'Корҳои умумӣ: роҳ, об, равшании кӯчаҳо, ёрӣ ба ҳамсояҳо, тӯй ва маъракаҳо.' },
        { icon: '🤝', title: 'Ҷамъиятҳо', text: 'Ҳамдиёрон, кумитаҳои волидайн, ҳар гурӯҳе, ки хазинаи умумӣ дорад.' },
      ],
    },
    steps: {
      title: 'Чӣ тавр кор мекунад',
      items: [
        { title: 'Фонд созед', text: 'Ном, суроға ва саҳми моҳонаро нишон диҳед. Шумо раис мешавед, даъват — бо пайванд ё рамзи фонд.' },
        { title: 'Ҳамсояҳо ҳамроҳ мешаванд', text: 'Сокинон фондро бо рамз меёбанд ва ҳуҷра ё хонаашонро нишон медиҳанд. Шӯро аризаҳоро тасдиқ мекунад.' },
        { title: 'Саҳм бо чек', text: 'Иштирокчӣ пулро ба реквизитҳои фонд мегузаронад ва чекро замима мекунад. Шӯро месанҷад ва ворид мекунад — қарз худ аз нав ҳисоб мешавад.' },
        { title: 'Хароҷоти кушод', text: 'Ҳар хароҷот бо маблағ, категория ва ҳуҷҷатҳо нашр мешавад. Ҳисоботи моҳонаро ҳамаи иштирокчиён мебинанд.' },
      ],
    },
    features: {
      title: 'Ҳашар чӣ кор карда метавонад',
      items: [
        { icon: '🧾', title: 'Саҳм бо чек', text: 'Акс ё скриншоти интиқол, санҷиши шӯро, таърих барои ҳар иштирокчӣ.' },
        { icon: '📉', title: 'Қарз ва пешпардохт', text: 'Ҳисобкунии моҳона худкор аст, пардохти зиёдатӣ ба моҳҳои оянда мегузарад.' },
        { icon: '📢', title: 'Хароҷот ва хабарҳо', text: 'Тасмаи хароҷот бо ҳуҷҷатҳо, эълонҳо ва тамосҳои фаврӣ барои тамоми фонд.' },
        { icon: '🎯', title: 'Ҷамъовариҳои мақсаднок', text: 'Ҷамъоварӣ барои мақсади мушаххас бо пешрафт: таъмир, майдонча, ёрӣ ба ҳамсоя.' },
        { icon: '💱', title: 'Якчанд асъор', text: 'Ҳисобҳо бо TJS, RUB ва USD — ҳар кадом бо тавозуни худ, интиқолҳо ба ҳама намоёнанд.' },
        { icon: '👥', title: 'Шӯрои фонд', text: 'Раис ва тафтишгарон, дафтари амалҳои онҳо, манъ ва баромади иштирокчиён бе гум шудани таърих.' },
      ],
    },
    trust: {
      title: 'Пул ва маълумот',
      lead: 'Ҳашар пулро қабул намекунад ва нигоҳ намедорад: саҳмҳо мустақиман ба реквизитҳои фонд гузаронида мешаванд, хизматрасонӣ танҳо ҳисоб мебарад.',
      items: [
        'Маълумоти фондро танҳо иштирокчиёни он мебинанд; чеки сокинони дигарро танҳо шӯро мебинад.',
        'Бе реклама, трекерҳо ва фурӯши маълумот.',
        'Пайвастшавӣ танҳо тавассути HTTPS, паролҳо ҳамчун хеш нигоҳ дошта мешаванд, воридшавиро дар ҳамаи дастгоҳҳо бекор кардан мумкин аст.',
        'Аккаунтро ҳар вақт мустақиман дар барнома нест кардан мумкин аст.',
      ],
      link: 'Сиёсати махфият',
    },
    plans: {
      title: 'Тарифҳо',
      lead: 'Тариф барои фонд интихоб мешавад, на барои ҳар сокин. Иштирокчиён ба платформа чизе намепардозанд.',
      items: [
        { plan: 'free', name: 'Free', limit: 'то 10 иштирокчӣ', price: 'Ройгон', note: 'Ҳамаи имкониятҳо, бе маҳдудияти вақт' },
        { plan: 'pro', name: 'Pro', limit: 'то 100 иштирокчӣ', note: 'Барои бино ё маҳаллаи хурд' },
        { plan: 'max', name: 'Max', limit: 'то 500 иштирокчӣ', note: 'Барои маҳаллаҳо ва деҳаҳои калон' },
        { plan: 'individual', name: 'Инфиродӣ', limit: 'маҳдудияти худ', price: 'Бо мувофиқа', note: 'Барои ҷамъиятҳо ва иттиҳодияҳои калон' },
      ],
      payment:
        'Тарифи пулакиро раис пайваст мекунад: дар барнома ариза мефиристад, маъмур барои пардохт тамос мегирад ва тарифро фаъол мекунад. Ҳангоми иваз кардани тариф бақияи пардохтшуда нест намешавад.',
    },
    faq: {
      title: 'Саволҳо',
      items: [
        { q: 'Ҳашар пули фондро нигоҳ медорад?', a: 'Не. Пул ба корт ва ҳисобҳое гузаронида мешавад, ки шӯрои фонд нишон додааст. Ҳашар — ин ҳисоб аст: кӣ, чӣ қадар ва барои чӣ пардохт ва пул ба куҷо рафт.' },
        { q: 'Саҳмро кӣ тасдиқ мекунад?', a: 'Шӯрои фонд — раис ва тафтишгарон. Онҳо чекро мебинанд, воридшавиро месанҷанд ва саҳмро ворид мекунанд. То тасдиқ қарз кам намешавад.' },
        { q: 'Дар якчанд фонд будан мумкин аст?', a: 'Ҳа. Масалан, дар фонди бино ва фонди маҳалла — гузариш бо як ламс.' },
        { q: 'Чӣ тавр ворид шавам?', a: 'Бо телефон ё email ва парол ё тавассути Google. Сайти hashar.app ва барнома барои Android мавҷуд аст.' },
        { q: 'Агар сокин аккаунташро нест кунад, сабтҳо чӣ мешаванд?', a: 'Маълумоти шахсии ӯ пок мешавад, саҳмҳо ва хароҷот дар ҳисоботи фонд беному нишон боқӣ мемонанд — вагарна ҳисобот мувофиқ намеояд.' },
      ],
    },
    final: {
      title: 'Аз фонди ройгон оғоз кунед',
      text: 'То 10 иштирокчӣ — ройгон ва бе мӯҳлат. Сохтани фонд ду-се дақиқа вақт мегирад.',
      cta: 'Фонд созед',
    },
    footer: { about: 'Ҳисоби шаффофи фонди умумии бино, маҳалла ё деҳа.', contact: 'Дастгирӣ' },
  },

  en: {
    nav: { login: 'Sign in', open: 'Open' },
    hero: {
      badge: 'For apartment buildings, mahallas and villages',
      title: 'A shared fund where every somoni is visible',
      lead:
        'Hashar is a service for keeping track of neighbours’ shared money. Residents submit contributions with a photo of the receipt, the fund council confirms them and publishes expenses with documents, and everyone sees reports and debts for themselves — no notebooks, spreadsheets or arguments.',
      start: 'Create a fund for free',
      login: 'Sign in',
      open: 'Open the app',
    },
    demo: {
      caption: 'What a fund looks like in the app (example)',
      fund: 'Building 12, Rudaki St.',
      balance: 'Fund balance',
      balanceValue: '12,450 TJS',
      paid: 'Paid for October',
      paidValue: '38 of 42',
      rows: [
        { title: 'Contribution · apt 17', meta: 'Receipt confirmed', amount: '+150 TJS', kind: 'in' },
        { title: 'Roof repair', meta: 'Expense · 2 documents', amount: '−4,200 TJS', kind: 'out' },
        { title: 'Playground campaign', meta: '68% collected', amount: '+300 TJS', kind: 'in' },
      ],
    },
    audience: {
      title: 'Who it’s for',
      items: [
        { icon: '🏢', title: 'Apartment buildings', text: 'Monthly contributions for cleaning, the lift, lighting and stairwell repairs.' },
        { icon: '🏘️', title: 'Mahallas and villages', text: 'Shared matters: roads, water, street lights, helping neighbours, weddings and gatherings.' },
        { icon: '🤝', title: 'Communities', text: 'Diaspora groups, parent committees — any group with a shared cash box.' },
      ],
    },
    steps: {
      title: 'How it works',
      items: [
        { title: 'Create a fund', text: 'Set the name, address and monthly fee. You become the chairman; invite people with a link or the fund code.' },
        { title: 'Neighbours join', text: 'Residents find the fund by its code and enter their apartment or house. The council approves requests.' },
        { title: 'Contributions with receipts', text: 'A member transfers money to the fund’s account and attaches the receipt. The council checks and credits it — debts update automatically.' },
        { title: 'Open expenses', text: 'Every expense is published with its amount, category and documents. All members see the monthly report.' },
      ],
    },
    features: {
      title: 'What Hashar does',
      items: [
        { icon: '🧾', title: 'Contributions with receipts', text: 'A photo or screenshot of the transfer, council review, history for every member.' },
        { icon: '📉', title: 'Debts and advances', text: 'Monthly charges are calculated automatically; overpayments roll over to the next months.' },
        { icon: '📢', title: 'Expenses and news', text: 'An expense feed with documents, announcements and emergency contacts for the whole fund.' },
        { icon: '🎯', title: 'Campaigns', text: 'Raise money for a specific goal with progress: repairs, a playground, helping a neighbour.' },
        { icon: '💱', title: 'Multiple currencies', text: 'Accounts in TJS, RUB and USD, each with its own balance; transfers between them are visible to all.' },
        { icon: '👥', title: 'Fund council', text: 'Chairman and auditors, a log of their actions, blocking and leaving without losing history.' },
      ],
    },
    trust: {
      title: 'Money and data',
      lead: 'Hashar never receives or holds money: contributions go directly to the fund’s own accounts, the service only keeps the records.',
      items: [
        'Fund data is visible only to its members; other residents’ receipts are visible only to the council.',
        'No ads, no trackers, no selling of data.',
        'HTTPS-only connections, passwords stored as hashes, sign-ins can be revoked on all devices.',
        'You can delete your account at any time right in the app.',
      ],
      link: 'Privacy policy',
    },
    plans: {
      title: 'Plans',
      lead: 'A plan is chosen for the fund, not for each resident. Members pay nothing to the platform.',
      items: [
        { plan: 'free', name: 'Free', limit: 'up to 10 members', price: 'Free', note: 'All features, no time limit' },
        { plan: 'pro', name: 'Pro', limit: 'up to 100 members', note: 'For a building or a small mahalla' },
        { plan: 'max', name: 'Max', limit: 'up to 500 members', note: 'For large mahallas and villages' },
        { plan: 'individual', name: 'Individual', limit: 'custom limit', price: 'By agreement', note: 'For large communities and associations' },
      ],
      payment:
        'The chairman enables a paid plan: they send a request in the app, the administrator gets in touch about payment and turns the plan on. When changing plans, the paid remainder is not lost.',
    },
    faq: {
      title: 'Questions',
      items: [
        { q: 'Does Hashar hold the fund’s money?', a: 'No. Money goes to the cards and accounts specified by the fund council. Hashar is the record: who paid how much and for what, and where the money went.' },
        { q: 'Who confirms contributions?', a: 'The fund council — the chairman and auditors. They see the receipt, check that the money arrived and credit the contribution. Until then the debt does not decrease.' },
        { q: 'Can I be in several funds?', a: 'Yes. For example, your building’s fund and your mahalla’s fund — switch between them in one tap.' },
        { q: 'How do I sign in?', a: 'With a phone number or email and password, or with Google. There is the hashar.app website and an Android app.' },
        { q: 'What happens to records if a resident deletes their account?', a: 'Their personal data is erased, while contributions and expenses stay in the fund’s reports anonymised — otherwise the accounts would not add up.' },
      ],
    },
    final: {
      title: 'Start with a free fund',
      text: 'Up to 10 members — free with no time limit. Creating a fund takes a couple of minutes.',
      cta: 'Create a fund',
    },
    footer: { about: 'Transparent accounting for the shared fund of a building, mahalla or village.', contact: 'Support' },
  },
}
