"""
Day 100 - Supplementary Content: Python Mastery Wrap-Up
=======================================================

This module consolidates additional Python features, useful libraries,
best practices, career advice, and learning resources that round out
the Python-100-Days curriculum. It serves as both a reference and a
runnable demonstration of enterprise-grade patterns.

Topics covered:
    1. Advanced Python features and idioms
    2. Useful standard-library and third-party libraries
    3. Enterprise utility collection
    4. Best practices summary
    5. Career advice and learning resources
    6. Interview preparation pointers
    7. Mathematics foundations for ML / data science
    8. Deep learning orientation
"""

from __future__ import annotations

import abc
import collections
import contextlib
import dataclasses
import datetime
import enum
import functools
import hashlib
import itertools
import json
import logging
import operator
import os
import pathlib
import re
import statistics
import sys
import textwrap
import time
import typing
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Final,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    Protocol,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    runtime_checkable,
)

# ---------------------------------------------------------------------------
# Configure module-level logger
# ---------------------------------------------------------------------------
logger: Final = logging.getLogger(__name__)


# ===================================================================
# Section 1 -- Advanced Python Features & Idioms
# ===================================================================


# --- 1a. Dataclasses with advanced features ------------------------

@dataclasses.dataclass(frozen=True, order=True, slots=True)
class Point:
    """Immutable, ordered, slot-based dataclass (Python 3.10+)."""

    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        """Euclidean distance to another point."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    @property
    def magnitude(self) -> float:
        """Distance from the origin."""
        return (self.x**2 + self.y**2) ** 0.5


# --- 1b. Enum with custom methods -----------------------------------

class Direction(enum.Enum):
    """Cardinal directions with vector offsets."""

    NORTH = (0, 1)
    SOUTH = (0, -1)
    EAST = (1, 0)
    WEST = (-1, 0)

    def move(self, point: Point, distance: float = 1.0) -> Point:
        """Return a new point moved in this direction."""
        dx, dy = self.value
        return Point(point.x + dx * distance, point.y + dy * distance)


# --- 1c. Protocols (structural subtyping) ----------------------------

@runtime_checkable
class Serializable(Protocol):
    """Any object that can be serialized to a JSON string."""

    def to_json(self) -> str: ...


@runtime_checkable
class Drawable(Protocol):
    """Any object that knows how to draw itself."""

    def draw(self) -> str: ...


# --- 1d. Generics with TypeVar and bounded types --------------------

T = TypeVar("T")
NumericT = TypeVar("NumericT", int, float)


class Stack(Generic[T]):
    """A generic, typed stack data structure."""

    def __init__(self) -> None:
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek on empty stack")
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)

    def __iter__(self) -> Iterator[T]:
        return reversed(self._items)


# --- 1e. Context managers -------------------------------------------

class Timer:
    """Measure wall-clock time of a code block.

    Usage::

        with Timer("my operation") as t:
            do_something()
        print(t.elapsed)
    """

    def __init__(self, label: str = "Timer") -> None:
        self.label = label
        self.elapsed: float = 0.0
        self._start: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.elapsed = time.perf_counter() - self._start
        logger.info("%s: %.6f seconds", self.label, self.elapsed)


@contextlib.contextmanager
def temporary_directory(prefix: str = "tmp_") -> Iterator[pathlib.Path]:
    """Create a temporary directory and clean up after use.

    >>> with temporary_directory() as tmpdir:
    ...     (tmpdir / "hello.txt").write_text("world")
    """
    import tempfile
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield tmpdir
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


# --- 1f. Descriptors -------------------------------------------------

class Validated:
    """A descriptor that validates attribute values on set."""

    def __init__(
        self,
        validator: Callable[[Any], bool],
        error_msg: str = "Invalid value",
    ) -> None:
        self.validator = validator
        self.error_msg = error_msg

    def __set_name__(self, owner: type, name: str) -> None:
        self.attr_name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return obj.__dict__.get(self.attr_name)

    def __set__(self, obj: Any, value: Any) -> None:
        if not self.validator(value):
            raise ValueError(f"{self.error_msg}: {value!r}")
        obj.__dict__[self.attr_name] = value


class Person:
    """Demonstrates descriptor-based validation."""

    name: str = Validated(lambda v: isinstance(v, str) and len(v) > 0, "Name must be non-empty string")
    age: int = Validated(lambda v: isinstance(v, int) and 0 < v < 200, "Age must be between 1 and 199")

    def __init__(self, name: str, age: int) -> None:
        self.name = name  # type: ignore[assignment]
        self.age = age    # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"Person(name={self.name!r}, age={self.age})"


# --- 1g. functools classics -----------------------------------------

def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """Decorator: retry a function on exception.

    >>> @retry(max_attempts=2, delay=0.1)
    ... def flaky() -> int:
    ...     raise RuntimeError("oops")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        "Attempt %d/%d for %s failed: %s",
                        attempt, max_attempts, func.__name__, exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise RuntimeError(
                f"{func.__name__} failed after {max_attempts} attempts"
            ) from last_exc
        return wrapper
    return decorator


