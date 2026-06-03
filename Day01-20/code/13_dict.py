"""
Day 13 - 常用数据结构之字典 (Dictionary Data Structure)

Covers:
  - dict fundamentals: creation, access, iteration, methods
  - defaultdict: automatic default values for missing keys
  - dict comprehension: filtering and transforming dictionaries
  - Enterprise patterns: config management, caching
  - C++ comparison: Python dict vs C++ std::unordered_map
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any


# ---------------------------------------------------------------------------
# 1. Python dict vs C++ std::unordered_map
# ---------------------------------------------------------------------------
#
# | Feature              | Python dict                         | C++ std::unordered_map              |
# |----------------------|-------------------------------------|-------------------------------------|
# | Underlying impl      | Compact dict (CPython 3.6+): hash  | Separate-chaining hash table        |
# |                      | table + insertion-ordered array     |                                     |
# | Insertion order      | Guaranteed (Python 3.7+)            | NOT guaranteed                      |
# | Hash requirement     | Keys must be hashable (__hash__)    | Keys need std::hash specialization  |
# | Default missing key  | KeyError (use .get / defaultdict)   | Default-constructs value on []      |
# | Memory layout        | More compact (sparse indices)       | Node-based, higher overhead         |
# | Resize strategy      | Grows when 2/3 full                 | Grows when load_factor exceeded     |
# | Thread safety        | NOT thread-safe (use locks)         | NOT thread-safe (use mutexes)       |
# | Typical lookup       | O(1) amortized                      | O(1) amortized                      |
#
# Key takeaway: Both are hash maps with O(1) average lookup. Python dict
# preserves insertion order and uses a more memory-efficient layout since
# CPython 3.6. C++ unordered_map gives explicit control over hash functions,
# bucket count, and memory allocation.

# ---------------------------------------------------------------------------
# 2. Dict Basics — Creation
# ---------------------------------------------------------------------------

def demo_dict_creation() -> None:
    """Demonstrate multiple ways to create a dictionary."""
    print("=" * 60)
    print("1. Dict Creation")
    print("=" * 60)

    # Literal syntax
    person: dict[str, Any] = {
        "name": "王大锤",
        "age": 55,
        "height": 168,
        "weight": 60,
        "addr": "成都市武侯区科华北路62号1栋101",
        "tel": "13122334455",
    }
    print(f"Literal:          {person}")

    # dict() constructor
    person2: dict[str, Any] = dict(
        name="李小明", age=25, height=178, weight=70
    )
    print(f"Constructor:      {person2}")

    # zip two sequences
    keys: list[str] = ["AAPL", "GOOG", "IBM", "ORCL"]
    values: list[float] = [191.88, 1186.96, 149.24, 48.44]
    stocks: dict[str, float] = dict(zip(keys, values))
    print(f"zip():            {stocks}")

    # fromkeys — bulk default values
    defaults: dict[str, int] = dict.fromkeys(["a", "b", "c"], 0)
    print(f"fromkeys():       {defaults}")

    # Nested dict (dict value can be any mutable type)
    car_info: dict[str, Any] = {
        "brand": "BMW X7",
        "max_speed": 250,
        "dimensions": {"length": 5170, "width": 2000, "height": 1835},
    }
    print(f"Nested:           {car_info}")
    print()


# ---------------------------------------------------------------------------
# 3. Dict Operations — Access, Update, Delete
# ---------------------------------------------------------------------------

def demo_dict_operations() -> None:
    """Demonstrate member test, indexing, and common methods."""
    print("=" * 60)
    print("2. Dict Operations")
    print("=" * 60)

    person: dict[str, Any] = {
        "name": "王大锤",
        "age": 25,
        "height": 178,
    }

    # --- member test ---
    print(f"'name' in person: {'name' in person}")
    print(f"'tel' in person:  {'tel' in person}")

    # --- indexing (read / write / insert) ---
    print(f"person['name']:   {person['name']}")
    person["age"] = 30                      # update
    person["tel"] = "13122334455"           # insert new key
    print(f"After mutations:  {person}")

    # --- .get() — safe access with default ---
    print(f"get('name'):      {person.get('name')}")
    print(f"get('sex'):       {person.get('sex')}")          # None
    print(f"get('sex', True): {person.get('sex', True)}")    # True

    # --- .setdefault() — get-or-insert ---
    person.setdefault("signature", "Hello World")
    print(f"setdefault:       {person['signature']}")

    # --- .keys(), .values(), .items() ---
    print(f"keys():           {list(person.keys())}")
    print(f"values():         {list(person.values())}")
    print(f"items():          {list(person.items())}")

    # --- .update() and | merge (Python 3.9+) ---
    extra: dict[str, Any] = {"age": 28, "addr": "北京市西城区"}
    person_copy = person.copy()
    person_copy.update(extra)
    print(f"update():         {person_copy}")

    if hasattr(dict, "__or__"):  # Python 3.9+
        merged = person | extra
        print(f"merge |:          {merged}")

    # --- deletion ---
    sample: dict[str, Any] = {"a": 1, "b": 2, "c": 3, "d": 4}
    print(f"pop('b'):         {sample.pop('b')}")
    print(f"popitem():        {sample.popitem()}")
    del sample["a"]
    print(f"After deletes:    {sample}")
    sample.clear()
    print(f"clear():          {sample}")
    print()


# ---------------------------------------------------------------------------
# 4. Iteration Patterns
# ---------------------------------------------------------------------------

def demo_dict_iteration() -> None:
    """Show common iteration patterns over dictionaries."""
    print("=" * 60)
    print("3. Dict Iteration")
    print("=" * 60)

    scores: dict[str, int] = {
        "Alice": 92,
        "Bob": 85,
        "Charlie": 78,
        "Diana": 95,
    }

    # Iterate over keys
    print("Keys:")
    for name in scores:
        print(f"  {name}")

    # Iterate over key-value pairs
    print("Key-value pairs:")
    for name, score in scores.items():
        print(f"  {name}: {score}")

    # Sorted iteration by value (descending)
    print("Sorted by score (desc):")
    for name in sorted(scores, key=scores.get, reverse=True):  # type: ignore[arg-type]
        print(f"  {name}: {scores[name]}")
    print()


# ---------------------------------------------------------------------------
# 5. defaultdict — Automatic Default Values
# ---------------------------------------------------------------------------

def demo_defaultdict() -> None:
    """
    defaultdict(factory) returns a dict subclass that calls factory()
    to supply a default value when a missing key is accessed.

    Compared to dict.get(key, default), defaultdict mutates the dict
    on first access, which is ideal for accumulation patterns.
    """
    print("=" * 60)
    print("4. defaultdict")
    print("=" * 60)

    # --- Pattern 1: Counting ---
    sentence = (
        "Man is distinguished not only by his reason but by this "
        "singular passion from other animals"
    )
    counter: defaultdict[str, int] = defaultdict(int)
    for ch in sentence.lower():
        if ch.isalpha():
            counter[ch] += 1
    top5 = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:5]
    print("Top 5 letter frequencies:")
    for letter, count in top5:
        print(f"  '{letter}': {count}")

    # --- Pattern 2: Grouping ---
    students: list[tuple[str, str]] = [
        ("Alice", "Math"),
        ("Bob", "Physics"),
        ("Alice", "Physics"),
        ("Charlie", "Math"),
        ("Bob", "Math"),
        ("Diana", "Physics"),
    ]
    by_subject: defaultdict[str, list[str]] = defaultdict(list)
    for name, subject in students:
        by_subject[subject].append(name)
    print("\nStudents by subject:")
    for subject, names in by_subject.items():
        print(f"  {subject}: {names}")

    # --- Pattern 3: Nested defaultdict (auto-vivification) ---
    # Useful for multi-level grouping without KeyError worries.
    tree: defaultdict[str, defaultdict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    tree["dept_a"]["team_1"].append("Alice")
    tree["dept_a"]["team_1"].append("Bob")
    tree["dept_a"]["team_2"].append("Charlie")
    print("\nNested defaultdict (org tree):")
    for dept, teams in tree.items():
        print(f"  {dept}:")
        for team, members in teams.items():
            print(f"    {team}: {members}")
    print()


# ---------------------------------------------------------------------------
# 6. Dict Comprehension
# ---------------------------------------------------------------------------

def demo_dict_comprehension() -> None:
    """
    Dict comprehension: {key_expr: value_expr for ... in ... if ...}

    C++ equivalent: requires std::transform + std::copy_if or a loop.
    Python's comprehension is more concise and Pythonic.
    """
    print("=" * 60)
    print("5. Dict Comprehension")
    print("=" * 60)

    # --- Basic: squares ---
    squares: dict[int, int] = {x: x ** 2 for x in range(1, 7)}
    print(f"Squares:          {squares}")

    # --- Filter: stocks > 100 ---
    stocks: dict[str, float] = {
        "AAPL": 191.88,
        "GOOG": 1186.96,
        "IBM": 149.24,
        "ORCL": 48.44,
        "ACN": 166.89,
        "FB": 208.09,
        "SYMC": 21.29,
    }
    expensive: dict[str, float] = {
        k: v for k, v in stocks.items() if v > 100
    }
    print(f"Stocks > 100:     {expensive}")

    # --- Transform: invert keys/values ---
    inverted: dict[float, str] = {v: k for k, v in stocks.items()}
    print(f"Inverted:         {inverted}")

    # --- Conditional expression in value ---
    labels: dict[str, str] = {
        k: "expensive" if v > 150 else "affordable"
        for k, v in stocks.items()
    }
    print(f"Labels:           {labels}")

    # --- Build from two lists ---
    names = ["Alice", "Bob", "Charlie"]
    ages = [25, 30, 35]
    people: dict[str, int] = {n: a for n, a in zip(names, ages)}
    print(f"From zip:         {people}")

    # --- Flatten a nested dict ---
    nested: dict[str, dict[str, int]] = {
        "a": {"x": 1, "y": 2},
        "b": {"x": 3, "y": 4},
    }
    flat: dict[str, int] = {
        f"{outer}_{inner}": val
        for outer, inner_dict in nested.items()
        for inner, val in inner_dict.items()
    }
    print(f"Flattened:        {flat}")
    print()


# ---------------------------------------------------------------------------
# 7. Enterprise Pattern — Configuration Management
# ---------------------------------------------------------------------------

class ConfigManager:
    """
    A layered configuration manager backed by dictionaries.

    Layers (lowest to highest priority):
      1. defaults — built-in safe defaults
      2. file     — loaded from a JSON config file
      3. env      — environment / runtime overrides

    C++ comparison: In C++ you might use nlohmann::json or a TOML library
    combined with std::unordered_map<std::string, std::any>. Python's
    dict is more flexible because values can be any type natively.
    """

    def __init__(self) -> None:
        self._defaults: dict[str, Any] = {}
        self._file_config: dict[str, Any] = {}
        self._overrides: dict[str, Any] = {}

    def set_defaults(self, defaults: dict[str, Any]) -> None:
        """Set the lowest-priority default layer."""
        self._defaults = defaults

    def load_json(self, filepath: str) -> None:
        """Load configuration from a JSON file (middle layer)."""
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                self._file_config = json.load(fh)
            print(f"  [Config] Loaded {len(self._file_config)} keys from {filepath}")
        except FileNotFoundError:
            print(f"  [Config] File not found: {filepath}, using defaults only")

    def set_override(self, key: str, value: Any) -> None:
        """Set a high-priority runtime override."""
        self._overrides[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Resolve a config value with layered priority."""
        if key in self._overrides:
            return self._overrides[key]
        if key in self._file_config:
            return self._file_config[key]
        if key in self._defaults:
            return self._defaults[key]
        return default

    def snapshot(self) -> dict[str, Any]:
        """Return the fully-merged configuration as a plain dict."""
        merged: dict[str, Any] = {}
        merged.update(self._defaults)
        merged.update(self._file_config)
        merged.update(self._overrides)
        return merged

    def __repr__(self) -> str:
        return f"ConfigManager({self.snapshot()})"


