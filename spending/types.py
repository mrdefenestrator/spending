from datetime import date
from decimal import Decimal
from typing import TypedDict


class ParsedTransaction(TypedDict):
    date: date
    amount: Decimal
    raw_description: str


class ImportResult(TypedDict):
    transactions: list[ParsedTransaction]
    account_name: str | None
