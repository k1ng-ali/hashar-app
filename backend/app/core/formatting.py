"""
Проверка и единый формат банковских реквизитов и телефонов.

Те же правила — во фронтенде (src/shared/lib/formatters.ts), чтобы форма
форматировала ввод на лету, а API не принимало некорректные данные.
"""

import re

CARD_DIGITS = 16
ACCOUNT_PATTERN = re.compile(r"^[A-Z0-9]{10,34}$")
PHONE_DIGITS = (10, 15)  # E.164: до 15 цифр с кодом страны


def _group(value: str, size: int = 4) -> str:
    return " ".join(value[i : i + size] for i in range(0, len(value), size))


def format_card(raw: str) -> str:
    """«2202203456789101» → «2202 2034 5678 9101». ValueError, если не 16 цифр."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) != CARD_DIGITS or len(re.sub(r"[\s-]", "", raw)) != CARD_DIGITS:
        raise ValueError(f"card number must contain exactly {CARD_DIGITS} digits")
    return _group(digits)


def format_account(raw: str) -> str:
    """Номер счёта / IBAN: 10–34 латинских букв и цифр, группами по 4."""
    value = re.sub(r"[\s-]", "", raw).upper()
    if not ACCOUNT_PATTERN.match(value):
        raise ValueError("account number must be 10-34 latin letters and digits")
    return _group(value)


def format_phone(raw: str) -> str:
    """
    Международный формат: «+» и 10–15 цифр с кодом страны.
    +992 90 123 45 67 · +7 916 123-45-67 · остальные — группами по 3.
    """
    digits = re.sub(r"\D", "", raw)
    if not PHONE_DIGITS[0] <= len(digits) <= PHONE_DIGITS[1]:
        raise ValueError("phone must contain 10-15 digits with the country code")
    if digits.startswith("992") and len(digits) == 12:
        d = digits[3:]
        return f"+992 {d[:2]} {d[2:5]} {d[5:7]} {d[7:]}"
    if digits.startswith("7") and len(digits) == 11:
        d = digits[1:]
        return f"+7 {d[:3]} {d[3:6]}-{d[6:8]}-{d[8:]}"
    return "+" + " ".join(digits[i : i + 3] for i in range(0, len(digits), 3))


def display_phone(phone: str | None) -> str:
    """Телефон для показа (CSV, письма): единый формат, а если он некорректен — как есть."""
    if not phone:
        return ""
    try:
        return format_phone(phone)
    except ValueError:
        return phone
