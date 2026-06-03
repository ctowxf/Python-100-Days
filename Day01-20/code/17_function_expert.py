"""
Day 17 - Advanced Function Applications
=======================================
Topics: decorators, higher-order functions, map/filter/reduce,
         generators, iterators, functools, recursion, functional composition.

C++ Comparison Notes:
  - Python map/filter       vs  C++ std::transform / std::copy_if
  - Python generator         vs  C++ coroutine (C++20 co_yield)
  - Python functools.lru_cache  vs  C++ memoization pattern
  - Python decorator         vs  C++ compile-time wrappers / CRTP
"""

import time
import sys
import itertools
import functools
from functools import (
    wraps, lru_cache, reduce, partial, total_ordering,
    singledispatch, cache
)
from typing import (
    Callable, Iterator, Generator, Iterable, Any, TypeVar, List, Tuple
)

T = TypeVar("T")
R = TypeVar("R")


# ============================================================
# 1. DECORATORS - The Pythonic Way to Enhance Functions
# ============================================================
# Decorators are higher-order functions that wrap another function
# to add extra behavior without modifying the original code.
# C++ equivalent: no direct syntax; closest is CRTP or lambda wrappers.

def record_time(func: Callable) -> Callable:
    """Decorator that records and prints the execution time of a function.

    C++ comparison: In C++ you would need a RAII timer object or a
    template wrapper; Python's @decorator syntax is far more concise.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] executed in {elapsed:.6f}s")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 0.5):
    """Parameterized decorator: retries a function on failure.

    Demonstrates decorator factories - decorators that accept arguments.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    print(f"  [retry] attempt {attempt}/{max_attempts} "
                          f"failed: {exc}")
                    time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator


