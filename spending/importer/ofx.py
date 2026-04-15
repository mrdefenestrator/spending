from decimal import Decimal
from pathlib import Path

from ofxparse import OfxParser

from spending.types import AccountMeta, ImportResult, ParsedTransaction

_ACCOUNT_TYPE_MAP = {
    "CHECKING": "checking",
    "SAVINGS": "savings",
    "MONEYMRKT": "savings",
    "CREDITLINE": "credit",
    "CREDITCARD": "credit",
}


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


def extract_ofx_metadata(file_path: str | Path) -> AccountMeta | None:
    """Parse OFX institution/account metadata without importing transactions.

    Returns None on any parse failure so callers degrade gracefully.
    """
    try:
        with open(file_path, "rb") as f:
            ofx = OfxParser.parse(f)

        account = ofx.account
        if not account:
            return None

        institution = ""
        if account.institution and account.institution.organization:
            institution = account.institution.organization

        raw_type = (account.account_type or "").upper()
        account_type = _ACCOUNT_TYPE_MAP.get(raw_type, "other")

        account_id = account.account_id or ""
        last4 = account_id[-4:] if len(account_id) >= 4 else account_id

        parts = []
        if institution:
            parts.append(institution)
        if account_type and account_type != "other":
            parts.append(account_type.capitalize())
        if last4:
            parts.append(f"...{last4}")
        suggested_name = " ".join(parts) if parts else "New Account"

        return AccountMeta(
            institution=institution,
            account_type=account_type,
            suggested_name=suggested_name,
        )
    except Exception:
        return None
