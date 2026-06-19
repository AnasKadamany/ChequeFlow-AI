"""Scheduled daily reminder broadcast.

Run standalone (e.g. via cron or APScheduler) to push reminders for
cheques that are due soon. Reads cheques from a simple JSON store.
"""

import json
import logging
import os
from datetime import date, datetime
from pathlib import Path

import telegram

from models import Cheque
from reminders import reminder_message

logger = logging.getLogger(__name__)

STORE_PATH = Path(os.environ.get("CHEQUE_STORE", "cheques.json"))
REMIND_DAYS_BEFORE = {7, 3, 1, 0}


def load_cheques() -> list[tuple[int, Cheque]]:
    """Return list of (chat_id, Cheque) pairs from the JSON store."""
    if not STORE_PATH.exists():
        return []
    records = json.loads(STORE_PATH.read_text())
    result = []
    for r in records:
        cheque = Cheque(
            amount=r["amount"],
            currency=r["currency"],
            due_date=datetime.strptime(r["due_date"], "%Y-%m-%d").date(),
            payee=r.get("payee"),
            cheque_number=r.get("cheque_number"),
            bank=r.get("bank"),
        )
        result.append((r["chat_id"], cheque))
    return result


def save_cheque(chat_id: int, cheque: Cheque) -> None:
    records = []
    if STORE_PATH.exists():
        records = json.loads(STORE_PATH.read_text())
    records.append(
        {
            "chat_id": chat_id,
            "amount": cheque.amount,
            "currency": cheque.currency,
            "due_date": cheque.due_date.isoformat(),
            "payee": cheque.payee,
            "cheque_number": cheque.cheque_number,
            "bank": cheque.bank,
        }
    )
    STORE_PATH.write_text(json.dumps(records, indent=2))


async def send_due_reminders() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    bot = telegram.Bot(token)
    today = date.today()

    for chat_id, cheque in load_cheques():
        days_left = (cheque.due_date - today).days
        if days_left in REMIND_DAYS_BEFORE or days_left < 0:
            msg = reminder_message(cheque, today)
            try:
                await bot.send_message(chat_id=chat_id, text=msg)
                logger.info("Reminder sent to %s for cheque due %s", chat_id, cheque.due_date)
            except Exception:
                logger.exception("Failed to send reminder to %s", chat_id)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    asyncio.run(send_due_reminders())
