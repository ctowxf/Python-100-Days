"""
Day 61 - Network Data Collection Overview

This module covers the fundamentals of web scraping:
  - What web crawlers/spiders are and their application domains
  - The Robots Exclusion Protocol (robots.txt) and ethical scraping
  - HTTP protocol basics (request/response structure)
  - Basic scraping workflow: fetch -> parse -> store
  - Tools: Chrome DevTools, Postman, HTTPie, builtwith, python-whois

Key principles from the course material:
  1. Respect robots.txt -- a gentleman's agreement for crawlers
  2. Rate-limit your requests to avoid overloading servers
  3. Only scrape publicly visible front-end data
  4. Respect the site's intellectual property rights
  5. Do not publicly share crawler source code
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class ScrapedPage:
    """Represents the result of scraping a single page."""

    url: str
    status_code: int
    title: str
    links: list[str] = field(default_factory=list)
    text_snippet: str = ""


# ---------------------------------------------------------------------------
# robots.txt checker
# ---------------------------------------------------------------------------
class RobotsChecker:
    """
    Wraps urllib.robotparser.RobotFileParser to check whether a given
    URL is allowed to be fetched by our user-agent.

    The robots.txt file is a *voluntary* standard (not legally binding
    in all jurisdictions) that webmasters use to communicate crawling
    preferences.  Respecting it is a cornerstone of ethical scraping.
    """

    def __init__(self, user_agent: str = "*") -> None:
        self._user_agent: str = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    def _get_parser(self, base_url: str) -> RobotFileParser:
        """Download and cache the robots.txt for the given site."""
        parsed = urlparse(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._parsers:
            rp = RobotFileParser()
            robots_url = f"{origin}/robots.txt"
            rp.set_url(robots_url)
            try:
                rp.read()
                logger.info("Loaded robots.txt from %s", robots_url)
            except Exception:
                logger.warning(
                    "Could not fetch robots.txt at %s -- assuming all allowed",
                    robots_url,
                )
            self._parsers[origin] = rp
        return self._parsers[origin]

    def is_allowed(self, url: str) -> bool:
        """Return True if the URL is permitted by the site's robots.txt."""
        parser = self._get_parser(url)
        return parser.can_fetch(self._user_agent, url)