def memoize(func: Callable) -> Callable:
    """Simple memoization decorator with cache stats."""
    cache: Dict = {}
    hits = [0]
    misses = [0]

    @functools.wraps(func)
    def wrapper(*args: Any) -> Any:
        if args in cache:
            hits[0] += 1
            return cache[args]
        misses[0] += 1
        result = func(*args)
        cache[args] = result
        return result

    wrapper.cache = cache  # type: ignore[attr-defined]
    wrapper.stats = lambda: {"hits": hits[0], "misses": misses[0]}  # type: ignore[attr-defined]
    wrapper.cache_clear = lambda: (cache.clear(), hits.__setitem__(0, 0), misses.__setitem__(0, 0))  # type: ignore[attr-defined]
    return wrapper


# ===================================================================
# Section 2 -- Useful Standard-Library Highlights
# ===================================================================


class StdlibShowcase:
    """Demonstrates powerful but underused standard-library modules."""

    @staticmethod
    def collections_demo() -> Dict[str, Any]:
        """Showcase collections module utilities."""
        # Counter -- count occurrences
        words = "the quick brown fox jumps over the lazy dog the fox".split()
        word_counts: collections.Counter[str] = collections.Counter(words)

        # defaultdict -- auto-initialize missing keys
        dd: collections.defaultdict[str, List[int]] = collections.defaultdict(list)
        for i, word in enumerate(words):
            dd[word].append(i)

        # deque -- fast appends/pops on both ends
        dq: collections.deque[str] = collections.deque(maxlen=5)
        for word in words:
            dq.append(word)

        # namedtuple -- lightweight immutable record
        Color = collections.namedtuple("Color", ["r", "g", "b"])
        red = Color(255, 0, 0)

        return {
            "most_common_3": word_counts.most_common(3),
            "defaultdict_sample": dict(list(dd.items())[:3]),
            "deque_final": list(dq),
            "namedtuple_red": red,
        }

    @staticmethod
    def itertools_demo() -> List[Tuple]:
        """Showcase itertools combinatoric helpers."""
        items = ["A", "B", "C"]
        return [
            ("permutations", list(itertools.permutations(items, 2))),
            ("combinations", list(itertools.combinations(items, 2))),
            ("product", list(itertools.product([0, 1], repeat=3))),
            ("chain", list(itertools.chain([1, 2], [3, 4], [5]))),
            ("groupby", [
                (k, list(g))
                for k, g in itertools.groupby("AAABBBCCCAA")
            ]),
        ]

    @staticmethod
    def statistics_demo() -> Dict[str, float]:
        """Showcase statistics module for quick descriptive stats."""
        data = [2.75, 1.75, 1.25, 0.25, 0.5, 1.25, 3.5]
        return {
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "stdev": statistics.stdev(data),
            "variance": statistics.variance(data),
            "harmonic_mean": statistics.harmonic_mean([1, 2, 4]),
        }

    @staticmethod
    def pathlib_demo() -> Dict[str, str]:
        """Showcase pathlib for modern path manipulation."""
        p = pathlib.Path("/home/user/projects/app/main.py")
        return {
            "name": p.name,
            "stem": p.stem,
            "suffix": p.suffix,
            "parent": str(p.parent),
            "parts": str(p.parts),
            "with_suffix": str(p.with_suffix(".pyc")),
        }


