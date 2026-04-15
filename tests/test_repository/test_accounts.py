import pytest
from sqlalchemy.exc import IntegrityError

from spending.repository.accounts import (
    add_account,
    delete_account,
    edit_account,
    get_account_by_name,
    list_accounts,
)


def test_add_and_list_accounts(conn):
    add_account(
        conn, name="Chase Visa", institution="Chase", account_type="credit_card"
    )
    add_account(conn, name="BofA Checking", institution="BofA", account_type="checking")
    accts = list_accounts(conn)
    assert len(accts) == 2
    assert accts[0]["name"] == "BofA Checking"


def test_add_duplicate_name_fails(conn):
    add_account(
        conn, name="Chase Visa", institution="Chase", account_type="credit_card"
    )
    with pytest.raises(IntegrityError):
        add_account(
            conn, name="Chase Visa", institution="Chase", account_type="credit_card"
        )


def test_get_account_by_name(conn):
    add_account(
        conn, name="Chase Visa", institution="Chase", account_type="credit_card"
    )
    acct = get_account_by_name(conn, "Chase Visa")
    assert acct is not None
    assert acct["institution"] == "Chase"


def test_get_account_by_name_not_found(conn):
    acct = get_account_by_name(conn, "Nonexistent")
    assert acct is None


def test_edit_account(conn):
    add_account(
        conn, name="Chase Visa", institution="Chase", account_type="credit_card"
    )
    acct = get_account_by_name(conn, "Chase Visa")
    edit_account(conn, acct["id"], name="Chase Freedom")
    updated = get_account_by_name(conn, "Chase Freedom")
    assert updated is not None


def test_delete_account(conn):
    add_account(
        conn, name="Chase Visa", institution="Chase", account_type="credit_card"
    )
    acct = get_account_by_name(conn, "Chase Visa")
    delete_account(conn, acct["id"])
    assert list_accounts(conn) == []