def demo_config_management() -> None:
    """Enterprise pattern: layered configuration management."""
    print("=" * 60)
    print("6. Enterprise: Configuration Management")
    print("=" * 60)

    cfg = ConfigManager()
    cfg.set_defaults({
        "db_host": "localhost",
        "db_port": 5432,
        "debug": False,
        "max_connections": 10,
    })

    # Simulate loading a JSON config file
    # In production this would be: cfg.load_json("/etc/myapp/config.json")
    cfg._file_config = {
        "db_host": "prod-db.example.com",
        "db_port": 5432,
        "app_name": "MyService",
    }

    # Runtime overrides (e.g. from CLI flags or env vars)
    cfg.set_override("debug", True)
    cfg.set_override("db_port", 6432)

    print(f"  db_host:          {cfg.get('db_host')}")
    print(f"  db_port:          {cfg.get('db_port')}")        # override wins
    print(f"  debug:            {cfg.get('debug')}")          # override wins
    print(f"  max_connections:  {cfg.get('max_connections')}")# default wins
    print(f"  app_name:         {cfg.get('app_name')}")      # file wins
    print(f"  missing_key:      {cfg.get('missing', 'N/A')}")
    print(f"\n  Full snapshot:    {cfg.snapshot()}")
    print()


# ---------------------------------------------------------------------------
# 8. Enterprise Pattern — Simple Cache with TTL
# ---------------------------------------------------------------------------

