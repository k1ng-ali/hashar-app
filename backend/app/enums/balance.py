from enum import Enum


class BalanceStatusEnum(str, Enum):
    ok = "ok"  # всё оплачено ровно по текущий месяц
    debt = "debt"  # есть задолженность
    advance = "advance"  # оплачено вперёд
