"""
Day 63 - Concurrent Programming in Web Crawling

This module demonstrates three approaches to building concurrent web crawlers:
1. Single-threaded (baseline)
2. Multi-threaded with ThreadPoolExecutor
3. Async I/O with aiohttp

It also covers practical enterprise patterns: rate limiting, retry logic,
image downloading, and distributed scraping coordination.

Usage:
    python 63_concurrent_crawler.py

Dependencies:
    pip install requests aiohttp aiofiles
"""

import asyncio
import json
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

# ---------------------------------------------------------------------------
# Optional async imports -- only needed for async examples
# ---------------------------------------------------------------------------
try:
    import aiohttp
    import aiofiles
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration & Data Classes
# ============================================================================

class CrawlMode(Enum):
    """Supported crawl execution modes."""
    SINGLE_THREADED = "single"
    MULTI_THREADED = "multi"
    ASYNC_IO = "async"


@dataclass
class CrawlConfig:
    """Configuration for a crawl job."""
    base_url: str = "https://image.so.com/zjl"
    channel: str = "beauty"
    pages: int = 3
    page_size: int = 30
    output_dir: str = "images"
    max_workers: int = 16
    max_concurrency: int = 20
    request_timeout: int = 15
    rate_limit_per_sec: float = 10.0
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = False


@dataclass
class CrawlResult:
    """Tracks the outcome of a crawl run."""
    mode: CrawlMode
    total_urls: int = 0
    success_count: int = 0
    fail_count: int = 0
    elapsed_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """Thread-safe token-bucket rate limiter.

    Args:
        rate: Maximum number of operations per second.
    """

    def __init__(self, rate: float) -> None:
        self._rate = rate
        self._tokens = rate
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
                self._last_refill = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
            time.sleep(1.0 / self._rate)


class AsyncRateLimiter:
    """Async-compatible rate limiter using a semaphore + delay approach.

    Args:
        rate: Maximum number of operations per second.
    """

    def __init__(self, rate: float) -> None:
        self._delay = 1.0 / rate
        self._semaphore = asyncio.Semaphore(int(rate))
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request slot is available."""
        await self._semaphore.acquire()
        try:
            await asyncio.sleep(self._delay)
        finally:
            self._semaphore.release()


# ============================================================================
# Retry Decorator
# ============================================================================

def with_retry(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator that retries a function on failure.

    Args:
        max_retries: Maximum number of retry attempts.
        retry_delay: Seconds to wait between retries.
        exceptions: Exception types that trigger a retry.
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    logger.warning(
                        "Attempt %d/%d failed: %s", attempt, max_retries, exc
                    )
                    if attempt < max_retries:
                        time.sleep(retry_delay * attempt)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


def async_with_retry(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Async version of the retry decorator."""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    logger.warning(
                        "Async attempt %d/%d failed: %s", attempt, max_retries, exc
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay * attempt)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


# ============================================================================
# Abstract Crawler Interface
# ============================================================================

class BaseCrawler(ABC):
    """Abstract base class for all crawler implementations."""

    def __init__(self, config: CrawlConfig) -> None:
        self.config = config
        self.output_dir = Path(config.output_dir) / config.channel
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_page_urls(self) -> list[str]:
        """Build the list of API page URLs to fetch."""
        return [
            f"{self.config.base_url}?ch={self.config.channel}&sn={page * self.config.page_size}"
            for page in range(self.config.pages)
        ]

    @abstractmethod
    def crawl(self) -> CrawlResult:
        """Execute the crawl and return results."""
        ...


# ============================================================================
# 1. Single-Threaded Crawler
# ============================================================================

