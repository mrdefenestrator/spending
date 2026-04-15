import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import yaml

from spending.types import ImportResult, ParsedTransaction


def parse_csv(file_path: str | Path, config_path: str | Path) -> ImportResult:
    with open(config_path) as f:
        config = yaml.safe_load(f)

    date_col = config["date_column"]
    amount_col = config["amount_column"]
    desc_col = config["description_column"]
    date_fmt = config["date_format"]

    transactions: list[ParsedTransaction] = []

    with open(file_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            txn_date = datetime.strptime(row[date_col].strip(), date_fmt).date()
            amount = Decimal(row[amount_col].strip().replace(",", ""))
            description = row[desc_col].strip()

            transactions.append(
                ParsedTransaction(
                    date=txn_date,
                    amount=amount,
                    raw_description=description,
                )
            )

    return ImportResult(
        transactions=transactions,
        account_name=config.get("account_name"),
    )


def detect_institution_config(
    csv_path: str | Path, configs_dir: str | Path
) -> str | None:
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return None

    headers = [h.strip() for h in headers]

    configs_dir = Path(configs_dir)
    for config_file in configs_dir.glob("*.yaml"):
        with open(config_file) as f:
            config = yaml.safe_load(f)

        pattern = config.get("header_pattern", [])
        if pattern and all(col in headers for col in pattern):
            return str(config_file)

    return None
