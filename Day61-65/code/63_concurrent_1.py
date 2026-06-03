"""
Day 63 - Python Concurrency Programming (Part 1): Threading Fundamentals
=========================================================================

This module demonstrates Python's threading capabilities, synchronization
primitives, and enterprise-grade concurrency patterns.

Topics Covered:
    - threading.Thread basics (target, args, kwargs)
    - Subclassing Thread and overriding run()
    - Lock and RLock for mutual exclusion
    - Semaphore for resource access control
    - Event for signaling between threads
    - Condition for producer-consumer coordination
    - ThreadPoolExecutor from concurrent.futures

C++ Comparison Notes:
    -----------------------------------------------------------------------
    | Python threading              | C++ std::thread                      |
    -----------------------------------------------------------------------
    | threading.Thread(target=fn)   | std::thread t(fn)                    |
    | thread.start()                | t.join() auto-starts on construction |
    | thread.join()                 | t.join()                             |
    | daemon=True                   | No direct equivalent; use detach()   |
    | GIL limits true parallelism   | True parallelism on multi-core       |
    -----------------------------------------------------------------------

    | Python Lock / RLock           | C++ std::mutex / std::recursive_mutex|
    -----------------------------------------------------------------------
    | lock.acquire() / release()    | mutex.lock() / unlock()              |
    | with lock:                    | std::lock_guard<std::mutex>          |
    | threading.Lock()              | std::mutex                           |
    | threading.RLock()             | std::recursive_mutex                 |
    -----------------------------------------------------------------------

    GIL Limitation vs C++ True Parallelism:
        - CPython's GIL ensures only one thread executes Python bytecode
          at a time, regardless of CPU core count.
        - C++ std::thread provides true OS-level parallelism; each thread
          runs on a separate core simultaneously.
        - For CPU-bound work in Python, use multiprocessing instead.
        - For I/O-bound work, Python threading remains effective because
          the GIL is released during I/O operations.
    -----------------------------------------------------------------------

Author: Python-100-Days Project
License: MIT
"""

from __future__ import annotations

import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable


# =============================================================================
# Section 1: Threading Basics - Thread Class
# =============================================================================
#
# C++ comparison:
#   Python:  t = threading.Thread(target=fn, args=(a,), kwargs={"k": v})
#            t.start()   # explicitly start
#            t.join()    # wait for completion
#
#   C++:     std::thread t(fn, a);  // starts immediately on construction
#            t.join();              // wait for completion
#
# Key difference: Python threads require an explicit start() call.
# C++ threads begin executing immediately upon construction.
# =============================================================================


def download_file(filename: str, delay: float | None = None) -> float:
    """Simulate downloading a file with an I/O-bound delay.

    Args:
        filename: Name of the file to download.
        delay: Simulated download duration in seconds. If None, a random
               delay between 1.0 and 3.0 seconds is used.

    Returns:
        The elapsed time in seconds for the simulated download.
    """
    if delay is None:
        delay = random.uniform(1.0, 3.0)
    print(f"  [Download] Starting: {filename}")
    time.sleep(delay)  # Simulates I/O wait (GIL is released here)
    print(f"  [Download] Completed: {filename} ({delay:.2f}s)")
    return delay


def sequential_downloader(filenames: list[str]) -> float:
    """Download files one after another (no concurrency).

    Args:
        filenames: List of file names to download.

    Returns:
        Total elapsed time in seconds.
    """
    print("\n[Sequential Downloader]")
    start = time.perf_counter()
    for name in filenames:
        download_file(name)
    elapsed = time.perf_counter() - start
    print(f"  Total time (sequential): {elapsed:.2f}s\n")
    return elapsed


