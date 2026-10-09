from enum import Enum


class CurrencyEnum(str, Enum):
    """Валюты счетов фонда. Курсы платформа не пересчитывает — суммы вводят пользователи."""

    tjs = "tjs"
    rub = "rub"
    usd = "usd"
