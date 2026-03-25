from __future__ import annotations

import pandas as pd

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
    from .web_extractor import extract_web_records
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
    from web_extractor import extract_web_records


def _empty_result() -> dict:
    empty = pd.DataFrame()
    summary = {
        'source_mode': 'none',
        'files_processed': 0,
        'rows_read': 0,
        'rows_after_cleaning': 0,
        'duplicates_removed': 0,
        'invalid_rows': 0,
        'output_file': 'output/master.csv',
        'config_files': ['config/column_mapping.json', 'config/rules.json'],
    }
    return {
        'merged': empty,
        'cleaned': empty,
        'valid': empty,
        'invalid': empty,
        'output': empty,
        'rejected': empty,
        'summary': summary,
    }


def process_dataframes(
    dataframes: list[pd.DataFrame],
    file_names: list[str] | None = None,
    column_aliases: dict[str, list[str]] | None = None,
    rules: dict | None = None,
) -> dict:
    aliases = column_aliases or load_column_aliases()
    resolved_rules = rules or load_rules()
    source_names = file_names or [f'file_{index + 1}' for index in range(len(dataframes))]

    prepared_frames: list[pd.DataFrame] = []
    for index, dataframe in enumerate(dataframes):
        frame = dataframe.copy()
        if '_source_file' not in frame.columns:
            frame['_source_file'] = source_names[index]
        prepared_frames.append(frame)

    if not prepared_frames:
        return _empty_result()

    standardized_frames = [standardize_columns(dataframe, column_aliases=aliases) for dataframe in prepared_frames]
    merged_dataframe = merge_dataframes(standardized_frames)
    cleaned_dataframe = apply_cleaning_rules(merged_dataframe, rules=resolved_rules)
    valid_rows, invalid_rows = split_valid_and_invalid_rows(
        cleaned_dataframe,
        required_columns=resolved_rules.get('required_columns', []),
    )
    deduplicated_rows, duplicates_removed = deduplicate_rows(
        valid_rows,
        primary_keys=resolved_rules.get('dedupe_keys_primary', []),
        fallback_keys=resolved_rules.get('dedupe_keys_fallback', []),
    )
    output_dataframe = prepare_output_dataframe(
        deduplicated_rows,
        output_columns=resolved_rules.get('output_columns', []),
        drop_columns=resolved_rules.get('drop_columns', []),
    )
    rejected_dataframe = prepare_output_dataframe(
        invalid_rows,
        output_columns=resolved_rules.get('output_columns', []) + ['_error_reason'],
        drop_columns=resolved_rules.get('drop_columns', []),
    )

    summary = {
        'source_mode': 'files',
        'files_processed': int(len(prepared_frames)),
        'rows_read': int(sum(len(dataframe) for dataframe in prepared_frames)),
        'rows_after_cleaning': int(len(output_dataframe)),
        'duplicates_removed': int(duplicates_removed),
        'invalid_rows': int(len(rejected_dataframe)),
        'output_file': 'output/master.csv',
        'config_files': ['config/column_mapping.json', 'config/rules.json'],
    }

    return {
        'merged': merged_dataframe,
        'cleaned': cleaned_dataframe,
        'valid': deduplicated_rows,
        'invalid': invalid_rows,
        'output': output_dataframe,
        'rejected': rejected_dataframe,
        'summary': summary,
    }


def process_urls(
    urls: list[str],
    extract_fields: list[str] | None = None,
    fetch_html_func=None,
    column_aliases: dict[str, list[str]] | None = None,
    rules: dict | None = None,
) -> dict:
    extracted_dataframe = extract_web_records(
        urls=urls,
        extract_fields=extract_fields,
        fetch_html_func=fetch_html_func,
    )
    result = process_dataframes(
        dataframes=[extracted_dataframe] if not extracted_dataframe.empty else [],
        file_names=['url_import'],
        column_aliases=column_aliases,
        rules=rules,
    )
    result['extracted'] = extracted_dataframe
    result['summary']['source_mode'] = 'web'
    result['summary']['urls_processed'] = int(len(urls))
    result['summary']['successful_fetches'] = int((extracted_dataframe.get('fetch_status') == 'ok').sum()) if not extracted_dataframe.empty else 0
    result['summary']['failed_fetches'] = int((extracted_dataframe.get('fetch_status') == 'error').sum()) if not extracted_dataframe.empty else 0
    return result