def threaded_downloader(filenames: list[str]) -> float:
    """Download files concurrently using Thread objects.

    Each file is downloaded in its own thread. The main thread waits
    for all downloads to finish via join().

    Args:
        filenames: List of file names to download.

    Returns:
        Total elapsed time in seconds.
    """
    print("[Threaded Downloader]")
    threads: list[threading.Thread] = []
    start = time.perf_counter()

    for name in filenames:
        t = threading.Thread(
            target=download_file,
            kwargs={"filename": name},
            name=f"Downloader-{name}",  # Useful for debugging
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()  # Block until this thread completes

    elapsed = time.perf_counter() - start
    print(f"  Total time (threaded): {elapsed:.2f}s\n")
    return elapsed


# =============================================================================
# Section 2: Subclassing Thread
# =============================================================================
#
# C++ comparison:
#   In C++, you don't subclass std::thread. Instead, you pass a callable
#   (function, lambda, or functor object) to the constructor.
#
#   C++ functor pattern (closest analogy):
#       class DownloadTask {
#       public:
#           void operator()() const { /* work here */ }
#       };
#       std::thread t(DownloadTask{});
#
#   Python's Thread subclass pattern with run() override has no direct
#   C++ equivalent. The C++ approach is composition-based.
# =============================================================================


class DownloadThread(threading.Thread):
    """A thread that simulates downloading a file.

    Demonstrates the Thread subclass pattern: override __init__ to store
    state, override run() to define the thread's work.

    Attributes:
        filename: The name of the file to download.
        elapsed: The time taken to complete the download (set after join).
    """

    def __init__(self, filename: str, delay: float | None = None) -> None:
        super().__init__(name=f"DL-{filename}")
        self.filename = filename
        self.delay = delay if delay is not None else random.uniform(1.0, 3.0)
        self.elapsed: float = 0.0

    def run(self) -> None:
        """Execute the download simulation. Called by start()."""
        print(f"  [{self.name}] Starting download")
        time.sleep(self.delay)
        self.elapsed = self.delay
        print(f"  [{self.name}] Finished ({self.delay:.2f}s)")


def demo_subclassed_threads() -> None:
    """Demonstrate downloading with subclassed Thread objects."""
    print("[Subclassed Thread Downloader]")
    files = ["report.pdf", "data.csv", "image.png"]
    threads = [DownloadThread(f) for f in files]

    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start

    for t in threads:
        print(f"  {t.filename}: {t.elapsed:.2f}s")
    print(f"  Total time: {elapsed:.2f}s\n")


# =============================================================================
# Section 3: Thread Pool (concurrent.futures.ThreadPoolExecutor)
# =============================================================================
#
# C++ comparison:
#   Python's ThreadPoolExecutor is similar in concept to a C++ thread pool
#   library (e.g., BS::thread_pool, or a custom implementation using
#   std::vector<std::thread> + a task queue + std::condition_variable).
#
#   C++ does not have a standard thread pool in the library (as of C++23).
#   Python's concurrent.futures provides this out of the box.
#
#   C++23 std::execution senders/receivers offer a higher-level approach
#   but with a very different API surface.
# =============================================================================


def process_task(task_id: int) -> dict[str, Any]:
    """Simulate processing a task that takes variable time.

    Args:
        task_id: An integer identifying the task.

    Returns:
        A dictionary with task_id, result, and duration.
    """
    duration = random.uniform(0.5, 2.0)
    time.sleep(duration)
    return {"task_id": task_id, "result": task_id ** 2, "duration": duration}


def demo_thread_pool() -> None:
    """Demonstrate ThreadPoolExecutor with task submission and result collection."""
    print("[Thread Pool Demo]")
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="Worker") as pool:
        futures = {pool.submit(process_task, i): i for i in range(8)}

        for future in as_completed(futures):
            result = future.result()
            print(
                f"  Task {result['task_id']}: result={result['result']}, "
                f"duration={result['duration']:.2f}s"
            )
    print()


# =============================================================================
# Section 4: Lock - Mutual Exclusion
# =============================================================================
#
# C++ comparison:
#   Python Lock    <->  C++ std::mutex
#   Python RLock   <->  C++ std::recursive_mutex
#
#   Python:
#       lock = threading.Lock()
#       with lock:              # __enter__ -> acquire, __exit__ -> release
#           critical_section()
#
#   C++:
#       std::mutex mtx;
#       {
#           std::lock_guard<std::mutex> guard(mtx);  // RAII lock
#           critical_section();
#       }  // destructor releases lock
#
#   Both use RAII-style (or context-manager-style) patterns for safe
#   lock management. Python's "with" statement is analogous to C++ RAII.
#
#   Important: Python's Lock is NOT reentrant. If the same thread tries
#   to acquire it twice, it deadlocks. Use RLock for reentrant needs.
# =============================================================================


