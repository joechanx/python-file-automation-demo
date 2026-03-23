from __future__ import annotations

import re

import pandas as pd

try:
    from .config import get_standard_columns, load_column_aliases, load_rules
except ImportError:
    from config import get_standard_columns, load_column_aliases, load_rules


DIGIT_ONLY_PATTERN = re.compile(r"\D+")
HEADER_NORMALIZE_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_header(header: object) -> str:
    text = str(header).strip().lower()
    if text.startswith("_"):
        cleaned = HEADER_NORMALIZE_PATTERN.sub("_", text[1:]).strip("_")
        return f"_{cleaned}" if cleaned else "_"

    cleaned = HEADER_NORMALIZE_PATTERN.sub("_", text)
    return cleaned.strip("_")


def build_column_mapping(
    columns: list[object],
    column_aliases: dict[str, list[str]] | None = None,
) -> dict[object, str]:
    mapping: dict[object, str] = {}
    aliases = column_aliases or load_column_aliases()
    normalized_columns = {column: normalize_header(column) for column in columns}

    for target, alias_list in aliases.items():
        valid_aliases = {normalize_header(alias) for alias in alias_list}
        for original_column, normalized_column in normalized_columns.items():
            if normalized_column == target or normalized_column in valid_aliases:
                mapping[original_column] = target
                break

    return mapping


def standardize_columns(
    dataframe: pd.DataFrame,
    column_aliases: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    dataframe = dataframe.copy()
    mapping = build_column_mapping(list(dataframe.columns), column_aliases=column_aliases)
    dataframe = dataframe.rename(columns=mapping)
    dataframe.columns = [normalize_header(column) for column in dataframe.columns]
    return dataframe


def _to_optional_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _clean_lowercase_text(value: object) -> str | None:
    text = _to_optional_text(value)
    if text is None:
        return None
    return text.lower()


def _clean_digits_only(value: object) -> str | None:
    text = _to_optional_text(value)
    if text is None:
        return None
    digits = DIGIT_ONLY_PATTERN.sub("", text)
    return digits or None


def _clean_date(value: object, output_format: str) -> str | None:
    if pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime(output_format)


def ensure_configured_columns(
    dataframe: pd.DataFrame,
    standard_columns: list[str] | None = None,
) -> pd.DataFrame:
    dataframe = dataframe.copy()
    for column in (standard_columns or get_standard_columns()):
        if column not in dataframe.columns:
            dataframe[column] = None
    return dataframe


def apply_cleaning_rules(
    dataframe: pd.DataFrame,
    rules: dict | None = None,
) -> pd.DataFrame:
    dataframe = ensure_configured_columns(dataframe)
    config = rules or load_rules()
    cleaning_rules = config.get("cleaning_rules", {})

    for column in cleaning_rules.get("trim_whitespace", []):
        dataframe[column] = dataframe[column].apply(_to_optional_text)

    for column in cleaning_rules.get("lowercase", []):
        dataframe[column] = dataframe[column].apply(_clean_lowercase_text)

    for column in cleaning_rules.get("digits_only", []):
        dataframe[column] = dataframe[column].apply(_clean_digits_only)

    for column, output_format in cleaning_rules.get("date_format", {}).items():
        dataframe[column] = dataframe[column].apply(lambda value: _clean_date(value, output_format))

    return dataframe


def split_valid_and_invalid_rows(
    dataframe: pd.DataFrame,
    required_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dataframe = dataframe.copy()
    config = load_rules()
    fields = required_columns or config.get("required_columns", [])

    def row_error_reason(row: pd.Series) -> str:
        missing_fields = [field for field in fields if not row.get(field)]
        if missing_fields:
            return f"missing_required_fields:{','.join(missing_fields)}"
        return ""

    dataframe["_error_reason"] = dataframe.apply(row_error_reason, axis=1)
    invalid_rows = dataframe[dataframe["_error_reason"] != ""].copy()
    valid_rows = dataframe[dataframe["_error_reason"] == ""].copy()

    return valid_rows, invalid_rows


def deduplicate_rows(
    dataframe: pd.DataFrame,
    primary_keys: list[str] | None = None,
    fallback_keys: list[str] | None = None,
) -> tuple[pd.DataFrame, int]:
    dataframe = dataframe.copy()
    config = load_rules()
    primary = primary_keys or config.get("dedupe_keys_primary", [])
    fallback = fallback_keys or config.get("dedupe_keys_fallback", [])
    before_count = len(dataframe)

    if primary and all(key in dataframe.columns for key in primary):
        primary_missing = dataframe[primary].isna().any(axis=1)
        with_primary = dataframe[~primary_missing].drop_duplicates(subset=primary, keep="first")
        without_primary = dataframe[primary_missing]

        if fallback and all(key in without_primary.columns for key in fallback):
            without_primary = without_primary.drop_duplicates(subset=fallback, keep="first")

        dataframe = pd.concat([with_primary, without_primary], ignore_index=True)
    elif fallback and all(key in dataframe.columns for key in fallback):
        dataframe = dataframe.drop_duplicates(subset=fallback, keep="first")

    removed_count = before_count - len(dataframe)
    return dataframe, removed_count


def prepare_output_dataframe(
    dataframe: pd.DataFrame,
    output_columns: list[str] | None = None,
    drop_columns: list[str] | None = None,
) -> pd.DataFrame:
    dataframe = dataframe.copy()
    config = load_rules()
    columns_to_output = output_columns or config.get("output_columns", [])
    columns_to_drop = set(drop_columns or config.get("drop_columns", []))

    if columns_to_drop:
        dataframe = dataframe.drop(columns=[column for column in columns_to_drop if column in dataframe.columns])

    if columns_to_output:
        dataframe = ensure_configured_columns(dataframe, columns_to_output)
        dataframe = dataframe[[column for column in columns_to_output if column in dataframe.columns]]

    return dataframe
