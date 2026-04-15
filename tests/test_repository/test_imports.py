from datetime import date
from decimal import Decimal

from spending.repository.accounts import add_account
from spending.repository.imports import (
    check_file_hash,
    confirm_import,
    create_import,
    get_existing_fingerprints,
    get_staging_imports,
    insert_transactions,
    reject_import,
)


def test_create_import(conn):
    acct_id = add_account(
        conn, name="Chase", institution="Chase", account_type="credit_card"
    )
    imp_id = create_import(
        conn, account_id=acct_id, filename="test.ofx", file_hash="abc123"
    )
    assert imp_id > 0


def test_check_file_hash_not_exists(conn):
    assert check_file_hash(conn, "abc123") is False


def test_check_file_hash_exists(conn):
    acct_id = add_account(
        conn, name="Chase", institution="Chase", account_type="credit_card"
    )
    create_import(conn, account_id=acct_id, filename="test.ofx", file_hash="abc123")
    assert check_file_hash(conn, "abc123") is True


def test_insert_and_get_transactions(conn):
    acct_id = add_account(
        conn, name="Chase", institution="Chase", account_type="credit_card"
    )
    imp_id = create_import(
        conn, account_id=acct_id, filename="test.ofx", file_hash="abc123"
    )
    insert_transactions(
        conn,
        import_id=imp_id,
        account_id=acct_id,
        transactions_data=[
            {
                "date": date(2024, 1, 15),
                "amount": Decimal("-42.50"),
                "raw_description": "WHOLE FOODS #1234",
                "normalized_merchant": "WHOLE FOODS",
                "fingerprint": "fp1",
            }
        ],
    )
    fps = get_existing_fingerprints(conn, acct_id)
    assert "fp1" in fps


def test_confirm_import(conn):
    acct_id = add_account(
        conn, name="Chase", institution="Chase", account_type="credit_card"
    )
    imp_id = create_import(
        conn, account_id=acct_id, filename="test.ofx", file_hash="abc123"
    )
    confirm_import(conn, imp_id)
    staging = get_staging_imports(conn)
    assert len(staging) == 0


def test_reject_import(conn):
    acct_id = add_account(
        conn, name="Chase", institution="Chase", account_type="credit_card"
    )
    imp_id = create_import(
        conn, account_id=acct_id, filename="test.ofx", file_hash="abc123"
    )
    reject_import(conn, imp_id)
    staging = get_staging_imports(conn)
    assert len(staging) == 0