class SingleThreadCrawler(BaseCrawler):
    """Baseline crawler that downloads images sequentially."""

    @with_retry(max_retries=3, retry_delay=1.0)
    def _download_image(self, url: str, session: requests.Session) -> None:
        filename = urlparse(url).path.split("/")[-1] or f"img_{hash(url)}.jpg"
        filepath = self.output_dir / filename
        if filepath.exists():
            logger.debug("Skipping existing file: %s", filepath)
            return
        resp = session.get(url, timeout=self.config.request_timeout)
        resp.raise_for_status()
        filepath.write_bytes(resp.content)
        logger.info("Downloaded: %s", filepath.name)

    def crawl(self) -> CrawlResult:
        result = CrawlResult(mode=CrawlMode.SINGLE_THREADED)
        start = time.perf_counter()

        with requests.Session() as session:
            for page_url in self._build_page_urls():
                try:
                    resp = session.get(page_url, timeout=self.config.request_timeout)
                    resp.raise_for_status()
                    image_list: list[dict[str, Any]] = resp.json().get("list", [])
                except Exception as exc:
                    logger.error("Failed to fetch page %s: %s", page_url, exc)
                    result.errors.append(str(exc))
                    continue

                for pic in image_list:
                    img_url: str = pic.get("qhimg_url", "")
                    if not img_url:
                        continue
                    result.total_urls += 1
                    try:
                        self._download_image(img_url, session)
                        result.success_count += 1
                    except Exception as exc:
                        result.fail_count += 1
                        result.errors.append(f"{img_url}: {exc}")
                        logger.error("Download failed for %s: %s", img_url, exc)

        result.elapsed_seconds = time.perf_counter() - start
        return result


# ============================================================================
# 2. Multi-Threaded Crawler
# ============================================================================

class MultiThreadCrawler(BaseCrawler):
    """Crawler that uses a thread pool for parallel downloads."""

    def __init__(self, config: CrawlConfig) -> None:
        super().__init__(config)
        self._rate_limiter = RateLimiter(config.rate_limit_per_sec)
        self._stats_lock = threading.Lock()

    def _download_image(
        self,
        url: str,
        session: requests.Session,
        result: CrawlResult,
    ) -> None:
        self._rate_limiter.acquire()
        filename = urlparse(url).path.split("/")[-1] or f"img_{hash(url)}.jpg"
        filepath = self.output_dir / filename
        if filepath.exists():
            with self._stats_lock:
                result.success_count += 1
            return

        for attempt in range(1, self.config.max_retries + 1):
            try:
                resp = session.get(url, timeout=self.config.request_timeout)
                resp.raise_for_status()
                filepath.write_bytes(resp.content)
                logger.info("Downloaded (thread): %s", filepath.name)
                with self._stats_lock:
                    result.success_count += 1
                return
            except Exception as exc:
                logger.warning(
                    "Thread attempt %d/%d for %s: %s",
                    attempt, self.config.max_retries, url, exc,
                )
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * attempt)

        with self._stats_lock:
            result.fail_count += 1
            result.errors.append(f"{url}: max retries exceeded")

    def crawl(self) -> CrawlResult:
        result = CrawlResult(mode=CrawlMode.MULTI_THREADED)
        start = time.perf_counter()

        # Gather all image URLs first
        all_image_urls: list[str] = []
        with requests.Session() as session:
            for page_url in self._build_page_urls():
                try:
                    resp = session.get(page_url, timeout=self.config.request_timeout)
                    resp.raise_for_status()
                    for pic in resp.json().get("list", []):
                        img_url: str = pic.get("qhimg_url", "")
                        if img_url:
                            all_image_urls.append(img_url)
                except Exception as exc:
                    logger.error("Page fetch failed: %s", exc)
                    result.errors.append(str(exc))

        result.total_urls = len(all_image_urls)
        logger.info("Found %d images, starting threaded download...", result.total_urls)

        # Download images in parallel
        session = requests.Session()
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as pool:
            futures = [
                pool.submit(self._download_image, url, session, result)
                for url in all_image_urls
            ]
            for future in as_completed(futures):
                # Propagate unexpected exceptions
                exc = future.exception()
                if exc is not None:
                    logger.error("Unexpected thread error: %s", exc)
        session.close()

        result.elapsed_seconds = time.perf_counter() - start
        return result


# ============================================================================
# 3. Async I/O Crawler
# ============================================================================

