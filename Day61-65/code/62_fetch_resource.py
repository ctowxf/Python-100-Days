"""
Day 62 - Fetching Network Resources with Python's requests Library
==================================================================

Comprehensive guide covering:
  - requests library: GET, POST, PUT, DELETE
  - Custom headers and User-Agent spoofing
  - Cookies and persistent Sessions
  - Proxy configuration and rotation
  - Error handling and retry strategies
  - Enterprise patterns: API client, authenticated scraping, proxy pool

C++ Comparison: Python requests.Session vs C++ HttpClient
==========================================================
  Python requests.Session:
    - Built-in cookie jar, connection pooling, redirect handling
    - Single object manages full HTTP lifecycle
    - ~10 lines to build a reusable client with auth + proxy

  C++ HttpClient (e.g., libcurl / Boost.Beast / cpp-httplib):
    - Must manually configure cookie storage, TLS, redirect policy
    - Connection pooling requires explicit multi-handle setup
    - ~50-100 lines for equivalent functionality with RAII wrappers
    - Header management and body serialization are manual

  Trade-off: Python requests trades raw throughput for developer
  speed and safety. C++ wins on latency-critical servers but costs
  far more engineering effort for HTTP client code.

Run directly:
    python 62_fetch_resource.py
"""

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------------------------------------------------------------------
# 1. Basic GET request
# ---------------------------------------------------------------------------

def basic_get(url: str) -> dict[str, Any]:
    """Perform a simple GET request and return structured result."""
    resp: requests.Response = requests.get(url, timeout=10)
    return {
        "status_code": resp.status_code,
        "content_type": resp.headers.get("Content-Type", ""),
        "body_length": len(resp.content),
        "text_preview": resp.text[:200],
    }


# ---------------------------------------------------------------------------
# 2. Custom headers - User-Agent spoofing (as described in the lesson)
# ---------------------------------------------------------------------------

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.7,en;q=0.5",
}


def fetch_with_headers(url: str, extra_headers: dict[str, str] | None = None) -> str:
    """Fetch a URL using browser-like headers to avoid bot detection."""
    headers: dict[str, str] = {**DEFAULT_HEADERS, **(extra_headers or {})}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


# ---------------------------------------------------------------------------
# 3. POST requests with different body types
# ---------------------------------------------------------------------------

