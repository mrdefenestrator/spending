from datetime import date
from decimal import Decimal

from spending.importer.ofx import extract_ofx_metadata, parse_ofx


def test_parse_ofx_returns_transactions(sample_ofx):
    result = parse_ofx(sample_ofx)
    assert len(result["transactions"]) == 2


def test_parse_ofx_debit_transaction(sample_ofx):
    result = parse_ofx(sample_ofx)
    txn = result["transactions"][0]
    assert txn["date"] == date(2024, 1, 15)
    assert txn["amount"] == Decimal("-42.50")
    assert txn["raw_description"] == "WHOLE FOODS MARKET #10234"


def test_parse_ofx_credit_transaction(sample_ofx):
    result = parse_ofx(sample_ofx)
    txn = result["transactions"][1]
    assert txn["date"] == date(2024, 1, 16)
    assert txn["amount"] == Decimal("1500.00")


def test_parse_ofx_account_name_is_none(sample_ofx):
    result = parse_ofx(sample_ofx)
    assert result["account_name"] is None


def test_extract_ofx_metadata_institution(sample_ofx_with_meta):
    meta = extract_ofx_metadata(sample_ofx_with_meta)
    assert meta is not None
    assert meta["institution"] == "Chase"


def test_extract_ofx_metadata_account_type(sample_ofx_with_meta):
    meta = extract_ofx_metadata(sample_ofx_with_meta)
    assert meta is not None
    assert meta["account_type"] == "checking"


def test_extract_ofx_metadata_suggested_name(sample_ofx_with_meta):
    meta = extract_ofx_metadata(sample_ofx_with_meta)
    assert meta is not None
    assert "7890" in meta["suggested_name"]
    assert "Chase" in meta["suggested_name"]


def test_extract_ofx_metadata_corrupt_file(tmp_path):
    bad = tmp_path / "bad.ofx"
    bad.write_text("not valid ofx content at all")
    meta = extract_ofx_metadata(bad)
    assert meta is None
