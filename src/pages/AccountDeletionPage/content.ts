// src/pages/AccountDeletionPage/content.ts
// Что происходит при удалении аккаунта. Должно совпадать с AuthService.delete_account на backend.
// Ссылка на эту страницу указана в Google Play (требование: удаление без установки приложения).
import type { AppLocale } from '@/shared/i18n/index.ts'
import { SUPPORT_EMAIL, type LegalDocument } from '@/shared/lib/legal.ts'

export const ACCOUNT_DELETION: Record<AppLocale, LegalDocument> = {
  ru: {
    title: 'Удаление аккаунта',
    intro:
      'Аккаунт в Ҳашар (hashar.app) можно удалить в любой момент. Личные данные стираются, а записи учёта фонда остаются обезличенными: ' +
      'взносы и расходы — общая отчётность всех участников, и баланс фонда не должен меняться из-за ухода одного человека.',
    sections: [
      {
        heading: 'Как удалить',
        items: [
          'В приложении или на сайте: Профиль → «Удалить аккаунт», затем подтвердите паролем (аккаунт со входом только через Google пароль не спрашивает).',
          'Или войдите на этой странице и нажмите «Удалить аккаунт» ниже.',
          `Не можете войти — напишите на ${SUPPORT_EMAIL} с телефона или email аккаунта. Удалим в течение 30 дней и сообщим об этом.`,
        ],
      },
      {
        heading: 'Что удаляется сразу',
        items: [
          'Имя, телефон, email, пароль и фото профиля.',
          'Все сессии входа на всех устройствах, подтверждённые устройства, коды из SMS и привязанные способы входа.',
          'Сообщения к заявкам на вступление и ваш контакт в заявках на тариф.',
          'Вы выходите из всех фондов, заявки на вступление отзываются. Войти в этот аккаунт больше нельзя.',
        ],
      },
      {
        heading: 'Что остаётся — без вашего имени и контактов',
        paragraphs: [
          'Эти записи остаются в фонде под именем «Удалённый пользователь» с номером помещения (например, «кв. 12»):',
        ],
        items: [
          'взносы с чеками и комментариями — по ним совет сверяет остатки и долги помещения;',
          'объявления и комментарии, которые вы написали;',
          'записи журнала действий совета.',
        ],
      },
      {
        heading: 'Важно',
        items: [
          'Удаление нельзя отменить. Восстановить аккаунт и связать с ним историю невозможно.',
          'Председатель фонда, в котором есть другие участники, сначала передаёт права председателя: Фонд → Участники.',
          'Тем же телефоном или email можно зарегистрироваться снова — это будет новый аккаунт без прошлой истории.',
          'Из резервных копий данные исчезают в течение 14 дней.',
        ],
      },
    ],
  },

  tg: {
    title: 'Нест кардани аккаунт',
    intro:
      'Аккаунтро дар Ҳашар (hashar.app) ҳар вақт нест кардан мумкин аст. Маълумоти шахсӣ пок мешавад, вале сабтҳои баҳисобгирии фонд беном мемонанд: ' +
      'саҳмҳо ва хароҷот — ҳисоботи умумии ҳамаи аъзоён аст ва бақияи фонд набояд аз рафтани як нафар тағйир ёбад.',
    sections: [
      {
        heading: 'Чӣ тавр нест кардан',
        items: [
          'Дар барнома ё сайт: Профил → «Нест кардани аккаунт», сипас бо парол тасдиқ кунед (аккаунте, ки танҳо тавассути Google ворид мешавад, парол намепурсад).',
          'Ё дар ҳамин саҳифа ворид шавед ва дар поён «Нест кардани аккаунт»-ро пахш кунед.',
          `Ворид шуда наметавонед — аз телефон ё email-и аккаунт ба ${SUPPORT_EMAIL} нависед. Дар давоми 30 рӯз нест мекунем ва хабар медиҳем.`,
        ],
      },
      {
        heading: 'Чӣ фавран нест мешавад',
        items: [
          'Ном, телефон, email, парол ва акси профил.',
          'Ҳамаи сессияҳои воридшавӣ дар ҳамаи дастгоҳҳо, дастгоҳҳои тасдиқшуда, рамзҳои SMS ва усулҳои пайвасташудаи воридшавӣ.',
          'Паёмҳо ба аризаҳои узвият ва тамоси шумо дар аризаҳо ба тариф.',
          'Шумо аз ҳамаи фондҳо мебароед, аризаҳои узвият бозхонда мешаванд. Ба ин аккаунт дигар ворид шудан мумкин нест.',
        ],
      },
      {
        heading: 'Чӣ мемонад — бе ном ва тамосҳои шумо',
        paragraphs: [
          'Ин сабтҳо дар фонд бо номи «Удалённый пользователь» (Корбари несшуда) ва рақами ҷои истиқомат (масалан, «ҳуҷраи 12») мемонанд:',
        ],
        items: [
          'саҳмҳо бо чекҳо ва шарҳҳо — шӯро аз рӯи онҳо бақия ва қарзҳои ҷойро месанҷад;',
          'эълонҳо ва шарҳҳое, ки шумо навиштаед;',
          'сабтҳои журнали амалҳои шӯро.',
        ],
      },
      {
        heading: 'Муҳим',
        items: [
          'Нест карданро бекор кардан мумкин нест. Барқарор кардани аккаунт ва пайваст кардани таърих ба он ғайриимкон аст.',
          'Раиси фонде, ки дар он дигар аъзоён ҳастанд, аввал ҳуқуқи раисро месупорад: Фонд → Аъзоён.',
          'Бо ҳамон телефон ё email аз нав сабти ном шудан мумкин аст — ин аккаунти нав бе таърихи пешина мешавад.',
          'Аз нусхаҳои эҳтиётӣ маълумот дар давоми 14 рӯз нест мешавад.',
        ],
      },
    ],
  },

  en: {
    title: 'Account deletion',
    intro:
      'You can delete your Hashar (hashar.app) account at any time. Personal data is erased, while the fund’s records stay anonymised: ' +
      'contributions and expenses are shared reporting for all members, and the fund’s balance must not change because one person leaves.',
    sections: [
      {
        heading: 'How to delete',
        items: [
          'In the app or on the website: Profile → "Delete account", then confirm with your password (accounts that only sign in with Google are not asked for one).',
          'Or sign in on this page and press "Delete account" below.',
          `Can’t sign in? Write to ${SUPPORT_EMAIL} from your account’s phone or email. We will delete the account within 30 days and let you know.`,
        ],
      },
      {
        heading: 'Deleted immediately',
        items: [
          'Name, phone, email, password and profile photo.',
          'All sign-in sessions on all devices, confirmed devices, SMS codes and linked sign-in methods.',
          'Messages attached to join requests and your contact in plan requests.',
          'You leave all funds and pending join requests are withdrawn. The account can no longer be signed in to.',
        ],
      },
      {
        heading: 'Kept — without your name or contacts',
        paragraphs: [
          'These records stay in the fund under the name «Удалённый пользователь» ("Deleted user") with the unit number (e.g. "apt. 12"):',
        ],
        items: [
          'contributions with receipts and comments — the council uses them to reconcile the unit’s balance and debts;',
          'announcements and comments you wrote;',
          'entries in the council’s action log.',
        ],
      },
      {
        heading: 'Please note',
        items: [
          'Deletion cannot be undone. The account and its history cannot be restored.',
          'A chairman of a fund that has other members must first hand over the chairman role: Fund → Members.',
          'You can register again with the same phone or email — it will be a new account without the previous history.',
          'Data disappears from backups within 14 days.',
        ],
      },
    ],
  },
}