def validate_types(**expected_types):
    """Decorator that validates function argument types at runtime.

    Acts as a lightweight alternative to static type checkers.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for param_name, expected in expected_types.items():
                if param_name in bound.arguments:
                    val = bound.arguments[param_name]
                    if not isinstance(val, expected):
                        raise TypeError(
                            f"Parameter '{param_name}' must be {expected.__name__}, "
                            f"got {type(val).__name__}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# 2. HIGHER-ORDER FUNCTIONS
# ============================================================
# A higher-order function takes a function as argument or returns one.

def apply_operation(x: float, y: float, operation: Callable[[float, float], float]) -> float:
    """Apply a binary operation to two values."""
    return operation(x, y)


def compose(*functions: Callable) -> Callable:
    """Compose multiple single-argument functions right-to-left.

    compose(f, g, h)(x) == f(g(h(x)))

    C++ equivalent: you would chain calls manually or use pipeline
    operators; std::ranges in C++20 provides some composition.
    """
    def composed(arg):
        result = arg
        for fn in reversed(functions):
            result = fn(result)
        return result
    return composed


def pipeline(*functions: Callable) -> Callable:
    """Compose functions left-to-right (data flows naturally).

    pipeline(f, g, h)(x) == h(g(f(x)))
    More intuitive for data processing chains.
    """
    def piped(arg):
        result = arg
        for fn in functions:
            result = fn(result)
        return result
    return piped


# ============================================================
# 3. MAP / FILTER / REDUCE
# ============================================================
# Python's built-in map() and filter() are lazy iterators.
# C++ comparison:
#   map()      -> std::transform (applies function, writes to output)
#   filter()   -> std::copy_if   (copies elements matching predicate)
#   reduce()   -> std::accumulate (in <numeric>)

def demonstrate_map_filter_reduce():
    """Showcase map, filter, and reduce with practical examples."""
    print("\n" + "=" * 60)
    print("MAP / FILTER / REDUCE")
    print("=" * 60)

    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # --- map: apply a function to every element ---
    # C++ equivalent:
    #   std::transform(data.begin(), data.end(), out.begin(),
    #                  [](int x) { return x * x; });
    squares = list(map(lambda x: x ** 2, data))
    print(f"\nmap(x**2):       {squares}")

    # --- filter: keep elements matching a predicate ---
    # C++ equivalent:
    #   std::copy_if(data.begin(), data.end(), out.begin(),
    #                [](int x) { return x % 2 == 0; });
    evens = list(filter(lambda x: x % 2 == 0, data))
    print(f"filter(even):    {evens}")

    # --- reduce: accumulate elements into a single value ---
    # C++ equivalent:
    #   std::accumulate(data.begin(), data.end(), 0, std::plus<int>());
    total = reduce(lambda acc, x: acc + x, data, 0)
    print(f"reduce(sum):     {total}")

    # --- Chaining map + filter + reduce ---
    # Sum of squares of even numbers
    result = reduce(
        lambda acc, x: acc + x,
        map(lambda x: x ** 2,
            filter(lambda x: x % 2 == 0, data)),
        0
    )
    print(f"sum(sq of even): {result}")

    # --- Practical: normalize strings ---
    raw_names = ["  Alice  ", "BOB", "  charlie "]
    cleaned = list(map(
        lambda s: s.strip().title(), raw_names
    ))
    print(f"cleaned names:   {cleaned}")


# ============================================================
# 4. ITERATORS AND ITERABLES
# ============================================================
# An iterator implements __iter__() and __next__().
# An iterable returns an iterator from __iter__().

class Countdown:
    """A custom iterator that counts down from n to 1.

    C++ comparison: C++ iterators follow a different model (begin/end
    pairs with operator++ and operator*). Python unifies this into
    the __iter__/__next__ protocol.
    """

    def __init__(self, start: int):
        self._current = start

    def __iter__(self) -> "Countdown":
        return self

    def __next__(self) -> int:
        if self._current <= 0:
            raise StopIteration
        value = self._current
        self._current -= 1
        return value


class FibonacciIterator:
    """Iterator that yields Fibonacci numbers indefinitely.

    Call next() to get the next Fibonacci number.
    """

    def __init__(self):
        self._a, self._b = 0, 1

    def __iter__(self) -> "FibonacciIterator":
        return self

    def __next__(self) -> int:
        value = self._a
        self._a, self._b = self._b, self._a + self._b
        return value


# ============================================================
# 5. GENERATORS
# ============================================================
# Generators are a concise way to create iterators using yield.
# They produce values lazily, saving memory for large sequences.
#
# C++ comparison (C++20):
#   Python generator          ->  C++20 coroutine with co_yield
#   Python generator.send()   ->  C++ coroutine promise_type::yield_value
#   Python yield from         ->  C++ co_await or recursive co_yield
#   Python itertools          ->  C++ std::views (C++20 ranges)

def fibonacci_generator() -> Generator[int, None, None]:
    """Generate Fibonacci numbers lazily (infinite generator).

    C++20 equivalent:
        cppcoro::generator<long long> fibonacci() {
            long long a = 0, b = 1;
            while (true) {
                co_yield a;
                auto tmp = a;
                a = b;
                b = tmp + b;
            }
        }
    """
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def countdown_generator(start: int) -> Generator[int, None, None]:
    """Simple countdown generator."""
    current = start
    while current > 0:
        yield current
        current -= 1


def sliding_window(iterable: Iterable, size: int) -> Generator[tuple, None, None]:
    """Yield sliding windows of a given size from an iterable.

    Example: sliding_window([1,2,3,4], 2) -> (1,2), (2,3), (3,4)
    """
    it = iter(iterable)
    window = []
    for _ in range(size):
        window.append(next(it))
    yield tuple(window)
    for item in it:
        window = window[1:] + [item]
        yield tuple(window)


def chunked(iterable: Iterable, size: int) -> Generator[list, None, None]:
    """Yield successive chunks of a given size from an iterable."""
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk


def generator_send_demo():
    """Demonstrate generator .send() for two-way communication.

    Generators can receive values via .send(), enabling coroutine-style
    patterns. This is similar to how C++20 co_yield can both produce
    and receive values.
    """
    print("\n" + "-" * 40)
    print("Generator .send() Demo (Coroutines)")
    print("-" * 40)

    def accumulator():
        """A generator that accumulates sent values."""
        total = 0
        while True:
            value = yield total
            if value is None:
                break
            total += value

    gen = accumulator()
    next(gen)  # Prime the generator
    print(f"  After send(10): {gen.send(10)}")
    print(f"  After send(20): {gen.send(20)}")
    print(f"  After send(30): {gen.send(30)}")


# ============================================================
# 6. FUNCTOOLS DEEP DIVE
# ============================================================

def demonstrate_functools():
    """Showcase functools module utilities."""
    print("\n" + "=" * 60)
    print("FUNCTOOLS MODULE")
    print("=" * 60)

    # --- lru_cache: memoization decorator ---
    # C++ equivalent: manual std::unordered_map cache or external lib
    @lru_cache(maxsize=256)
    def fibonacci_cached(n: int) -> int:
        if n < 2:
            return n
        return fibonacci_cached(n - 1) + fibonacci_cached(n - 2)

    start = time.perf_counter()
    fib_100 = fibonacci_cached(100)
    elapsed = time.perf_counter() - start
    print(f"\n  fib(100) via lru_cache = {fib_100}")
    print(f"  Computed in {elapsed:.6f}s")
    print(f"  Cache info: {fibonacci_cached.cache_info()}")

    # --- partial: fix some arguments of a function ---
    # C++ equivalent: std::bind or lambda capture
    def power(base: float, exponent: float) -> float:
        return base ** exponent

    square_fn = partial(power, exponent=2)
    cube_fn = partial(power, exponent=3)
    print(f"\n  square(5) = {square_fn(5)}")
    print(f"  cube(5)   = {cube_fn(3)}")

    # --- reduce: fold a sequence ---
    product = reduce(lambda a, b: a * b, range(1, 11))
    print(f"\n  10! = {product}")

    # --- singledispatch: type-based function overloading ---
    @singledispatch
    def format_value(val):
        return str(val)

    @format_value.register(int)
    def _(val):
        return f"int({val})"

    @format_value.register(float)
    def _(val):
        return f"float({val:.2f})"

    @format_value.register(list)
    def _(val):
        return f"list[{len(val)} items]"

    print(f"\n  format_value(42)      -> {format_value(42)}")
    print(f"  format_value(3.14159) -> {format_value(3.14159)}")
    print(f"  format_value([1,2,3]) -> {format_value([1, 2, 3])}")

    # --- total_ordering: auto-generate comparison methods ---
    @total_ordering
    class Temperature:
        """Temperature with auto-generated comparison operators."""
        def __init__(self, celsius: float):
            self.celsius = celsius

        def __eq__(self, other):
            if not isinstance(other, Temperature):
                return NotImplemented
            return self.celsius == other.celsius

        def __lt__(self, other):
            if not isinstance(other, Temperature):
                return NotImplemented
            return self.celsius < other.celsius

        def __repr__(self):
            return f"Temperature({self.celsius}C)"

    temps = [Temperature(100), Temperature(0), Temperature(37), Temperature(-40)]
    print(f"\n  Sorted temperatures: {sorted(temps)}")


# ============================================================
# 7. RECURSION AND MEMOIZATION
# ============================================================

def demonstrate_recursion():
    """Show recursion with and without memoization."""
    print("\n" + "=" * 60)
    print("RECURSION & MEMOIZATION")
    print("=" * 60)

    # Naive recursive Fibonacci - O(2^n) time complexity
    def fib_naive(n: int) -> int:
        if n < 2:
            return n
        return fib_naive(n - 1) + fib_naive(n - 2)

    # Memoized version - O(n) time complexity
    @lru_cache(maxsize=None)
    def fib_memo(n: int) -> int:
        if n < 2:
            return n
        return fib_memo(n - 1) + fib_memo(n - 2)

    # Iterative version - O(n) time, O(1) space
    def fib_iterative(n: int) -> int:
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    # Compare performance
    n = 35
    print(f"\n  Computing fib({n}):\n")

    start = time.perf_counter()
    result_naive = fib_naive(n)
    t_naive = time.perf_counter() - start
    print(f"  Naive recursive: {result_naive:>12}  ({t_naive:.4f}s)")

    start = time.perf_counter()
    result_memo = fib_memo(n)
    t_memo = time.perf_counter() - start
    print(f"  Memoized (lru):  {result_memo:>12}  ({t_memo:.6f}s)")

    start = time.perf_counter()
    result_iter = fib_iterative(n)
    t_iter = time.perf_counter() - start
    print(f"  Iterative:       {result_iter:>12}  ({t_iter:.6f}s)")

    # Tower of Hanoi - classic recursion problem
    print("\n  Tower of Hanoi (3 disks):")
    moves = []

    def hanoi(n, source, target, auxiliary):
        if n == 1:
            moves.append(f"    Move disk 1: {source} -> {target}")
            return
        hanoi(n - 1, source, auxiliary, target)
        moves.append(f"    Move disk {n}: {source} -> {target}")
        hanoi(n - 1, auxiliary, target, source)

    hanoi(3, "A", "C", "B")
    for move in moves:
        print(move)
    print(f"  Total moves: {len(moves)}")


# ============================================================
# 8. ENTERPRISE: DATA PIPELINE WITH GENERATORS
# ============================================================
# Real-world data processing often uses generator pipelines for
# memory-efficient, lazy evaluation of large datasets.

def enterprise_data_pipeline():
    """Demonstrate a generator-based data processing pipeline.

    This pattern is common in ETL systems, log processing, and
    streaming data applications. Each stage is a generator that
    yields transformed data to the next stage, enabling lazy
    evaluation and constant memory usage regardless of input size.

    C++ comparison:
      - C++20 ranges/views provide similar lazy pipeline semantics:
            auto result = data | std::views::filter(pred)
                               | std::views::transform(fn)
                               | std::views::take(10);
      - Before C++20, you would need Boost.Range or manual loops.
    """
    print("\n" + "=" * 60)
    print("ENTERPRISE: GENERATOR DATA PIPELINE")
    print("=" * 60)

    # Simulated raw data source (could be a file, database, API)
    def read_raw_data():
        """Stage 1: Read raw data (simulated)."""
        records = [
            {"id": 1,  "name": "alice",   "dept": "engineering", "salary": 120000, "active": True},
            {"id": 2,  "name": "bob",     "dept": "marketing",   "salary": 85000,  "active": True},
            {"id": 3,  "name": "charlie", "dept": "engineering", "salary": 135000, "active": False},
            {"id": 4,  "name": "diana",   "dept": "engineering", "salary": 110000, "active": True},
            {"id": 5,  "name": "eve",     "dept": "sales",       "salary": 75000,  "active": True},
            {"id": 6,  "name": "frank",   "dept": "marketing",   "salary": 92000,  "active": False},
            {"id": 7,  "name": "grace",   "dept": "engineering", "salary": 145000, "active": True},
            {"id": 8,  "name": "henry",   "dept": "sales",       "salary": 68000,  "active": True},
        ]
        for record in records:
            yield record

    def filter_active(records):
        """Stage 2: Filter only active employees."""
        for r in records:
            if r["active"]:
                yield r

    def filter_department(records, dept: str):
        """Stage 3: Filter by department."""
        for r in records:
            if r["dept"] == dept:
                yield r

    def normalize_names(records):
        """Stage 4: Normalize name fields."""
        for r in records:
            r["name"] = r["name"].strip().title()
            yield r

    def add_bonus(records, bonus_pct: float = 0.10):
        """Stage 5: Calculate annual bonus."""
        for r in records:
            r["bonus"] = r["salary"] * bonus_pct
            r["total_comp"] = r["salary"] + r["bonus"]
            yield r

    def select_fields(records, fields: list):
        """Stage 6: Project only selected fields."""
        for r in records:
            yield {k: r[k] for k in fields if k in r}

    # --- Build and execute the pipeline ---
    print("\n  Pipeline: source -> filter_active -> engineering -> "
          "normalize -> bonus -> select_fields\n")

    # Lazy pipeline construction - nothing executes until consumed
    pipeline_stages = read_raw_data()
    pipeline_stages = filter_active(pipeline_stages)
    pipeline_stages = filter_department(pipeline_stages, "engineering")
    pipeline_stages = normalize_names(pipeline_stages)
    pipeline_stages = add_bonus(pipeline_stages, bonus_pct=0.12)
    pipeline_stages = select_fields(pipeline_stages, ["name", "salary", "bonus", "total_comp"])

    # Consume the pipeline
    for record in pipeline_stages:
        print(f"    {record}")

    # --- Pipeline as a reusable function ---
    print("\n  Reusable pipeline function:")

    def build_pipeline(dept: str, bonus_pct: float = 0.10):
        stages = read_raw_data()
        stages = filter_active(stages)
        stages = filter_department(stages, dept)
        stages = normalize_names(stages)
        stages = add_bonus(stages, bonus_pct)
        return select_fields(stages, ["name", "salary", "total_comp"])

    for record in build_pipeline("sales"):
        print(f"    {record}")


# ============================================================
# 9. ENTERPRISE: LAZY EVALUATION PATTERNS
# ============================================================

def demonstrate_lazy_evaluation():
    """Show lazy evaluation with generators for memory efficiency.

    Lazy evaluation defers computation until the result is needed.
    This is critical when processing datasets that don't fit in memory.
    """
    print("\n" + "=" * 60)
    print("LAZY EVALUATION PATTERNS")
    print("=" * 60)

    # --- Lazy range (simulates Python's built-in range) ---
    def lazy_range(start, stop, step=1):
        current = start
        while current < stop:
            yield current
            current += step

    # --- Infinite sequence generators ---
    def naturals(start=1):
        """Yield natural numbers starting from start."""
        n = start
        while True:
            yield n
            n += 1

    def primes():
        """Yield prime numbers using a lazy sieve."""
        yield 2
        composites = {}
        n = 3
        while True:
            if n not in composites:
                yield n
                composites[n * n] = [n]
            else:
                for p in composites[n]:
                    composites.setdefault(n + 2 * p, []).append(p)
                del composites[n]
            n += 2

    # --- Demonstrate lazy access ---
    print("\n  First 15 primes (lazy):")
    first_15 = list(itertools.islice(primes(), 15))
    print(f"    {first_15}")

    print("\n  Sum of first 1000 primes:")
    total = sum(itertools.islice(primes(), 1000))
    print(f"    {total}")

    # --- Lazy file processing (pattern) ---
    def lazy_read_lines(filepath: str) -> Generator[str, None, None]:
        """Read a file line by line without loading entire file into memory.

        For large log files (GB+), this pattern is essential.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    yield line.rstrip("\n")
        except FileNotFoundError:
            yield from []  # Gracefully handle missing file

    print("\n  Lazy file reader generator created (pattern demo)")
    print("    Processes one line at a time - constant memory usage")