# ===================================================================
# Section 3 -- Enterprise Utility Collection
# ===================================================================


class EnvironmentConfig:
    """Load configuration from environment variables with type coercion.

    Enterprise apps commonly use 12-factor config via env vars.
    """

    _CASTERS: Dict[Type, Callable] = {
        int: int,
        float: float,
        bool: lambda v: v.lower() in ("1", "true", "yes"),
        str: str,
        list: lambda v: [s.strip() for s in v.split(",")],
    }

    def __init__(self, prefix: str = "APP_") -> None:
        self._prefix = prefix

    def get(self, key: str, default: Any = None, cast: Type = str) -> Any:
        """Read an env var with optional type casting."""
        raw = os.environ.get(f"{self._prefix}{key}")
        if raw is None:
            return default
        caster = self._CASTERS.get(cast, str)
        try:
            return caster(raw)
        except (ValueError, TypeError):
            return default


class RateLimiter:
    """Token-bucket rate limiter for API call throttling."""

    def __init__(self, rate: float, capacity: int) -> None:
        self.rate = rate          # tokens per second
        self.capacity = capacity  # max burst size
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def acquire(self, tokens: int = 1) -> float:
        """Block until *tokens* are available; return wait time."""
        self._refill()
        wait = 0.0
        while self._tokens < tokens:
            deficit = tokens - self._tokens
            sleep_time = deficit / self.rate
            time.sleep(sleep_time)
            wait += sleep_time
            self._refill()
        self._tokens -= tokens
        return wait


class LRUCache:
    """Thread-unsafe LRU cache built on OrderedDict."""

    def __init__(self, capacity: int = 128) -> None:
        self._cache: collections.OrderedDict = collections.OrderedDict()
        self._capacity = capacity

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        return len(self._cache)


class EventBus:
    """Simple synchronous publish/subscribe event bus."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = collections.defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        self._handlers[event].append(handler)

    def unsubscribe(self, event: str, handler: Callable) -> None:
        self._handlers[event].remove(handler)

    def publish(self, event: str, *args: Any, **kwargs: Any) -> None:
        for handler in self._handlers.get(event, []):
            handler(*args, **kwargs)

    def clear(self) -> None:
        self._handlers.clear()


class StructuredLogger:
    """Minimal structured (JSON) logger for enterprise services."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self._logger = logging.getLogger(service_name)

    def _emit(self, level: str, message: str, **extra: Any) -> None:
        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "service": self.service_name,
            "level": level,
            "message": message,
            **extra,
        }
        getattr(self._logger, level.lower(), self._logger.info)(
            json.dumps(record, ensure_ascii=False, default=str)
        )

    def info(self, message: str, **extra: Any) -> None:
        self._emit("INFO", message, **extra)

    def error(self, message: str, **extra: Any) -> None:
        self._emit("ERROR", message, **extra)

    def warning(self, message: str, **extra: Any) -> None:
        self._emit("WARNING", message, **extra)


class HashUtils:
    """Convenience wrappers around hashlib for common hashing tasks."""

    @staticmethod
    def sha256(data: Union[str, bytes]) -> str:
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def md5(data: Union[str, bytes]) -> str:
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def file_hash(path: Union[str, pathlib.Path], algorithm: str = "sha256") -> str:
        h = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()


# ===================================================================
# Section 4 -- Best Practices Summary
# ===================================================================


