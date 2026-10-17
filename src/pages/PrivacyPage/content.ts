// src/pages/PrivacyPage/content.ts
// Политика конфиденциальности. Меняя текст, обновите LEGAL_UPDATED в shared/lib/legal.ts
// и проверьте, что описание совпадает с тем, что на самом деле хранит backend.
import type { AppLocale } from '@/shared/i18n/index.ts'
import { SUPPORT_EMAIL, type LegalDocument } from '@/shared/lib/legal.ts'

export const PRIVACY: Record<AppLocale, LegalDocument> = {
  ru: {
    title: 'Политика конфиденциальности',
    intro:
      'Ҳашар (hashar.app) — сервис для учёта общего фонда дома, махалли или посёлка: взносы с чеками, расходы, целевые сборы и отчёты. ' +
      'Здесь описано, какие данные мы собираем, зачем, кто их видит и как удалить аккаунт. Документ действует для сайта hashar.app и Android-приложения «Ҳашар».',
    sections: [
      {
        heading: 'Какие данные мы собираем',
        items: [
          'Аккаунт: имя, телефон и/или email, пароль (храним только в виде хеша — сам пароль не знает никто).',
          'При входе через Google: идентификатор аккаунта Google, имя, email и ссылка на фото профиля — их передаёт Google с вашего согласия. Пароль Google мы не получаем.',
          'Подтверждение личности: одноразовые коды из SMS (храним только их хеш, код действует 5 минут) и список подтверждённых устройств (тип браузера и даты входа) — чтобы вход с нового устройства и смена пароля требовали подтверждения.',
          'Участие в фондах: в каких фондах вы состоите, ваше помещение (например, «кв. 12»), роль, сообщение к заявке на вступление.',
          'Взносы: сумма, валюта, период, выбранный реквизит, фото или скриншот чека, комментарий.',
          'То, что вы публикуете в фонде: объявления, комментарии, отметки «нравится»; для совета — расходы с документами, переводы между счетами, экстренные контакты.',
          'Заявки на тариф (для председателя): выбранный тариф и контакт для связи по оплате.',
          'Технические данные: тип устройства и браузера (User-Agent) для списка сессий входа; IP-адрес — для защиты от подбора пароля и в журналах сервера.',
        ],
      },
      {
        heading: 'Зачем',
        items: [
          'Чтобы вести учёт фонда: зачислять взносы, считать долги и остатки, показывать отчёты участникам.',
          'Чтобы вы могли входить в аккаунт и чтобы совет фонда мог проверить, кто и за какое помещение платит.',
          'Для безопасности: ограничение попыток входа, отзыв сессий, журнал действий совета для разбора споров.',
        ],
        paragraphs: [
          'Мы не показываем рекламу, не используем аналитику и трекеры, не продаём и не передаём данные для маркетинга.',
        ],
      },
      {
        heading: 'Кто видит ваши данные',
        items: [
          'Совет вашего фонда (председатель и ревизоры): имя, телефон, email, помещение, ваши взносы с чеками и комментарии.',
          'Другие участники фонда: ваше имя и помещение рядом с объявлениями, комментариями и взносами в целевые сборы. Если у вас долг по взносам, в списке должников участники видят имя, помещение, телефон и сумму долга. Чеки других участников жители не видят.',
          'Администратор платформы: контакты совета фонда — для подключения тарифа.',
          'Никто, кроме участников фонда, данные фонда не видит. В поиске фондов видны только название и адрес фонда.',
        ],
      },
      {
        heading: 'Где хранятся данные и кто помогает нам работать',
        items: [
          'База данных и API работают на нашем сервере у хостинг-провайдера.',
          'Cloudflare — защищает и ускоряет соединение с API (через него проходят запросы).',
          'GitHub Pages — хостинг сайта hashar.app.',
          'Google Fonts — загрузка шрифта; Google видит IP-адрес устройства при загрузке.',
          'Google Play — распространение Android-приложения.',
          'Google (вход через Google) — подтверждает вашу личность, если вы выбрали этот способ входа; на сайте кнопка загружается с серверов Google.',
          'Payomchi (payomchi.tj, Таджикистан) — отправляет SMS с кодом подтверждения на номера +992; получает только номер телефона и текст SMS с кодом.',
        ],
        paragraphs: [
          'Эти компании обрабатывают данные только для того, чтобы сервис работал, по своим политикам конфиденциальности. Данные могут обрабатываться за пределами вашей страны.',
        ],
      },
      {
        heading: 'Cookie и хранилище браузера',
        paragraphs: [
          'Мы используем две cookie, обе недоступны скриптам: refresh_token — чтобы вы оставались в аккаунте (до 30 дней), ' +
            'и device_token — отметка, что вы уже подтвердили личность на этом устройстве (до года). ' +
            'В хранилище браузера сохраняются только выбранный язык и текущий фонд. Рекламных и аналитических cookie нет.',
        ],
      },
      {
        heading: 'Защита',
        items: [
          'Все соединения — только по HTTPS.',
          'Пароли хранятся в виде хеша bcrypt.',
          'Выход из аккаунта сразу отзывает сессию; можно выйти на всех устройствах.',
          'Доступ к данным фонда проверяется на сервере при каждом запросе.',
        ],
      },
      {
        heading: 'Сколько храним',
        paragraphs: [
          'Данные аккаунта — пока аккаунт существует. Записи учёта фонда хранятся, пока существует фонд: на них держится отчётность перед другими участниками. ' +
            'Резервные копии базы хранятся 14 дней, журналы сервера перезаписываются по мере заполнения.',
        ],
      },
      {
        heading: 'Удаление аккаунта',
        paragraphs: [
          'Аккаунт можно удалить в приложении: Профиль → «Удалить аккаунт», или на странице hashar.app/account-deletion. ' +
            'Имя, телефон, email, пароль и сессии стираются сразу. Взносы, чеки и комментарии остаются в учёте фонда обезличенными — под именем «Удалённый пользователь» с номером помещения. ' +
            'Подробно — на странице удаления аккаунта.',
        ],
      },
      {
        heading: 'Ваши права',
        paragraphs: [
          `Вы можете узнать, какие данные о вас хранятся, попросить исправить или выгрузить их, удалить аккаунт. Напишите на ${SUPPORT_EMAIL} с телефона или email вашего аккаунта — ответим в течение 30 дней.`,
        ],
      },
      {
        heading: 'Дети',
        paragraphs: ['Сервис не предназначен для детей младше 16 лет. Мы сознательно не собираем их данные.'],
      },
      {
        heading: 'Изменения',
        paragraphs: [
          'Если политика изменится, мы обновим эту страницу и дату редакции; о существенных изменениях сообщим в приложении.',
        ],
      },
      {
        heading: 'Контакты',
        paragraphs: [`По вопросам о данных: ${SUPPORT_EMAIL}`],
      },
    ],
  },

  tg: {
    title: 'Сиёсати махфият',
    intro:
      'Ҳашар (hashar.app) — хизмат барои баҳисобгирии фонди умумии хона, маҳалла ё деҳа: саҳмҳо бо чекҳо, хароҷот, ҷамъоварии мақсаднок ва ҳисоботҳо. ' +
      'Дар ин ҷо гуфта мешавад, ки мо кадом маълумотро ҷамъ мекунем, барои чӣ, кӣ онро мебинад ва чӣ тавр аккаунтро нест кардан мумкин аст. Ҳуҷҷат барои сайти hashar.app ва барномаи Android «Ҳашар» амал мекунад.',
    sections: [
      {
        heading: 'Мо кадом маълумотро ҷамъ мекунем',
        items: [
          'Аккаунт: ном, телефон ва/ё email, парол (танҳо ҳамчун хеш нигоҳ дошта мешавад — худи паролро ҳеҷ кас намедонад).',
          'Ҳангоми воридшавӣ тавассути Google: идентификатори аккаунти Google, ном, email ва пайванд ба акси профил — онҳоро Google бо розигии шумо медиҳад. Пароли Google-ро мо намегирем.',
          'Тасдиқи шахсият: рамзҳои якдафъаинаи SMS (танҳо хеши онҳоро нигоҳ медорем, рамз 5 дақиқа амал мекунад) ва рӯйхати дастгоҳҳои тасдиқшуда (навъи браузер ва санаҳои воридшавӣ) — то воридшавӣ аз дастгоҳи нав ва иваз кардани рамз тасдиқро талаб кунад.',
          'Иштирок дар фондҳо: шумо дар кадом фондҳо ҳастед, ҷои истиқомататон (масалан, «ҳуҷраи 12»), нақш, паём ба аризаи узвият.',
          'Саҳмҳо: маблағ, асъор, давра, реквизити интихобшуда, акс ё скриншоти чек, шарҳ.',
          'Он чи шумо дар фонд нашр мекунед: эълонҳо, шарҳҳо, «писанд»-ҳо; барои шӯро — хароҷот бо ҳуҷҷатҳо, интиқолҳо байни ҳисобҳо, тамосҳои фаврӣ.',
          'Аризаҳо ба тариф (барои раис): тарифи интихобшуда ва тамос барои пардохт.',
          'Маълумоти техникӣ: навъи дастгоҳ ва браузер (User-Agent) барои рӯйхати сессияҳо; суроғаи IP — барои ҳимоя аз интихоби парол ва дар журналҳои сервер.',
        ],
      },
      {
        heading: 'Барои чӣ',
        items: [
          'Барои баҳисобгирии фонд: қабули саҳмҳо, ҳисоби қарзҳо ва бақияҳо, нишон додани ҳисоботҳо ба аъзоён.',
          'То шумо ба аккаунт ворид шуда тавонед ва шӯрои фонд санҷад, ки кӣ ва барои кадом ҷой пардохт мекунад.',
          'Барои амният: маҳдуд кардани кӯшишҳои воридшавӣ, бекор кардани сессияҳо, журнали амалҳои шӯро барои ҳалли баҳсҳо.',
        ],
        paragraphs: [
          'Мо реклама нишон намедиҳем, аналитика ва трекерҳо истифода намебарем, маълумотро намефурӯшем ва барои маркетинг намедиҳем.',
        ],
      },
      {
        heading: 'Кӣ маълумоти шуморо мебинад',
        items: [
          'Шӯрои фонди шумо (раис ва тафтишгарон): ном, телефон, email, ҷои истиқомат, саҳмҳои шумо бо чекҳо ва шарҳҳо.',
          'Дигар аъзоёни фонд: ном ва ҷои истиқомати шумо дар назди эълонҳо, шарҳҳо ва саҳмҳо ба ҷамъоварии мақсаднок. Агар шумо аз саҳмҳо қарз дошта бошед, дар рӯйхати қарздорон аъзоён ном, ҷои истиқомат, телефон ва маблағи қарзро мебинанд. Чекҳои дигар аъзоёнро сокинон намебинанд.',
          'Маъмури платформа: тамосҳои шӯрои фонд — барои пайваст кардани тариф.',
          'Ҷуз аъзоёни фонд, касе маълумоти фондро намебинад. Дар ҷустуҷӯи фондҳо танҳо ном ва суроғаи фонд намоён аст.',
        ],
      },
      {
        heading: 'Маълумот дар куҷо нигоҳ дошта мешавад ва кӣ ба мо кӯмак мекунад',
        items: [
          'Пойгоҳи додаҳо ва API дар сервери мо назди провайдери хостинг кор мекунанд.',
          'Cloudflare — пайвастро бо API ҳимоя ва тез мекунад (дархостҳо аз он мегузаранд).',
          'GitHub Pages — хостинги сайти hashar.app.',
          'Google Fonts — боркунии шрифт; Google ҳангоми боркунӣ суроғаи IP-и дастгоҳро мебинад.',
          'Google Play — паҳн кардани барномаи Android.',
          'Google (воридшавӣ тавассути Google) — шахсияти шуморо тасдиқ мекунад, агар шумо ин усулро интихоб кунед; дар сайт тугма аз серверҳои Google бор мешавад.',
          'Payomchi (payomchi.tj, Тоҷикистон) — SMS бо рамзи тасдиқро ба рақамҳои +992 мефиристад; танҳо рақами телефон ва матни SMS бо рамзро мегирад.',
        ],
        paragraphs: [
          'Ин ширкатҳо маълумотро танҳо барои кори хизмат, мувофиқи сиёсатҳои махфияти худ коркард мекунанд. Маълумот метавонад берун аз кишвари шумо коркард шавад.',
        ],
      },
      {
        heading: 'Cookie ва хотираи браузер',
        paragraphs: [
          'Мо ду cookie истифода мебарем, ҳарду барои скриптҳо дастнорасанд: refresh_token — то шумо дар аккаунт бимонед (то 30 рӯз), ' +
            'ва device_token — нишона, ки шумо дар ин дастгоҳ шахсияти худро аллакай тасдиқ кардаед (то як сол). ' +
            'Дар хотираи браузер танҳо забони интихобшуда ва фонди ҷорӣ нигоҳ дошта мешаванд. Cookie-ҳои рекламавӣ ва аналитикӣ нестанд.',
        ],
      },
      {
        heading: 'Ҳифз',
        items: [
          'Ҳамаи пайвастҳо — танҳо тавассути HTTPS.',
          'Паролҳо ҳамчун хеши bcrypt нигоҳ дошта мешаванд.',
          'Баромадан аз аккаунт сессияро фавран бекор мекунад; аз ҳамаи дастгоҳҳо баромадан мумкин аст.',
          'Дастрасӣ ба маълумоти фонд ҳангоми ҳар дархост дар сервер санҷида мешавад.',
        ],
      },
      {
        heading: 'Чӣ қадар нигоҳ медорем',
        paragraphs: [
          'Маълумоти аккаунт — то вақте ки аккаунт вуҷуд дорад. Сабтҳои баҳисобгирии фонд то вақте ки фонд вуҷуд дорад, нигоҳ дошта мешаванд: ҳисобот дар назди дигар аъзоён ба онҳо такя мекунад. ' +
            'Нусхаҳои эҳтиётии пойгоҳ 14 рӯз нигоҳ дошта мешаванд, журналҳои сервер ҳангоми пур шудан аз нав навишта мешаванд.',
        ],
      },
      {
        heading: 'Нест кардани аккаунт',
        paragraphs: [
          'Аккаунтро дар барнома нест кардан мумкин аст: Профил → «Нест кардани аккаунт», ё дар саҳифаи hashar.app/account-deletion. ' +
            'Ном, телефон, email, парол ва сессияҳо фавран пок мешаванд. Саҳмҳо, чекҳо ва шарҳҳо дар баҳисобгирии фонд беном мемонанд — бо номи «Удалённый пользователь» (Корбари несшуда) ва рақами ҷои истиқомат. ' +
            'Муфассал — дар саҳифаи нест кардани аккаунт.',
        ],
      },
      {
        heading: 'Ҳуқуқҳои шумо',
        paragraphs: [
          `Шумо метавонед донед, ки кадом маълумот дар бораи шумо нигоҳ дошта мешавад, ислоҳ ё содир кардани онро талаб кунед, аккаунтро нест кунед. Аз телефон ё email-и аккаунти худ ба ${SUPPORT_EMAIL} нависед — дар давоми 30 рӯз ҷавоб медиҳем.`,
        ],
      },
      {
        heading: 'Кӯдакон',
        paragraphs: ['Хизмат барои кӯдакони то 16-сола пешбинӣ нашудааст. Мо дидаву дониста маълумоти онҳоро ҷамъ намекунем.'],
      },
      {
        heading: 'Тағйирот',
        paragraphs: [
          'Агар сиёсат тағйир ёбад, мо ин саҳифа ва санаи таҳрирро нав мекунем; дар бораи тағйироти муҳим дар барнома хабар медиҳем.',
        ],
      },
      {
        heading: 'Тамос',
        paragraphs: [`Оид ба саволҳои маълумот: ${SUPPORT_EMAIL}`],
      },
    ],
  },

  en: {
    title: 'Privacy Policy',
    intro:
      'Hashar (hashar.app) is a service for keeping the books of a shared fund of a building, neighbourhood (mahalla) or village: contributions with receipts, expenses, fundraisers and reports. ' +
      'This page explains what data we collect, why, who can see it and how to delete your account. It applies to the hashar.app website and the Hashar Android app.',
    sections: [
      {
        heading: 'What we collect',
        items: [
          'Account: name, phone number and/or email, password (stored only as a hash — nobody knows the password itself).',
          'When you sign in with Google: your Google account ID, name, email and profile photo link — Google shares them with your consent. We never receive your Google password.',
          'Identity verification: one-time SMS codes (we store only their hash; a code is valid for 5 minutes) and a list of confirmed devices (browser type and sign-in dates) — so that signing in on a new device and changing the password require confirmation.',
          'Fund membership: which funds you belong to, your unit (e.g. "apt. 12"), your role, the message attached to your join request.',
          'Contributions: amount, currency, period, chosen payment details, a photo or screenshot of the receipt, a comment.',
          'What you post in a fund: announcements, comments, likes; for the council — expenses with documents, transfers between accounts, emergency contacts.',
          'Plan requests (chairman only): the chosen plan and a contact for payment.',
          'Technical data: device and browser type (User-Agent) for the list of sign-in sessions; IP address — to protect against password guessing and in server logs.',
        ],
      },
      {
        heading: 'Why',
        items: [
          'To keep the fund’s books: record contributions, calculate debts and balances, show reports to members.',
          'To let you sign in, and to let the fund council check who pays for which unit.',
          'For security: limiting sign-in attempts, revoking sessions, a log of council actions for resolving disputes.',
        ],
        paragraphs: [
          'We do not show ads, do not use analytics or trackers, and do not sell or share data for marketing.',
        ],
      },
      {
        heading: 'Who can see your data',
        items: [
          'Your fund council (chairman and auditors): name, phone, email, unit, your contributions with receipts and comments.',
          'Other members of the fund: your name and unit next to announcements, comments and fundraiser contributions. If you owe contributions, members see your name, unit, phone number and the amount owed in the debtors list. Residents do not see other members’ receipts.',
          'The platform administrator: contacts of the fund council — to activate a plan.',
          'Nobody outside the fund sees the fund’s data. Fund search shows only the fund’s name and address.',
        ],
      },
      {
        heading: 'Where data is stored and who helps us run the service',
        items: [
          'The database and API run on our server at a hosting provider.',
          'Cloudflare — protects and speeds up the connection to the API (requests pass through it).',
          'GitHub Pages — hosting for the hashar.app website.',
          'Google Fonts — font loading; Google sees the device IP address when the font is loaded.',
          'Google Play — distribution of the Android app.',
          'Google (Sign in with Google) — confirms your identity if you choose this sign-in method; on the website the button is loaded from Google servers.',
          'Payomchi (payomchi.tj, Tajikistan) — sends SMS verification codes to +992 numbers; receives only the phone number and the SMS text with the code.',
        ],
        paragraphs: [
          'These companies process data only to keep the service running, under their own privacy policies. Data may be processed outside your country.',
        ],
      },
      {
        heading: 'Cookies and browser storage',
        paragraphs: [
          'We use two cookies, neither accessible to scripts: refresh_token keeps you signed in (up to 30 days), ' +
            'and device_token marks that you have already confirmed your identity on this device (up to a year). ' +
            'Browser storage holds only your chosen language and current fund. There are no advertising or analytics cookies.',
        ],
      },
      {
        heading: 'Security',
        items: [
          'All connections use HTTPS only.',
          'Passwords are stored as bcrypt hashes.',
          'Signing out revokes the session immediately; you can sign out on all devices.',
          'Access to fund data is checked on the server for every request.',
        ],
      },
      {
        heading: 'Retention',
        paragraphs: [
          'Account data is kept while the account exists. Fund records are kept while the fund exists, because reporting to other members relies on them. ' +
            'Database backups are kept for 14 days; server logs are overwritten as they fill up.',
        ],
      },
      {
        heading: 'Deleting your account',
        paragraphs: [
          'You can delete your account in the app (Profile → "Delete account") or at hashar.app/account-deletion. ' +
            'Your name, phone, email, password and sessions are erased immediately. Contributions, receipts and comments stay in the fund’s books anonymised — under the name «Удалённый пользователь» ("Deleted user") with the unit number. ' +
            'See the account deletion page for details.',
        ],
      },
      {
        heading: 'Your rights',
        paragraphs: [
          `You can ask what data we hold about you, ask us to correct or export it, or delete your account. Write to ${SUPPORT_EMAIL} from your account’s phone or email — we reply within 30 days.`,
        ],
      },
      {
        heading: 'Children',
        paragraphs: ['The service is not intended for children under 16. We do not knowingly collect their data.'],
      },
      {
        heading: 'Changes',
        paragraphs: [
          'If this policy changes, we will update this page and its date; we will announce significant changes in the app.',
        ],
      },
      {
        heading: 'Contact',
        paragraphs: [`Questions about your data: ${SUPPORT_EMAIL}`],
      },
    ],
  },
}
