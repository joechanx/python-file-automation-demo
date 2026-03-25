from __future__ import annotations

import csv
import io
from pathlib import Path

import pandas as pd


def normalize_urls(urls: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for url in urls:
        value = str(url).strip()
        if not value:
            continue
        if not value.startswith(("http://", "https://")):
            value = f"https://{value}"
        if value not in seen:
            seen.add(value)
            normalized.append(value)
    return normalized


def parse_pasted_urls(text: str) -> list[str]:
    parts = [line.strip() for line in text.replace(',', '\n').splitlines()]
    return normalize_urls(parts)


def load_urls_from_csv_bytes(payload: bytes, url_column: str | None = None) -> list[str]:
    dataframe = pd.read_csv(io.BytesIO(payload))
    columns = [str(column) for column in dataframe.columns]
    if url_column and url_column in dataframe.columns:
        selected = dataframe[url_column].dropna().astype(str).tolist()
        return normalize_urls(selected)

    preferred = ['url', 'source_url', 'website_url', 'link']
    for candidate in preferred:
        if candidate in columns:
            selected = dataframe[candidate].dropna().astype(str).tolist()
            return normalize_urls(selected)

    if len(columns) == 1:
        selected = dataframe.iloc[:, 0].dropna().astype(str).tolist()
        return normalize_urls(selected)

    raise ValueError('Could not determine a URL column from the uploaded CSV file.')


def load_urls_from_text_bytes(payload: bytes) -> list[str]:
    text = payload.decode('utf-8-sig', errors='ignore')
    return parse_pasted_urls(text)


def load_urls_from_file(file_name: str, payload: bytes) -> list[str]:
    suffix = Path(file_name).suffix.lower()
    if suffix == '.csv':
        return load_urls_from_csv_bytes(payload)
    if suffix in {'.txt', '.md'}:
        return load_urls_from_text_bytes(payload)
    raise ValueError(f'Unsupported URL list file type: {suffix}')