class TTLCache:
    """
    A simple in-memory cache with per-entry time-to-live (TTL).

    Uses a dict to store (value, expiry_timestamp) pairs.
    Expired entries are lazily evicted on access.

    C++ comparison: In C++ you might use
    std::unordered_map<Key, std::pair<Value, std::chrono::steady_clock::time_point>>
    with manual expiry logic. Python's dict + time.time() achieves the
    same with far less boilerplate.
    """

    def __init__(self, default_ttl: float = 300.0) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def put(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Insert or overwrite a cache entry."""
        expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
        self._store[key] = (value, expiry)

    def get(self, key: str) -> Any | None:
        """Retrieve a value, or None if missing or expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.time() > expiry:
            del self._store[key]  # lazy eviction
            return None
        return value

    def invalidate(self, key: str) -> bool:
        """Remove a key. Returns True if the key existed."""
        return self._store.pop(key, None) is not None

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"TTLCache(entries={len(self)}, default_ttl={self._default_ttl}s)"


def demo_cache() -> None:
    """Enterprise pattern: TTL-based in-memory cache."""
    print("=" * 60)
    print("7. Enterprise: TTL Cache")
    print("=" * 60)

    cache: TTLCache = TTLCache(default_ttl=2.0)

    # Populate cache
    cache.put("user:1001", {"name": "Alice", "role": "admin"})
    cache.put("user:1002", {"name": "Bob", "role": "viewer"}, ttl=5.0)
    cache.put("session:abc", "active", ttl=1.0)

    print(f"  Cache state: {cache}")
    print(f"  user:1001  -> {cache.get('user:1001')}")
    print(f"  user:1002  -> {cache.get('user:1002')}")
    print(f"  session:abc -> {cache.get('session:abc')}")

    # Wait for the short-TTL entry to expire
    print("\n  Waiting 1.5s for session:abc to expire...")
    time.sleep(1.5)
    print(f"  session:abc -> {cache.get('session:abc')}")   # None (expired)
    print(f"  user:1001  -> {cache.get('user:1001')}")      # still alive
    print(f"  Cache state: {cache}")

    # Invalidate manually
    cache.invalidate("user:1001")
    print(f"\n  After invalidating user:1001: {cache.get('user:1001')}")
    print(f"  Cache state: {cache}")
    print()


# ---------------------------------------------------------------------------
# 9. Practical Example — Letter Frequency Counter
# ---------------------------------------------------------------------------

def letter_frequency(text: str) -> list[tuple[str, int]]:
    """
    Count English letter frequencies in *text* and return them
    sorted from most to least frequent.

    Uses dict.get() for counting — the classic pattern from the
    textbook. For the defaultdict version, see demo_defaultdict().
    """
    counter: dict[str, int] = {}
    for ch in text:
        if ch.isalpha():
            counter[ch] = counter.get(ch, 0) + 1
    return sorted(counter.items(), key=lambda kv: kv[1], reverse=True)


def demo_letter_frequency() -> None:
    """Practical example: count and rank letter frequencies."""
    print("=" * 60)
    print("8. Practical: Letter Frequency")
    print("=" * 60)

    text = (
        "Man is distinguished not only by his reason but by this "
        "singular passion from other animals which is a lust of the "
        "mind that by a perseverance of delight in the continued and "
        "indefatigable generation of knowledge exceeds the short "
        "vehemence of any carnal pleasure"
    )
    freq = letter_frequency(text)
    print("  Letter frequencies (top 10):")
    for letter, count in freq[:10]:
        print(f"    '{letter}': {count}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations."""
    print()
    print("  Python dict vs C++ std::unordered_map")
    print("  --------------------------------------")
    print("  Both are hash maps with O(1) average lookup/insert/delete.")
    print("  Python dict guarantees insertion order (3.7+) and uses a")
    print("  compact memory layout. C++ unordered_map offers explicit")
    print("  control over hash functions and bucket management.")
    print()

    demo_dict_creation()
    demo_dict_operations()
    demo_dict_iteration()
    demo_defaultdict()
    demo_dict_comprehension()
    demo_config_management()
    demo_cache()
    demo_letter_frequency()


if __name__ == "__main__":
    main()