BEST_PRACTICES: Final[List[Dict[str, str]]] = [
    {
        "category": "Code Style",
        "practice": "Follow PEP 8; use a linter (ruff, flake8) and formatter (black).",
    },
    {
        "category": "Code Style",
        "practice": "Use type hints throughout; validate with mypy in strict mode.",
    },
    {
        "category": "Code Style",
        "practice": "Prefer f-strings over .format() or % formatting.",
    },
    {
        "category": "Architecture",
        "practice": "Apply SOLID principles; favor composition over inheritance.",
    },
    {
        "category": "Architecture",
        "practice": "Separate business logic from I/O; use dependency injection.",
    },
    {
        "category": "Architecture",
        "practice": "Design for testability: small functions, explicit dependencies.",
    },
    {
        "category": "Testing",
        "practice": "Write unit tests with pytest; aim for > 80% branch coverage.",
    },
    {
        "category": "Testing",
        "practice": "Use fixtures for setup/teardown; parametrize tests for data variation.",
    },
    {
        "category": "Testing",
        "practice": "Mock external services; never hit real APIs in unit tests.",
    },
    {
        "category": "Security",
        "practice": "Never store secrets in code; use env vars or a secrets manager.",
    },
    {
        "category": "Security",
        "practice": "Sanitize all user input; guard against SQL injection and XSS.",
    },
    {
        "category": "Security",
        "practice": "Keep dependencies pinned and audited (pip-audit, safety).",
    },
    {
        "category": "Performance",
        "practice": "Profile before optimizing; use cProfile, line_profiler, or py-spy.",
    },
    {
        "category": "Performance",
        "practice": "Use generators for large data streams to minimize memory.",
    },
    {
        "category": "Performance",
        "practice": "Cache expensive computations (functools.lru_cache, Redis).",
    },
    {
        "category": "DevOps",
        "practice": "Containerize with Docker; pin base-image versions.",
    },
    {
        "category": "DevOps",
        "practice": "Automate CI/CD with GitHub Actions, GitLab CI, or Jenkins.",
    },
    {
        "category": "DevOps",
        "practice": "Use infrastructure-as-code (Terraform, Pulumi) for cloud resources.",
    },
    {
        "category": "Documentation",
        "practice": "Write docstrings for all public modules, classes, and functions.",
    },
    {
        "category": "Documentation",
        "practice": "Maintain a README with setup instructions, architecture overview.",
    },
    {
        "category": "Documentation",
        "practice": "Use Sphinx or MkDocs to auto-generate API reference docs.",
    },
]


def print_best_practices() -> None:
    """Pretty-print the best-practices table."""
    by_category: Dict[str, List[str]] = {}
    for entry in BEST_PRACTICES:
        by_category.setdefault(entry["category"], []).append(entry["practice"])

    output_lines = ["=" * 70, "Python Best Practices Summary", "=" * 70]
    for category, practices in by_category.items():
        output_lines.append(f"\n[{category}]")
        for i, p in enumerate(practices, 1):
            output_lines.append(f"  {i}. {p}")
    output_lines.append("")
    print("\n".join(output_lines))


# ===================================================================
# Section 5 -- Career Advice & Learning Resources
# ===================================================================


class CareerResource(NamedTuple):
    """A career/learning resource entry."""

    topic: str
    title: str
    url: str
    description: str


CAREER_RESOURCES: Final[List[CareerResource]] = [
    CareerResource(
        topic="Interview Preparation",
        title="Python Interview Bible",
        url="https://github.com/jackfrued/Python-Interview-Bible",
        description="Comprehensive Python interview questions and answers.",
    ),
    CareerResource(
        topic="Interview Preparation",
        title="Business Analyst Interview Bible",
        url="https://github.com/jackfrued/Python-Interview-Bible",
        description="Interview preparation for business analyst roles.",
    ),
    CareerResource(
        topic="Interview Preparation",
        title="Data Analyst SQL Interview Bible",
        url="https://github.com/jackfrued/Python-Interview-Bible",
        description="SQL-focused interview questions for data analyst roles.",
    ),
    CareerResource(
        topic="Interview Preparation",
        title="Machine Learning Interview Bible",
        url="https://github.com/jackfrued/Python-Interview-Bible",
        description="ML interview questions covering algorithms and systems.",
    ),
    CareerResource(
        topic="Mathematics for ML",
        title="Math for Machine Learning",
        url="https://github.com/jackfrued/Math_for_ML",
        description="Linear algebra, probability, calculus, and information theory.",
    ),
    CareerResource(
        topic="Deep Learning",
        title="Deep Learning Is Nothing",
        url="https://github.com/jackfrued/Deep-Learning-Is-Nothing",
        description="Practical deep learning from scratch with clear explanations.",
    ),
    CareerResource(
        topic="Career Growth",
        title="Effective Engineer",
        url="https://effectiveengineer.com/",
        description="High-leverage habits for software engineers.",
    ),
    CareerResource(
        topic="Career Growth",
        title="The Pragmatic Programmer",
        url="https://pragprog.com/titles/tpp20/",
        description="Timeless advice on craftsmanship and professional growth.",
    ),
    CareerResource(
        topic="Python Mastery",
        title="CPython Internals",
        url="https://realpython.com/products/cpython-internals-book/",
        description="Understand the Python interpreter under the hood.",
    ),
    CareerResource(
        topic="System Design",
        title="System Design Primer",
        url="https://github.com/donnemartin/system-design-primer",
        description="Learn to design large-scale systems for interviews.",
    ),
]

