"""Справочные категории. На фронтенде подписи берутся из i18n по коду."""

from enum import Enum


class ExpenseCategoryEnum(str, Enum):
    repair = "repair"  # ремонт
    electrical = "electrical"  # электрика
    emergency = "emergency"  # аварийные работы
    household = "household"  # хознужды
    landscaping = "landscaping"  # озеленение
    cctv = "cctv"  # видеонаблюдение


class TargetFundCategoryEnum(str, Enum):
    security = "security"  # безопасность
    landscaping = "landscaping"  # благоустройство
    major_repair = "major_repair"  # капремонт
    infrastructure = "infrastructure"  # инфраструктура


class AnnouncementCategoryEnum(str, Enum):
    news = "news"  # новости
    meeting = "meeting"  # собрание
    emergency = "emergency"  # аварийные работы
    cleanup = "cleanup"  # субботник
    finance = "finance"  # движение по счетам фонда (создаётся автоматически при переводах)