@dataclass
class BankAccount:
    """A thread-safe bank account protected by an RLock.

    Demonstrates the classic race condition problem and its solution
    using a reentrant lock.

    Attributes:
        name: The account holder's name.
        balance: The current account balance (in arbitrary currency units).
        _lock: An RLock protecting the balance.
        _history: A log of all transactions.
    """

    name: str
    balance: float = 0.0
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _history: list[str] = field(default_factory=list, repr=False)

    def deposit(self, amount: float) -> None:
        """Deposit money into the account (thread-safe).

        Args:
            amount: The amount to deposit. Must be positive.
        """
        if amount <= 0:
            raise ValueError(f"Deposit amount must be positive, got {amount}")
        with self._lock:
            old_balance = self.balance
            time.sleep(0.001)  # Simulates processing latency
            self.balance += amount
            self._history.append(
                f"deposit +{amount:.2f}: {old_balance:.2f} -> {self.balance:.2f}"
            )

    def withdraw(self, amount: float) -> bool:
        """Withdraw money from the account (thread-safe).

        Args:
            amount: The amount to withdraw. Must be positive.

        Returns:
            True if withdrawal succeeded, False if insufficient funds.
        """
        if amount <= 0:
            raise ValueError(f"Withdrawal amount must be positive, got {amount}")
        with self._lock:
            if self.balance >= amount:
                old_balance = self.balance
                time.sleep(0.001)  # Simulates processing latency
                self.balance -= amount
                self._history.append(
                    f"withdraw -{amount:.2f}: {old_balance:.2f} -> {self.balance:.2f}"
                )
                return True
            return False

    def get_balance(self) -> float:
        """Return the current balance (thread-safe)."""
        with self._lock:
            return self.balance

    def get_history(self) -> list[str]:
        """Return a copy of the transaction history."""
        with self._lock:
            return list(self._history)


def demo_bank_account_race_condition() -> None:
    """Show the race condition problem and how RLock fixes it.

    Without a lock, 100 concurrent deposits of $1 will likely produce
    a final balance less than $100 due to lost updates.
    """
    print("[Bank Account - Race Condition Demo]")

    # --- Without lock: demonstrate lost updates ---
    class UnsafeAccount:
        def __init__(self) -> None:
            self.balance: float = 0.0

        def deposit(self, amount: float) -> None:
            new_balance = self.balance + amount
            time.sleep(0.001)  # Simulates latency; increases race window
            self.balance = new_balance

    unsafe = UnsafeAccount()
    with ThreadPoolExecutor(max_workers=16) as pool:
        for _ in range(100):
            pool.submit(unsafe.deposit, 1.0)
    print(f"  Without lock: 100 deposits of $1 -> balance = ${unsafe.balance:.2f}")

    # --- With RLock: correct result ---
    safe = BankAccount(name="SafeAccount")
    with ThreadPoolExecutor(max_workers=16) as pool:
        for _ in range(100):
            pool.submit(safe.deposit, 1.0)
    print(f"  With RLock:   100 deposits of $1 -> balance = ${safe.get_balance():.2f}")
    print()


# =============================================================================
# Section 5: Lock vs RLock - Key Differences
# =============================================================================
#
# Lock:  Non-reentrant. If the same thread tries to acquire it twice,
#        it will deadlock.
#
# RLock: Reentrant (recursive). The same thread can acquire it multiple
#        times. It must release it the same number of times before
#        another thread can acquire it.
#
# C++ comparison:
#   Python threading.Lock()   <-> std::mutex (non-reentrant)
#   Python threading.RLock()  <-> std::recursive_mutex (reentrant)
#
# Recommendation: Use RLock unless you have a specific reason to prefer
# the stricter Lock. RLock is safer when lock acquisition may happen
# at multiple call levels in the same thread.
# =============================================================================


