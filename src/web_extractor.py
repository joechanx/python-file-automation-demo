from __future__ import annotations

import re
from typing import Callable

import pandas as pd
from bs4 import BeautifulSoup

try:
    from .url_loader import normalize_urls
    from .web_fetcher import fetch_html
except ImportError:
    from url_loader import normalize_urls
    from web_fetcher import fetch_html

EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:\+?\d[\d().\-\s]{7,}\d)")
YEAR_RANGE_PATTERN = re.compile(r"^\s*(?:19|20)\d{2}\s*-\s*(?:19|20)\d{2}\s*$")


def _clean_text(text: str | None) -> str | None:
    if text is None:
        return None
    cleaned = ' '.join(text.split()).strip()
    return cleaned or None


def _collect_unique(matches: list[str]) -> str | None:
    seen: list[str] = []
    for match in matches:
        candidate = ' '.join(match.split()).strip()
        if candidate and candidate not in seen:
            seen.append(candidate)
    return '; '.join(seen) if seen else None


def _is_valid_phone_candidate(value: str) -> bool:
    candidate = ' '.join(value.split()).strip()
    if not candidate:
        return False

    # Exclude year spans like 2001-2026 that happen to match the loose phone regex.
    if YEAR_RANGE_PATTERN.match(candidate):
        return False

    digits_only = re.sub(r"\D", "", candidate)
    if len(digits_only) < 7 or len(digits_only) > 15:
        return False

    return True


def extract_record_from_html(url: str, html: str, extract_fields: list[str] | None = None) -> dict[str, str | None]:
    fields = set(extract_fields or ['page_title', 'meta_description', 'h1', 'emails_found', 'phones_found'])
    soup = BeautifulSoup(html, 'html.parser')

    page_title = _clean_text(soup.title.get_text()) if soup.title and 'page_title' in fields else None
    meta_tag = soup.find('meta', attrs={'name': 'description'}) if 'meta_description' in fields else None
    meta_description = _clean_text(meta_tag.get('content')) if meta_tag else None
    h1_tag = soup.find('h1') if 'h1' in fields else None
    h1 = _clean_text(h1_tag.get_text()) if h1_tag else None
    emails = _collect_unique(EMAIL_PATTERN.findall(html)) if 'emails_found' in fields else None

    if 'phones_found' in fields:
        raw_phone_matches = PHONE_PATTERN.findall(html)
        valid_phone_matches = [match for match in raw_phone_matches if _is_valid_phone_candidate(match)]
        phones = _collect_unique(valid_phone_matches)
    else:
        phones = None

    return {
        'source_url': url,
        'page_title': page_title,
        'meta_description': meta_description,
        'h1': h1,
        'emails_found': emails,
        'phones_found': phones,
        'fetch_status': 'ok',
        'fetch_error': None,
    }


def extract_web_records(
    urls: list[str],
    extract_fields: list[str] | None = None,
    fetch_html_func: Callable[[str], str] | None = None,
) -> pd.DataFrame:
    fetcher = fetch_html_func or fetch_html
    records: list[dict[str, str | None]] = []
    for url in normalize_urls(urls):
        try:
            html = fetcher(url)
            record = extract_record_from_html(url=url, html=html, extract_fields=extract_fields)
        except Exception as exc:  # pragma: no cover - exercised by tests with deterministic exception
            record = {
                'source_url': url,
                'page_title': None,
                'meta_description': None,
                'h1': None,
                'emails_found': None,
                'phones_found': None,
                'fetch_status': 'error',
                'fetch_error': str(exc),
            }
        records.append(record)

    dataframe = pd.DataFrame(records)
    if not dataframe.empty:
        dataframe['_source_file'] = 'url_import'
    return dataframe
