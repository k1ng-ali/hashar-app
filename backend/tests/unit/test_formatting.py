import pytest

from app.core.formatting import format_account, format_card, format_phone
from app.schemas.account import RequisiteCreateIn


def test_card_needs_exactly_16_digits():
    assert format_card("2202203456789101") == "2202 2034 5678 9101"
    assert format_card("2202-2034-5678-9101") == "2202 2034 5678 9101"
    with pytest.raises(ValueError):
        format_card("2202 2034 5678 910")
    with pytest.raises(ValueError):
        format_card("23432432432423432")
    with pytest.raises(ValueError):
        format_card("2202 2034 5678 91ab")


def test_account_is_grouped_and_uppercased():
    assert format_account("tj22 0000 1111 2222 3333") == "TJ22 0000 1111 2222 3333"
    with pytest.raises(ValueError):
        format_account("12345")


def test_phone_formats_by_country():
    assert format_phone("+992901234567") == "+992 90 123 45 67"
    assert format_phone("8 (916) 123-45-67".replace("8", "7", 1)) == "+7 916 123-45-67"
    assert format_phone("+44 20 7946 0958") == "+442 079 460 958"
    with pytest.raises(ValueError):
        format_phone("0098263")


def test_requisite_schema_normalizes():
    payload = RequisiteCreateIn(
        currency="tjs",
        kind="card",
        bank_name="Алиф",
        card_or_account_number="4444888812345678",
        recipient_name="Али",
        phone_number="992901234567",
    )
    assert payload.card_or_account_number == "4444 8888 1234 5678"
    assert payload.phone_number == "+992 90 123 45 67"

    with pytest.raises(ValueError):
        RequisiteCreateIn(
            currency="tjs", bank_name="ДС", card_or_account_number="23432432432423432", recipient_name="Али"
        )
