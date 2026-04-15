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


class AccountMeta(TypedDict):
    institution: str       # e.g. "Chase" (empty string if unavailable)
    account_type: str      # "checking" | "savings" | "credit" | "other"
    suggested_name: str    # e.g. "Chase Checking ...7890"