class AsyncCrawler(BaseCrawler):
    """Crawler using asyncio and aiohttp for non-blocking I/O."""

    def __init__(self, config: CrawlConfig) -> None:
        super().__init__(config)
        if not ASYNC_AVAILABLE:
            raise RuntimeError(
                "Install 'aiohttp' and 'aiofiles' for async crawler: "
                "pip install aiohttp aiofiles"
            )
        self._semaphore = asyncio.Semaphore(config.max_concurrency)

    @async_with_retry(max_retries=3, retry_delay=1.0)
    async def _download_image(
        self,
        session: "aiohttp.ClientSession",
        url: str,
        result: CrawlResult,
        stats_lock: asyncio.Lock,
    ) -> None:
        async with self._semaphore:
            filename = urlparse(url).path.split("/")[-1] or f"img_{hash(url)}.jpg"
            filepath = self.output_dir / filename
            if filepath.exists():
                async with stats_lock:
                    result.success_count += 1
                return

            async with session.get(url, ssl=self.config.verify_ssl) as resp:
                if resp.status != 200:
                    raise aiohttp.ClientResponseError(
                        resp.request_info,
                        resp.history,
                        status=resp.status,
                    )
                data: bytes = await resp.read()

            async with aiofiles.open(filepath, "wb") as f:  # type: ignore[union-attr]
                await f.write(data)

            logger.info("Downloaded (async): %s", filepath.name)
            async with stats_lock:
                result.success_count += 1

    async def _fetch_page(
        self,
        session: "aiohttp.ClientSession",
        page_url: str,
    ) -> list[str]:
        """Fetch a single page and return image URLs."""
        async with session.get(page_url, ssl=self.config.verify_ssl) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
            return [
                pic["qhimg_url"]
                for pic in data.get("list", [])
                if pic.get("qhimg_url")
            ]

    async def _run(self) -> CrawlResult:
        result = CrawlResult(mode=CrawlMode.ASYNC_IO)
        stats_lock = asyncio.Lock()

        connector = aiohttp.TCPConnector(limit=self.config.max_concurrency)
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Gather all image URLs concurrently
            page_urls = self._build_page_urls()
            page_results = await asyncio.gather(
                *[self._fetch_page(session, u) for u in page_urls],
                return_exceptions=True,
            )

            all_image_urls: list[str] = []
            for page_result in page_results:
                if isinstance(page_result, Exception):
                    logger.error("Page fetch error: %s", page_result)
                    result.errors.append(str(page_result))
                else:
                    all_image_urls.extend(page_result)

            result.total_urls = len(all_image_urls)
            logger.info(
                "Found %d images, starting async download...", result.total_urls
            )

            # Download all images concurrently with bounded parallelism
            tasks = [
                self._download_image(session, url, result, stats_lock)
                for url in all_image_urls
            ]
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)
            for outcome in outcomes:
                if isinstance(outcome, Exception):
                    result.fail_count += 1
                    result.errors.append(str(outcome))

        return result

    def crawl(self) -> CrawlResult:
        start = time.perf_counter()
        result = asyncio.run(self._run())
        result.elapsed_seconds = time.perf_counter() - start
        return result


# ============================================================================
# Distributed Scraping Coordinator (Conceptual)
# ============================================================================

@dataclass
class WorkerNode:
    """Represents a worker in a distributed scraping cluster."""
    worker_id: str
    endpoint: str
    is_alive: bool = True
    assigned_urls: list[str] = field(default_factory=list)


class DistributedCoordinator:
    """Coordinates work across multiple worker nodes.

    This is a simplified demonstration of how a master node can partition
    URL lists among workers and collect results. In production, workers
    would run as separate processes or on separate machines communicating
    via a message queue (Redis, RabbitMQ, etc.) or an HTTP API.

    Args:
        worker_endpoints: List of worker endpoint URLs.
        urls: Total list of URLs to scrape.
    """

    def __init__(
        self,
        worker_endpoints: list[str],
        urls: list[str],
    ) -> None:
        self.workers = [
            WorkerNode(
                worker_id=f"worker-{i}",
                endpoint=endpoint,
            )
            for i, endpoint in enumerate(worker_endpoints)
        ]
        self.urls = urls

    def partition_work(self) -> dict[str, list[str]]:
        """Distribute URLs evenly across workers using round-robin."""
        assignment: dict[str, list[str]] = {
            w.worker_id: [] for w in self.workers
        }
        worker_ids = list(assignment.keys())
        for idx, url in enumerate(self.urls):
            target = worker_ids[idx % len(worker_ids)]
            assignment[target].append(url)
        return assignment

    def run(self) -> dict[str, Any]:
        """Simulate distributing work and collecting results."""
        assignment = self.partition_work()
        results: dict[str, Any] = {}

        for worker in self.workers:
            worker.assigned_urls = assignment[worker.worker_id]
            logger.info(
                "Assigned %d URLs to %s (%s)",
                len(worker.assigned_urls),
                worker.worker_id,
                worker.endpoint,
            )
            # In a real system, you would send these URLs via HTTP/gRPC/queue
            # and await a response or callback.
            results[worker.worker_id] = {
                "endpoint": worker.endpoint,
                "assigned_count": len(worker.assigned_urls),
                "status": "dispatched",
            }

        return results