# Broad career advice distilled into actionable tips.
CAREER_ADVICE: Final[List[str]] = [
    "Build a public portfolio on GitHub; quality beats quantity.",
    "Contribute to open-source projects to sharpen collaboration skills.",
    "Master at least one web framework (Django, FastAPI, Flask) deeply.",
    "Learn SQL thoroughly -- it is the lingua franca of data.",
    "Understand Linux fundamentals: shell, networking, process management.",
    "Practice coding problems regularly (LeetCode, HackerRank) for interviews.",
    "Study system design for senior-level interviews and real-world architecture.",
    "Communicate clearly: write good commit messages, docs, and emails.",
    "Read source code of well-maintained open-source libraries.",
    "Never stop learning: attend meetups, read blogs, watch conference talks.",
    "Specialize in a domain (web, data, ML, DevOps) but stay broadly curious.",
    "Seek mentorship and also mentor others -- teaching deepens understanding.",
]


def print_career_resources() -> None:
    """Pretty-print career and learning resources."""
    output_lines = ["=" * 70, "Career & Learning Resources", "=" * 70]
    grouped: Dict[str, List[CareerResource]] = {}
    for res in CAREER_RESOURCES:
        grouped.setdefault(res.topic, []).append(res)

    for topic, resources in grouped.items():
        output_lines.append(f"\n--- {topic} ---")
        for r in resources:
            output_lines.append(f"  * {r.title}")
            output_lines.append(f"    URL: {r.url}")
            output_lines.append(f"    {r.description}")

    output_lines.append(f"\n{'=' * 70}")
    output_lines.append("Career Advice")
    output_lines.append("=" * 70)
    for i, tip in enumerate(CAREER_ADVICE, 1):
        output_lines.append(f"  {i:2d}. {tip}")

    output_lines.append("")
    print("\n".join(output_lines))


# ===================================================================
# Section 6 -- Interview Preparation Helpers
# ===================================================================


class InterviewTopic(NamedTuple):
    """A topic area for technical interview preparation."""

    name: str
    key_concepts: List[str]
    recommended_practice: str


INTERVIEW_TOPICS: Final[List[InterviewTopic]] = [
    InterviewTopic(
        name="Data Structures",
        key_concepts=[
            "Lists, tuples, sets, dicts -- internals and Big-O",
            "collections.deque, heapq, bisect",
            "Tree traversals, graph BFS/DFS",
            "Hash tables: collision handling, load factor",
        ],
        recommended_practice="Implement each from scratch in Python.",
    ),
    InterviewTopic(
        name="Algorithms",
        key_concepts=[
            "Sorting: Timsort, quicksort, mergesort",
            "Binary search and variants",
            "Dynamic programming patterns",
            "Greedy vs. DP decision framework",
        ],
        recommended_practice="Solve 3 problems per pattern on LeetCode.",
    ),
    InterviewTopic(
        name="Python Internals",
        key_concepts=[
            "GIL and its implications for threading",
            "Memory management: reference counting, garbage collector",
            "MRO and cooperative multiple inheritance",
            "Descriptor protocol, __slots__, metaclasses",
        ],
        recommended_practice="Read CPython source for the relevant C modules.",
    ),
    InterviewTopic(
        name="System Design",
        key_concepts=[
            "Scalability: horizontal vs. vertical scaling",
            "Caching layers (Redis, CDN) and invalidation",
            "Database sharding, replication, CAP theorem",
            "Message queues (RabbitMQ, Kafka) for async processing",
        ],
        recommended_practice="Design 2 systems per week; write a one-page doc.",
    ),
    InterviewTopic(
        name="SQL & Databases",
        key_concepts=[
            "JOIN types, window functions, CTEs",
            "Indexing: B-tree, hash, covering indexes",
            "Normalization and denormalization trade-offs",
            "Transaction isolation levels and deadlocks",
        ],
        recommended_practice="Practice on SQLZoo, LeetCode SQL, and Mode Analytics.",
    ),
    InterviewTopic(
        name="Mathematics for ML",
        key_concepts=[
            "Linear algebra: eigenvalues, SVD, matrix factorization",
            "Probability: Bayes theorem, distributions, MLE",
            "Calculus: gradients, chain rule, optimization",
            "Information theory: entropy, KL divergence",
        ],
        recommended_practice="Work through exercises in the Math_for_ML repository.",
    ),
]


