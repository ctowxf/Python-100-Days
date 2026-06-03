"""
Day 14 - Functions and Modules
==============================
Covers: function def, *args/**kwargs, module imports, type hints.

C++ Comparison Note:
    Python *args/**kwargs vs C++ Variadic Templates
    ------------------------------------------------
    C++ uses variadic templates (parameter packs) to accept any number of
    arguments at compile time:
        template<typename... Args>
        void foo(Args... args) { /* sizeof...(args) gives count */ }
    Python achieves the same at runtime with *args (tuple) and **kwargs (dict).
    The key difference: C++ resolves types and generates specialized code at
    compile time, while Python simply collects arguments into a tuple/dict
    dynamically.

Enterprise Utility Functions:
    This module also demonstrates production-grade utility functions commonly
    found in enterprise codebases - data validation, formatting helpers,
    and aggregation utilities - all using proper type hints.

Author: Auto-generated from Day 14 curriculum
Version: 1.0
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Union


# ---------------------------------------------------------------------------
# 1. Basic function definition with type hints
# ---------------------------------------------------------------------------

def factorial(n: int) -> int:
    """Return n! using math.factorial (reuse over reinvention)."""
    if n < 0:
        raise ValueError("Factorial is undefined for negative numbers")
    return math.factorial(n)


def combinations(m: int, n: int) -> int:
    """Calculate C(m, n) = m! / (n! * (m-n)!)."""
    if m < 0 or n < 0 or n > m:
        raise ValueError(f"Invalid arguments: m={m}, n={n}")
    return factorial(m) // (factorial(n) * factorial(m - n))


# ---------------------------------------------------------------------------
# 2. Positional, keyword, and default parameters
# ---------------------------------------------------------------------------

def is_triangle(a: float, b: float, c: float) -> bool:
    """Check whether three sides can form a valid triangle."""
    return a + b > c and b + c > a and a + c > b


def greet(name: str, greeting: str = "Hello") -> str:
    """Return a greeting string. Demonstrates default parameter."""
    return f"{greeting}, {name}!"


# ---------------------------------------------------------------------------
# 3. *args - variable positional arguments (tuple)
# ---------------------------------------------------------------------------

def sum_numbers(*args: Union[int, float]) -> Union[int, float]:
    """Sum any number of numeric arguments.

    C++ analogy:
        template<typename... Args>
        auto sum(Args... args) { return (args + ...); }  // C++17 fold
    In Python, *args collects positional args into a tuple at runtime.
    """
    return sum(val for val in args if isinstance(val, (int, float)))


def describe_items(*items: str) -> str:
    """Accept any number of string items and describe them."""
    if not items:
        return "No items provided."
    count = len(items)
    listing = ", ".join(items)
    return f"Received {count} item(s): {listing}"


# ---------------------------------------------------------------------------
# 4. **kwargs - variable keyword arguments (dict)
# ---------------------------------------------------------------------------

def build_profile(**kwargs: Any) -> dict[str, Any]:
    """Build a profile dictionary from keyword arguments.

    **kwargs collects all keyword arguments into a dict at runtime.
    Useful for constructing configuration objects or records dynamically.
    """
    return dict(kwargs)


def format_report(title: str, *data: float, **options: Any) -> str:
    """Combine *args and **kwargs in one signature.

    Args:
        title:   Report title.
        *data:   Variable number of numeric data points.
        **options: Optional settings like 'precision', 'prefix'.
    """
    precision: int = options.get("precision", 2)
    prefix: str = options.get("prefix", "")

    if not data:
        return f"{prefix}{title}: No data available."

    avg = statistics.mean(data)
    lo = min(data)
    hi = max(data)

    lines = [
        f"{prefix}{title}",
        f"  Count  : {len(data)}",
        f"  Min    : {lo:.{precision}f}",
        f"  Max    : {hi:.{precision}f}",
        f"  Mean   : {avg:.{precision}f}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. Enterprise utility functions (production-style helpers)
# ---------------------------------------------------------------------------

def validate_email(email: str) -> bool:
    """Basic email format validation (enterprise utility)."""
    import re
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def sanitize_string(value: str, *, max_length: int = 256, strip: bool = True) -> str:
    """Sanitize user input (enterprise utility).

    Uses a named keyword-only argument (after *) to enforce clarity
    at call sites: sanitize_string(text, max_length=100).
    """
    result = value.strip() if strip else value
    return result[:max_length]


def flatten_records(*records: dict[str, Any], key: str = "id") -> list[Any]:
    """Extract values for a given key from multiple record dicts.

    Demonstrates *args with dict items - a common enterprise pattern
    for batch-processing database rows or API responses.
    """
    return [record.get(key) for record in records if key in record]


def weighted_score(scores: dict[str, float], weights: dict[str, float]) -> float:
    """Calculate weighted average score (enterprise utility).

    Useful for performance reviews, grading systems, risk scoring, etc.
    """
    total_weight = 0.0
    weighted_sum = 0.0
    for category, score in scores.items():
        w = weights.get(category, 0.0)
        weighted_sum += score * w
        total_weight += w
    if total_weight == 0:
        return 0.0
    return weighted_sum / total_weight


# ---------------------------------------------------------------------------
# 6. Module demonstration helpers
# ---------------------------------------------------------------------------

def demo_args_kwargs() -> None:
    """Show *args and **kwargs in action."""
    print("=" * 60)
    print("DEMO: *args and **kwargs")
    print("=" * 60)

    # *args: variable positional arguments
    print(f"\nsum_numbers()          -> {sum_numbers()}")
    print(f"sum_numbers(1,2,3)     -> {sum_numbers(1, 2, 3)}")
    print(f"sum_numbers(1,2,3.45)  -> {sum_numbers(1, 2, 3.45)}")

    # describe_items with *args
    print(f"\ndescribe_items()       -> {describe_items()}")
    print(f"describe_items('a','b')-> {describe_items('a', 'b')}")

    # **kwargs: variable keyword arguments
    profile = build_profile(name="Alice", role="Engineer", level=5)
    print(f"\nbuild_profile(name='Alice', role='Engineer', level=5)")
    print(f"  -> {profile}")

    # format_report combines *args and **kwargs
    print()
    print(format_report("Sales Q1", 120.5, 98.3, 145.0, 112.7,
                         precision=1, prefix="[REPORT] "))


def demo_basic_functions() -> None:
    """Demonstrate basic function definitions."""
    print("=" * 60)
    print("DEMO: Basic Function Definitions")
    print("=" * 60)

    # Factorial and combinations (from the lesson)
    print(f"\nC(7, 3) = {combinations(7, 3)}")  # 35
    print(f"C(10, 4) = {combinations(10, 4)}")  # 210

    # Triangle check
    print(f"\nis_triangle(3, 4, 5)  -> {is_triangle(3, 4, 5)}")
    print(f"is_triangle(1, 2, 10) -> {is_triangle(1, 2, 10)}")

    # Default parameter
    print(f"\ngreet('World')            -> {greet('World')}")
    print(f"greet('World', 'Hi')      -> {greet('World', 'Hi')}")


def demo_enterprise_utils() -> None:
    """Demonstrate enterprise utility functions."""
    print("=" * 60)
    print("DEMO: Enterprise Utility Functions")
    print("=" * 60)

    # Email validation
    emails = ["user@example.com", "bad@@email", "test@host.co"]
    for em in emails:
        print(f"  validate_email('{em}') -> {validate_email(em)}")

    # String sanitization
    raw = "  <script>alert('xss')</script>  "
    print(f"\n  sanitize_string('{raw}', max_length=20)")
    print(f"    -> '{sanitize_string(raw, max_length=20)}'")

    # Flatten records
    rows = (
        {"id": 101, "name": "Alice"},
        {"id": 102, "name": "Bob"},
        {"id": 103, "name": "Charlie"},
    )
    ids = flatten_records(*rows, key="id")
    print(f"\n  flatten_records(*rows, key='id') -> {ids}")

    # Weighted score
    scores = {"technical": 88.0, "communication": 92.0, "leadership": 75.0}
    weights = {"technical": 0.5, "communication": 0.3, "leadership": 0.2}
    ws = weighted_score(scores, weights)
    print(f"\n  weighted_score(scores, weights) -> {ws:.2f}")


# ---------------------------------------------------------------------------
# 7. __main__ guard - only runs when executed directly, not when imported
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_basic_functions()
    print()
    demo_args_kwargs()
    print()
    demo_enterprise_utils()
    print()

    # Quick summary table
    print("=" * 60)
    print("SUMMARY: Python vs C++ Variadic Arguments")
    print("=" * 60)
    print("""
    Python *args    -> tuple of positional args   | C++: Args... args (parameter pack)
    Python **kwargs -> dict of keyword args        | C++: no direct equivalent
    Python runtime  -> dynamic, introspectable     | C++: compile-time, type-safe
    Python syntax   -> def f(*a, **kw)             | C++: template<typename... Args>
    """)