# ============================================================================
# Factory & Benchmark Runner
# ============================================================================

def create_crawler(mode: CrawlMode, config: CrawlConfig) -> BaseCrawler:
    """Factory function to create a crawler by mode."""
    crawlers: dict[CrawlMode, type[BaseCrawler]] = {
        CrawlMode.SINGLE_THREADED: SingleThreadCrawler,
        CrawlMode.MULTI_THREADED: MultiThreadCrawler,
        CrawlMode.ASYNC_IO: AsyncCrawler,
    }
    cls = crawlers.get(mode)
    if cls is None:
        raise ValueError(f"Unsupported crawl mode: {mode}")
    return cls(config)


def print_result(result: CrawlResult) -> None:
    """Pretty-print a CrawlResult."""
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  Crawl Mode : {result.mode.value}")
    print(f"  Total URLs : {result.total_urls}")
    print(f"  Successes  : {result.success_count}")
    print(f"  Failures   : {result.fail_count}")
    print(f"  Elapsed    : {result.elapsed_seconds:.3f}s")
    if result.errors:
        print(f"  Errors     : {len(result.errors)} (first 3 shown)")
        for err in result.errors[:3]:
            print(f"    - {err}")
    print(sep)


def run_benchmark(config: CrawlConfig | None = None) -> None:
    """Run all crawler modes and compare performance.

    Note: This will attempt real network requests.  If the target site is
    unreachable, each mode will report failures but still demonstrate the
    concurrency patterns.
    """
    if config is None:
        config = CrawlConfig()

    modes = [CrawlMode.SINGLE_THREADED, CrawlMode.MULTI_THREADED]
    if ASYNC_AVAILABLE:
        modes.append(CrawlMode.ASYNC_IO)
    else:
        logger.warning("Skipping async benchmark (aiohttp/aiofiles not installed)")

    results: list[CrawlResult] = []
    for mode in modes:
        logger.info("Running %s crawler...", mode.value)
        crawler = create_crawler(mode, config)
        result = crawler.crawl()
        results.append(result)
        print_result(result)

    # Summary comparison
    if len(results) > 1:
        print("\n--- Performance Comparison ---")
        baseline = results[0].elapsed_seconds
        for r in results:
            speedup = baseline / r.elapsed_seconds if r.elapsed_seconds > 0 else float("inf")
            print(
                f"  {r.mode.value:>12}: {r.elapsed_seconds:.3f}s "
                f"(speedup: {speedup:.2f}x)"
            )


# ============================================================================
# Distributed Scraping Demo
# ============================================================================

def demonstrate_distributed_scraping() -> None:
    """Show how work would be partitioned in a distributed setup."""
    print("\n--- Distributed Scraping Coordinator Demo ---")
    sample_urls = [
        f"https://image.so.com/zjl?ch=beauty&sn={i * 30}"
        for i in range(6)
    ]
    coordinator = DistributedCoordinator(
        worker_endpoints=[
            "http://worker-1.internal:8000",
            "http://worker-2.internal:8000",
            "http://worker-3.internal:8000",
        ],
        urls=sample_urls,
    )
    results = coordinator.run()
    for worker_id, info in results.items():
        print(f"  {worker_id}: {info}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> None:
    """Main entry point demonstrating concurrent crawling techniques."""
    config = CrawlConfig(
        pages=2,            # Small page count for demo
        max_workers=8,
        max_concurrency=10,
        rate_limit_per_sec=5.0,
        output_dir="images/demo",
    )

    print("=" * 60)
    print("  Day 63 - Concurrent Programming in Web Crawling")
    print("=" * 60)

    # Run benchmark across all modes
    run_benchmark(config)

    # Show distributed coordinator concept
    demonstrate_distributed_scraping()

    print("\nAll demonstrations complete.")


if __name__ == "__main__":
    main()
