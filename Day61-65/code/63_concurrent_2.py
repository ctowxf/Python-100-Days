"""
Day 63 - Python Concurrency Part 2: Multiprocessing
=====================================================

This module demonstrates multiprocessing in Python, covering:
  - Process creation and lifecycle
  - Process pools (Pool) for task distribution
  - Inter-process communication via Queue
  - Shared memory with Value and Array
  - Manager objects for complex shared state
  - Enterprise-grade parallel data processing patterns

Key insight: Each process has its own GIL, so multiprocessing truly
leverages multiple CPU cores -- unlike multithreading in CPython.

=============================================================================
C++ Comparison Notes:
=============================================================================

  Python multiprocessing               | C++ equivalent
  --------------------------------------|------------------------------------------
  multiprocessing.Process               | fork() + exec() or std::thread (via clone)
  multiprocessing.Pool                  | Manual thread pool (or std::async futures)
  multiprocessing.Queue                 | Lock-free queues, pipes (pipe()/socketpair())
  multiprocessing.shared_memory         | POSIX shm_open / mmap, or Boost.Interprocess
  multiprocessing.Manager               | No direct equivalent; typically use shared
                                        |   memory + mutexes, or IPC mechanisms
  Process.start()/join()                | pthread_create()/pthread_join()
  os.fork()                             | fork() syscall (Linux/macOS only)

  In C++, threads share the same address space by default; explicit
  synchronization (mutex, atomic) is required. In Python multiprocessing,
  processes are isolated by default -- you must explicitly opt in to
  sharing via shared_memory, Manager, or Queue.

  Python Pool.map()  ≈  C++ with std::execution::parallel_policy
  Python ProcessPoolExecutor  ≈  C++ std::async + std::future
=============================================================================
"""

from __future__ import annotations

import hashlib
import multiprocessing
import os
import time
from dataclasses import dataclass
from multiprocessing import (
    Array,
    Manager,
    Process,
    Queue,
    Value,
    current_process,
)
from multiprocessing.pool import Pool
from multiprocessing.shared_memory import SharedMemory
from typing import Any

# ---------------------------------------------------------------------------
# Section 1: Basic Process Creation
# ---------------------------------------------------------------------------
# C++ comparison: In C++, creating a child process uses fork() which
# duplicates the entire address space. Python's Process class abstracts
# this -- on Linux it uses fork internally; on Windows it uses spawn
# (pickling the target function and re-importing in a new interpreter).


def sub_task(content: str, nums: list[int]) -> None:
    """Worker function executed in a child process.

    Each child process gets its own copy of ``nums`` because processes
    do not share memory. This is fundamentally different from threads,
    which would all reference the same list object.
    """
    proc = current_process()
    print(f"[PID {proc.pid}] Name: {proc.name}")
    # Each process pops independently -- all get 20 (the first element)
    counter: int = 0
    total: int = nums.pop(0)
    print(f"[PID {proc.pid}] Loop count: {total}")
    while counter < total:
        counter += 1
        print(f"[PID {proc.pid}] {counter}: {content}")
        time.sleep(0.01)


def demo_basic_process() -> None:
    """Launch three processes (two children + the main process)."""
    nums: list[int] = [20, 30, 40]
    p1 = Process(target=sub_task, args=("Ping", nums), name="PingProcess")
    p2 = Process(target=sub_task, args=("Pong", nums), name="PongProcess")
    p1.start()
    p2.start()
    # Main process also does work
    sub_task("Good", nums)
    p1.join()
    p2.join()
    print("All basic processes finished.\n")


# ---------------------------------------------------------------------------
# Section 2: Process Pool -- CPU-bound Task Distribution
# ---------------------------------------------------------------------------
# C++ comparison: In C++, a thread pool is typically built manually or
# using libraries like Intel TBB. Python's multiprocessing.Pool provides
# a ready-made process pool that distributes tasks across worker processes.
#
#   C++ thread pool (pseudocode):
#     std::vector<std::thread> pool;
#     for (int i = 0; i < N; ++i)
#         pool.emplace_back(worker, task_queue);
#
#   Python equivalent:
#     with Pool(processes=N) as pool:
#         results = pool.map(worker, tasks)
#
# For CPU-bound work, Python multiprocessing.Pool outperforms
# ThreadPoolExecutor because each worker has its own GIL.

