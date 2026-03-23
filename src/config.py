from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
ARCHIVE_DIR = PROJECT_ROOT / "archive"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"
COLUMN_MAPPING_FILE = CONFIG_DIR / "column_mapping.json"
RULES_FILE = CONFIG_DIR / "rules.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_column_aliases() -> dict[str, list[str]]:
    return _load_json(COLUMN_MAPPING_FILE)


@lru_cache(maxsize=1)
def load_rules() -> dict:
    return _load_json(RULES_FILE)


@lru_cache(maxsize=1)
def get_standard_columns() -> list[str]:
    aliases = load_column_aliases()
    rules = load_rules()

    columns: list[str] = []
    for bucket in [
        list(aliases.keys()),
        rules.get("required_columns", []),
        rules.get("output_columns", []),
        rules.get("drop_columns", []),
        rules.get("dedupe_keys_primary", []),
        rules.get("dedupe_keys_fallback", []),
        rules.get("cleaning_rules", {}).get("trim_whitespace", []),
        rules.get("cleaning_rules", {}).get("lowercase", []),
        rules.get("cleaning_rules", {}).get("digits_only", []),
        rules.get("cleaning_rules", {}).get("amount_decimal", []),
        list(rules.get("cleaning_rules", {}).get("date_format", {}).keys()),
    ]:
        for column in bucket:
            if column not in columns:
                columns.append(column)

    return columns