# ============================================================
# 10. FUNCTIONAL COMPOSITION IN PRACTICE
# ============================================================

def demonstrate_functional_composition():
    """Show functional composition patterns used in enterprise code."""
    print("\n" + "=" * 60)
    print("FUNCTIONAL COMPOSITION")
    print("=" * 60)

    # --- Compose small reusable functions ---
    strip = lambda s: s.strip()
    lower = lambda s: s.lower()
    split = lambda s: s.split()
    join_dash = lambda words: "-".join(words)
    slugify = compose(join_dash, split, lower, strip)

    raw_title = "  Hello World from Python  "
    print(f"\n  slugify('{raw_title}') = '{slugify(raw_title)}'")

    # --- Validation pipeline ---
    def is_non_empty(s: str) -> bool:
        return len(s) > 0

    def is_short_enough(s: str, max_len: int = 50) -> bool:
        return len(s) <= max_len

    def has_no_special_chars(s: str) -> bool:
        return all(c.isalnum() or c.isspace() for c in s)

    def validate_username(username: str) -> Tuple[bool, List[str]]:
        """Validate username through a chain of checks."""
        errors = []
        if not is_non_empty(username):
            errors.append("Username cannot be empty")
        if not is_short_enough(username, 20):
            errors.append("Username must be 20 characters or fewer")
        if not has_no_special_chars(username):
            errors.append("Username must not contain special characters")
        return (len(errors) == 0, errors)

    test_names = ["alice123", "", "a" * 25, "bob@home", "charlie"]
    print("\n  Username validation:")
    for name in test_names:
        valid, errs = validate_username(name)
        status = "PASS" if valid else f"FAIL: {', '.join(errs)}"
        print(f"    '{name}' -> {status}")

    # --- Transform pipeline with map + filter ---
    raw_data = [
        "  order-001: shipped ",
        "order-002: pending",
        "  order-003: cancelled",
        "order-004: shipped  ",
        "order-005: pending",
    ]

    # Extract and clean shipped order IDs
    shipped_ids = list(
        map(lambda x: x.split(":")[0].strip(),
            filter(lambda x: "shipped" in x,
                   map(lambda s: s.strip(), raw_data)))
    )
    print(f"\n  Shipped order IDs: {shipped_ids}")


