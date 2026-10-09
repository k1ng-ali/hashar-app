"""Публичный код фонда для поиска и ссылки-приглашения."""

import secrets

# Без похожих символов (0/O, 1/I/L), чтобы код было удобно диктовать
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8


def generate_fund_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
