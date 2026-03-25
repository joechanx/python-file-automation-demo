from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.url_loader import load_urls_from_file, parse_pasted_urls  # noqa: E402


def test_parse_pasted_urls_normalizes_and_deduplicates() -> None:
    urls = parse_pasted_urls('example.com\nhttps://example.com\nhttps://openai.com')
    assert urls == ['https://example.com', 'https://openai.com']


def test_load_urls_from_csv_file() -> None:
    payload = b'url\nexample.com\nhttps://openai.com\n'
    urls = load_urls_from_file('sample_urls.csv', payload)
    assert urls == ['https://example.com', 'https://openai.com']