# ============================================================
# 11. C++ COMPARISON SUMMARY
# ============================================================

def print_cpp_comparison():
    """Print a summary of Python vs C++ function features."""
    print("\n" + "=" * 60)
    print("C++ COMPARISON SUMMARY")
    print("=" * 60)

    comparisons = [
        ("Python map()",           "C++ std::transform()"),
        ("Python filter()",        "C++ std::copy_if()"),
        ("Python reduce()",        "C++ std::accumulate()"),
        ("Python generator/yield", "C++20 coroutine/co_yield"),
        ("Python functools.cache", "C++ manual memoization (std::unordered_map)"),
        ("Python decorator @",     "C++ template wrapper / CRTP / aspects"),
        ("Python partial()",       "C++ std::bind / lambda capture"),
        ("Python itertools",       "C++20 std::views / ranges"),
        ("Python generator pipeline", "C++20 range pipeline (| operator)"),
        ("Python singledispatch",  "C++ function overloading (compile-time)"),
    ]

    print()
    for py, cpp in comparisons:
        print(f"  {py:<30s} <->  {cpp}")
    print()
    print("  Key difference: Python favors runtime dynamism and duck typing;")
    print("  C++ favors compile-time resolution and zero-cost abstractions.")
    print("  C++20 coroutines bring C++ closer to Python's generator model,")
    print("  but with explicit promise types and suspend points.")


