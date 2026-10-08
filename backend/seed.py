import os
import sys
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.core.security import get_password_hash
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.models.rate import BillingRate
from backend.app.models.target_fund import TargetFund
from backend.app.models.requisite import PaymentRequisite
from backend.app.models.contribution import Contribution, ContributionCategory, ContributionStatus
from backend.app.models.expense import Expense
from backend.app.models.announcement import Announcement, AnnouncementComment


def seed_database():
    print("Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("База данных уже содержит данные. Пропуск сидинга.")
            return

        print("Заполнение тестовыми данными, синхронизированными с интерфейсом...")

        default_pwd = get_password_hash("password123")

        # 1. Users
        users = [
            User(
                id="user-1",
                phone="+7 (916) 123-45-67",
                full_name="Алексей Николаев",
                address_unit="кв. 15",
                role=UserRole.SUPERADMIN,
                status=UserStatus.ACTIVE,
                email="chairman@community-fund.ru",
                avatar_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&auto=format&fit=crop&q=80",
                hashed_password=default_pwd,
            ),
            User(
                id="user-2",
                phone="+7 (926) 345-67-89",
                full_name="Марат Каримов",
                address_unit="кв. 28",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                email="marat.k@community-fund.ru",
                avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
                hashed_password=default_pwd,
            ),
            User(
                id="user-3",
                phone="+7 (903) 789-01-23",
                full_name="Иван Петров",
                address_unit="кв. 12",
                role=UserRole.RESIDENT,
                status=UserStatus.ACTIVE,
                email="ivan.petrov@mail.ru",
                avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
                hashed_password=default_pwd,
            ),
            User(
                id="user-4",
                phone="+7 (915) 456-78-90",
                full_name="Анна Сидорова",
                address_unit="кв. 24",
                role=UserRole.RESIDENT,
                status=UserStatus.ACTIVE,
                email="anna.sidorova@gmail.com",
                avatar_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
                hashed_password=default_pwd,
            ),
            User(
                id="user-5",
                phone="+7 (925) 567-89-01",
                full_name="Сергей Васильев",
                address_unit="кв. 7",
                role=UserRole.RESIDENT,
                status=UserStatus.ACTIVE,
                email="sergey.v@yandex.ru",
                avatar_url="https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&auto=format&fit=crop&q=80",
                hashed_password=default_pwd,
            ),
            User(
                id="user-6",
                phone="+7 (909) 678-90-12",
                full_name="Елена Михайлова",
                address_unit="кв. 31",
                role=UserRole.RESIDENT,
                status=UserStatus.ACTIVE,
                email="elena.m@mail.ru",
                avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
                hashed_password=default_pwd,
            ),
            User(
                id="user-7",
                phone="+7 (917) 890-12-34",
                full_name="Ольга Смирнова",
                address_unit="кв. 42",
                role=UserRole.RESIDENT,
                status=UserStatus.ACTIVE,
                email="olga.smirnova@gmail.com",
                hashed_password=default_pwd,
            ),
            User(
                id="user-8",
                phone="+7 (985) 901-23-45",
                full_name="Дмитрий Ковалев",
                address_unit="кв. 18",
                role=UserRole.RESIDENT,
                status=UserStatus.PENDING_APPROVAL,
                email="dmitry.k18@mail.ru",
                hashed_password=default_pwd,
            ),
            User(
                id="user-9",
                phone="+7 (968) 012-34-56",
                full_name="Руслан Ахметов",
                address_unit="кв. 5",
                role=UserRole.RESIDENT,
                status=UserStatus.ACTIVE,
                hashed_password=default_pwd,
            ),
        ]
        db.add_all(users)
        db.commit()

        # 2. Billing Rate
        rate = BillingRate(
            id=1,
            amount=1500,
            effective_from="2026-01-01",
            created_by_admin_id="user-1",
            created_at=datetime.fromisoformat("2025-12-20T10:00:00"),
        )
        db.add(rate)
        db.commit()

        # 3. Target Funds
        tf1 = TargetFund(
            id=1,
            title="Автоматический шлагбаум и видеонаблюдение въезда",
            description="Установка GSM-модуля, стрелы шлагбаума и 2 камер с распознаванием госномеров на въезде во двор.",
            target_amount=280000,
            category="Безопасность",
            is_active=True,
            created_by_admin_id="user-1",
            created_at=datetime.fromisoformat("2026-06-01T10:00:00"),
        )
        tf2 = TargetFund(
            id=2,
            title="Озеленение двора и детская зона",
            description="Закупка газонного рулона, 15 саженцев туй, ремонт песочницы и новые безопасные качели.",
            target_amount=90000,
            category="Благоустройство",
            is_active=True,
            created_by_admin_id="user-2",
            created_at=datetime.fromisoformat("2026-07-15T12:00:00"),
        )
        tf3 = TargetFund(
            id=3,
            title="Замена светильников в подъездах на энергосберегающие LED",
            description="Установка антивандальных LED-светильников с оптико-акустическими датчиками во всех 3 подъездах.",
            target_amount=45000,
            category="Инфраструктура",
            is_active=False,
            created_by_admin_id="user-1",
            created_at=datetime.fromisoformat("2026-03-10T10:00:00"),
        )
        db.add_all([tf1, tf2, tf3])
        db.commit()

        # 4. Payment Requisites
        req1 = PaymentRequisite(
            id=1,
            bank_name="Сбербанк",
            card_or_account_number="2202 2034 5678 9101",
            recipient_name="Алексей Викторович Н. (Председатель)",
            phone_number="+7 (916) 123-45-67",
            is_active=True,
            note="Переводы по номеру карты или СБП на Сбербанк без комиссии. В сообщении укажите: Квартира и Фамилия.",
        )
        req2 = PaymentRequisite(
            id=2,
            bank_name="Т-Банк (Тинькофф)",
            card_or_account_number="5536 9140 8821 4321",
            recipient_name="Алексей Викторович Н.",
            phone_number="+7 (916) 123-45-67",
            is_active=True,
            note="СБП на Т-Банк. Мгновенное зачисление.",
        )
        db.add_all([req1, req2])
        db.commit()

        # 5. Contributions
        sample_receipt = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 420 580' width='100%' height='100%'><rect width='420' height='580' fill='%23f8fafc'/><text x='30' y='60' font-family='sans-serif' font-size='18' font-weight='bold' fill='%2310b981'>ЧЕК ОПЕРАЦИИ</text><text x='30' y='100' font-family='sans-serif' font-size='14' fill='%23334155'>ЖК СЕВЕРНАЯ ЗВЕЗДА</text></svg>"
        contributions = [
            Contribution(
                id="cont-1",
                user_id="user-3",
                user_name="Иван Петров",
                user_unit="кв. 12",
                amount=1500,
                category=ContributionCategory.MONTHLY_FEE,
                billing_period="2026-07",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.APPROVED,
                comment_user="Оплата за июль, кв. 12",
                reviewed_by_admin_id="user-1",
                reviewed_by_admin_name="Алексей Николаев",
                reviewed_at=datetime.fromisoformat("2026-07-06T10:15:00"),
                created_at=datetime.fromisoformat("2026-07-05T14:22:00"),
            ),
            Contribution(
                id="cont-2",
                user_id="user-3",
                user_name="Иван Петров",
                user_unit="кв. 12",
                amount=1500,
                category=ContributionCategory.MONTHLY_FEE,
                billing_period="2026-08",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.APPROVED,
                comment_user="Оплата за август",
                reviewed_by_admin_id="user-1",
                reviewed_by_admin_name="Алексей Николаев",
                reviewed_at=datetime.fromisoformat("2026-08-04T16:00:00"),
                created_at=datetime.fromisoformat("2026-08-04T11:05:00"),
            ),
            Contribution(
                id="cont-3",
                user_id="user-3",
                user_name="Иван Петров",
                user_unit="кв. 12",
                amount=1500,
                category=ContributionCategory.MONTHLY_FEE,
                billing_period="2026-09",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.APPROVED,
                comment_user="Сентябрь оплачен вовремя",
                reviewed_by_admin_id="user-2",
                reviewed_by_admin_name="Марат Каримов",
                reviewed_at=datetime.fromisoformat("2026-09-02T12:00:00"),
                created_at=datetime.fromisoformat("2026-09-02T09:12:00"),
            ),
            Contribution(
                id="cont-4",
                user_id="user-3",
                user_name="Иван Петров",
                user_unit="кв. 12",
                amount=5000,
                category=ContributionCategory.TARGET_FUND,
                target_fund_id=1,
                target_fund_title="Автоматический шлагбаум и видеонаблюдение въезда",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.APPROVED,
                comment_user="На шлагбаум, ждем установку!",
                reviewed_by_admin_id="user-1",
                reviewed_by_admin_name="Алексей Николаев",
                reviewed_at=datetime.fromisoformat("2026-08-11T09:00:00"),
                created_at=datetime.fromisoformat("2026-08-10T18:30:00"),
            ),
            Contribution(
                id="cont-5",
                user_id="user-6",
                user_name="Елена Михайлова",
                user_unit="кв. 31",
                amount=3000,
                category=ContributionCategory.MONTHLY_FEE,
                billing_period="2026-08",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.APPROVED,
                comment_user="Взнос за июль и август",
                reviewed_by_admin_id="user-1",
                reviewed_by_admin_name="Алексей Николаев",
                reviewed_at=datetime.fromisoformat("2026-08-01T15:00:00"),
                created_at=datetime.fromisoformat("2026-08-01T10:00:00"),
            ),
            Contribution(
                id="cont-6",
                user_id="user-6",
                user_name="Елена Михайлова",
                user_unit="кв. 31",
                amount=2000,
                category=ContributionCategory.TARGET_FUND,
                target_fund_id=2,
                target_fund_title="Озеленение двора и детская зона",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.APPROVED,
                reviewed_by_admin_id="user-2",
                reviewed_by_admin_name="Марат Каримов",
                reviewed_at=datetime.fromisoformat("2026-08-20T17:00:00"),
                created_at=datetime.fromisoformat("2026-08-20T14:15:00"),
            ),
            Contribution(
                id="cont-7",
                user_id="user-5",
                user_name="Сергей Васильев",
                user_unit="кв. 7",
                amount=4500,
                category=ContributionCategory.MONTHLY_FEE,
                billing_period="2026-11",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.APPROVED,
                comment_user="Оплата сразу за 3 месяца вперед",
                reviewed_by_admin_id="user-1",
                reviewed_by_admin_name="Алексей Николаев",
                reviewed_at=datetime.fromisoformat("2026-08-15T11:00:00"),
                created_at=datetime.fromisoformat("2026-08-15T10:20:00"),
            ),
            Contribution(
                id="cont-8",
                user_id="user-9",
                user_name="Руслан Ахметов",
                user_unit="кв. 5",
                amount=1500,
                category=ContributionCategory.MONTHLY_FEE,
                billing_period="2026-09",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.APPROVED,
                reviewed_by_admin_id="user-1",
                reviewed_by_admin_name="Алексей Николаев",
                reviewed_at=datetime.fromisoformat("2026-09-03T10:00:00"),
                created_at=datetime.fromisoformat("2026-09-03T08:30:00"),
            ),
            Contribution(
                id="cont-pending-1",
                user_id="user-4",
                user_name="Анна Сидорова",
                user_unit="кв. 24",
                amount=1500,
                category=ContributionCategory.MONTHLY_FEE,
                billing_period="2026-08",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.PENDING,
                comment_user="Оплата за август, проверьте чек",
                created_at=datetime.fromisoformat("2026-09-05T21:14:00"),
            ),
            Contribution(
                id="cont-pending-2",
                user_id="user-7",
                user_name="Ольга Смирнова",
                user_unit="кв. 42",
                amount=3000,
                category=ContributionCategory.TARGET_FUND,
                target_fund_id=1,
                target_fund_title="Автоматический шлагбаум и видеонаблюдение въезда",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.PENDING,
                comment_user="Сбор на шлагбаум от 42 квартиры",
                created_at=datetime.fromisoformat("2026-09-06T09:45:00"),
            ),
            Contribution(
                id="cont-rejected-1",
                user_id="user-4",
                user_name="Анна Сидорова",
                user_unit="кв. 24",
                amount=1500,
                category=ContributionCategory.MONTHLY_FEE,
                billing_period="2026-07",
                receipt_image_path=sample_receipt,
                status=ContributionStatus.REJECTED,
                comment_user="Взнос за июль",
                comment_admin="Сумма в прикрепленном чеке (750 ₽) не соответствует установленному тарифу (1 500 ₽). Пожалуйста, доплатите остаток или прикрепите верный чек.",
                reviewed_by_admin_id="user-1",
                reviewed_by_admin_name="Алексей Николаев",
                reviewed_at=datetime.fromisoformat("2026-08-29T10:00:00"),
                created_at=datetime.fromisoformat("2026-08-28T12:00:00"),
            ),
        ]
        db.add_all(contributions)
        db.commit()

        # 6. Expenses
        expenses = [
            Expense(
                id="exp-1",
                title="Замена прожекторов освещения во дворе (6 шт) и датчиков движения",
                category="Электрика",
                amount=14200,
                description="Куплены светодиодные уличные прожекторы Jazzway 50W (6 шт), монтажные коробки, клеммы WAGO и сумеречные реле. Установлены электриком Сергеем.",
                receipt_image_paths=[sample_receipt],
                created_by_admin_id="user-1",
                created_by_admin_name="Алексей Николаев",
                created_at=datetime.fromisoformat("2026-08-12T16:00:00"),
            ),
            Expense(
                id="exp-2",
                title="Аварийная гидродинамическая прочистка ливневой канализации",
                category="Аварийные работы",
                amount=18500,
                description="В связи с сильным ливнем произошло засорение колодца ливнестока у 2-го подъезда. Вызвана спецслужба с гидродинамической машиной высокого давления. Акт № 104.",
                receipt_image_paths=[sample_receipt],
                created_by_admin_id="user-1",
                created_by_admin_name="Алексей Николаев",
                created_at=datetime.fromisoformat("2026-08-18T19:00:00"),
            ),
            Expense(
                id="exp-3",
                title="Покупка саженцев туй, кустарников и грунта для субботника",
                category="Озеленение",
                amount=22400,
                target_fund_id=2,
                target_fund_title="Озеленение двора и детская зона",
                description="10 саженцев западной туи Смарагд (100-120см), 5 мешков плодородного грунта, удобрения длительного действия для дворовой аллеи.",
                receipt_image_paths=[sample_receipt],
                created_by_admin_id="user-2",
                created_by_admin_name="Марат Каримов",
                created_at=datetime.fromisoformat("2026-08-25T13:00:00"),
            ),
            Expense(
                id="exp-4",
                title="Хозтовары и дезинфицирующие средства для влажной уборки подъездов",
                category="Хознужды",
                amount=6800,
                description="Профессиональная химия для мытья плитки, новые швабры с отжимом, мусорные пакеты 120л, перчатки для технического персонала на сентябрь.",
                receipt_image_paths=[sample_receipt],
                created_by_admin_id="user-1",
                created_by_admin_name="Алексей Николаев",
                created_at=datetime.fromisoformat("2026-09-01T14:00:00"),
            ),
        ]
        db.add_all(expenses)
        db.commit()

        # 7. Announcements
        ann1 = Announcement(
            id="ann-1",
            title="📢 Ежемесячный финансовый отчет за Август 2026 и подготовка к субботнику",
            category="Новости",
            content="Уважаемые соседи! Публикуем краткие итоги расходования средств фонда за август.\n1. Выполнена гидропромывка ливнестока (18 500 ₽).\n2. Заменены прожекторы освещения (14 200 ₽).\n3. В рамках целевого фонда благоустройства закуплены туи.\nВ субботу, 12 сентября, в 11:00 приглашаем всех на общий субботник!",
            is_pinned=True,
            author_id="user-1",
            author_name="Алексей Николаев",
            author_role="Председатель ТСЖ",
            likes_count=18,
            liked_by_user_ids=["user-3", "user-4"],
            created_at=datetime.fromisoformat("2026-09-03T12:00:00"),
        )
        ann2 = Announcement(
            id="ann-2",
            title="🚧 Сбор средств на шлагбаум: собрано 70% от требуемой суммы!",
            category="Благоустройство",
            content="Продолжается сбор на установку автоматического шлагбаума и камер фиксации номеров.\nНа текущий момент собрано 195 000 ₽ из 280 000 ₽.\nКто еще не успел внести целевой взнос — вы можете сделать это в разделе «Внести взнос».",
            is_pinned=False,
            author_id="user-2",
            author_name="Марат Каримов",
            author_role="Ревизионная комиссия",
            likes_count=23,
            liked_by_user_ids=["user-3"],
            created_at=datetime.fromisoformat("2026-09-01T10:00:00"),
        )
        db.add_all([ann1, ann2])
        db.commit()

        # 8. Comments
        comm1 = AnnouncementComment(
            id="comm-1",
            announcement_id="ann-1",
            user_id="user-3",
            user_name="Иван Петров",
            user_unit="кв. 12",
            text="Спасибо совету дома за оперативное решение с ливневкой! Во время недавнего дождя луж действительно не было.",
            created_at=datetime.fromisoformat("2026-09-03T13:40:00"),
        )
        comm2 = AnnouncementComment(
            id="comm-2",
            announcement_id="ann-1",
            user_id="user-6",
            user_name="Елена Михайлова",
            user_unit="кв. 31",
            text="Обязательно выйдем на субботник всей семьей! Поможем высадить туи.",
            created_at=datetime.fromisoformat("2026-09-03T15:10:00"),
        )
        comm3 = AnnouncementComment(
            id="comm-3",
            announcement_id="ann-2",
            user_id="user-5",
            user_name="Сергей Васильев",
            user_unit="кв. 7",
            text="Поддерживаю! Двор забит чужими машинами из соседнего БЦ, шлагбаум жизненно необходим.",
            created_at=datetime.fromisoformat("2026-09-01T11:20:00"),
        )
        db.add_all([comm1, comm2, comm3])
        db.commit()

        print("База данных успешно наполнена данными, на 100% совпадающими с клиентом!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
