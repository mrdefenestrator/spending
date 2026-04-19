from datetime import date
from decimal import Decimal

import pytest

from spending.importer.csv_parser import (
    parse_csv,
    detect_institution_config,
    _parse_signed_dollar,
)


def test_parse_csv(sample_csv, tmp_path):
    config_path = tmp_path / "inst.yaml"
    config_path.write_text(
        """
name: Test Bank
institution: Test
date_column: "Transaction Date"
amount_column: "Amount"
description_column: "Description"
date_format: "%m/%d/%Y"
account_name: "Test Card"
header_pattern:
  - "Transaction Date"
  - "Post Date"
  - "Description"
  - "Category"
  - "Type"
  - "Amount"
"""
    )
    result = parse_csv(sample_csv, str(config_path))
    assert len(result["transactions"]) == 4
    assert result["account_name"] == "Test Card"


def test_parse_csv_amounts(sample_csv, tmp_path):
    config_path = tmp_path / "inst.yaml"
    config_path.write_text(
        """
name: Test Bank
institution: Test
date_column: "Transaction Date"
amount_column: "Amount"
description_column: "Description"
date_format: "%m/%d/%Y"
account_name: null
header_pattern: []
"""
    )
    result = parse_csv(sample_csv, str(config_path))
    txn = result["transactions"][0]
    assert txn["date"] == date(2024, 1, 15)
    assert txn["amount"] == Decimal("-42.50")
    assert txn["raw_description"] == "WHOLE FOODS MARKET #10234"


def test_detect_institution_config(sample_csv, tmp_path):
    config_dir = tmp_path / "institutions"
    config_dir.mkdir()
    config_file = config_dir / "test.yaml"
    config_file.write_text(
        """
name: Test Bank
institution: Test
date_column: "Transaction Date"
amount_column: "Amount"
description_column: "Description"
date_format: "%m/%d/%Y"
account_name: null
header_pattern:
  - "Transaction Date"
  - "Post Date"
  - "Description"
  - "Category"
  - "Type"
  - "Amount"
"""
    )
    detected = detect_institution_config(sample_csv, str(config_dir))
    assert detected is not None
    assert "Test Bank" in open(detected).read()


@pytest.mark.parametrize(
    "value,expected",
    [
        ("+ $46.74", Decimal("46.74")),
        ("- $208.85", Decimal("-208.85")),
        ("+ $1,234.56", Decimal("1234.56")),
        ("- $0.50", Decimal("-0.50")),
    ],
)
def test_parse_signed_dollar(value, expected):
    assert _parse_signed_dollar(value) == expected


def test_parse_csv_venmo(sample_venmo_csv, tmp_path):
    config_path = tmp_path / "venmo.yaml"
    config_path.write_text(
        """
name: Venmo
institution: Venmo
header_row: 2
date_column: "Datetime"
date_format: "%Y-%m-%dT%H:%M:%S"
amount_column: "Amount (total)"
amount_format: signed_dollar
description_column: "Note"
type_column: "Type"
party_columns:
  - "From"
  - "To"
account_name: null
header_pattern:
  - "ID"
  - "Datetime"
  - "Amount (total)"
  - "From"
"""
    )
    result = parse_csv(sample_venmo_csv, str(config_path))
    # 2 payments + 1 standard transfer; opening balance and footer rows skipped
    assert len(result["transactions"]) == 3
    txns = result["transactions"]
    assert txns[0]["date"] == date(2026, 4, 3)
    assert txns[0]["amount"] == Decimal("46.74")
    assert txns[0]["raw_description"] == "Payment: March phone bill (Alice Smith)"
    assert txns[1]["raw_description"] == "Payment: Dinner (Bob Jones)"
    assert txns[2]["amount"] == Decimal("-66.74")
    assert txns[2]["raw_description"] == "Standard Transfer"


def test_detect_institution_config_venmo(sample_venmo_csv, tmp_path):
    config_dir = tmp_path / "institutions"
    config_dir.mkdir()
    config_file = config_dir / "venmo.yaml"
    config_file.write_text(
        """
name: Venmo
institution: Venmo
header_row: 2
date_column: "Datetime"
date_format: "%Y-%m-%dT%H:%M:%S"
amount_column: "Amount (total)"
amount_format: signed_dollar
description_column: "Note"
account_name: null
header_pattern:
  - "ID"
  - "Datetime"
  - "Amount (total)"
  - "From"
"""
    )
    detected = detect_institution_config(sample_venmo_csv, str(config_dir))
    assert detected is not None
    assert "Venmo" in open(detected).read()


def test_detect_institution_config_no_match(sample_csv, tmp_path):
    config_dir = tmp_path / "institutions"
    config_dir.mkdir()
    config_file = config_dir / "other.yaml"
    config_file.write_text(
        """
name: Other Bank
institution: Other
date_column: "Date"
amount_column: "Amt"
description_column: "Desc"
date_format: "%Y-%m-%d"
account_name: null
header_pattern:
  - "Date"
  - "Amt"
  - "Desc"
"""
    )
    detected = detect_institution_config(sample_csv, str(config_dir))
    assert detected is None
