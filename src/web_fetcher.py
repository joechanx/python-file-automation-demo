from __future__ import annotations

import requests

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; FileAutomationDemo/1.0; +https://example.com/demo)',
    'Accept-Language': 'en-US,en;q=0.9',
}


def fetch_html(url: str, timeout: int = 15) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text
