from datetime import date
from models import Cheque


def reminder_message(cheque: Cheque, today: date) -> str:
    days_left = (cheque.due_date - today).days
    amount_str = f"{cheque.currency} {cheque.amount:,.2f}"

    if days_left < 0:
        urgency = f"OVERDUE by {abs(days_left)} day(s)"
    elif days_left == 0:
        urgency = "due TODAY"
    elif days_left <= 3:
        urgency = f"due in {days_left} day(s) — urgent"
    else:
        urgency = f"due in {days_left} days ({cheque.due_date.strftime('%d %b %Y')})"

    parts = [f"Cheque for {amount_str} is {urgency}."]
    if cheque.payee:
        parts.append(f"Payee: {cheque.payee}")
    if cheque.cheque_number:
        parts.append(f"Cheque #: {cheque.cheque_number}")
    if cheque.bank:
        parts.append(f"Bank: {cheque.bank}")

    return "\n".join(parts)