# ============================================================
# 12. BONUS: DESIGN PATTERNS WITH FUNCTIONS
# ============================================================

def demonstrate_strategy_pattern():
    """Strategy pattern implemented with first-class functions.

    Instead of creating Strategy classes, we pass functions directly.
    """
    print("\n" + "=" * 60)
    print("STRATEGY PATTERN (FUNCTION-BASED)")
    print("=" * 60)

    # Sorting strategies
    def sort_by_name(items):
        return sorted(items, key=lambda x: x["name"])

    def sort_by_salary_desc(items):
        return sorted(items, key=lambda x: x["salary"], reverse=True)

    def sort_by_salary_asc(items):
        return sorted(items, key=lambda x: x["salary"])

    employees = [
        {"name": "Diana",  "salary": 110000},
        {"name": "Alice",  "salary": 120000},
        {"name": "Charlie","salary": 95000},
        {"name": "Bob",    "salary": 135000},
    ]

    strategies = {
        "name":       sort_by_name,
        "salary_desc": sort_by_salary_desc,
        "salary_asc": sort_by_salary_asc,
    }

    for strategy_name, strategy_fn in strategies.items():
        result = strategy_fn(employees)
        names = [e["name"] for e in result]
        print(f"  {strategy_name:<15s}: {names}")


