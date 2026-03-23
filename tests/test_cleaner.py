from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cleaner import (  # noqa: E402
    apply_cleaning_rules,
    deduplicate_rows,
    prepare_output_dataframe,
    split_valid_and_invalid_rows,
    standardize_columns,
)
from src.config import load_column_aliases, load_rules  # noqa: E402


def test_standardize_columns_uses_alias_mapping() -> None:
    dataframe = pd.DataFrame(
        {
            "Full Name": [" Alice "],
            "Email Address": ["Alice@Example.com"],
            "Mobile": ["0912-345-678"],
            "Signup Date": ["2026/03/01"],
            "Business Name": [" Example Co. "],
        }
    )

    standardized = standardize_columns(dataframe, column_aliases=load_column_aliases())

    assert list(standardized.columns) == ["name", "email", "phone", "date", "company"]


def test_cleaning_rules_and_required_columns_are_config_driven() -> None:
    dataframe = pd.DataFrame(
        {
            "name": [" Alice ", "Bob"],
            "email": ["Alice@Example.com", None],
            "phone": ["0912-345-678", "02 1234 5678"],
            "date": ["2026/03/01", "invalid-date"],
            "company": [" Example Co. ", "Beta Ltd"],
            "status": [" New ", "Qualified"],
        }
    )

    cleaned = apply_cleaning_rules(dataframe, rules=load_rules())
    valid_rows, invalid_rows = split_valid_and_invalid_rows(
        cleaned,
        required_columns=load_rules()["required_columns"],
    )

    assert cleaned.loc[0, "email"] == "alice@example.com"
    assert cleaned.loc[0, "phone"] == "0912345678"
    assert cleaned.loc[0, "date"] == "2026-03-01"
    assert cleaned.loc[0, "company"] == "Example Co."
    assert cleaned.loc[0, "status"] == "New"
    assert len(valid_rows) == 1
    assert len(invalid_rows) == 1
    assert invalid_rows.iloc[0]["_error_reason"] == "missing_required_fields:email,date"


def test_deduplicate_and_prepare_output_follow_rules() -> None:
    rules = load_rules()
    dataframe = pd.DataFrame(
        {
            "name": ["Alice", "Alice", "Carol"],
            "email": ["alice@example.com", "alice@example.com", None],
            "phone": ["0912345678", "0912345678", "0223456789"],
            "date": ["2026-03-01", "2026-03-01", "2026-03-02"],
            "company": ["Example Co.", "Example Co.", "Gamma Inc."],
            "status": ["New", "New", "Qualified"],
            "extra_note": ["x", "y", "z"],
            "_source_file": ["a.csv", "b.csv", "c.csv"],
        }
    )

    deduplicated, removed = deduplicate_rows(
        dataframe,
        primary_keys=rules["dedupe_keys_primary"],
        fallback_keys=rules["dedupe_keys_fallback"],
    )
    output = prepare_output_dataframe(
        deduplicated,
        output_columns=rules["output_columns"],
        drop_columns=rules["drop_columns"],
    )

    assert removed == 1
    assert list(output.columns) == rules["output_columns"]
    assert "extra_note" not in output.columns


def test_internal_source_file_column_is_preserved() -> None:
    dataframe = pd.DataFrame({"_source_file": ["sample.csv"]})
    standardized = standardize_columns(dataframe, column_aliases=load_column_aliases())
    assert list(standardized.columns) == ["_source_file"]



def test_apply_cleaning_rules_normalizes_amount_decimal() -> None:
    dataframe = pd.DataFrame(
        {
            "amount": ["1000", "1,000", "$1,000", "NT$ 1,000.5", "(1,200.75)", None, "abc"]
        }
    )

    rules = {
        "cleaning_rules": {
            "amount_decimal": ["amount"]
        }
    }

    cleaned = apply_cleaning_rules(dataframe, rules=rules)

    assert cleaned["amount"].tolist() == [
        "1000.00",
        "1000.00",
        "1000.00",
        "1000.50",
        "-1200.75",
        None,
        None,
    ]
