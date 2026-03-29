import argparse
import asyncio
import html
import json
import re
import sys
import time
import urllib.parse
from typing import Any

import requests

try:
    import cloudscraper
except Exception:
    cloudscraper = None

try:
    import aiohttp
except Exception:
    aiohttp = None

BASE_URL = "https://au.indeed.com"
RESULTS_PER_PAGE = 50

SEARCH_QUERY = """
Python AND ("software engineer" OR "software developer" OR "backend engineer" OR "backend developer" OR "API developer" OR "API engineer" OR "web developer" OR "web engineer" OR "full stack developer" OR "full stack engineer" OR "fullstack developer" OR "systems engineer" OR "systems developer" OR "applications developer" OR "application developer" OR "programmer" OR "engineer" OR "developer") NOT TypeScript NOT React NOT "Machine Learning" NOT Lead NOT Staff NOT QA
""".strip()

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _build_session() -> Any:
    if cloudscraper is not None:
        session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "darwin", "mobile": False}
        )
    else:
        session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def build_session() -> Any:
    """Public wrapper for creating an HTTP session with Indeed-friendly headers."""
    return _build_session()


def _fetch_html(session: Any, url: str, timeout: float = 30.0) -> str:
    response = session.get(url, timeout=timeout)
    if response.status_code == 403:
        raise RuntimeError("Indeed returned 403 (bot protection). Try again later or reduce request rate.")
    response.raise_for_status()
    return response.text


def fetch_html(session: Any, url: str, timeout: float = 30.0) -> str:
    """Public wrapper for loading HTML with common error handling."""
    return _fetch_html(session=session, url=url, timeout=timeout)


async def fetch_html_async(session: Any, url: str, timeout: float = 30.0) -> str:
    """Async HTML loader for aiohttp sessions."""
    if aiohttp is None:
        raise RuntimeError("Package 'aiohttp' is required for async mode")

    request_timeout = aiohttp.ClientTimeout(total=timeout)
    async with session.get(url, timeout=request_timeout) as response:
        if response.status == 403:
            raise RuntimeError("Indeed returned 403 (bot protection). Try again later or reduce request rate.")
        response.raise_for_status()
        return await response.text()


def _is_valid_jk(jk: str) -> bool:
    if not re.fullmatch(r"[A-Za-z0-9]{8,32}", jk):
        return False
    if jk.lower() == "abcdef0123456789":
        return False
    return True


def _extract_links(search_html: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    for jk in re.findall(r'data-jk="([A-Za-z0-9]+)"', search_html):
        if not _is_valid_jk(jk):
            continue
        link = f"{BASE_URL}/viewjob?jk={jk}"
        if link not in seen:
            seen.add(link)
            links.append(link)

    href_patterns = [
        r'href="(/viewjob\\?[^"#]+)"',
        r"href='(/viewjob\\?[^'#]+)'",
        r'href="(/rc/clk\\?[^"#]+)"',
        r"href='(/rc/clk\\?[^'#]+)'",
    ]
    for pattern in href_patterns:
        for raw_href in re.findall(pattern, search_html):
            href = html.unescape(raw_href)
            absolute = urllib.parse.urljoin(BASE_URL, href)
            parsed = urllib.parse.urlparse(absolute)
            qs = urllib.parse.parse_qs(parsed.query)
            jk = qs.get("jk", [""])[0]
            if not _is_valid_jk(jk):
                continue
            link = f"{BASE_URL}/viewjob?jk={jk}"
            if link not in seen:
                seen.add(link)
                links.append(link)

    return links


def search_indeed_links(query: str = SEARCH_QUERY, pages: int = 1, pause_seconds: float = 0.5) -> list[str]:
    if pages < 1:
        raise ValueError("pages must be >= 1")

    session = _build_session()

    # Инициализируем cookies на домене Indeed перед поиском.
    _fetch_html(session, BASE_URL)

    all_links: list[str] = []
    seen: set[str] = set()
    for page in range(pages):
        """
        https://au.indeed.com/
        jobs?
        q=Python+AND+%28%22software+engineer%22+OR+%22software+developer%22+OR+%22backend+engineer%22+OR+%22backend+developer%22+OR+%22API+developer%22+OR+%22API+engineer%22+OR+%22web+developer%22+OR+%22web+engineer%22+OR+%22full+stack+developer%22+OR+%22full+stack+engineer%22+OR+%22fullstack+developer%22+OR+%22systems+engineer%22+OR+%22systems+developer%22+OR+%22applications+developer%22+OR+%22application+developer%22+OR+%22programmer%22+OR+%22engineer%22+OR+%22developer%22%29+NOT+TypeScript+NOT+React+NOT+%22Machine+Learning%22+NOT+Lead+NOT+Staff+NOT+QA&l=Melbourne+VIC&
        radius=50&
        from=searchOnDesktopSerp&
        vjk=f45c80722ae0cf84
        """
        params = {
            "q": query,
            "start": str(page * RESULTS_PER_PAGE),
        }
        search_url = f"{BASE_URL}/jobs?{urllib.parse.urlencode(params)}"
        search_html = _fetch_html(session, search_url)
        page_links = _extract_links(search_html)

        for link in page_links:
            if link not in seen:
                seen.add(link)
                all_links.append(link)

        if pause_seconds > 0 and page < pages - 1:
            time.sleep(pause_seconds)

    return all_links


async def search_indeed_links_async(
    query: str = SEARCH_QUERY,
    pages: int = 1,
    pause_seconds: float = 0.5,
) -> list[str]:
    if pages < 1:
        raise ValueError("pages must be >= 1")

    # Indeed often blocks plain aiohttp traffic.
    # If cloudscraper is available, use it in a worker thread for better resilience.
    if cloudscraper is not None:
        return await asyncio.to_thread(
            search_indeed_links,
            query,
            pages,
            pause_seconds,
        )

    if aiohttp is None:
        raise RuntimeError("Package 'aiohttp' is required for async mode")

    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
        # Инициализируем cookies на домене Indeed перед поиском.
        await fetch_html_async(session=session, url=BASE_URL)

        all_links: list[str] = []
        seen: set[str] = set()
        for page in range(pages):
            params = {
                "q": query,
                "start": str(page * RESULTS_PER_PAGE),
            }
            search_url = f"{BASE_URL}/jobs?{urllib.parse.urlencode(params)}"
            search_html = await fetch_html_async(session=session, url=search_url)
            page_links = _extract_links(search_html)

            for link in page_links:
                if link not in seen:
                    seen.add(link)
                    all_links.append(link)

            if pause_seconds > 0 and page < pages - 1:
                await asyncio.sleep(pause_seconds)

    return all_links


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch job result links from au.indeed.com using a predefined query."
    )
    parser.add_argument("--pages", type=int, default=1, help="How many search pages to fetch (default: 1).")
    parser.add_argument(
        "--pause",
        type=float,
        default=0.5,
        help="Pause in seconds between page requests (default: 0.5).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if aiohttp is None:
            links = search_indeed_links(pages=args.pages, pause_seconds=args.pause)
        else:
            links = asyncio.run(search_indeed_links_async(pages=args.pages, pause_seconds=args.pause))
    except Exception as exc:
        print(f"Failed to fetch links: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(links, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
