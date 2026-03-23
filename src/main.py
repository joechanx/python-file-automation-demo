from __future__ import annotations

try:
    from .cleaner import (
        apply_cleaning_rules,
        deduplicate_rows,
        prepare_output_dataframe,
        split_valid_and_invalid_rows,
        standardize_columns,
    )
    from .config import load_column_aliases, load_rules
    from .merger import merge_dataframes
    from .reader import load_input_data
    from .reporter import setup_logging, write_master_file, write_rejected_rows, write_summary
    from .utils import archive_file, ensure_directories
except ImportError:
    from cleaner import (
        apply_cleaning_rules,
        deduplicate_rows,
        prepare_output_dataframe,
        split_valid_and_invalid_rows,
        standardize_columns,
    )
    from config import load_column_aliases, load_rules
    from merger import merge_dataframes
    from reader import load_input_data
    from reporter import setup_logging, write_master_file, write_rejected_rows, write_summary
    from utils import archive_file, ensure_directories


def run() -> dict:
    ensure_directories()
    logger = setup_logging()
    column_aliases = load_column_aliases()
    rules = load_rules()

    dataframes, file_paths = load_input_data()
    if not dataframes:
        logger.info("No input files found.")
        summary = {
            "files_processed": 0,
            "rows_read": 0,
            "rows_after_cleaning": 0,
            "duplicates_removed": 0,
            "invalid_rows": 0,
            "output_file": None,
        }
        write_summary(summary)
        return summary

    standardized_frames = [standardize_columns(dataframe, column_aliases=column_aliases) for dataframe in dataframes]
    merged_dataframe = merge_dataframes(standardized_frames)
    cleaned_dataframe = apply_cleaning_rules(merged_dataframe, rules=rules)

    valid_rows, invalid_rows = split_valid_and_invalid_rows(
        cleaned_dataframe,
        required_columns=rules.get("required_columns", []),
    )
    deduplicated_rows, duplicates_removed = deduplicate_rows(
        valid_rows,
        primary_keys=rules.get("dedupe_keys_primary", []),
        fallback_keys=rules.get("dedupe_keys_fallback", []),
    )

    output_dataframe = prepare_output_dataframe(
        deduplicated_rows,
        output_columns=rules.get("output_columns", []),
        drop_columns=rules.get("drop_columns", []),
    )
    rejected_dataframe = prepare_output_dataframe(
        invalid_rows,
        output_columns=rules.get("output_columns", []) + ["_error_reason"],
        drop_columns=rules.get("drop_columns", []),
    )

    output_path = write_master_file(output_dataframe)
    write_rejected_rows(rejected_dataframe)
    summary = {
        "files_processed": len(file_paths),
        "rows_read": int(len(merged_dataframe)),
        "rows_after_cleaning": int(len(output_dataframe)),
        "duplicates_removed": int(duplicates_removed),
        "invalid_rows": int(len(rejected_dataframe)),
        "output_file": str(output_path.relative_to(output_path.parent.parent)),
        "config_files": ["config/column_mapping.json", "config/rules.json"],
    }
    write_summary(summary)

    for file_path in file_paths:
        archived_path = archive_file(file_path)
        logger.info("Archived processed file: %s", archived_path.name)

    logger.info("Processing completed: %s", summary)
    return summary


if __name__ == "__main__":
    result = run()
    print("Processing completed.")
    print(result)