def demo_lock_vs_rlock() -> None:
    """Demonstrate the difference between Lock and RLock."""
    print("[Lock vs RLock Demo]")

    rlock = threading.RLock()
    results: list[str] = []

    def nested_operation(thread_name: str) -> None:
        """Acquires the lock at two levels (only safe with RLock)."""
        with rlock:
            results.append(f"{thread_name}: outer lock acquired")
            with rlock:  # Would deadlock with a plain Lock
                results.append(f"{thread_name}: inner lock acquired")
            results.append(f"{thread_name}: inner lock released")
        results.append(f"{thread_name}: outer lock released")

    threads = [
        threading.Thread(target=nested_operation, args=(f"T{i}",)) for i in range(3)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  Nested locking completed successfully ({len(results)} operations)")
    print(f"  Sample: {results[:4]}")
    print()


# =============================================================================
# Section 6: Semaphore - Limiting Concurrent Access
# =============================================================================
#
# C++ comparison:
#   Python threading.Semaphore(n)  <->  C++ std::counting_semaphore<n> (C++20)
#   Python threading.BoundedSemaphore(n) <-> std::counting_semaphore with
#                                            max value enforcement
#
#   Before C++20, C++ programmers used std::mutex + std::condition_variable
#   to implement semaphore-like behavior manually.
#
#   Python Semaphore is commonly used to limit the number of threads
#   accessing a resource pool (e.g., database connections, API rate limits).
# =============================================================================


class ConnectionPool:
    """A simulated connection pool with bounded capacity.

    Uses a Semaphore to limit the number of concurrent connections.

    Attributes:
        name: The pool's name for logging.
        _sem: A BoundedSemaphore limiting concurrent access.
        _active: Count of currently active connections.
    """

    def __init__(self, name: str, max_connections: int) -> None:
        self.name = name
        self._max = max_connections
        self._sem = threading.BoundedSemaphore(max_connections)
        self._active = 0
        self._lock = threading.Lock()

    def acquire_connection(self, client_id: int) -> None:
        """Acquire a connection (blocks if pool is exhausted).

        Args:
            client_id: Identifier for the requesting client.
        """
        print(f"  Client {client_id}: waiting for connection...")
        self._sem.acquire()
        with self._lock:
            self._active += 1
            print(
                f"  Client {client_id}: connected "
                f"(active={self._active}/{self._max})"
            )

    def release_connection(self, client_id: int) -> None:
        """Release a connection back to the pool.

        Args:
            client_id: Identifier for the releasing client.
        """
        with self._lock:
            self._active -= 1
        self._sem.release()
        print(
            f"  Client {client_id}: disconnected "
            f"(active={self._active}/{self._max})"
        )

    def use_connection(self, client_id: int, work_duration: float) -> None:
        """Simulate using a database connection.

        Args:
            client_id: Identifier for the client.
            work_duration: How long the simulated work takes (seconds).
        """
        self.acquire_connection(client_id)
        try:
            time.sleep(work_duration)  # Simulate database work
        finally:
            self.release_connection(client_id)


def demo_semaphore() -> None:
    """Demonstrate Semaphore limiting concurrent database connections."""
    print("[Semaphore Demo - Connection Pool]")
    pool = ConnectionPool(name="PostgresPool", max_connections=3)

    with ThreadPoolExecutor(max_workers=6) as executor:
        for cid in range(6):
            executor.submit(pool.use_connection, cid, random.uniform(0.5, 1.5))
    print()


# =============================================================================
# Section 7: Event - Signaling Between Threads
# =============================================================================
#
# C++ comparison:
#   Python threading.Event()  <->  C++ std::condition_variable + bool flag
#
#   C++ approach:
#       std::mutex mtx;
#       std::condition_variable cv;
#       bool ready = false;
#
#       // Waiting thread:
#       std::unique_lock<std::mutex> lk(mtx);
#       cv.wait(lk, [&]{ return ready; });
#
#       // Signaling thread:
#       {
#           std::lock_guard<std::mutex> lk(mtx);
#           ready = true;
#       }
#       cv.notify_all();
#
#   Python's Event encapsulates this pattern into a single object
#   with set(), clear(), wait(), and is_set() methods.
# =============================================================================


def demo_event() -> None:
    """Demonstrate Event for coordinating a startup sequence.

    Multiple worker threads wait for a 'ready' event before starting work.
    A coordinator thread sets the event after initialization.
    """
    print("[Event Demo - Startup Coordination]")
    ready_event = threading.Event()
    results: list[str] = []
    lock = threading.Lock()

    def worker(worker_id: int) -> None:
        """Worker that waits for the ready signal before proceeding."""
        print(f"  Worker {worker_id}: waiting for ready signal...")
        ready_event.wait()  # Block until event is set
        with lock:
            results.append(f"Worker-{worker_id}")
        print(f"  Worker {worker_id}: started working!")

    def coordinator() -> None:
        """Simulate initialization, then signal all workers."""
        print("  Coordinator: initializing system...")
        time.sleep(1.0)  # Simulate initialization work
        print("  Coordinator: system ready! Signaling workers.")
        ready_event.set()  # Wake up all waiting threads

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    threads.append(threading.Thread(target=coordinator))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  All workers completed: {results}\n")


# =============================================================================
# Section 8: Condition - Producer-Consumer Pattern
# =============================================================================
#
# C++ comparison:
#   Python threading.Condition  <->  C++ std::condition_variable
#
#   Python:
#       cond = threading.Condition(lock)
#       with cond:           # acquires the lock
#           cond.wait()      # releases lock, blocks, re-acquires on wake
#           cond.notify()    # wakes one waiting thread
#           cond.notify_all()  # wakes all waiting threads
#
#   C++:
#       std::condition_variable cv;
#       std::unique_lock<std::mutex> lk(mtx);
#       cv.wait(lk, predicate);   // releases lock, blocks, re-acquires
#       cv.notify_one();
#       cv.notify_all();
#
#   The Condition in Python bundles a lock internally (or accepts one),
#   making it a convenient all-in-one synchronization primitive.
# =============================================================================


@dataclass
class BoundedBuffer:
    """A thread-safe bounded buffer (producer-consumer queue).

    This is the classic solution to the bounded-buffer problem using
    a Condition variable for coordination.

    Attributes:
        capacity: Maximum number of items the buffer can hold.
        _buffer: Internal list storing items.
        _cond: Condition variable for synchronization.
    """

    capacity: int = 5
    _buffer: list[Any] = field(default_factory=list, repr=False)
    _cond: threading.Condition = field(
        default_factory=threading.Condition, repr=False
    )

    def put(self, item: Any, producer_id: int) -> None:
        """Add an item to the buffer. Blocks if the buffer is full.

        Args:
            item: The item to add.
            producer_id: Identifier of the producing thread.
        """
        with self._cond:
            while len(self._buffer) >= self.capacity:
                print(
                    f"  Producer {producer_id}: buffer full, waiting..."
                    f" (size={len(self._buffer)})"
                )
                self._cond.wait()
            self._buffer.append(item)
            print(
                f"  Producer {producer_id}: added {item} "
                f"(size={len(self._buffer)})"
            )
            self._cond.notify_all()  # Wake up consumers

    def get(self, consumer_id: int) -> Any:
        """Remove and return an item from the buffer. Blocks if empty.

        Args:
            consumer_id: Identifier of the consuming thread.

        Returns:
            The item removed from the buffer.
        """
        with self._cond:
            while len(self._buffer) == 0:
                print(f"  Consumer {consumer_id}: buffer empty, waiting...")
                self._cond.wait()
            item = self._buffer.pop(0)
            print(
                f"  Consumer {consumer_id}: got {item} "
                f"(size={len(self._buffer)})"
            )
            self._cond.notify_all()  # Wake up producers
            return item

    def size(self) -> int:
        """Return the current number of items in the buffer."""
        with self._cond:
            return len(self._buffer)


def demo_producer_consumer() -> None:
    """Demonstrate the producer-consumer pattern with a bounded buffer.

    Multiple producers generate items and multiple consumers process them.
    The bounded buffer ensures producers wait when full and consumers wait
    when empty.
    """
    print("[Producer-Consumer Demo]")
    buffer = BoundedBuffer(capacity=3)
    sentinel = None  # Poison pill to signal consumers to stop

    def producer(producer_id: int, count: int) -> None:
        """Produce `count` items and put them into the buffer."""
        for i in range(count):
            item = f"P{producer_id}-Item{i}"
            buffer.put(item, producer_id)
            time.sleep(random.uniform(0.1, 0.3))
        print(f"  Producer {producer_id}: done producing")

    def consumer(consumer_id: int) -> None:
        """Consume items until a sentinel (None) is received."""
        while True:
            item = buffer.get(consumer_id)
            if item is sentinel:
                print(f"  Consumer {consumer_id}: received stop signal")
                break
            time.sleep(random.uniform(0.1, 0.4))  # Simulate processing
        print(f"  Consumer {consumer_id}: done")

    num_producers = 2
    items_per_producer = 4
    num_consumers = 2

    threads: list[threading.Thread] = []

    # Start producers
    for pid in range(num_producers):
        t = threading.Thread(
            target=producer, args=(pid, items_per_producer), name=f"Producer-{pid}"
        )
        threads.append(t)

    # Start consumers
    for cid in range(num_consumers):
        t = threading.Thread(
            target=consumer, args=(cid,), name=f"Consumer-{cid}"
        )
        threads.append(t)

    for t in threads:
        t.start()

    # Wait for producers to finish, then send sentinels to stop consumers
    for t in threads[:num_producers]:
        t.join()

    for _ in range(num_consumers):
        buffer.put(sentinel, producer_id=-1)  # Poison pills

    for t in threads:
        t.join()

    print(f"  Final buffer size: {buffer.size()}\n")


# =============================================================================
# Section 9: Daemon Threads
# =============================================================================
#
# C++ comparison:
#   Python daemon=True  <->  C++ t.detach()
#
#   However, detached C++ threads continue running independently until
#   the process exits. Python daemon threads are forcibly terminated
#   when all non-daemon threads have finished.
#
#   C++ detached threads do not automatically stop; you must implement
#   your own shutdown mechanism (e.g., atomic flag, condition variable).
# =============================================================================


def demo_daemon_threads() -> None:
    """Demonstrate daemon vs non-daemon thread behavior."""
    print("[Daemon Thread Demo]")

    stop_event = threading.Event()

    def background_monitor(name: str) -> None:
        """A background task that runs until stopped."""
        count = 0
        while not stop_event.is_set():
            count += 1
            time.sleep(0.1)
        print(f"  {name}: stopped after {count} iterations")

    # Daemon thread: will be terminated when main thread exits
    daemon_t = threading.Thread(
        target=background_monitor, args=("Daemon-Monitor",), daemon=True
    )
    daemon_t.start()

    # Simulate main thread doing work
    print("  Main thread: doing work for 0.5 seconds...")
    time.sleep(0.5)

    # Signal the non-daemon thread to stop
    stop_event.set()
    daemon_t.join(timeout=1.0)
    print("  Main thread: all done\n")


# =============================================================================
# Section 10: Enterprise Example - Concurrent Web Scraper
# =============================================================================
#
# A realistic example combining ThreadPoolExecutor, Semaphore (rate limiting),
# and Lock (thread-safe result collection).
#
# C++ comparison:
#   In C++, this would typically use a thread pool library + a mutex-protected
#   shared vector for results. Python's ThreadPoolExecutor and threading.Lock
#   provide equivalent functionality with less boilerplate.
# =============================================================================


@dataclass
class ScrapingResult:
    """Result from scraping a single URL."""

    url: str
    status_code: int
    content_length: int
    elapsed: float


class RateLimitedScraper:
    """A thread-safe web scraper with rate limiting.

    Uses a Semaphore to limit concurrent requests and a Lock to safely
    collect results from multiple threads.

    Attributes:
        max_concurrent: Maximum number of simultaneous requests.
        _sem: Semaphore for rate limiting.
        _lock: Lock for thread-safe result collection.
        _results: List of scraping results.
    """

    def __init__(self, max_concurrent: int = 3) -> None:
        self.max_concurrent = max_concurrent
        self._sem = threading.BoundedSemaphore(max_concurrent)
        self._lock = threading.Lock()
        self._results: list[ScrapingResult] = []

    def scrape(self, url: str) -> ScrapingResult:
        """Scrape a single URL with rate limiting.

        Args:
            url: The URL to scrape.

        Returns:
            A ScrapingResult with simulated response data.
        """
        with self._sem:
            start = time.perf_counter()
            # Simulate HTTP request (random status and delay)
            time.sleep(random.uniform(0.2, 1.0))
            elapsed = time.perf_counter() - start

            result = ScrapingResult(
                url=url,
                status_code=random.choice([200, 200, 200, 404, 500]),
                content_length=random.randint(1000, 50000),
                elapsed=elapsed,
            )

            with self._lock:
                self._results.append(result)

            return result

    def scrape_all(self, urls: list[str]) -> list[ScrapingResult]:
        """Scrape all URLs concurrently.

        Args:
            urls: List of URLs to scrape.

        Returns:
            List of ScrapingResult objects.
        """
        self._results.clear()
        with ThreadPoolExecutor(
            max_workers=self.max_concurrent, thread_name_prefix="Scraper"
        ) as pool:
            futures = {pool.submit(self.scrape, url): url for url in urls}
            for future in as_completed(futures):
                result = future.result()
                status_marker = "OK" if result.status_code == 200 else "FAIL"
                print(
                    f"  [{status_marker}] {result.url} "
                    f"(status={result.status_code}, "
                    f"size={result.content_length}, "
                    f"time={result.elapsed:.2f}s)"
                )
        return self._results

    def get_results(self) -> list[ScrapingResult]:
        """Return a copy of all collected results."""
        with self._lock:
            return list(self._results)


def demo_enterprise_scraper() -> None:
    """Demonstrate the rate-limited concurrent scraper."""
    print("[Enterprise Scraper Demo]")
    scraper = RateLimitedScraper(max_concurrent=3)

    urls = [
        "https://api.example.com/users",
        "https://api.example.com/products",
        "https://api.example.com/orders",
        "https://api.example.com/reviews",
        "https://api.example.com/categories",
        "https://api.example.com/inventory",
    ]

    results = scraper.scrape_all(urls)
    successful = sum(1 for r in results if r.status_code == 200)
    total_time = sum(r.elapsed for r in results)
    wall_time = max(r.elapsed for r in results) if results else 0

    print(f"\n  Summary: {successful}/{len(results)} successful")
    print(f"  Total CPU time: {total_time:.2f}s")
    print(f"  Wall clock time: ~{wall_time:.2f}s (concurrent execution)")
    print(f"  Speedup: ~{total_time / wall_time:.1f}x\n")


# =============================================================================
# Section 11: Thread-Safe Singleton with Lock
# =============================================================================
#
# A common enterprise pattern: ensuring only one instance of a class
# exists, even when accessed from multiple threads.
# =============================================================================


class ThreadSafeSingleton:
    """A thread-safe singleton implementation using double-checked locking.

    C++ comparison:
        C++11 guarantees thread-safe local static initialization:
            static Singleton& instance() {
                static Singleton s;
                return s;
            }
        Python requires explicit locking for the same guarantee.
    """

    _instance: ThreadSafeSingleton | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> ThreadSafeSingleton:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._initialized = True
            self._data: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Thread-safe setter."""
        with self._lock:
            self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe getter."""
        with self._lock:
            return self._data.get(key, default)


def demo_singleton() -> None:
    """Verify that the singleton produces the same instance across threads."""
    print("[Thread-Safe Singleton Demo]")
    instances: list[int] = []
    lock = threading.Lock()

    def get_instance_id() -> None:
        inst = ThreadSafeSingleton()
        with lock:
            instances.append(id(inst))

    threads = [threading.Thread(target=get_instance_id) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    unique_ids = set(instances)
    print(f"  Threads created: {len(instances)}")
    print(f"  Unique instances: {len(unique_ids)}")
    print(f"  Singleton verified: {len(unique_ids) == 1}\n")


# =============================================================================
# Section 12: Thread Lifecycle and Information
# =============================================================================


def demo_thread_info() -> None:
    """Display information about threading state and active threads."""
    print("[Thread Information Demo]")
    print(f"  Main thread: {threading.main_thread().name}")
    print(f"  Current thread: {threading.current_thread().name}")
    print(f"  Active thread count: {threading.active_count()}")
    print(f"  All threads: {[t.name for t in threading.enumerate()]}")
    print(f"  Python threading module version info:")
    print(f"    GIL present: Yes (CPython limitation)")
    print(f"    Lock type: {type(threading.Lock()).__name__}")
    print(f"    RLock type: {type(threading.RLock()).__name__}")
    print()


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """Run all demonstrations of Python threading concepts."""
    print("=" * 70)
    print("  Day 63: Python Concurrency Programming (Part 1) - Threading")
    print("=" * 70)

    # 1. Sequential vs threaded downloading
    files = ["Python101.pdf", "MySQL_tutorial.avi", "Linux_guide.mp4"]
    sequential_downloader(files)
    threaded_downloader(files)

    # 2. Subclassed Thread
    demo_subclassed_threads()

    # 3. Thread pool
    demo_thread_pool()

    # 4. Lock / RLock - race condition
    demo_bank_account_race_condition()

    # 5. Lock vs RLock
    demo_lock_vs_rlock()

    # 6. Semaphore - connection pool
    demo_semaphore()

    # 7. Event - startup coordination
    demo_event()

    # 8. Condition - producer-consumer
    demo_producer_consumer()

    # 9. Daemon threads
    demo_daemon_threads()

    # 10. Enterprise scraper
    demo_enterprise_scraper()

    # 11. Singleton
    demo_singleton()

    # 12. Thread info
    demo_thread_info()

    print("=" * 70)
    print("  All demonstrations completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
