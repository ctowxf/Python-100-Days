"""
Day 63 - Asyncio and Asynchronous Programming (Part 3)
======================================================

This module demonstrates advanced asynchronous programming patterns in Python
using asyncio, async/await syntax, coroutines, aiohttp, and the event loop.

C++ Comparison Notes:
---------------------
1. Python asyncio vs C++20 Coroutines:
   - Python asyncio uses cooperative multitasking with an event loop (epoll/kqueue/IOCP).
     Coroutines are first-class objects (async def / await).
   - C++20 introduces native coroutines (co_await, co_yield, co_return) with compiler-
     generated state machines. C++ coroutines are zero-cost abstractions — no heap
     allocation is required when the coroutine frame fits in the caller's stack.
     Python coroutines always allocate a coroutine object on the heap.
   - Python's event loop (uvloop or the default selector) is analogous to C++ libraries
     like Boost.Asio's io_context, but Python's is single-threaded by default.

2. Python aiohttp vs C++ Boost.Beast Async:
   - aiohttp provides a high-level async HTTP client/server built on asyncio.
     Connection pooling, session management, and SSL are handled transparently.
   - Boost.Beast provides low-level HTTP/WebSocket primitives on top of Boost.Asio.
     The programmer must manage buffers, completion tokens, and composed operations.
     Beast is significantly faster (~10-50x in microbenchmarks) but requires far
     more boilerplate (handler types, strand synchronization, buffer lifetimes).

Architecture Overview:
----------------------
- Generators and Coroutines: yield-based coroutines vs async/await
- Event Loop: how asyncio schedules and dispatches coroutines
- aiohttp: async HTTP client for web scraping
- Enterprise Patterns: async API client, concurrent scraper, database queries

Requirements:
    pip install aiohttp aiofiles aiosqlite
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from typing import Any, Generator, Optional, Sequence

# ---------------------------------------------------------------------------
# Section 1: Generator-Based Coroutines (Legacy Pattern)
# ---------------------------------------------------------------------------

def fibonacci_generator(max_count: int) -> Generator[int, None, None]:
    """
    A generator that yields Fibonacci numbers.

    In Python, a generator with 'yield' is the foundation of coroutines.
    After calling .send(None) (pre-activation), it becomes a coroutine
    that can receive values via .send().

    C++ Comparison:
        In C++20, this would be:
            generator<int> fibonacci(int max_count) {
                int a = 0, b = 1;
                for (int i = 0; i < max_count; ++i) {
                    co_yield (a = std::exchange(b, a + b));
                }
            }
        C++20 co_yield is syntactic sugar for promise_type::yield_value.
    """
    a, b = 0, 1
    for _ in range(max_count):
        a, b = b, a + b
        yield a


def running_average_coroutine() -> Generator[None, float, None]:
    """
    A generator-based coroutine that computes a running average.

    After pre-activation with .send(None), it accepts floats via .send()
    and yields the current running average.

    This demonstrates the classic "coroutine pattern" before async/await
    existed in Python. The caller and callee cooperate: caller sends data,
    callee yields results.
    """
    total: float = 0.0
    count: int = 0
    average: Optional[float] = None

    while True:
        value: float = yield average  # type: ignore[assignment]
        total += value
        count += 1
        average = total / count


# ---------------------------------------------------------------------------
# Section 2: async/await Coroutines (Modern Pattern)
# ---------------------------------------------------------------------------

async def async_display(num: int, delay: float = 1.0) -> None:
    """
    An async function (coroutine) that simulates an I/O-bound task.

    'async def' makes this a coroutine function. Calling it returns a
    coroutine object — it does NOT execute the body. The body runs only
    when the coroutine is scheduled on an event loop and reaches an
    'await' point.

    C++ Comparison:
        C++20 equivalent:
            task<void> async_display(int num, double delay) {
                co_await std::chrono::seconds(static_cast<int>(delay));
                std::cout << num << std::endl;
            }
        The key difference: C++ co_await can suspend the coroutine frame
        without heap allocation if the compiler can prove the frame is
        small enough. Python always allocates a coroutine object.
    """
    await asyncio.sleep(delay)
    print(f"  [async_display] Task {num} completed after {delay}s")


async def demo_basic_asyncio() -> None:
    """
    Demonstrates the fundamental asyncio pattern:
    multiple coroutines running concurrently on a single thread.

    Key concepts:
    - async def: defines a coroutine function
    - await: yields control back to the event loop
    - asyncio.gather(): runs multiple coroutines concurrently
    - Event loop: the scheduler that drives all coroutines
    """
    print("=" * 60)
    print("DEMO: Basic asyncio — concurrent coroutines")
    print("=" * 60)

    start = time.perf_counter()

    # Create 9 coroutine objects — they don't run yet
    coros = [async_display(i, delay=1.0) for i in range(1, 10)]

    # Run them all concurrently; total wall time ~1s, not ~9s
    await asyncio.gather(*coros)

    elapsed = time.perf_counter() - start
    print(f"  All 9 tasks completed in {elapsed:.3f}s (expected ~1.0s)\n")


# ---------------------------------------------------------------------------
# Section 3: aiohttp — Async HTTP Client
# ---------------------------------------------------------------------------

# Conditional import: aiohttp is an optional dependency
try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL | re.IGNORECASE)


@dataclass
class PageResult:
    """Holds the result of fetching a single web page."""
    url: str
    title: Optional[str] = None
    status: int = 0
    elapsed_ms: float = 0.0
    error: Optional[str] = None


async def fetch_page(
    session: ClientSession,
    url: str,
    semaphore: asyncio.Semaphore,
) -> PageResult:
    """
    Fetch a single URL and extract its <title>.

    Uses a semaphore to limit concurrency — a common enterprise pattern
    to avoid overwhelming servers or hitting rate limits.

    C++ Comparison (Boost.Beast async):
        In C++ with Boost.Beast, you would write:
            net::co_spawn(ioc,
                [&ioc, host, port, target]() -> net::awaitable<void> {
                    tcp::resolver resolver(ioc);
                    beast::tcp_stream stream(ioc);
                    auto results = co_await resolver.async_resolve(host, port, ...);
                    co_await stream.async_connect(results, ...);
                    http::request<http::empty_body> req{http::verb::get, target, 11};
                    co_await http::async_write(stream, req, ...);
                    beast::flat_buffer buffer;
                    http::response<http::dynamic_body> res;
                    co_await http::async_read(stream, buffer, res, ...);
                },
                net::detached);

        Python aiohttp achieves the same in ~5 lines because connection
        management, buffer handling, and SSL are abstracted away.
    """
    result = PageResult(url=url)
    start = time.perf_counter()

    async with semaphore:
        try:
            async with session.get(url, ssl=False) as response:
                result.status = response.status
                if response.status == 200:
                    html: str = await response.text()
                    match = TITLE_PATTERN.search(html)
                    if match:
                        result.title = match.group(1).strip()
        except Exception as exc:
            result.error = str(exc)

    result.elapsed_ms = (time.perf_counter() - start) * 1000
    return result


async def demo_aiohttp_scraper(urls: Sequence[str]) -> list[PageResult]:
    """
    Concurrent web scraper using aiohttp.

    Enterprise patterns demonstrated:
    1. Connection pooling via a single ClientSession
    2. Semaphore-based concurrency limiting
    3. Structured error handling per URL
    4. Timing instrumentation
    """
    print("=" * 60)
    print("DEMO: aiohttp concurrent web scraper")
    print("=" * 60)

    semaphore = asyncio.Semaphore(5)  # max 5 concurrent requests
    timeout = ClientTimeout(total=15)

    async with aiohttp.ClientSession(
        headers={"User-Agent": "Mozilla/5.0 (compatible; AsyncScraper/1.0)"},
        timeout=timeout,
    ) as session:
        tasks = [fetch_page(session, url, semaphore) for url in urls]
        results = await asyncio.gather(*tasks)

    for r in results:
        status_str = f"HTTP {r.status}" if r.status else "FAILED"
        title_str = r.title[:50] if r.title else "(no title)"
        error_str = f" — {r.error}" if r.error else ""
        print(f"  [{status_str:>8}] {r.elapsed_ms:7.0f}ms | {title_str}{error_str}")
        print(f"           {r.url}")

    print()
    return results


# ---------------------------------------------------------------------------
# Section 4: Async Database Operations (aiosqlite)
# ---------------------------------------------------------------------------

try:
    import aiosqlite
    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False


@dataclass
class UserRecord:
    """Simple data model for a user."""
    id: int
    name: str
    email: str
    created_at: str = ""


async def demo_async_database() -> None:
    """
    Demonstrates async database operations with aiosqlite.

    Enterprise patterns:
    1. Async context managers for connection lifecycle
    2. Parameterized queries (SQL injection prevention)
    3. Transaction management
    4. Concurrent read/write via asyncio.gather

    C++ Comparison:
        In C++, async database access typically uses:
        - Boost.MySQL (async MySQL with Boost.Asio coroutines)
        - libpq with non-blocking mode + event loop integration
        - soci with thread pool wrappers

        Python's aiosqlite wraps sqlite3 in a thread pool executor
        (SQLite itself is not async), exposing an async interface.
        For PostgreSQL, asyncpg is truly async (C extension using libpq
        in non-blocking mode, directly integrated with asyncio).
    """
    print("=" * 60)
    print("DEMO: Async database operations (aiosqlite)")
    print("=" * 60)

    db_path = ":memory:"  # in-memory database for demo

    async with aiosqlite.connect(db_path) as db:
        # Create table
        await db.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert multiple records concurrently (batched)
        users_data = [
            ("Alice", "alice@example.com"),
            ("Bob", "bob@example.com"),
            ("Charlie", "charlie@example.com"),
            ("Diana", "diana@example.com"),
            ("Eve", "eve@example.com"),
        ]

        await db.executemany(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            users_data,
        )
        await db.commit()
        print(f"  Inserted {len(users_data)} users")

        # Async read — multiple queries can be issued concurrently
        async def fetch_user(user_id: int) -> Optional[UserRecord]:
            async with db.execute(
                "SELECT id, name, email, created_at FROM users WHERE id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return UserRecord(
                        id=row[0], name=row[1],
                        email=row[2], created_at=row[3],
                    )
                return None

        # Fetch all users concurrently
        tasks = [fetch_user(i) for i in range(1, len(users_data) + 1)]
        users: list[Optional[UserRecord]] = await asyncio.gather(*tasks)

        for user in users:
            if user:
                print(f"  [{user.id}] {user.name} <{user.email}> ({user.created_at})")

        # Aggregate query
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            count = (await cursor.fetchone())[0]
        print(f"  Total users in database: {count}")

    print()


# ---------------------------------------------------------------------------
# Section 5: Enterprise Async API Client
# ---------------------------------------------------------------------------

@dataclass
class APIResponse:
    """Structured API response container."""
    status_code: int
    data: Any
    latency_ms: float
    endpoint: str


class AsyncAPIClient:
    """
    Enterprise-grade async API client with:
    - Connection pooling (single session, reused across requests)
    - Automatic retry with exponential backoff
    - Rate limiting via semaphore
    - Configurable timeouts
    - Structured logging

    C++ Comparison:
        In C++, an equivalent HTTP client would use Boost.Beast or
        cpp-httplib with an io_context-based executor. The retry logic
        would use Boost.Asio steady_timer. Connection pooling requires
        manual management or a library like Boost.MySQL's connection_pool.

        Python's aiohttp provides connection pooling out of the box via
        its TCPConnector, which is configured on the ClientSession.
    """

    def __init__(
        self,
        base_url: str,
        max_concurrency: int = 10,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = ClientTimeout(total=timeout_seconds)
        self._max_retries = max_retries
        self._session: Optional[ClientSession] = None

    async def __aenter__(self) -> AsyncAPIClient:
        self._session = aiohttp.ClientSession(
            timeout=self._timeout,
            headers={"Accept": "application/json"},
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._session:
            await self._session.close()

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> APIResponse:
        """Execute an HTTP request with exponential backoff retry."""
        if not self._session:
            raise RuntimeError("Client not initialized. Use 'async with'.")

        url = f"{self._base_url}{endpoint}"
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            start = time.perf_counter()
            try:
                async with self._semaphore:
                    async with self._session.request(method, url, **kwargs) as resp:
                        data = await resp.json()
                        latency = (time.perf_counter() - start) * 1000
                        return APIResponse(
                            status_code=resp.status,
                            data=data,
                            latency_ms=latency,
                            endpoint=endpoint,
                        )
            except Exception as exc:
                last_error = exc
                if attempt < self._max_retries:
                    backoff = 2 ** attempt * 0.1
                    print(f"  Retry {attempt + 1}/{self._max_retries} "
                          f"for {endpoint} after {backoff:.1f}s: {exc}")
                    await asyncio.sleep(backoff)

        raise last_error  # type: ignore[misc]

    async def get(self, endpoint: str, **kwargs: Any) -> APIResponse:
        return await self._request_with_retry("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> APIResponse:
        return await self._request_with_retry("POST", endpoint, **kwargs)


async def demo_async_api_client() -> None:
    """
    Demonstrates the enterprise async API client hitting a public API.
    """
    print("=" * 60)
    print("DEMO: Enterprise async API client with retry/backoff")
    print("=" * 60)

    # Using JSONPlaceholder — a free fake REST API
    async with AsyncAPIClient(
        base_url="https://jsonplaceholder.typicode.com",
        max_concurrency=5,
        timeout_seconds=10,
        max_retries=2,
    ) as client:
        # Fetch multiple endpoints concurrently
        endpoints = [f"/posts/{i}" for i in range(1, 6)]
        tasks = [client.get(ep) for ep in endpoints]
        responses: list[APIResponse] = await asyncio.gather(*tasks)

        for resp in responses:
            title = resp.data.get("title", "")[:50] if isinstance(resp.data, dict) else ""
            print(f"  [{resp.status_code}] {resp.latency_ms:6.0f}ms | "
                  f"{resp.endpoint} — {title}")

    print()


# ---------------------------------------------------------------------------
# Section 6: Event Loop Deep Dive
# ---------------------------------------------------------------------------

async def demo_event_loop_internals() -> None:
    """
    Demonstrates event loop internals and coroutine lifecycle.

    C++ Comparison:
        Python's event loop is conceptually identical to Boost.Asio's
        io_context:
        - io_context::run()  <->  asyncio.run() / loop.run_until_complete()
        - co_await           <->  await
        - io_context::post() <->  asyncio.ensure_future() / loop.create_task()

        Key difference: Boost.Asio supports multi-threaded event loops
        (io_context::run() called from N threads) with strand-based
        synchronization. Python's asyncio is single-threaded; for CPU-bound
        work, use loop.run_in_executor() to offload to a thread/process pool.
    """
    print("=" * 60)
    print("DEMO: Event loop internals and task scheduling")
    print("=" * 60)

    loop = asyncio.get_running_loop()
    print(f"  Event loop type: {type(loop).__name__}")
    print(f"  Loop is running: {loop.is_running()}")

    # Demonstrate task creation and cancellation
    async def long_running_task(name: str, seconds: float) -> str:
        print(f"  Task '{name}' started")
        await asyncio.sleep(seconds)
        print(f"  Task '{name}' finished")
        return f"{name}_result"

    # Create tasks explicitly
    task_a = asyncio.create_task(long_running_task("A", 0.3))
    task_b = asyncio.create_task(long_running_task("B", 0.1))

    # task_b should finish first (0.1s vs 0.3s)
    results = await asyncio.gather(task_a, task_b)
    print(f"  Results (order of completion): {results}")

    # Demonstrate task cancellation
    async def cancellable_task() -> None:
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("  Task was cancelled (as expected)")

    task_c = asyncio.create_task(cancellable_task())
    await asyncio.sleep(0.05)  # let it start
    task_c.cancel()
    try:
        await task_c
    except asyncio.CancelledError:
        print("  Caught CancelledError in caller")

    # Demonstrate wait_for with timeout
    async def slow_task() -> str:
        await asyncio.sleep(5)
        return "done"

    try:
        await asyncio.wait_for(slow_task(), timeout=0.1)
    except asyncio.TimeoutError:
        print("  wait_for timed out after 0.1s (as expected)")

    print()


# ---------------------------------------------------------------------------
# Section 7: Synchronization Primitives
# ---------------------------------------------------------------------------

async def demo_async_synchronization() -> None:
    """
    Demonstrates asyncio synchronization primitives.

    These are the async equivalents of threading.Lock, threading.Event, etc.
    They do NOT block the thread — they yield control to the event loop
    while waiting.
    """
    print("=" * 60)
    print("DEMO: Async synchronization primitives")
    print("=" * 60)

    # Async Lock — protects shared mutable state
    counter = 0
    lock = asyncio.Lock()

    async def increment(n: int) -> None:
        nonlocal counter
        for _ in range(n):
            async with lock:
                counter += 1

    await asyncio.gather(*[increment(100) for _ in range(10)])
    print(f"  Lock-protected counter: {counter} (expected 1000)")

    # Async Event — signal between coroutines
    ready = asyncio.Event()

    async def waiter(name: str) -> None:
        await ready.wait()
        print(f"  {name} proceeded after event was set")

    async def setter() -> None:
        await asyncio.sleep(0.1)
        print("  Setting the event...")
        ready.set()

    await asyncio.gather(
        waiter("Waiter-1"),
        waiter("Waiter-2"),
        waiter("Waiter-3"),
        setter(),
    )

    # Async Queue — producer-consumer pattern
    queue: asyncio.Queue[Optional[int]] = asyncio.Queue(maxsize=5)

    async def producer() -> None:
        for i in range(10):
            await queue.put(i)
        await queue.put(None)  # sentinel
        print(f"  Producer: queued 10 items + sentinel")

    async def consumer(name: str) -> None:
        consumed = 0
        while True:
            item = await queue.get()
            if item is None:
                break
            consumed += 1
            queue.task_done()
        print(f"  Consumer '{name}': consumed {consumed} items")

    await asyncio.gather(producer(), consumer("C1"), consumer("C2"))
    print()


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

async def main() -> None:
    """Run all demonstrations."""
    print()
    print("#" * 60)
    print("# Day 63: Asyncio and Asynchronous Programming (Part 3)")
    print("#" * 60)
    print()

    # 1. Generator-based coroutine (sync, no event loop needed)
    print("=" * 60)
    print("DEMO: Generator-based coroutine (running average)")
    print("=" * 60)
    avg_coro = running_average_coroutine()
    next(avg_coro)  # pre-activate (send None)
    test_values = [10.0, 20.0, 30.0, 25.0, 15.0]
    for v in test_values:
        result = avg_coro.send(v)
        print(f"  Sent {v:5.1f} -> running average: {result:.2f}")
    avg_coro.close()
    print()

    # 2. Fibonacci generator
    print("=" * 60)
    print("DEMO: Fibonacci generator (first 12 numbers)")
    print("=" * 60)
    fib_numbers = list(fibonacci_generator(12))
    print(f"  {fib_numbers}")
    print()

    # 3. Basic async/await
    await demo_basic_asyncio()

    # 4. Event loop internals
    await demo_event_loop_internals()

    # 5. Synchronization primitives
    await demo_async_synchronization()

    # 6. aiohttp web scraper (skip if aiohttp not installed)
    if HAS_AIOHTTP:
        urls = [
            "https://www.python.org/",
            "https://httpbin.org/get",
            "https://jsonplaceholder.typicode.com/posts/1",
            "https://www.github.com/",
            "https://httpbin.org/delay/1",
        ]
        await demo_aiohttp_scraper(urls)

        await demo_async_api_client()
    else:
        print("  [SKIP] aiohttp not installed. Run: pip install aiohttp")
        print()

    # 7. Async database (skip if aiosqlite not installed)
    if HAS_AIOSQLITE:
        await demo_async_database()
    else:
        print("  [SKIP] aiosqlite not installed. Run: pip install aiosqlite")
        print()

    print("=" * 60)
    print("All demonstrations completed.")
    print("=" * 60)


if __name__ == "__main__":
    # asyncio.run() creates a new event loop, runs the coroutine, and
    # cleans up. This is the recommended entry point since Python 3.7.
    #
    # C++ Comparison:
    #   Boost.Asio equivalent:
    #     net::io_context ioc;
    #     net::co_spawn(ioc, main_coroutine(), net::detached);
    #     ioc.run();
    #
    #   The key difference: Python's asyncio.run() handles signal
    #   installation, loop cleanup, and generator-based coroutine
    #   detection automatically.

    asyncio.run(main())