def print_interview_preparation() -> None:
    """Pretty-print interview preparation guide."""
    output_lines = ["=" * 70, "Interview Preparation Guide", "=" * 70]
    for topic in INTERVIEW_TOPICS:
        output_lines.append(f"\n>> {topic.name}")
        for concept in topic.key_concepts:
            output_lines.append(f"   - {concept}")
        output_lines.append(f"   Practice: {topic.recommended_practice}")
    output_lines.append("")
    print("\n".join(output_lines))


# ===================================================================
# Section 7 -- Deep Learning Orientation
# ===================================================================


DEEP_LEARNING_TOPICS: Final[List[Dict[str, Any]]] = [
    {
        "area": "Foundations",
        "topics": [
            "Neural network basics: perceptron, activation functions, backprop",
            "Loss functions: cross-entropy, MSE, contrastive loss",
            "Optimizers: SGD, Adam, learning rate scheduling",
            "Regularization: dropout, batch normalization, weight decay",
        ],
    },
    {
        "area": "Computer Vision",
        "topics": [
            "CNNs: convolution, pooling, stride, padding",
            "Architectures: ResNet, EfficientNet, Vision Transformer (ViT)",
            "Transfer learning and fine-tuning pre-trained models",
            "Object detection: YOLO, Faster R-CNN",
        ],
    },
    {
        "area": "Natural Language Processing",
        "topics": [
            "Word embeddings: Word2Vec, GloVe, FastText",
            "Sequence models: RNN, LSTM, GRU",
            "Attention mechanism and Transformer architecture",
            "Large Language Models: GPT, BERT, fine-tuning strategies",
        ],
    },
    {
        "area": "Tools & Frameworks",
        "topics": [
            "PyTorch: tensors, autograd, nn.Module, DataLoaders",
            "TensorFlow / Keras for production deployment",
            "Hugging Face Transformers for NLP tasks",
            "MLOps: MLflow, Weights & Biases, model versioning",
        ],
    },
]


def print_deep_learning_orientation() -> None:
    """Pretty-print deep learning study roadmap."""
    output_lines = ["=" * 70, "Deep Learning Study Roadmap", "=" * 70]
    for block in DEEP_LEARNING_TOPICS:
        output_lines.append(f"\n>> {block['area']}")
        for t in block["topics"]:
            output_lines.append(f"   - {t}")
    output_lines.append("")
    print("\n".join(output_lines))


# ===================================================================
# Section 8 -- Comprehensive Demonstrations
# ===================================================================


