// src/pages/TermsPage/content.ts
// Условия использования. Меняя текст, обновите LEGAL_UPDATED в shared/lib/legal.ts;
// тарифы — как в backend/app/enums/plan.py, удаление аккаунта — как в AuthService.delete_account.
import type { AppLocale } from '@/shared/i18n/index.ts'
import { SUPPORT_EMAIL, type LegalDocument } from '@/shared/lib/legal.ts'

export const TERMS: Record<AppLocale, LegalDocument> = {
  ru: {
    title: 'Условия использования',
    intro:
      'Эти условия регулируют использование сервиса Ҳашар — сайта hashar.app и Android-приложения «Ҳашар». ' +
      'Регистрируясь или входя в сервис (в том числе через Google), вы соглашаетесь с ними и с политикой конфиденциальности.',
    sections: [
      {
        heading: '1. Что такое Ҳашар',
        paragraphs: [
          'Ҳашар — инструмент учёта общего фонда дома, махалли, посёлка или другого сообщества: взносы участников, расходы, целевые сборы, объявления и отчёты.',
          'Ҳашар не принимает, не хранит и не переводит деньги и не является банком или платёжной организацией. Участники переводят деньги напрямую на реквизиты, которые указал совет фонда. Сервис только хранит записи об этих операциях.',
          'Ҳашар не участвует в отношениях между участниками фонда и не отвечает за решения совета фонда, сбор и расходование денег.',
        ],
      },
      {
        heading: '2. Аккаунт',
        items: [
          'Указывайте настоящее имя и действующий контакт: по ним совет фонда узнаёт, кто платит за помещение.',
          'Один аккаунт — для одного человека. Не передавайте пароль другим и сообщите нам, если считаете, что аккаунтом воспользовался кто-то другой.',
          'Вы отвечаете за действия, совершённые из вашего аккаунта.',
          'Если вы входите через Google, вход в Ҳашар зависит и от доступа к вашему аккаунту Google.',
        ],
      },
      {
        heading: '3. Фонды и совет фонда',
        items: [
          'Создатель фонда становится председателем. Председатель может назначать ревизоров и передать свои права другому участнику.',
          'Совет фонда (председатель и ревизоры) подтверждает заявки на вступление и взносы, ведёт расходы, реквизиты и настройки фонда. Совет отвечает за то, чтобы эти данные были верными.',
          'Вступая в фонд, вы соглашаетесь, что совет видит ваши контакты и взносы с чеками, а участники — ваше имя и помещение, как описано в политике конфиденциальности.',
          'Записи учёта фонда (взносы, расходы, журнал действий) принадлежат фонду: они остаются в нём и после выхода участника или удаления аккаунта — в обезличенном виде.',
        ],
      },
      {
        heading: '4. Что вы публикуете',
        items: [
          'Вы отвечаете за чеки, документы, объявления и комментарии, которые загружаете.',
          'Нельзя загружать поддельные или чужие чеки, вводить совет в заблуждение о платежах, публиковать чужие персональные данные без основания, оскорбления, рекламу и незаконные материалы.',
          'Мы можем удалить такие материалы и ограничить доступ к аккаунту или фонду, если они нарушают эти условия или закон.',
        ],
      },
      {
        heading: '5. Тарифы и оплата',
        items: [
          'Тариф действует для фонда. Free — до 10 участников, бесплатно и без срока. Pro — до 100 участников, 199 сомони в месяц. Max — до 500 участников, 399 сомони в месяц. Индивидуальный — по договорённости.',
          'Платный тариф подключает председатель через заявку в приложении. Оплата проходит вне сервиса по договорённости с администратором платформы, после неё тариф включается на оплаченный срок.',
          'При смене тарифа неиспользованный остаток текущего тарифа пересчитывается в дни нового. После окончания срока фонд переходит на Free: участники и данные сохраняются, но новых участников сверх лимита принять нельзя.',
          'Цены могут меняться; новая цена действует для следующих оплат, а не для уже оплаченного срока. Вопросы о возврате решаются индивидуально через поддержку.',
        ],
      },
      {
        heading: '6. Что запрещено',
        items: [
          'Пытаться получить доступ к чужим аккаунтам и фондам, подбирать пароли, обходить ограничения сервиса.',
          'Мешать работе сервиса, массово и автоматически собирать данные.',
          'Использовать Ҳашар для мошенничества, отмывания денег или иной незаконной деятельности.',
        ],
      },
      {
        heading: '7. Доступность и ответственность',
        paragraphs: [
          'Мы стараемся, чтобы сервис работал без перебоев, и делаем резервные копии, но не можем гарантировать, что он будет доступен всегда и без ошибок. Сервис предоставляется «как есть».',
          'Мы не отвечаем за точность данных, которые вносят участники и совет фонда, за споры между участниками и за решения, принятые на основе данных в сервисе. ' +
            'Насколько это допускает закон, наша ответственность ограничена суммой, уплаченной фондом за тариф за последние три месяца.',
        ],
      },
      {
        heading: '8. Удаление аккаунта и блокировка',
        paragraphs: [
          'Вы можете в любой момент удалить аккаунт: Профиль → «Удалить аккаунт» или на странице hashar.app/account-deletion. ' +
            'Председатель фонда, где есть другие участники, сначала передаёт свои права.',
          'Мы можем заблокировать аккаунт или фонд, нарушающий эти условия, и по возможности предупредим об этом заранее.',
        ],
      },
      {
        heading: '9. Изменения условий',
        paragraphs: [
          'Мы можем обновлять эти условия. Дата редакции указана вверху страницы; о существенных изменениях сообщим в приложении. ' +
            'Продолжая пользоваться сервисом после изменений, вы принимаете новую редакцию.',
        ],
      },
      {
        heading: '10. Контакты',
        paragraphs: [`Вопросы об условиях и работе сервиса: ${SUPPORT_EMAIL}.`],
      },
    ],
  },

  tg: {
    title: 'Шартҳои истифода',
    intro:
      'Ин шартҳо истифодаи хизматрасонии Ҳашар — сайти hashar.app ва барномаи Android-и «Ҳашар»-ро танзим мекунанд. ' +
      'Бо сабти ном ё воридшавӣ (аз ҷумла тавассути Google) шумо ба онҳо ва ба сиёсати махфият розӣ мешавед.',
    sections: [
      {
        heading: '1. Ҳашар чист',
        paragraphs: [
          'Ҳашар — абзори ҳисоби фонди умумии бино, маҳалла, деҳа ё ҷамъияти дигар: саҳмҳои иштирокчиён, хароҷот, ҷамъовариҳои мақсаднок, эълонҳо ва ҳисоботҳо.',
          'Ҳашар пулро қабул намекунад, нигоҳ намедорад ва интиқол намедиҳад ва бонк ё ташкилоти пардохтӣ нест. Иштирокчиён пулро мустақиман ба реквизитҳое мегузаронанд, ки шӯрои фонд нишон додааст. Хизматрасонӣ танҳо сабти ин амалиётҳоро нигоҳ медорад.',
          'Ҳашар дар муносибатҳои байни иштирокчиёни фонд иштирок намекунад ва барои қарорҳои шӯрои фонд, ҷамъоварӣ ва харҷи пул ҷавобгар нест.',
        ],
      },
      {
        heading: '2. Аккаунт',
        items: [
          'Номи воқеӣ ва тамоси амалкунандаро нишон диҳед: бо онҳо шӯрои фонд мефаҳмад, ки кӣ барои ҳуҷра пардохт мекунад.',
          'Як аккаунт — барои як нафар. Паролро ба дигарон надиҳед ва агар гумон доред, ки аккаунтатонро каси дигар истифода бурдааст, ба мо хабар диҳед.',
          'Шумо барои амалҳое, ки аз аккаунти шумо иҷро шудаанд, ҷавобгаред.',
          'Агар тавассути Google ворид шавед, воридшавӣ ба Ҳашар инчунин аз дастрасӣ ба аккаунти Google-и шумо вобаста аст.',
        ],
      },
      {
        heading: '3. Фондҳо ва шӯрои фонд',
        items: [
          'Созандаи фонд раис мешавад. Раис метавонад тафтишгаронро таъин кунад ва ҳуқуқҳои худро ба иштирокчии дигар супорад.',
          'Шӯрои фонд (раис ва тафтишгарон) аризаҳои узвият ва саҳмҳоро тасдиқ мекунад, хароҷот, реквизитҳо ва танзимоти фондро пеш мебарад. Шӯро барои дурустии ин маълумот ҷавобгар аст.',
          'Ҳангоми ҳамроҳ шудан ба фонд шумо розӣ мешавед, ки шӯро тамосҳо ва саҳмҳои шуморо бо чекҳо мебинад, иштирокчиён бошанд — ном ва ҳуҷраи шуморо, чуноне ки дар сиёсати махфият навишта шудааст.',
          'Сабтҳои ҳисоби фонд (саҳмҳо, хароҷот, дафтари амалҳо) ба фонд тааллуқ доранд: онҳо пас аз баромадани иштирокчӣ ё нест кардани аккаунт низ дар он боқӣ мемонанд — дар шакли беном.',
        ],
      },
      {
        heading: '4. Он чи шумо нашр мекунед',
        items: [
          'Шумо барои чекҳо, ҳуҷҷатҳо, эълонҳо ва шарҳҳое, ки бор мекунед, ҷавобгаред.',
          'Бор кардани чекҳои қалбакӣ ё бегона, гумроҳ кардани шӯро дар бораи пардохтҳо, нашри маълумоти шахсии дигарон бе асос, таҳқир, реклама ва маводи ғайриқонунӣ манъ аст.',
          'Мо метавонем чунин маводро нест кунем ва дастрасӣ ба аккаунт ё фондро маҳдуд намоем, агар онҳо ин шартҳо ё қонунро вайрон кунанд.',
        ],
      },
      {
        heading: '5. Тарифҳо ва пардохт',
        items: [
          'Тариф барои фонд амал мекунад. Free — то 10 иштирокчӣ, ройгон ва бе мӯҳлат. Pro — то 100 иштирокчӣ, 199 сомонӣ дар як моҳ. Max — то 500 иштирокчӣ, 399 сомонӣ дар як моҳ. Инфиродӣ — бо мувофиқа.',
          'Тарифи пулакиро раис тавассути ариза дар барнома пайваст мекунад. Пардохт берун аз хизматрасонӣ бо мувофиқаи маъмури платформа сурат мегирад, пас аз он тариф ба мӯҳлати пардохтшуда фаъол мешавад.',
          'Ҳангоми иваз кардани тариф бақияи истифоданашудаи тарифи ҷорӣ ба рӯзҳои тарифи нав табдил дода мешавад. Пас аз анҷоми мӯҳлат фонд ба Free мегузарад: иштирокчиён ва маълумот нигоҳ дошта мешаванд, аммо иштирокчиёни навро аз ҳад зиёд қабул кардан мумкин нест.',
          'Нархҳо метавонанд тағйир ёбанд; нархи нав барои пардохтҳои оянда амал мекунад, на барои мӯҳлати аллакай пардохтшуда. Масъалаҳои баргардонидани пул ба таври инфиродӣ тавассути дастгирӣ ҳал карда мешаванд.',
        ],
      },
      {
        heading: '6. Чӣ манъ аст',
        items: [
          'Кӯшиши дастрасӣ ба аккаунтҳо ва фондҳои бегона, интихоби парол, гузаштан аз маҳдудиятҳои хизматрасонӣ.',
          'Халал расондан ба кори хизматрасонӣ, ҷамъоварии оммавӣ ва худкори маълумот.',
          'Истифодаи Ҳашар барои қаллобӣ, қонунигардонии пул ё дигар фаъолияти ғайриқонунӣ.',
        ],
      },
      {
        heading: '7. Дастрасӣ ва ҷавобгарӣ',
        paragraphs: [
          'Мо кӯшиш мекунем, ки хизматрасонӣ бе танаффус кор кунад ва нусхаҳои эҳтиётӣ месозем, аммо кафолат дода наметавонем, ки он ҳамеша ва бе хато дастрас бошад. Хизматрасонӣ «чунон ки ҳаст» пешниҳод карда мешавад.',
          'Мо барои дурустии маълумоте, ки иштирокчиён ва шӯрои фонд ворид мекунанд, барои баҳсҳои байни иштирокчиён ва қарорҳое, ки дар асоси маълумоти хизматрасонӣ қабул шудаанд, ҷавобгар нестем. ' +
            'То ҳадде ки қонун иҷозат медиҳад, ҷавобгарии мо бо маблағе маҳдуд аст, ки фонд барои тариф дар се моҳи охир пардохтааст.',
        ],
      },
      {
        heading: '8. Нест кардани аккаунт ва манъ',
        paragraphs: [
          'Шумо метавонед ҳар вақт аккаунтро нест кунед: Профил → «Нест кардани аккаунт» ё дар саҳифаи hashar.app/account-deletion. ' +
            'Раиси фонде, ки дар он иштирокчиёни дигар ҳастанд, аввал ҳуқуқҳои худро месупорад.',
          'Мо метавонем аккаунт ё фондеро, ки ин шартҳоро вайрон мекунад, манъ кунем ва то имкон пешакӣ огоҳ менамоем.',
        ],
      },
      {
        heading: '9. Тағйири шартҳо',
        paragraphs: [
          'Мо метавонем ин шартҳоро навсозӣ кунем. Санаи таҳрир дар болои саҳифа нишон дода шудааст; дар бораи тағйироти муҳим дар барнома хабар медиҳем. ' +
            'Агар пас аз тағйирот истифодаи хизматрасониро идома диҳед, таҳрири навро қабул мекунед.',
        ],
      },
      {
        heading: '10. Тамос',
        paragraphs: [`Саволҳо дар бораи шартҳо ва кори хизматрасонӣ: ${SUPPORT_EMAIL}.`],
      },
    ],
  },

  en: {
    title: 'Terms of use',
    intro:
      'These terms govern the use of Hashar — the hashar.app website and the “Hashar” Android app. ' +
      'By signing up or signing in (including with Google), you agree to them and to the privacy policy.',
    sections: [
      {
        heading: '1. What Hashar is',
        paragraphs: [
          'Hashar is a tool for keeping the records of a shared fund of a building, mahalla, village or other community: member contributions, expenses, campaigns, announcements and reports.',
          'Hashar does not receive, hold or transfer money and is not a bank or a payment institution. Members transfer money directly to the accounts specified by the fund council. The service only stores records of these transactions.',
          'Hashar is not a party to relations between fund members and is not responsible for decisions of the fund council or for how money is collected and spent.',
        ],
      },
      {
        heading: '2. Your account',
        items: [
          'Use your real name and a working contact: this is how the fund council knows who pays for which unit.',
          'One account is for one person. Do not share your password and tell us if you believe someone else has used your account.',
          'You are responsible for actions taken from your account.',
          'If you sign in with Google, access to Hashar also depends on access to your Google account.',
        ],
      },
      {
        heading: '3. Funds and the fund council',
        items: [
          'The creator of a fund becomes its chairman. The chairman can appoint auditors and transfer their rights to another member.',
          'The fund council (the chairman and auditors) approves join requests and contributions and manages expenses, payment details and fund settings. The council is responsible for this data being correct.',
          'By joining a fund, you agree that the council sees your contacts and contributions with receipts, and members see your name and unit, as described in the privacy policy.',
          'The fund’s records (contributions, expenses, action log) belong to the fund: they stay there after a member leaves or deletes their account — in anonymised form.',
        ],
      },
      {
        heading: '4. What you publish',
        items: [
          'You are responsible for the receipts, documents, announcements and comments you upload.',
          'You must not upload fake or other people’s receipts, mislead the council about payments, publish other people’s personal data without grounds, insults, advertising or illegal content.',
          'We may remove such content and restrict access to an account or fund if it breaks these terms or the law.',
        ],
      },
      {
        heading: '5. Plans and payment',
        items: [
          'A plan applies to a fund. Free — up to 10 members, free with no time limit. Pro — up to 100 members, 199 TJS per month. Max — up to 500 members, 399 TJS per month. Individual — by agreement.',
          'The chairman enables a paid plan through a request in the app. Payment is made outside the service as agreed with the platform administrator, after which the plan is turned on for the paid period.',
          'When changing plans, the unused remainder of the current plan is converted into days of the new one. When the period ends, the fund moves to Free: members and data are kept, but no new members can join above the limit.',
          'Prices may change; a new price applies to future payments, not to a period already paid for. Refund questions are handled individually through support.',
        ],
      },
      {
        heading: '6. What is not allowed',
        items: [
          'Trying to access other people’s accounts and funds, guessing passwords, circumventing the service’s limits.',
          'Disrupting the service, bulk or automated data collection.',
          'Using Hashar for fraud, money laundering or any other illegal activity.',
        ],
      },
      {
        heading: '7. Availability and liability',
        paragraphs: [
          'We work to keep the service running without interruptions and make backups, but we cannot guarantee that it will always be available and error-free. The service is provided “as is”.',
          'We are not responsible for the accuracy of data entered by members and the fund council, for disputes between members, or for decisions made based on data in the service. ' +
            'To the extent permitted by law, our liability is limited to the amount the fund paid for its plan over the last three months.',
        ],
      },
      {
        heading: '8. Account deletion and suspension',
        paragraphs: [
          'You can delete your account at any time: Profile → “Delete account”, or on the hashar.app/account-deletion page. ' +
            'The chairman of a fund with other members must transfer their rights first.',
          'We may suspend an account or fund that breaks these terms and will warn in advance where possible.',
        ],
      },
      {
        heading: '9. Changes to these terms',
        paragraphs: [
          'We may update these terms. The revision date is shown at the top of the page; we will announce significant changes in the app. ' +
            'By continuing to use the service after changes, you accept the new version.',
        ],
      },
      {
        heading: '10. Contact',
        paragraphs: [`Questions about these terms and the service: ${SUPPORT_EMAIL}.`],
      },
    ],
  },
}