def post_json(url: str, payload: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    """Send a JSON POST request (typical for REST APIs)."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def post_form(url: str, data: dict[str, str]) -> requests.Response:
    """Send a form-encoded POST request (traditional HTML form submission)."""
    return requests.post(url, data=data, headers=DEFAULT_HEADERS, timeout=10)


# ---------------------------------------------------------------------------
# 4. Cookies and Sessions
#    C++ comparison: requests.Session keeps a CookieJar automatically;
#    in C++ (libcurl) you must set CURLOPT_COOKIEJAR / CURLOPT_COOKIEFILE
#    explicitly and manage the file path yourself.
# ---------------------------------------------------------------------------

class CookieSession:
    """Demonstrates cookie-aware persistent sessions."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.session: requests.Session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def login(self, username: str, password: str) -> bool:
        """Authenticate and persist cookies in the session."""
        resp = self.session.post(
            urljoin(self.base_url, "/login"),
            data={"username": username, "password": password},
            timeout=10,
        )
        return resp.status_code == 200

    def get_protected_page(self, path: str) -> str:
        """Access a page that requires an authenticated session."""
        resp = self.session.get(urljoin(self.base_url, path), timeout=10)
        resp.raise_for_status()
        return resp.text

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "CookieSession":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# 5. Robust session with automatic retries
#    C++ comparison: Retry logic in C++ requires a manual loop with
#    back-off timers; requests + urllib3 gives it in one adapter call.
# ---------------------------------------------------------------------------

def create_robust_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple[int, ...] = (500, 502, 503, 504),
) -> requests.Session:
    """Build a session with connection pooling and automatic retries."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST", "HEAD"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    return session


# ---------------------------------------------------------------------------
# 6. Proxy configuration and rotation
#    As described in the lesson: commercial proxies like Mogu Proxy
#    use Proxy-Authorization header for authentication.
# ---------------------------------------------------------------------------

@dataclass
class ProxyConfig:
    """Configuration for a single proxy endpoint."""
    host: str
    port: int
    protocol: str = "http"
    username: str | None = None
    password: str | None = None
    app_key: str | None = None  # For services like Mogu Proxy

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def proxies(self) -> dict[str, str]:
        return {"http": self.url, "https": self.url}

    @property
    def auth_headers(self) -> dict[str, str]:
        """Generate Proxy-Authorization header for commercial proxies."""
        if self.app_key:
            return {"Proxy-Authorization": f"Basic {self.app_key}"}
        if self.username and self.password:
            import base64
            cred = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            return {"Proxy-Authorization": f"Basic {cred}"}
        return {}


class ProxyRotator:
    """Round-robin proxy pool with health checking.

    C++ comparison: In C++ you would store proxy endpoints in a vector
    and cycle through them manually, building curl easy handles per
    request.  This class shows how Python makes the same pattern
    trivial with dataclasses and list rotation.
    """

    def __init__(self, proxies: list[ProxyConfig]) -> None:
        self._proxies = proxies
        self._index: int = 0
        self._dead: set[int] = set()

    def next_proxy(self) -> ProxyConfig:
        """Return the next healthy proxy in round-robin order."""
        attempts = 0
        while attempts < len(self._proxies):
            if self._index not in self._dead:
                proxy = self._proxies[self._index]
                self._index = (self._index + 1) % len(self._proxies)
                return proxy
            self._index = (self._index + 1) % len(self._proxies)
            attempts += 1
        raise RuntimeError("All proxies are marked as dead")

    def mark_dead(self, proxy: ProxyConfig) -> None:
        idx = self._proxies.index(proxy)
        self._dead.add(idx)

    def fetch(self, url: str, timeout: int = 10) -> requests.Response:
        """Fetch a URL through the next available proxy."""
        proxy = self.next_proxy()
        headers = {**DEFAULT_HEADERS, **proxy.auth_headers}
        try:
            resp = requests.get(
                url,
                headers=headers,
                proxies=proxy.proxies,
                timeout=timeout,
                verify=False,  # Some commercial proxies need this
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException:
            self.mark_dead(proxy)
            raise


# ---------------------------------------------------------------------------
# 7. Enterprise Example: Generic API Client
# ---------------------------------------------------------------------------

@dataclass
class APIResponse:
    """Typed wrapper around an HTTP response for API consumers."""
    status_code: int
    data: Any
    headers: dict[str, str]
    elapsed_ms: float


class APIClient:
    """Reusable HTTP client for a REST API with auth, retries, and logging.

    This is the Python equivalent of a C++ HttpClient wrapper class.
    In C++ you would typically use libcurl with RAII handles or a
    library like cpp-httplib; Python's requests.Session provides the
    same connection pooling and header persistence with far less code.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 15,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session: requests.Session = create_robust_session(retries=max_retries)
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"
        self.session.headers["Accept"] = "application/json"

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> APIResponse:
        url = f"{self.base_url}{path}"
        resp = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return APIResponse(
            status_code=resp.status_code,
            data=resp.json() if "json" in resp.headers.get("Content-Type", "") else resp.text,
            headers=dict(resp.headers),
            elapsed_ms=resp.elapsed.total_seconds() * 1000,
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> APIResponse:
        return self._request("GET", path, params=params)

    def post(self, path: str, body: dict[str, Any]) -> APIResponse:
        return self._request("POST", path, json_body=body)

    def put(self, path: str, body: dict[str, Any]) -> APIResponse:
        return self._request("PUT", path, json_body=body)

    def delete(self, path: str) -> APIResponse:
        return self._request("DELETE", path)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# 8. Enterprise Example: Authenticated Scraper with polite delays
# ---------------------------------------------------------------------------

@dataclass
class ScrapedItem:
    """A single scraped result."""
    title: str
    link: str
    rating: str = ""


class DoubanScraper:
    """Scrape Douban Top250 with session persistence, headers, and polite delays.

    Demonstrates real-world scraping patterns:
      - Session reuse for connection pooling
      - Browser-like User-Agent
      - Random sleep to avoid rate-limiting
      - Proxy rotation (optional)
    """

    BASE_URL: str = "https://movie.douban.com/top250"
    TITLE_PATTERN: re.Pattern[str] = re.compile(r'<span class="title">([^&]*?)</span>')
    RATING_PATTERN: re.Pattern[str] = re.compile(r'<span class="rating_num".*?>(.*?)</span>')

    def __init__(
        self,
        proxy_rotator: ProxyRotator | None = None,
        delay_range: tuple[float, float] = (1.0, 5.0),
    ) -> None:
        self.session: requests.Session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.proxy_rotator = proxy_rotator
        self.delay_range = delay_range

    def _polite_delay(self) -> None:
        time.sleep(random.uniform(*self.delay_range))

    def scrape_page(self, page: int) -> list[ScrapedItem]:
        """Scrape a single page (1-indexed) of the Top250 list."""
        url = f"{self.BASE_URL}?start={(page - 1) * 25}"
        kwargs: dict[str, Any] = {"timeout": 15}

        if self.proxy_rotator:
            proxy = self.proxy_rotator.next_proxy()
            kwargs["proxies"] = proxy.proxies
            kwargs["headers"] = proxy.auth_headers
            kwargs["verify"] = False

        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()

        titles = self.TITLE_PATTERN.findall(resp.text)
        ratings = self.RATING_PATTERN.findall(resp.text)
        return [
            ScrapedItem(title=t, link="", rating=r)
            for t, r in zip(titles, ratings)
        ]

    def scrape_all(self, pages: int = 10) -> list[ScrapedItem]:
        """Scrape multiple pages with polite delays between requests."""
        items: list[ScrapedItem] = []
        for page in range(1, pages + 1):
            items.extend(self.scrape_page(page))
            if page < pages:
                self._polite_delay()
        return items

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "DoubanScraper":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# 9. Error handling helper
# ---------------------------------------------------------------------------

def safe_request(
    method: str,
    url: str,
    **kwargs: Any,
) -> tuple[requests.Response | None, str | None]:
    """Execute an HTTP request with comprehensive error handling.

    Returns (response, None) on success or (None, error_message) on failure.
    """
    try:
        resp = requests.request(method, url, timeout=kwargs.pop("timeout", 10), **kwargs)
        resp.raise_for_status()
        return resp, None
    except requests.ConnectionError as exc:
        return None, f"Connection failed: {exc}"
    except requests.Timeout as exc:
        return None, f"Request timed out: {exc}"
    except requests.HTTPError as exc:
        return None, f"HTTP error {exc.response.status_code}: {exc}"
    except requests.RequestException as exc:
        return None, f"Request failed: {exc}"


# ---------------------------------------------------------------------------
# 10. Binary download (as shown in the lesson - downloading an image)
# ---------------------------------------------------------------------------

def download_binary(url: str, dest_path: str, chunk_size: int = 8192) -> int:
    """Download a binary resource (image, PDF, etc.) to a local file.

    Uses streaming to handle large files without loading them entirely
    into memory -- the same pattern you would use in C++ with libcurl's
    write callback.
    """
    resp = requests.get(url, stream=True, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    bytes_written = 0
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            bytes_written += len(chunk)
    return bytes_written


# ---------------------------------------------------------------------------
# Main - demonstrate all patterns
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Day 62: Fetching Network Resources with Python requests")
    print("=" * 70)

    # --- 1. Basic GET ---
    print("\n[1] Basic GET request")
    result = basic_get("https://httpbin.org/get")
    print(f"    Status: {result['status_code']}, "
          f"Content-Type: {result['content_type']}, "
          f"Body length: {result['body_length']}")

    # --- 2. GET with custom headers ---
    print("\n[2] GET with browser-like headers")
    try:
        html = fetch_with_headers("https://httpbin.org/headers")
        print(f"    Response length: {len(html)} chars")
    except requests.RequestException as exc:
        print(f"    Skipped (network): {exc}")

    # --- 3. POST JSON ---
    print("\n[3] POST with JSON body")
    try:
        api_result = post_json(
            "https://httpbin.org/post",
            payload={"name": "Python100", "day": 62},
        )
        print(f"    Server received JSON: {json.dumps(api_result.get('json', {}), ensure_ascii=False)}")
    except requests.RequestException as exc:
        print(f"    Skipped (network): {exc}")

    # --- 4. POST form data ---
    print("\n[4] POST with form data")
    try:
        resp = post_form("https://httpbin.org/post", data={"user": "test", "pass": "secret"})
        print(f"    Status: {resp.status_code}")
    except requests.RequestException as exc:
        print(f"    Skipped (network): {exc}")

    # --- 5. Session with cookies ---
    print("\n[5] Cookie-aware session (httpbin cookies)")
    session = requests.Session()
    session.cookies.set("session_id", "abc123")
    session.cookies.set("lang", "zh-CN")
    try:
        resp = session.get("https://httpbin.org/cookies", timeout=10)
        print(f"    Cookies sent: {resp.json()}")
    except requests.RequestException as exc:
        print(f"    Skipped (network): {exc}")
    finally:
        session.close()

    # --- 6. Robust session with retries ---
    print("\n[6] Robust session with auto-retries")
    robust = create_robust_session(retries=2, backoff_factor=0.3)
    try:
        resp = robust.get("https://httpbin.org/get", timeout=10)
        print(f"    Status: {resp.status_code}, Retries handled automatically")
    except requests.RequestException as exc:
        print(f"    Skipped (network): {exc}")
    finally:
        robust.close()

    # --- 7. Error handling ---
    print("\n[7] Safe request with error handling")
    _, err = safe_request("GET", "https://httpbin.org/status/404")
    print(f"    Expected error: {err}")
    _, err = safe_request("GET", "http://localhost:1/no_such_port")
    print(f"    Expected error: {err}")

    # --- 8. API Client pattern ---
    print("\n[8] Enterprise API Client")
    with APIClient("https://httpbin.org", api_key="demo-key") as client:
        result = client.get("/get", params={"page": 1})
        print(f"    API response status={result.status_code}, "
              f"elapsed={result.elapsed_ms:.1f}ms")

    # --- 9. Proxy config (dry run - no actual proxy) ---
    print("\n[9] Proxy configuration (dry run)")
    proxy = ProxyConfig(host="proxy.example.com", port=9001, app_key="YOUR_KEY")
    print(f"    Proxy URL: {proxy.url}")
    print(f"    Auth headers: {proxy.auth_headers}")

    # --- 10. Scraper construction (no network call) ---
    print("\n[10] DoubanScraper pattern (construction only, no live call)")
    with DoubanScraper(delay_range=(1.0, 3.0)) as scraper:
        print(f"    Scraper ready, session headers: {list(scraper.session.headers.keys())}")

    print("\n" + "=" * 70)
    print("All demonstrations complete.")
    print("=" * 70)