def run_demonstrations() -> None:
    """Execute all demonstrations and print organized output."""

    # --- Advanced features demo ---
    print("=" * 70)
    print("1. ADVANCED PYTHON FEATURES")
    print("=" * 70)

    p1 = Point(3.0, 4.0)
    p2 = Point(0.0, 0.0)
    print(f"  Point p1       = {p1}")
    print(f"  |p1| (magnitude) = {p1.magnitude:.4f}")
    print(f"  dist(p1, p2)   = {p1.distance_to(p2):.4f}")

    print(f"  Direction.NORTH.move(p2) = {Direction.NORTH.move(p2)}")

    print(f"  p1 is Serializable? {isinstance(p1, Serializable)}")

    stack: Stack[int] = Stack()
    for val in [10, 20, 30]:
        stack.push(val)
    print(f"  Stack size      = {len(stack)}")
    print(f"  Stack pop       = {stack.pop()}")
    print(f"  Stack peek      = {stack.peek()}")

    with Timer("sum of squares") as t:
        _ = sum(i * i for i in range(100_000))
    print(f"  Timer result    = {t.elapsed:.6f}s")

    bob = Person("Bob", 30)
    print(f"  Person          = {bob}")
    try:
        Person("", 30)
    except ValueError as e:
        print(f"  Validation caught: {e}")

    @memoize
    def fib(n: int) -> int:
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    print(f"  fib(30)         = {fib(30)}")
    print(f"  fib cache stats = {fib.stats()}")

    # --- Stdlib showcase ---
    print(f"\n{'=' * 70}")
    print("2. STANDARD LIBRARY SHOWCASE")
    print("=" * 70)

    showcase = StdlibShowcase()
    for name in ("collections_demo", "itertools_demo", "statistics_demo", "pathlib_demo"):
        result = getattr(showcase, name)()
        print(f"\n  {name}:")
        if isinstance(result, dict):
            for k, v in result.items():
                print(f"    {k}: {v}")
        elif isinstance(result, list):
            for item in result:
                print(f"    {item}")

    # --- Enterprise utilities demo ---
    print(f"\n{'=' * 70}")
    print("3. ENTERPRISE UTILITY COLLECTION")
    print("=" * 70)

    config = EnvironmentConfig(prefix="DEMO_")
    print(f"  Config (missing key) = {config.get('MISSING', default='N/A')}")

    limiter = RateLimiter(rate=10.0, capacity=5)
    print(f"  RateLimiter created  = 10 tokens/sec, burst=5")

    lru = LRUCache(capacity=3)
    for k, v in [("a", 1), ("b", 2), ("c", 3)]:
        lru.put(k, v)
    print(f"  LRU cache size       = {len(lru)}")
    print(f"  LRU get('a')         = {lru.get('a')}")
    lru.put("d", 4)
    print(f"  After inserting 'd', get('b') = {lru.get('b')}")  # evicted

    bus = EventBus()
    received: List[str] = []
    bus.subscribe("greet", lambda name: received.append(f"Hello, {name}!"))
    bus.publish("greet", "Alice")
    print(f"  EventBus received    = {received}")

    slog = StructuredLogger("demo-service")
    slog.info("service started", version="1.0.0")
    print("  StructuredLogger emitted a JSON log entry (see logger).")

    print(f"  SHA-256('hello')     = {HashUtils.sha256('hello')[:32]}...")

    # --- Best practices ---
    print()
    print_best_practices()

    # --- Career resources ---
    print()
    print_career_resources()

    # --- Interview preparation ---
    print()
    print_interview_preparation()

    # --- Deep learning roadmap ---
    print()
    print_deep_learning_orientation()

    # --- Closing message ---
    print("=" * 70)
    print("Congratulations on completing Python-100-Days!")
    print("=" * 70)
    print(textwrap.dedent("""\
        You have journeyed through 100 days of Python learning.
        Key takeaways:
          * Python is versatile: web, data, ML, automation, DevOps.
          * Master the fundamentals deeply; libraries come and go.
          * Build real projects; ship something users can touch.
          * Read code, write code, review code -- every single day.
          * Stay curious and never stop learning.

        Recommended next steps:
          1. Pick a specialization (web, data, ML, DevOps) and go deep.
          2. Build a portfolio project and deploy it publicly.
          3. Contribute to open source to sharpen collaboration skills.
          4. Prepare for interviews using the resources listed above.
          5. Explore the companion repositories:
             - Python Interview Bible
             - Math for Machine Learning
             - Deep Learning Is Nothing

        Happy coding!
    """))


# ===================================================================
# Main Entry Point
# ===================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stderr,
    )
    run_demonstrations()