def demonstrate_observer_pattern():
    """Simple event system using function callbacks."""
    print("\n" + "=" * 60)
    print("OBSERVER PATTERN (FUNCTION CALLBACKS)")
    print("=" * 60)

    class EventEmitter:
        def __init__(self):
            self._listeners = {}

        def on(self, event: str, callback: Callable):
            self._listeners.setdefault(event, []).append(callback)

        def emit(self, event: str, *args, **kwargs):
            for callback in self._listeners.get(event, []):
                callback(*args, **kwargs)

    emitter = EventEmitter()

    # Register listeners
    emitter.on("order_created", lambda order_id: print(f"    [email]    Sent confirmation for order {order_id}"))
    emitter.on("order_created", lambda order_id: print(f"    [inventory] Reserved stock for order {order_id}"))
    emitter.on("order_created", lambda order_id: print(f"    [analytics] Logged order {order_id}"))

    print("\n  Emitting 'order_created' event:")
    emitter.emit("order_created", "ORD-2024-0042")


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    print("Day 17: Advanced Function Applications")
    print("=" * 60)

    # 1. Decorators
    print("\n" + "=" * 60)
    print("DECORATORS")
    print("=" * 60)

    @record_time
    def demo_task(n):
        """Simulate a task that takes some time."""
        total = sum(i * i for i in range(n))
        return total

    result = demo_task(1_000_000)
    print(f"  Result: {result}")

    # Retry decorator demo
    state = {"call_count": 0}

    @retry(max_attempts=3, delay=0.01)
    def flaky_function():
        state["call_count"] += 1
        if state["call_count"] < 3:
            raise ConnectionError("Server unavailable")
        return "Success!"

    print(f"\n  Retry demo result: {flaky_function()}")

    # Type validation decorator
    @validate_types(x=int, y=int)
    def add(x, y):
        return x + y

    print(f"\n  add(3, 5) = {add(3, 5)}")
    try:
        add(3, "5")
    except TypeError as e:
        print(f"  add(3, '5') -> TypeError: {e}")

    # 2. Higher-order functions
    print("\n" + "=" * 60)
    print("HIGHER-ORDER FUNCTIONS")
    print("=" * 60)

    print(f"\n  apply_operation(10, 3, lambda a,b: a+b) = {apply_operation(10, 3, lambda a, b: a + b)}")
    print(f"  apply_operation(10, 3, lambda a,b: a*b) = {apply_operation(10, 3, lambda a, b: a * b)}")

    # Composition
    add_one = lambda x: x + 1
    double = lambda x: x * 2
    square = lambda x: x ** 2

    transform = compose(square, double, add_one)
    print(f"  compose(sq, dbl, add1)(5) = sq(dbl(add1(5))) = sq(dbl(6)) = sq(12) = {transform(5)}")

    transform_pipe = pipeline(add_one, double, square)
    print(f"  pipeline(add1, dbl, sq)(5) = sq(dbl(add1(5))) = {transform_pipe(5)}")

    # 3. Map / Filter / Reduce
    demonstrate_map_filter_reduce()

    # 4. Iterators
    print("\n" + "=" * 60)
    print("ITERATORS")
    print("=" * 60)

    print("\n  Countdown from 5:")
    for num in Countdown(5):
        print(f"    {num}", end=" ")
    print()

    print("\n  First 10 Fibonacci numbers (iterator class):")
    fib_iter = FibonacciIterator()
    fibs = [next(fib_iter) for _ in range(10)]
    print(f"    {fibs}")

    # 5. Generators
    print("\n" + "=" * 60)
    print("GENERATORS")
    print("=" * 60)

    print("\n  First 12 Fibonacci numbers (generator):")
    fib_gen = fibonacci_generator()
    fibs = [next(fib_gen) for _ in range(12)]
    print(f"    {fibs}")

    print("\n  Sliding window of size 3 over [1..8]:")
    for window in sliding_window(range(1, 9), 3):
        print(f"    {window}")

    print("\n  Chunked([1..10], size=3):")
    for chunk in chunked(range(1, 11), 3):
        print(f"    {chunk}")

    generator_send_demo()

    # 6. functools
    demonstrate_functools()

    # 7. Recursion
    demonstrate_recursion()

    # 8. Enterprise data pipeline
    enterprise_data_pipeline()

    # 9. Lazy evaluation
    demonstrate_lazy_evaluation()

    # 10. Functional composition
    demonstrate_functional_composition()

    # 11. C++ comparison
    print_cpp_comparison()

    # 12. Design patterns
    demonstrate_strategy_pattern()
    demonstrate_observer_pattern()

    print("\n" + "=" * 60)
    print("Day 17 Complete!")
    print("=" * 60)
