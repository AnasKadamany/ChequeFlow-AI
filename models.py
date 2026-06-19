from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Cheque:
    amount: float
    currency: str
    due_date: date
    payee: Optional[str] = None
    cheque_number: Optional[str] = None
    bank: Optional[str] = None