# ---------------------------------------------------------------------------
# Polite scraper
# ---------------------------------------------------------------------------
class SimpleScraper:
    """
    A minimal, ethical web scraper that:
      1. Checks robots.txt before every request.
      2. Enforces a configurable delay between requests (rate-limiting).
      3. Uses a descriptive User-Agent header.
      4. Handles HTTP errors and timeouts gracefully.

    Workflow (mirrors the course material):
      1. Set a seed URL and fetch the page.
      2. Retry on transient failures up to ``max_retries`` times.
      3. Decode the response and extract the title + links.
      4. Yield a ScrapedPage for downstream processing / storage.
    """

    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; EducationalScraper/1.0; "
            "+https://github.com/example/learn-scraping)"
        ),
    }

    def __init__(
        self,
        delay: float = 1.0,
        max_retries: int = 3,
        timeout: float = 10.0,
        user_agent: str = "*",
    ) -> None:
        self._delay: float = delay
        self._max_retries: int = max_retries
        self._timeout: float = timeout
        self._session: requests.Session = requests.Session()
        self._session.headers.update(self.DEFAULT_HEADERS)
        self._robots: RobotsChecker = RobotsChecker(user_agent=user_agent)
        self._last_request_time: float = 0.0

    # -- internal helpers ---------------------------------------------------

    def _respect_rate_limit(self) -> None:
        """Sleep if necessary to maintain the minimum delay between requests."""
        elapsed: float = time.monotonic() - self._last_request_time
        if elapsed < self._delay:
            sleep_for: float = self._delay - elapsed
            logger.debug("Rate-limit: sleeping %.2fs", sleep_for)
            time.sleep(sleep_for)

    def _fetch(self, url: str) -> requests.Response:
        """
        Fetch *url* with retry logic and rate-limiting.

        Raises ``requests.RequestException`` after exhausting retries.
        """
        for attempt in range(1, self._max_retries + 1):
            self._respect_rate_limit()
            try:
                logger.info(
                    "Fetching %s (attempt %d/%d)", url, attempt, self._max_retries
                )
                response: requests.Response = self._session.get(
                    url, timeout=self._timeout
                )
                self._last_request_time = time.monotonic()
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                logger.warning("Request failed: %s", exc)
                if attempt == self._max_retries:
                    raise
        raise RuntimeError("Unreachable code")  # pragma: no cover

    # -- public API ---------------------------------------------------------

    def scrape(self, url: str) -> Optional[ScrapedPage]:
        """
        Scrape a single URL and return a ``ScrapedPage``.

        Returns ``None`` when the URL is disallowed by robots.txt or
        the page could not be fetched.
        """
        # Step 1 -- ethical gate: check robots.txt
        if not self._robots.is_allowed(url):
            logger.warning("Blocked by robots.txt: %s", url)
            return None

        # Step 2 -- download the page
        try:
            resp: requests.Response = self._fetch(url)
        except requests.RequestException:
            logger.error(
                "Failed to download %s after %d retries", url, self._max_retries
            )
            return None

        # Step 3 -- decode and parse
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup: BeautifulSoup = BeautifulSoup(resp.text, "html.parser")

        title: str = (
            soup.title.string.strip()
            if soup.title and soup.title.string
            else "(no title)"
        )

        # Extract absolute links from the page
        links: list[str] = []
        for anchor in soup.find_all("a", href=True):
            href: str = anchor["href"]  # type: ignore[assignment]
            absolute: str = urljoin(url, href)
            if urlparse(absolute).scheme in ("http", "https"):
                links.append(absolute)

        # Grab a short text snippet (first 300 chars of visible text)
        visible_text: str = soup.get_text(separator=" ", strip=True)
        snippet: str = visible_text[:300]

        page = ScrapedPage(
            url=url,
            status_code=resp.status_code,
            title=title,
            links=links,
            text_snippet=snippet,
        )
        logger.info(
            "Scraped: %s -- title=%r, links=%d", url, title, len(links)
        )
        return page

    def close(self) -> None:
        """Release underlying HTTP session resources."""
        self._session.close()

    # context-manager support
    def __enter__(self) -> SimpleScraper:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Demo helpers
# ---------------------------------------------------------------------------
def demo_robots_check(url: str) -> None:
    """Demonstrate checking a site's robots.txt for a given URL."""
    checker: RobotsChecker = RobotsChecker()
    allowed: bool = checker.is_allowed(url)
    status: str = "ALLOWED" if allowed else "BLOCKED"
    logger.info("robots.txt check for %s => %s", url, status)


def demo_scrape(seed_url: str) -> None:
    """Run the simple scraper on *seed_url* and print a summary."""
    with SimpleScraper(delay=1.5, max_retries=2) as scraper:
        page: Optional[ScrapedPage] = scraper.scrape(seed_url)
        if page is None:
            print(f"\n  Could not scrape {seed_url} (blocked or network error).\n")
            return

        print("\n" + "=" * 60)
        print(f"  URL    : {page.url}")
        print(f"  Status : {page.status_code}")
        print(f"  Title  : {page.title}")
        print(f"  Links  : {len(page.links)} found")
        print(f"  Snippet: {page.text_snippet[:120]}...")
        print("=" * 60 + "\n")

        # Show the first few outbound links
        print("  First 5 links:")
        for link in page.links[:5]:
            print(f"    -> {link}")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Demonstrate robots.txt checking
    print("\n--- robots.txt Checks ---\n")
    demo_robots_check("https://www.douban.com/search?q=python")
    demo_robots_check("https://www.douban.com/")

    # 2. Scrape a public, scraper-friendly page
    print("\n--- Simple Scraper Demo ---\n")
    demo_scrape("https://www.bootcss.com/")
