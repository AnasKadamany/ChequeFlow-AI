from datetime import date
import pytest
from models import Cheque
from reminders import reminder_message


def _cheque(**kwargs):
    defaults = dict(amount=1000.0, currency="SAR", due_date=date(2026, 7, 1))
    return Cheque(**{**defaults, **kwargs})


def test_overdue():
    msg = reminder_message(_cheque(due_date=date(2026, 6, 10)), today=date(2026, 6, 19))
    assert "OVERDUE" in msg
    assert "9 day" in msg


def test_due_today():
    today = date(2026, 6, 19)
    msg = reminder_message(_cheque(due_date=today), today=today)
    assert "TODAY" in msg


def test_due_in_one_day():
    msg = reminder_message(_cheque(due_date=date(2026, 6, 20)), today=date(2026, 6, 19))
    assert "1 day" in msg
    assert "urgent" in msg


def test_due_in_future():
    msg = reminder_message(_cheque(due_date=date(2026, 7, 5)), today=date(2026, 6, 19))
    assert "16 days" in msg


def test_optional_fields_included():
    c = _cheque(payee="Acme Corp", cheque_number="001234", bank="SNB")
    msg = reminder_message(c, today=date(2026, 6, 19))
    assert "Acme Corp" in msg
    assert "001234" in msg
    assert "SNB" in msg


def test_optional_fields_absent():
    msg = reminder_message(_cheque(), today=date(2026, 6, 19))
    assert "Payee" not in msg
    assert "Cheque #" not in msg


def test_amount_formatted():
    c = _cheque(amount=50000.5, currency="USD")
    msg = reminder_message(c, today=date(2026, 6, 19))
    assert "USD 50,000.50" in msg
