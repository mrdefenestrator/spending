from decimal import Decimal
from pathlib import Path

from ofxparse import OfxParser

from spending.types import ImportResult, ParsedTransaction


def parse_ofx(file_path: str | Path) -> ImportResult:
    with open(file_path, "rb") as f:
        ofx = OfxParser.parse(f)

    transactions: list[ParsedTransaction] = []

    account = ofx.account
    if account and account.statement:
        for txn in account.statement.transactions:
            transactions.append(
                ParsedTransaction(
                    date=txn.date.date() if hasattr(txn.date, "date") else txn.date,
                    amount=Decimal(str(txn.amount)),
                    raw_description=txn.payee or txn.memo or "",
                )
            )

    return ImportResult(transactions=transactions, account_name=None)
