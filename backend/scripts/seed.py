"""
Наполнение БД демо-данными.

Запуск из папки backend после миграций:
    python -m scripts.seed

Что создаётся:
- админ платформы (подтверждает тарифы)
- фонд «ЖК Северная Звезда»: тариф Pro, счета TJS (базовый) / RUB / USD,
  взнос 120 → 150 TJS (история тарифа), взносы, в т. ч. в RUB с зачётом в TJS,
  расходы, целевые сборы, перевод между счетами, заявки на вступление
- фонд «Дачный посёлок Варзоб»: тариф Free, заявка на Pro ждёт админа
- Сергей Васильев состоит в обоих фондах (переключатель фондов)
- Руслан вышел и просится обратно, Ольга заблокирована — совет решает о начислениях

Даты считаются относительно текущего месяца. Пароль у всех: password123
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.finance import current_period, shift_period
from app.core.security import hash_password
from app.models import (
    AccountTransfer,
    Announcement,
    AnnouncementComment,
    AnnouncementLike,
    Contribution,
    EmergencyContact,
    Expense,
    Fund,
    FundAccount,
    FundMember,
    FundRate,
    PaymentRequisite,
    PlanRequest,
    TargetFund,
    User,
)
from app.services.account_service import requisite_label

DEMO_PASSWORD = "password123"

SAMPLE_RECEIPT = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 420 580'>"
    "<rect width='420' height='580' rx='16' fill='%23ffffff'/>"
    "<rect width='420' height='80' rx='16' fill='%23234970'/>"
    "<text x='30' y='50' font-family='sans-serif' font-size='18' font-weight='bold' fill='%23ffffff'>"
    "ЧЕК ОПЕРАЦИИ</text>"
    "<text x='30' y='180' font-family='sans-serif' font-size='28' font-weight='bold' fill='%234EBEC2'>ИСПОЛНЕН</text>"
    "</svg>"
)

AVATARS = {
    "alexey": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&auto=format&fit=crop&q=80",
    "marat": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
    "ivan": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
    "anna": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
    "sergey": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&auto=format&fit=crop&q=80",
    "elena": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
}


def at(months_ago: int, day: int, hour: int = 12) -> datetime:
    """Дата в прошлом месяце относительно текущего (0 — текущий месяц)."""
    year, month = map(int, shift_period(current_period(), -months_ago).split("-"))
    moment = datetime(year, month, day, hour, tzinfo=timezone.utc)
    # Не уходим в будущее для текущего месяца
    return min(moment, datetime.now(timezone.utc) - timedelta(hours=1))


def period(months_ago: int) -> str:
    return shift_period(current_period(), -months_ago)


async def seed() -> None:
    if not settings.DEV_MODE:
        raise SystemExit(
            "Сидинг демо-данных доступен только при DEV_MODE=true (в проде он создал бы админа с известным паролем)."
        )

    async with AsyncSessionLocal() as db:
        if (await db.execute(select(func.count(User.id)))).scalar():
            print("В базе уже есть пользователи — пропускаю сидинг.")
            return

        password = hash_password(DEMO_PASSWORD)

        # ─── Пользователи ──────────────────────────────────────────────────────
        def user(full_name, phone, email=None, avatar=None, platform_admin=False):
            return User(
                full_name=full_name,
                phone=phone,
                email=email,
                avatar_url=avatar,
                hashed_password=password,
                is_platform_admin=platform_admin,
                verified_at=datetime.now(timezone.utc),
            )

        admin = user("Админ платформы", "+79990000000", "admin@fund.local", platform_admin=True)
        alexey = user("Алексей Николаев", "+79161234567", "chairman@fund.local", AVATARS["alexey"])
        marat = user("Марат Каримов", "+79263456789", avatar=AVATARS["marat"])
        ivan = user("Иван Петров", "+79037890123", avatar=AVATARS["ivan"])
        anna = user("Анна Сидорова", "+79154567890", avatar=AVATARS["anna"])
        sergey = user("Сергей Васильев", "+79255678901", avatar=AVATARS["sergey"])
        elena = user("Елена Михайлова", "+79096789012", avatar=AVATARS["elena"])
        olga = user("Ольга Смирнова", "+79178901234")
        dmitry = user("Дмитрий Ковалев", "+79859012345")
        ruslan = user("Руслан Ахметов", "+79680123456")
        db.add_all([admin, alexey, marat, ivan, anna, sergey, elena, olga, dmitry, ruslan])
        await db.flush()

        # ─── Фонд 1: ЖК «Северная Звезда» ──────────────────────────────────────
        star = Fund(
            name="ЖК «Северная Звезда»",
            description="Фонд дома: обслуживание двора, подъездов и общие проекты.",
            address="Душанбе, ул. Рудаки, 15",
            code="STAR2026",
            base_currency="tjs",
            start_period=period(3),
            plan="pro",
            plan_price=199,
            plan_expires_at=datetime.now(timezone.utc) + timedelta(days=25),
            created_by_id=alexey.id,
            created_at=at(4, 1),
        )
        db.add(star)
        await db.flush()
        db.add_all([FundAccount(fund_id=star.id, currency=c) for c in ("tjs", "rub", "usd")])
        db.add_all(
            [
                EmergencyContact(fund_id=star.id, title=title, phone=phone, created_by_id=alexey.id)
                for title, phone in (
                    ("Медпункт", "+992 37 221 03 03"),
                    ("Пожарная служба", "+992 37 221 01 01"),
                    ("Диспетчер ЖЭУ", "+992 90 555 12 34"),
                    ("Директор школы №15", "+992 93 777 45 45"),
                )
            ]
        )
        # Тариф поднимали: 120 TJS первые два месяца, затем 150 TJS
        db.add_all(
            [
                FundRate(fund_id=star.id, period=period(3), amount=120, created_by_id=alexey.id),
                FundRate(fund_id=star.id, period=period(1), amount=150, created_by_id=alexey.id),
            ]
        )

        def member(fund, who, role, unit, status="active", message=None, **extra):
            fields = dict(
                fund_id=fund.id,
                user_id=who.id,
                role=role,
                status=status,
                address_unit=unit,
                message=message,
                joined_at=at(4, 2) if status in ("active", "blocked") else None,
            )
            return FundMember(**{**fields, **extra})

        db.add_all(
            [
                member(star, alexey, "chairman", "кв. 15"),
                member(star, marat, "admin", "кв. 28"),
                member(star, ivan, "resident", "кв. 12"),
                member(star, anna, "resident", "кв. 24"),
                member(star, sergey, "resident", "кв. 7"),
                member(star, elena, "resident", "кв. 31"),
                # Заблокирована два месяца назад — при разблокировке совет решит про начисления
                member(star, olga, "resident", "кв. 42", status="blocked", blocked_at=at(2, 5)),
                member(star, dmitry, "resident", "кв. 18", status="pending", message="Купил квартиру в сентябре"),
                # Был участником, вышел и подал заявку на возвращение
                member(
                    star,
                    ruslan,
                    "resident",
                    "кв. 5",
                    status="pending",
                    message="Вернулся после ремонта квартиры",
                    joined_at=at(4, 2),
                    left_at=at(3, 10),
                ),
            ]
        )

        tjs_card = PaymentRequisite(
            fund_id=star.id,
            currency="tjs",
            bank_name="Алиф Банк",
            card_or_account_number="4444 8888 1234 5678",
            recipient_name="Алексей Н. (председатель)",
            phone_number="+992 90 123 45 67",
            note="В комментарии к переводу укажите номер квартиры.",
        )
        rub_card = PaymentRequisite(
            fund_id=star.id,
            currency="rub",
            bank_name="Сбербанк",
            card_or_account_number="2202 2034 5678 9101",
            recipient_name="Алексей Викторович Н.",
            phone_number="+7 916 123-45-67",
            note="Для жильцов, работающих в России. СБП без комиссии.",
        )
        usd_card = PaymentRequisite(
            fund_id=star.id,
            currency="usd",
            bank_name="Эсхата Банк",
            kind="account",
            card_or_account_number="TJ22 0000 1111 2222 3333",
            recipient_name="ТСЖ «Северная Звезда»",
        )
        db.add_all([tjs_card, rub_card, usd_card])

        barrier = TargetFund(
            fund_id=star.id,
            title="Автоматический шлагбаум и видеонаблюдение въезда",
            description="GSM-модуль, стрела шлагбаума и 2 камеры с распознаванием номеров.",
            target_amount=15000,
            currency="tjs",
            category="security",
            created_by_id=alexey.id,
            created_at=at(3, 5),
        )
        greening = TargetFund(
            fund_id=star.id,
            title="Озеленение двора и детская зона",
            description="Газон, саженцы туй, ремонт песочницы и новые качели.",
            target_amount=90000,
            currency="rub",
            category="landscaping",
            created_by_id=marat.id,
            created_at=at(2, 10),
        )
        db.add_all([barrier, greening])
        await db.flush()

        def contribution(
            fund, who, unit, amount, months_ago, day, requisite, status="approved", target=None, credited=None, **extra
        ):
            return Contribution(
                fund_id=fund.id,
                user_id=who.id,
                user_unit=unit,
                amount=amount,
                currency=requisite.currency,
                # Зачёт в валюте назначения; для оплаты в той же валюте — та же сумма
                credited_amount=credited or amount,
                credited_currency=target.currency if target else fund.base_currency,
                requisite_id=requisite.id,
                requisite_label=requisite_label(requisite),
                category="target_fund" if target else "monthly_fee",
                target_fund_id=target.id if target else None,
                billing_period=None if target else period(months_ago),
                receipt_image=SAMPLE_RECEIPT,
                status=status,
                reviewed_by_id=alexey.id if status != "pending" else None,
                reviewed_at=at(months_ago, day, 18) if status != "pending" else None,
                created_at=at(months_ago, day),
                **extra,
            )

        db.add_all(
            [
                # Ежемесячные взносы (TJS: 120 первые два месяца, затем 150)
                contribution(star, alexey, "кв. 15", 600, 3, 2, tjs_card, comment_user="Сразу за 4 месяца"),
                contribution(star, marat, "кв. 28", 450, 3, 3, tjs_card),
                contribution(star, ivan, "кв. 12", 150, 3, 5, tjs_card),
                contribution(star, ivan, "кв. 12", 150, 2, 4, tjs_card, comment_user="Оплачено вовремя"),
                contribution(star, elena, "кв. 31", 600, 2, 1, tjs_card, comment_user="Взнос до конца квартала"),
                contribution(star, sergey, "кв. 7", 900, 2, 15, tjs_card, comment_user="Оплата на полгода вперёд"),
                contribution(star, anna, "кв. 24", 300, 2, 8, tjs_card),
                contribution(star, anna, "кв. 24", 150, 0, 3, tjs_card, status="pending", comment_user="Проверьте чек"),
                # Взнос в рублях: участник сам указал, сколько зачесть в TJS
                contribution(
                    star,
                    marat,
                    "кв. 28",
                    1300,
                    0,
                    4,
                    rub_card,
                    status="pending",
                    credited=150,
                    comment_user="Перевёл в рублях, зачтите 150 TJS за этот месяц",
                ),
                contribution(
                    star,
                    olga,
                    "кв. 42",
                    75,
                    1,
                    28,
                    tjs_card,
                    status="rejected",
                    comment_admin="Сумма в чеке (75 TJS) меньше тарифа (150 TJS). Доплатите остаток.",
                ),
                # Целевые сборы
                contribution(star, alexey, "кв. 15", 3000, 3, 12, tjs_card, target=barrier),
                contribution(star, marat, "кв. 28", 2500, 3, 14, tjs_card, target=barrier),
                contribution(star, sergey, "кв. 7", 2000, 2, 6, tjs_card, target=barrier),
                contribution(star, ivan, "кв. 12", 1000, 1, 9, tjs_card, target=barrier),
                contribution(star, elena, "кв. 31", 15000, 1, 11, rub_card, target=greening),
                contribution(star, anna, "кв. 24", 12000, 1, 16, rub_card, target=greening),
                contribution(
                    star,
                    olga,
                    "кв. 42",
                    500,
                    0,
                    2,
                    tjs_card,
                    status="pending",
                    target=barrier,
                    comment_user="На шлагбаум от кв. 42",
                ),
            ]
        )

        db.add_all(
            [
                Expense(
                    fund_id=star.id,
                    title="Замена прожекторов во дворе (6 шт)",
                    category="electrical",
                    amount=1400,
                    currency="tjs",
                    description="Прожекторы 50W, монтажные коробки и сумеречные реле.",
                    receipt_images=[SAMPLE_RECEIPT],
                    created_by_id=alexey.id,
                    created_at=at(2, 12),
                ),
                Expense(
                    fund_id=star.id,
                    title="Аварийная прочистка ливнёвки",
                    category="emergency",
                    amount=900,
                    currency="tjs",
                    description="Засор колодца у 2-го подъезда после ливня. Акт № 104.",
                    receipt_images=[SAMPLE_RECEIPT],
                    created_by_id=alexey.id,
                    created_at=at(1, 18),
                ),
                Expense(
                    fund_id=star.id,
                    title="Саженцы туй и грунт для субботника",
                    category="landscaping",
                    amount=22400,
                    currency="rub",
                    description="10 саженцев туи Смарагд, грунт и удобрения.",
                    receipt_images=[SAMPLE_RECEIPT],
                    target_fund_id=greening.id,
                    created_by_id=marat.id,
                    created_at=at(1, 25),
                ),
                Expense(
                    fund_id=star.id,
                    title="Хозтовары для уборки подъездов",
                    category="household",
                    amount=320,
                    currency="tjs",
                    description="Химия для мытья плитки, швабры, мусорные пакеты.",
                    receipt_images=[SAMPLE_RECEIPT],
                    created_by_id=alexey.id,
                    created_at=at(0, 1),
                ),
            ]
        )

        # Перевод между счетами + объявление о нём (прозрачность)
        transfer = AccountTransfer(
            fund_id=star.id,
            from_currency="tjs",
            from_amount=1000,
            to_currency="rub",
            to_amount=8500,
            comment="Обмен для оплаты саженцев у поставщика из России",
            created_by_id=alexey.id,
            created_at=at(1, 20),
        )
        db.add(transfer)
        await db.flush()

        report = Announcement(
            fund_id=star.id,
            title="📢 Финансовый отчёт за прошлый месяц и субботник",
            content=(
                "Уважаемые соседи! Публикуем итоги расходования средств фонда.\n"
                "1. Прочистка ливнёвки — 900 TJS.\n"
                "2. Из целевого сбора закуплены туи.\n"
                "В субботу в 11:00 приглашаем всех на субботник!"
            ),
            category="news",
            is_pinned=True,
            author_id=alexey.id,
            created_at=at(0, 3),
        )
        db.add_all(
            [
                report,
                Announcement(
                    fund_id=star.id,
                    title="Движение по счетам фонда",
                    content=transfer.comment,
                    category="finance",
                    author_id=alexey.id,
                    transfer_id=transfer.id,
                    created_at=transfer.created_at,
                ),
            ]
        )
        await db.flush()
        db.add_all(
            [
                AnnouncementComment(
                    announcement_id=report.id,
                    user_id=ivan.id,
                    user_unit="кв. 12",
                    text="Спасибо совету за оперативное решение с ливнёвкой!",
                    created_at=at(0, 3, 14),
                ),
                AnnouncementComment(
                    announcement_id=report.id,
                    user_id=elena.id,
                    user_unit="кв. 31",
                    text="Обязательно выйдем на субботник всей семьёй!",
                    created_at=at(0, 3, 16),
                ),
                AnnouncementLike(announcement_id=report.id, user_id=ivan.id),
                AnnouncementLike(announcement_id=report.id, user_id=anna.id),
            ]
        )

        # ─── Фонд 2: дачный посёлок (Free) ─────────────────────────────────────
        dacha = Fund(
            name="Дачный посёлок «Варзоб»",
            description="Дорога, охрана и вывоз мусора.",
            address="Варзобский район",
            code="VARZOB77",
            base_currency="usd",
            start_period=period(1),
            plan="free",
            created_by_id=sergey.id,
            created_at=at(2, 1),
        )
        db.add(dacha)
        await db.flush()
        db.add(FundAccount(fund_id=dacha.id, currency="usd"))
        db.add(FundRate(fund_id=dacha.id, period=period(1), amount=10, created_by_id=sergey.id))
        db.add_all(
            [
                member(dacha, sergey, "chairman", "участок 3"),
                member(dacha, ivan, "resident", "участок 11"),
            ]
        )
        dacha_card = PaymentRequisite(
            fund_id=dacha.id,
            currency="usd",
            bank_name="Душанбе Сити",
            card_or_account_number="5058 2700 1111 2222",
            recipient_name="Сергей В. (председатель)",
        )
        db.add(dacha_card)
        await db.flush()
        db.add(contribution(dacha, ivan, "участок 11", 20, 1, 5, dacha_card))
        db.add(
            PlanRequest(
                fund_id=dacha.id,
                plan="pro",
                months=3,
                list_price_tjs=199,
                price_tjs=199,
                contact="+79255678901, Telegram @sergey_varzob",
                comment="Посёлок растёт, нужно больше 10 участников",
                requested_by_id=sergey.id,
                created_at=at(0, 2),
            )
        )

        await db.commit()
        print(f"Готово: демо-данные загружены. Пароль у всех пользователей: {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