# A list of large integers to test for primality -- deliberately CPU-bound.
PRIMES: list[int] = [
    1116281, 1297337, 104395303, 472882027, 533000389,
    817504243, 982451653, 112272535095293, 112582705942171,
    112272535095293, 115280095190773, 115797848077099, 1099726899285419,
] * 5  # Repeat 5 times to amplify the workload


def is_prime(n: int) -> bool:
    """Trial-division primality test (CPU-bound)."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def demo_pool_map() -> None:
    """Use Pool.map to distribute prime-checking across all cores."""
    cpu_count: int = os.cpu_count() or 1
    print(f"CPU cores available: {cpu_count}")
    print(f"Number of primes to check: {len(PRIMES)}")

    start: float = time.perf_counter()
    with Pool(processes=cpu_count) as pool:
        results: list[bool] = pool.map(is_prime, PRIMES)
    elapsed: float = time.perf_counter() - start

    prime_count = sum(1 for r in results if r)
    print(f"Found {prime_count} primes in {elapsed:.2f}s using "
          f"{cpu_count} worker processes.\n")


def demo_pool_starmap() -> None:
    """Use Pool.starmap for tasks that require multiple arguments."""

    def weighted_sum(values: list[float], weight: float) -> float:
        """Simulate a CPU-bound weighted aggregation."""
        total = 0.0
        for v in values:
            # Artificially heavy computation
            total += v * weight
            for _ in range(100):
                total += 0.00001
        return total

    data_chunks: list[tuple[list[float], float]] = [
        ([float(i) for i in range(1000)], 1.0),
        ([float(i) for i in range(1000, 2000)], 1.5),
        ([float(i) for i in range(2000, 3000)], 2.0),
        ([float(i) for i in range(3000, 4000)], 2.5),
    ]

    start: float = time.perf_counter()
    with Pool(processes=min(4, os.cpu_count() or 1)) as pool:
        results: list[float] = pool.starmap(weighted_sum, data_chunks)
    elapsed: float = time.perf_counter() - start

    for idx, (chunk, result) in enumerate(zip(data_chunks, results)):
        weight = chunk[1]
        print(f"  Chunk {idx} (weight={weight}): weighted_sum = {result:.4f}")
    print(f"  starmap completed in {elapsed:.4f}s\n")


# ---------------------------------------------------------------------------
# Section 3: Inter-Process Communication with Queue
# ---------------------------------------------------------------------------
# C++ comparison: In C++, IPC via queues typically uses POSIX message
# queues, pipes, or lock-free ring buffers (e.g., boost::lockfree::queue).
# Python's multiprocessing.Queue is built on pipes + locks and is
# process-safe out of the box.
#
#   C++ pipe-based IPC (pseudocode):
#     int fd[2]; pipe(fd);
#     if (fork() == 0) { write(fd[1], ...); }
#     else              { read(fd[0], ...);  }
#
#   Python equivalent:
#     q = Queue()
#     q.put(data)   # in child
#     q.get()       # in parent


def ping_pong_worker(content: str, queue: Queue[int]) -> None:
    """Worker that alternates printing until the counter reaches 50.

    Demonstrates how Queue enables coordination between processes that
    cannot share a simple variable.
    """
    counter: int = queue.get()
    while counter < 50:
        print(content, end="", flush=True)
        counter += 1
        queue.put(counter)
        time.sleep(0.01)
        counter = queue.get()


def demo_queue_pingpong() -> None:
    """Ping-Pong demonstration using multiprocessing.Queue."""
    queue: Queue[int] = Queue()
    queue.put(0)

    p1 = Process(target=ping_pong_worker, args=("Ping", queue))
    p2 = Process(target=ping_pong_worker, args=("Pong", queue))
    p1.start()
    p2.start()

    # Wait for either process to finish, then unblock the other
    while p1.is_alive() and p2.is_alive():
        time.sleep(0.01)
    # Put a sentinel value so the surviving process exits its loop
    queue.put(50)

    p1.join()
    p2.join()
    print("\nQueue-based Ping-Pong finished.\n")


# ---------------------------------------------------------------------------
# Section 4: Producer-Consumer Pattern with Queue
# ---------------------------------------------------------------------------

def producer(queue: Queue[tuple[str, float] | None], num_items: int) -> None:
    """Produces data items and sends them through the queue."""
    proc = current_process()
    for i in range(num_items):
        # Simulate data production (e.g., reading sensor data)
        item: tuple[str, float] = (
            f"item_{proc.pid}_{i}",
            hash(str(i)) % 1000.0,
        )
        queue.put(item)
        time.sleep(0.005)
    # Signal completion
    queue.put(None)


def consumer(
    queue: Queue[tuple[str, float] | None],
    result_queue: Queue[str],
    num_producers: int,
) -> None:
    """Consumes data items until all producers have finished."""
    finished: int = 0
    while finished < num_producers:
        item = queue.get()
        if item is None:
            finished += 1
            continue
        name, value = item
        # Simulate processing (e.g., transformation, storage)
        result_queue.put(f"{name} -> {value:.2f}")


def demo_producer_consumer() -> None:
    """Multi-producer, single-consumer pipeline via Queue."""
    data_queue: Queue[tuple[str, float] | None] = Queue()
    result_queue: Queue[str] = Queue()
    num_producers = 3
    items_per_producer = 5

    producers = [
        Process(target=producer, args=(data_queue, items_per_producer))
        for _ in range(num_producers)
    ]
    consumer_proc = Process(
        target=consumer, args=(data_queue, result_queue, num_producers)
    )

    consumer_proc.start()
    for p in producers:
        p.start()
    for p in producers:
        p.join()
    consumer_proc.join()

    # Collect results
    results: list[str] = []
    while not result_queue.empty():
        results.append(result_queue.get())

    print(f"Producer-Consumer: processed {len(results)} items")
    for r in results[:6]:  # Show first 6
        print(f"  {r}")
    if len(results) > 6:
        print(f"  ... and {len(results) - 6} more")
    print()


# ---------------------------------------------------------------------------
# Section 5: Shared Memory with Value and Array
# ---------------------------------------------------------------------------
# C++ comparison: In C++, shared memory between threads is the default
# (global/static variables). Between processes, you need explicit
# shared memory segments (shmget/shmat on POSIX, CreateFileMapping on
# Windows).
#
#   C++ shared memory (pseudocode):
#     int* shared = mmap(NULL, sizeof(int), PROT_READ|PROT_WRITE,
#                        MAP_SHARED|MAP_ANONYMOUS, -1, 0);
#     if (fork() == 0) { (*shared)++; }  // visible to parent
#
#   Python multiprocessing.shared_memory (3.8+):
#     shm = SharedMemory(name="myshm", create=True, size=64)
#     buf = shm.buf  # memoryview -- accessible from any process
#
# Python Value/Array use underlying OS shared memory + locks.


def increment_counter(
    value: Value,  # type: ignore[type-arg]
    lock: Any,
    iterations: int,
) -> None:
    """Safely increment a shared counter using explicit locking."""
    for _ in range(iterations):
        with lock:
            value.value += 1


def demo_shared_value() -> None:
    """Demonstrate shared Value between processes."""
    # 'i' = signed int; the lock is created automatically
    counter: Value = Value("i", 0)  # type: ignore[type-arg]
    lock = counter.get_lock()
    iterations = 10_000
    num_workers = 4

    workers = [
        Process(target=increment_counter, args=(counter, lock, iterations))
        for _ in range(num_workers)
    ]
    start = time.perf_counter()
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    elapsed = time.perf_counter() - start

    expected = num_workers * iterations
    print(f"Shared Value counter: {counter.value} "
          f"(expected {expected}) in {elapsed:.3f}s")


def process_array_chunk(
    arr: Array,  # type: ignore[type-arg]
    start_idx: int,
    end_idx: int,
    multiplier: float,
) -> None:
    """Apply a multiplier to a slice of a shared array."""
    for i in range(start_idx, end_idx):
        arr[i] = arr[i] * multiplier


def demo_shared_array() -> None:
    """Demonstrate shared Array for parallel numerical computation."""
    size = 20
    # 'd' = double-precision float
    shared_arr: Array = Array("d", [float(i) for i in range(size)])  # type: ignore[type-arg]

    mid = size // 2
    p1 = Process(target=process_array_chunk, args=(shared_arr, 0, mid, 2.0))
    p2 = Process(target=process_array_chunk, args=(shared_arr, mid, size, 3.0))
    p1.start(); p2.start()
    p1.join(); p2.join()

    result: list[float] = list(shared_arr)
    print(f"Shared Array (first 10): {result[:10]}")
    print(f"Shared Array (last 10):  {result[10:]}\n")


# ---------------------------------------------------------------------------
# Section 6: Shared Memory (3.8+ SharedMemory API)
# ---------------------------------------------------------------------------

def demo_shared_memory_api() -> None:
    """Use the modern multiprocessing.shared_memory module (Python 3.8+).

    This API allows sharing raw bytes between processes without
    pickling -- useful for high-performance numerical data exchange.
    """
    # Create a shared memory block
    shm = SharedMemory(name="demo_shared_block", create=True, size=256)
    try:
        # Write data as bytes
        message = b"Hello from shared memory!"
        shm.buf[: len(message)] = message
        print(f"SharedMemory written: {message.decode()}")

        def read_from_shm(shm_name: str, expected_size: int) -> None:
            """Child process reads from the same shared memory block."""
            existing = SharedMemory(name=shm_name, create=False)
            data = bytes(existing.buf[:expected_size])
            print(f"  [Child PID {os.getpid()}] Read: {data.decode()}")
            existing.close()

        child = Process(target=read_from_shm, args=(shm.name, len(message)))
        child.start()
        child.join()
    finally:
        shm.close()
        shm.unlink()  # Release the OS resource
    print()


# ---------------------------------------------------------------------------
# Section 7: Manager Objects for Complex Shared State
# ---------------------------------------------------------------------------
# C++ comparison: There is no direct C++ equivalent to Manager. In C++,
# you would typically use:
#   - Shared memory + mutex for simple types
#   - A database or message broker for complex shared state
#   - Boost.Interprocess for managed shared memory segments
#
# Python Manager is convenient but slower than Value/Array because
# every access goes through a proxy over a socket connection.


def manager_worker(
    shared_dict: Any,  # multiprocessing.managers.DictProxy
    shared_list: Any,  # multiprocessing.managers.ListProxy
    worker_id: int,
    num_tasks: int,
) -> None:
    """Worker that writes to shared dict and list via Manager."""
    for i in range(num_tasks):
        key = f"worker_{worker_id}_task_{i}"
        shared_dict[key] = worker_id * 1000 + i
        shared_list.append(key)
        time.sleep(0.002)


def demo_manager() -> None:
    """Demonstrate Manager for sharing complex Python objects."""
    with Manager() as manager:
        shared_dict: dict[str, int] = manager.dict()
        shared_list: list[str] = manager.list()

        num_workers = 4
        tasks_per_worker = 10
        workers = [
            Process(
                target=manager_worker,
                args=(shared_dict, shared_list, wid, tasks_per_worker),
            )
            for wid in range(num_workers)
        ]

        start = time.perf_counter()
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        elapsed = time.perf_counter() - start

        print(f"Manager shared_dict size: {len(shared_dict)} "
              f"(expected {num_workers * tasks_per_worker})")
        print(f"Manager shared_list size: {len(shared_list)} "
              f"(expected {num_workers * tasks_per_worker})")
        print(f"Manager elapsed: {elapsed:.3f}s")
        # Show a few entries
        for key in list(shared_dict.keys())[:4]:
            print(f"  {key} = {shared_dict[key]}")
        print()


# ---------------------------------------------------------------------------
# Section 8: Enterprise Example -- Parallel Data Processing Pipeline
# ---------------------------------------------------------------------------

@dataclass
class ProcessingResult:
    """Result of processing a single data chunk."""
    chunk_id: int
    record_count: int
    checksum: str
    elapsed_sec: float


def process_data_chunk(chunk_id: int, records: list[dict[str, Any]]) -> ProcessingResult:
    """Simulate enterprise-grade data transformation on a chunk.

    In a real system this might involve:
      - Parsing CSV/Parquet files
      - Applying business rules / validation
      - Encrypting or hashing sensitive fields
      - Loading into a staging database
    """
    start = time.perf_counter()
    # Simulate CPU-heavy transformation
    hasher = hashlib.sha256()
    for record in records:
        # "Transform" each record
        transformed = {
            "id": record["id"],
            "value": record["value"] * 1.1,  # e.g., apply tax
            "category": record["category"].upper(),
        }
        hasher.update(str(transformed).encode())
    elapsed = time.perf_counter() - start

    return ProcessingResult(
        chunk_id=chunk_id,
        record_count=len(records),
        checksum=hasher.hexdigest()[:16],
        elapsed_sec=round(elapsed, 4),
    )


def demo_enterprise_data_pipeline() -> None:
    """Parallel data processing pipeline -- enterprise pattern.

    Scenario: A data warehouse ETL job receives 100,000 records
    split into chunks. Each chunk is processed in parallel across
    all available CPU cores using a process pool.

    This pattern is common in:
      - ETL pipelines (Apache Airflow, dbt)
      - Batch inference in ML systems
      - Log processing and analytics
    """
    import random

    random.seed(42)
    total_records = 100_000
    chunk_size = 10_000
    categories = ["electronics", "clothing", "food", "books", "furniture"]

    # Generate synthetic dataset
    all_records: list[dict[str, Any]] = [
        {
            "id": i,
            "value": round(random.uniform(10, 1000), 2),
            "category": random.choice(categories),
        }
        for i in range(total_records)
    ]

    # Split into chunks
    chunks: list[list[dict[str, Any]]] = [
        all_records[i : i + chunk_size]
        for i in range(0, total_records, chunk_size)
    ]

    cpu_count = os.cpu_count() or 1
    print(f"Enterprise Pipeline: {total_records} records in "
          f"{len(chunks)} chunks, {cpu_count} workers")

    start = time.perf_counter()
    with Pool(processes=cpu_count) as pool:
        results: list[ProcessingResult] = pool.starmap(
            process_data_chunk,
            [(cid, chunk) for cid, chunk in enumerate(chunks)],
        )
    total_elapsed = time.perf_counter() - start

    for r in results:
        print(f"  Chunk {r.chunk_id}: {r.record_count} records, "
              f"checksum={r.checksum}, time={r.elapsed_sec}s")
    print(f"  Pipeline completed in {total_elapsed:.3f}s\n")


# ---------------------------------------------------------------------------
# Section 9: Enterprise Example -- Distributed CPU-bound Task
# ---------------------------------------------------------------------------

@dataclass
class SimulationResult:
    """Result from a Monte Carlo simulation worker."""
    worker_id: int
    iterations: int
    pi_estimate: float
    elapsed_sec: float


def monte_carlo_pi(worker_id: int, iterations: int) -> SimulationResult:
    """Estimate pi using Monte Carlo method -- purely CPU-bound.

    This is the kind of embarrassingly parallel workload where
    multiprocessing shines: each worker runs independently with
    no shared state, and results are aggregated afterward.
    """
    import random

    start = time.perf_counter()
    inside = 0
    rng = random.Random(worker_id)  # Deterministic per-worker seed
    for _ in range(iterations):
        x, y = rng.random(), rng.random()
        if x * x + y * y <= 1.0:
            inside += 1
    elapsed = time.perf_counter() - start
    pi_est = 4.0 * inside / iterations
    return SimulationResult(worker_id, iterations, pi_est, round(elapsed, 4))


def demo_monte_carlo() -> None:
    """Distribute Monte Carlo simulation across all cores.

    Enterprise use cases:
      - Financial risk modeling (VaR, Monte Carlo pricing)
      - Physics simulations
      - A/B test power analysis
    """
    cpu_count = os.cpu_count() or 1
    total_iterations = 5_000_000
    iterations_per_worker = total_iterations // cpu_count

    print(f"Monte Carlo Pi: {total_iterations} iterations across "
          f"{cpu_count} workers")

    start = time.perf_counter()
    with Pool(processes=cpu_count) as pool:
        results: list[SimulationResult] = pool.starmap(
            monte_carlo_pi,
            [(wid, iterations_per_worker) for wid in range(cpu_count)],
        )
    total_elapsed = time.perf_counter() - start

    # Aggregate results
    total_inside_approx = sum(r.pi_estimate * r.iterations / 4 for r in results)
    combined_pi = 4.0 * total_inside_approx / total_iterations

    for r in results:
        print(f"  Worker {r.worker_id}: pi ~ {r.pi_estimate:.6f} "
              f"({r.iterations} iter, {r.elapsed_sec}s)")
    print(f"  Combined estimate: pi ~ {combined_pi:.6f}")
    print(f"  Total wall time: {total_elapsed:.3f}s\n")


# ---------------------------------------------------------------------------
# Section 10: Best Practices Summary
# ---------------------------------------------------------------------------

def print_guidelines() -> None:
    """Print guidelines for choosing between threading and multiprocessing."""
    guidelines = """
    ============================================================
    Threading vs Multiprocessing -- Decision Guidelines
    ============================================================

    USE MULTITHREADING when:
      1. Many shared mutable states are needed (list, dict, set
         are thread-safe in CPython).
      2. The workload is I/O-bound (network, disk, database).
      3. Memory footprint must be minimal.

    USE MULTIPROCESSING when:
      1. The workload is CPU-bound (math, image processing,
         video encoding, data transformation).
      2. The problem is embarrassingly parallel (chunks can be
         processed independently).
      3. Memory is not a constraint and I/O is minimal.

    C++ NOTES:
      - C++ threads share memory by default; Python processes do not.
      - C++ thread pools (e.g., Intel TBB) are closer to Python's
        multiprocessing.Pool in spirit, but use threads, not processes.
      - For true cross-process shared memory in C++, use POSIX shm
        or Boost.Interprocess; Python provides SharedMemory (3.8+)
        and Manager as convenient alternatives.
    ============================================================
    """
    print(guidelines)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations in sequence."""
    print("=" * 60)
    print("  Day 63: Python Concurrency Part 2 -- Multiprocessing")
    print("=" * 60)
    print(f"  Main process PID: {os.getpid()}")
    print(f"  CPU cores: {os.cpu_count()}")
    print("=" * 60)
    print()

    demos: list[tuple[str, Any]] = [
        ("1. Basic Process Creation", demo_basic_process),
        ("2. Pool.map -- Prime Checking", demo_pool_map),
        ("3. Pool.starmap -- Weighted Sums", demo_pool_starmap),
        ("4. Queue -- Ping-Pong", demo_queue_pingpong),
        ("5. Queue -- Producer/Consumer", demo_producer_consumer),
        ("6. Shared Value", demo_shared_value),
        ("7. Shared Array", demo_shared_array),
        ("8. SharedMemory API", demo_shared_memory_api),
        ("9. Manager Objects", demo_manager),
        ("10. Enterprise Data Pipeline", demo_enterprise_data_pipeline),
        ("11. Enterprise Monte Carlo", demo_monte_carlo),
    ]

    for title, func in demos:
        print(f"--- {title} ---")
        func()

    print_guidelines()
    print("All demos completed.")


if __name__ == "__main__":
    main()
