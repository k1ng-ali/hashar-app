from enum import Enum


class FundRoleEnum(str, Enum):
    resident = "resident"  # участник фонда (жилец)
    admin = "admin"  # член совета (ревизор / модератор)
    chairman = "chairman"  # председатель — у фонда всегда ровно один


class MemberStatusEnum(str, Enum):
    pending = "pending"  # заявка на вступление ждёт решения совета
    active = "active"  # участник фонда
    rejected = "rejected"  # заявка отклонена (можно подать снова)
    blocked = "blocked"  # заблокирован советом
    left = "left"  # вышел из фонда (запись и долг сохраняются, можно вернуться)


# Роли совета фонда — им доступно управление
COUNCIL_ROLES = (FundRoleEnum.admin, FundRoleEnum.chairman)
