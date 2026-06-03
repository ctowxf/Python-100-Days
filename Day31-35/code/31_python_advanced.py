"""
Day 31 - Python Advanced Language Features
============================================

Topics covered:
  1. Generators (iterators, yield, coroutines, send)
  2. Decorators (function decorators, parameterized, class-based)
  3. Metaclasses (type, SingletonMeta, ORM field descriptors)
  4. Dataclasses (frozen, slots, __post_init__, field metadata)
  5. Enterprise patterns (ORM descriptor framework, validation framework)
  6. C++ comparison: Python metaclass vs C++ template metaprogramming

All code uses type hints and idiomatic modern Python (3.10+).
"""

from __future__ import annotations

import re
import threading
import weakref
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field, fields, asdict
from enum import Enum, unique
from functools import wraps
from time import time
from typing import (
    Any,
    Callable,
    ClassVar,
    Generator,
    Generic,
    Iterator,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)


# ============================================================================
# SECTION 1: GENERATORS
# ============================================================================

def fib_generator(n: int) -> Generator[int, None, None]:
    """
    Generator that yields the first *n* Fibonacci numbers.

    Demonstrates the simplest form of generator -- a function that uses
    ``yield`` instead of building a full list in memory.  The generator
    protocol (``__iter__`` / ``__next__``) is synthesised automatically.
    """
    a: int = 0
    b: int = 1
    for _ in range(n):
        a, b = b, a + b
        yield a


def fibonacci_iterative_class(n: int) -> FibIterator:
    """
    Return a *FibIterator* -- an explicit iterator class implementing
    ``__iter__`` and ``__next__``.  This is the verbose equivalent of
    *fib_generator* and illustrates the iterator protocol directly.
    """
    return FibIterator(n)


class FibIterator:
    """
    Manual iterator for Fibonacci numbers.

    Python iterators must implement:
      - ``__iter__()`` returning *self*
      - ``__next__()`` raising ``StopIteration`` when exhausted
    """

    def __init__(self, num: int) -> None:
        self.num: int = num
        self.a: int = 0
        self.b: int = 1
        self.idx: int = 0

    def __iter__(self) -> FibIterator:
        return self

    def __next__(self) -> int:
        if self.idx < self.num:
            self.a, self.b = self.b, self.a + self.b
            self.idx += 1
            return self.a
        raise StopIteration


def yield_from_demo() -> Generator[int, None, None]:
    """
    ``yield from`` delegates to a sub-iterator, flattening one level.
    Useful for composing generators without manual loops.
    """
    yield from range(1, 6)
    yield from range(10, 15)


def calc_avg() -> Generator[Optional[float], float, None]:
    """
    Coroutine: a generator that *receives* values via ``send()`` and
    yields the running average.

    This demonstrates generator evolution into coroutines -- the caller
    pushes data into the generator with ``send(value)``, and the generator
    yields back a computed result.
    """
    total: float = 0.0
    counter: int = 0
    avg_value: Optional[float] = None
    while True:
        value: float = yield avg_value
        total += value
        counter += 1
        avg_value = total / counter


def stream_pipeline_demo() -> None:
    """
    Compose a small data-processing pipeline using generators:
      numbers -> square -> even filter -> take first 5

    Each stage is lazy; nothing is computed until the final consumer
    iterates.
    """
    def source(nums: list[int]) -> Generator[int, None, None]:
        for n in nums:
            yield n

    def square(gen: Generator[int, None, None]) -> Generator[int, None, None]:
        for n in gen:
            yield n * n

    def even_filter(gen: Generator[int, None, None]) -> Generator[int, None, None]:
        for n in gen:
            if n % 2 == 0:
                yield n

    def take(n: int, gen: Generator[int, None, None]) -> Generator[int, None, None]:
        for i, val in enumerate(gen):
            if i >= n:
                return
            yield val

    nums = list(range(1, 21))
    pipeline = take(5, even_filter(square(source(nums))))
    result = list(pipeline)
    print(f"  Pipeline (even squares, first 5): {result}")


# ============================================================================
# SECTION 2: DECORATORS
# ============================================================================

def record_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Simple decorator that prints the wall-clock execution time of the
    wrapped function.

    Uses ``@wraps`` to preserve the original function's ``__name__``,
    ``__doc__``, and ``__wrapped__`` attribute (allowing decorator removal
    via ``func.__wrapped__()``).
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start: float = time()
        result = func(*args, **kwargs)
        elapsed = time() - start
        print(f"  {func.__name__} took {elapsed:.6f}s")
        return result
    return wrapper


def parameterized_decorator(output: Callable[[str, float], None]) -> Callable[..., Any]:
    """
    A parameterised decorator factory.  The outer function accepts
    configuration (an *output* callable), then returns the actual
    decorator.

    This avoids coupling the decorator to a specific logging mechanism.
    """
    def decorate(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start: float = time()
            result = func(*args, **kwargs)
            output(func.__name__, time() - start)
            return result
        return wrapper
    return decorate


class RecordTimeClass:
    """
    Decorator implemented as a class (via ``__call__``).

    Class-based decorators are useful when you need to maintain state
    across calls or want a richer configuration interface.
    """

    def __init__(self, output: Callable[[str, float], None]) -> None:
        self.output = output

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start: float = time()
            result = func(*args, **kwargs)
            self.output(func.__name__, time() - start)
            return result
        return wrapper


def singleton(cls: Type) -> Type:
    """
    Thread-safe singleton decorator using double-checked locking.

    The first check avoids acquiring the lock once the instance exists.
    The second check (inside the lock) prevents a race between two
    threads that both passed the first check simultaneously.
    """
    instances: dict[Type, Any] = {}
    locker = threading.RLock()

    @wraps(cls)
    def get_instance(*args: Any, **kwargs: Any) -> Any:
        if cls not in instances:
            with locker:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance  # type: ignore[return-value]


def retry(max_attempts: int = 3, delay: float = 0.1) -> Callable[..., Any]:
    """
    Decorator that retries a function up to *max_attempts* times on
    exception, sleeping *delay* seconds between attempts.
    """
    import time as _time

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    print(f"  {func.__name__} attempt {attempt} failed: {exc}")
                    _time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


# ============================================================================
# SECTION 3: METACLASSES
# ============================================================================
#
# *** C++ Template Metaprogramming vs Python Metaclasses ***
#
# C++ template metaprogramming (TMP) operates at *compile time*:
#   - Templates are instantiated by the compiler; the generated code runs
#     at native speed with zero runtime overhead.
#   - Techniques like SFINAE, constexpr-if, and variadic templates let you
#     select implementations, unroll loops, and compute constants before
#     the program ever starts.
#   - Code generation is implicit -- the compiler produces specialised
#     classes/functions from the template patterns.
#
# Python metaclasses operate at *class-creation time* (which is runtime):
#   - ``type.__new__`` / ``type.__init__`` intercept ``class`` statement
#     processing and can modify, validate, or register the class.
#   - Because everything is runtime, metaclasses can inspect attributes,
#     call arbitrary Python code, and dynamically alter the class.
#   - The cost is paid at import / definition time, not per-instantiation,
#     so runtime performance of instances is unaffected.
#
# In summary:  C++ TMP = compile-time code generation; Python metaclass =
# runtime class construction customisation.  Both are "metaprogramming" in
# the sense that they program the programming language itself, but they
# target different phases of the program lifecycle.
# ============================================================================


class SingletonMeta(type):
    """
    Metaclass that makes every class using it a thread-safe singleton.

    ``__init__`` stores a per-class lock and ``None`` instance.
    ``__call__`` (triggered by ``cls(...)``) uses double-checked locking
    to create the instance at most once.
    """

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        cls.__instance: Optional[Any] = None  # type: ignore[attr-defined]
        cls.__lock: threading.RLock = threading.RLock()  # type: ignore[attr-defined]
        super().__init__(name, bases, namespace, **kwargs)

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__call__(*args, **kwargs)
        return cls.__instance


class ValidatedMeta(ABCMeta):
    """
    Metaclass that enforces that every concrete subclass defines a
    non-empty ``table_name`` class variable -- useful for an ORM base.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> ValidatedMeta:
        cls_obj = super().__new__(mcs, name, bases, namespace)
        # Skip the abstract base itself.
        if bases:
            table = namespace.get("table_name")
            if not table or not isinstance(table, str):
                raise TypeError(
                    f"{name} must define a non-empty 'table_name' string"
                )
        return cls_obj  # type: ignore[return-value]


# ============================================================================
# SECTION 4: DATACLASSES
# ============================================================================

@unique
class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __lt__(self, other: Priority) -> bool:
        return self.value < other.value


@dataclass(order=True)
class Task:
    """
    A frozen, orderable task dataclass.

    - ``order=True`` generates ``__lt__``, ``__le__``, etc. based on
      field declaration order (here: priority, then title).
    - ``__post_init__`` validates and transforms fields after the
      synthesised ``__init__``.
    """
    priority: Priority
    title: str
    tags: list[str] = field(default_factory=list)
    done: bool = False

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("Task title must not be empty")


@dataclass(frozen=True, slots=True)
class Point:
    """
    Immutable 3-D point using ``frozen=True`` (hashable, no mutation)
    and ``slots=True`` (lower memory footprint, faster attribute access).
    """
    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: Point) -> float:
        return ((self.x - other.x) ** 2 +
                (self.y - other.y) ** 2 +
                (self.z - other.z) ** 2) ** 0.5


# ============================================================================
# SECTION 5: ENTERPRISE PATTERNS -- ORM DESCRIPTOR FRAMEWORK
# ============================================================================
#
# This section models a mini-ORM (think SQLAlchemy Core or Django models)
# using Python descriptors and metaclasses.  Descriptors let us intercept
# attribute access on *instances*, while the metaclass wires up the
# descriptor-to-column mapping at *class-definition* time.
# ============================================================================


class Field:
    """
    A descriptor that represents a single database column.

    On ``__set__``, it stores the value in the instance's ``__dict__``
    under a mangled name (``_Field__<attr>``) so the descriptor's
    ``__get__`` is invoked on every read, enabling validation.
    """

    def __init__(
        self,
        column_type: str = "VARCHAR(256)",
        primary_key: bool = False,
        nullable: bool = True,
        default: Any = None,
    ) -> None:
        self.column_type = column_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.name: str = ""  # Set by ModelMeta.__new__

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self  # Access from the class itself returns the descriptor.
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        if value is None and not self.nullable:
            raise ValueError(f"{self.name} cannot be NULL")
        obj.__dict__[self.name] = value

    def __repr__(self) -> str:
        return (
            f"Field(name={self.name!r}, type={self.column_type!r}, "
            f"pk={self.primary_key})"
        )


class IntegerField(Field):
    """Column descriptor for integer values with type coercion."""

    def __init__(self, primary_key: bool = False, **kwargs: Any) -> None:
        super().__init__(column_type="INTEGER", primary_key=primary_key, **kwargs)

    def __set__(self, obj: Any, value: Any) -> None:
        if value is not None:
            value = int(value)
        super().__set__(obj, value)


class StringField(Field):
    """Column descriptor for text with optional max-length validation."""

    def __init__(self, max_length: int = 255, **kwargs: Any) -> None:
        self.max_length = max_length
        super().__init__(column_type=f"VARCHAR({max_length})", **kwargs)

    def __set__(self, obj: Any, value: Any) -> None:
        if value is not None and len(str(value)) > self.max_length:
            raise ValueError(
                f"{self.name} exceeds max length {self.max_length}"
            )
        super().__set__(obj, value)


class ModelMeta(ValidatedMeta):
    """
    Metaclass for ORM models.

    - Collects all ``Field`` descriptors and stores them in ``_fields``.
    - Derives ``table_name`` from the class name if not explicitly set.
    - Makes ``_fields`` available for ``CREATE TABLE`` generation.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> ModelMeta:
        # If the class itself didn't set table_name, derive from class name.
        if "table_name" not in namespace and bases:
            namespace["table_name"] = name.lower() + "s"

        cls_obj = super().__new__(mcs, name, bases, namespace)

        # Collect fields from this class only (not parents).
        _fields: dict[str, Field] = {}
        for key, val in namespace.items():
            if isinstance(val, Field):
                _fields[key] = val
        # Also inherit parent fields.
        for base in reversed(bases):
            if hasattr(base, "_fields"):
                _fields = {**getattr(base, "_fields"), **_fields}
        cls_obj._fields = _fields  # type: ignore[attr-defined]
        return cls_obj  # type: ignore[return-value]


class Model(metaclass=ModelMeta):
    """
    Abstract base for all ORM models.

    Provides:
      - ``create_table_sql()`` to emit a ``CREATE TABLE`` statement.
      - ``save()`` / ``to_dict()`` for persistence helpers.
      - ``__repr__`` that shows the table name and primary-key value.
    """

    table_name: ClassVar[str] = ""

    def __init__(self, **kwargs: Any) -> None:
        for name, field_obj in self._fields.items():
            value = kwargs.get(name, field_obj.default)
            setattr(self, name, value)

    @classmethod
    def create_table_sql(cls) -> str:
        """Return a ``CREATE TABLE`` DDL string for this model."""
        cols: list[str] = []
        pk_col: Optional[str] = None
        for name, f in cls._fields.items():
            nullable = "" if f.nullable else " NOT NULL"
            cols.append(f"    {name} {f.column_type}{nullable}")
            if f.primary_key:
                pk_col = name
        if pk_col:
            cols.append(f"    PRIMARY KEY ({pk_col})")
        col_str = ",\n".join(cols)
        return f"CREATE TABLE {cls.table_name} (\n{col_str}\n);"

    def to_dict(self) -> dict[str, Any]:
        """Serialise the model instance to a plain dictionary."""
        return {name: getattr(self, name) for name in self._fields}

    def __repr__(self) -> str:
        pk_field = next(
            (n for n, f in self._fields.items() if f.primary_key), "id"
        )
        pk_val = getattr(self, pk_field, "?")
        return f"<{type(self).__name__}({pk_field}={pk_val})>"


# --- Concrete models -------------------------------------------------------

class User(Model):
    table_name = "users"
    id = IntegerField(primary_key=True, nullable=False)
    username = StringField(max_length=64, nullable=False)
    email = StringField(max_length=128, nullable=False)


class Product(Model):
    table_name = "products"
    id = IntegerField(primary_key=True, nullable=False)
    name = StringField(max_length=256, nullable=False)
    price = Field(column_type="DECIMAL(10,2)", default=0.0)


# ============================================================================
# SECTION 6: ENTERPRISE PATTERNS -- VALIDATION FRAMEWORK
# ============================================================================

class Validator(Protocol):
    """Protocol that all validators must satisfy."""

    def validate(self, value: Any) -> bool: ...
    def error_message(self) -> str: ...


@runtime_checkable
class SupportsValidation(Protocol):
    """An object that exposes a ``validate`` method."""
    def validate(self) -> list[str]: ...


class RequiredValidator:
    """Rejects ``None`` and empty strings."""

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name

    def validate(self, value: Any) -> bool:
        return value is not None and str(value).strip() != ""

    def error_message(self) -> str:
        return f"{self.field_name} is required."


class RangeValidator:
    """Ensures a numeric value falls within [min_val, max_val]."""

    def __init__(
        self, field_name: str, min_val: float, max_val: float
    ) -> None:
        self.field_name = field_name
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value: Any) -> bool:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return False
        return self.min_val <= num <= self.max_val

    def error_message(self) -> str:
        return (
            f"{self.field_name} must be between "
            f"{self.min_val} and {self.max_val}."
        )


class PatternValidator:
    """Validates a string against a regex pattern."""

    def __init__(self, field_name: str, pattern: str) -> None:
        self.field_name = field_name
        self._regex = re.compile(pattern)

    def validate(self, value: Any) -> bool:
        return bool(self._regex.fullmatch(str(value)))

    def error_message(self) -> str:
        return f"{self.field_name} has an invalid format."


class ValidatedForm:
    """
    Base class for validated data forms.

    Subclasses declare class-level ``_validators`` mapping field names
    to lists of ``Validator`` instances.  Calling ``validate()`` returns
    a list of error messages (empty == valid).
    """

    _validators: ClassVar[dict[str, list[Validator]]] = {}

    def validate(self) -> list[str]:
        errors: list[str] = []
        for field_name, validators in self._validators.items():
            value = getattr(self, field_name, None)
            for v in validators:
                if not v.validate(value):
                    errors.append(v.error_message())
        return errors


# --- Concrete form ----------------------------------------------------------

class RegistrationForm(ValidatedForm):
    """
    Example registration form with cross-field validation logic.

    Demonstrates how the validation framework composes with descriptors
    and metaclasses into an enterprise-grade pattern.
    """

    _validators: ClassVar[dict[str, list[Validator]]] = {
        "username": [
            RequiredValidator("username"),
            PatternValidator("username", r"[A-Za-z][A-Za-z0-9_]{2,63}"),
        ],
        "email": [
            RequiredValidator("email"),
            PatternValidator(
                "email", r"[^@]+@[^@]+\.[^@]+"
            ),
        ],
        "age": [
            RequiredValidator("age"),
            RangeValidator("age", 0, 150),
        ],
    }

    def __init__(
        self, username: str, email: str, age: int | str
    ) -> None:
        self.username = username
        self.email = email
        self.age = age

    def __repr__(self) -> str:
        return (
            f"RegistrationForm(username={self.username!r}, "
            f"email={self.email!r}, age={self.age!r})"
        )


# ============================================================================
# SECTION 7: MIXIN DEMONSTRATION
# ============================================================================

class SetOnceMappingMixin:
    """
    Mixin that restricts a mapping so each key can only be set once.

    Demonstrates cooperative multiple inheritance and ``super()`` chaining.
    """
    __slots__ = ()

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self:
            raise KeyError(f"{key!r} already set")
        return super().__setitem__(key, value)  # type: ignore[misc]


class SetOnceDict(SetOnceMappingMixin, dict):  # type: ignore[type-arg]
    """A dictionary that rejects duplicate key assignments."""
    pass


# ============================================================================
# SECTION 8: WEAKREF AND CIRCULAR REFERENCE DEMO
# ============================================================================

class RefHolder:
    """
    Demonstrates ``weakref.proxy`` to avoid circular references.

    Instead of holding a strong reference that keeps the target alive,
    we store a proxy.  When the target is garbage-collected, accessing
    the proxy raises ``ReferenceError``.
    """

    def __init__(self, target: Any) -> None:
        self._ref = weakref.proxy(target)

    @property
    def target(self) -> Any:
        return self._ref


# ============================================================================
# MAIN GUARD -- All demonstrations
# ============================================================================

def _section(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def main() -> None:
    """Run all demonstrations."""

    # -- 1. Generators -------------------------------------------------------
    _section("1. Generators")

    print("  Fibonacci (generator function):")
    print(f"    {list(fib_generator(10))}")

    print("  Fibonacci (iterator class):")
    print(f"    {list(fibonacci_iterative_class(10))}")

    print("  yield from demo:")
    print(f"    {list(yield_from_demo())}")

    print("  Coroutine (streaming average via send):")
    gen = calc_avg()
    next(gen)  # Prime the coroutine.
    for val in [10, 20, 30, 40]:
        avg = gen.send(float(val))
        print(f"    Sent {val}, running avg = {avg:.2f}")

    print("  Generator pipeline (even squares, first 5):")
    stream_pipeline_demo()

    # -- 2. Decorators -------------------------------------------------------
    _section("2. Decorators")

    @record_time
    def sum_million() -> int:
        return sum(range(1_000_000))

    print("  Simple @record_time decorator:")
    sum_million()

    @parameterized_decorator(lambda name, t: print(f"    [{name}] {t:.6f}s"))
    def sum_half_million() -> int:
        return sum(range(500_000))

    print("  Parameterised decorator:")
    sum_half_million()

    @RecordTimeClass(lambda name, t: print(f"    <{name}> {t:.6f}s"))
    def sum_quarter_million() -> int:
        return sum(range(250_000))

    print("  Class-based decorator:")
    sum_quarter_million()

    @singleton
    class President:
        """Singleton -- only one instance ever exists."""
        def __init__(self) -> None:
            print("    President.__init__ called")

    print("  Singleton decorator:")
    p1 = President()
    p2 = President()
    print(f"    Same instance? {p1 is p2}")

    # -- 3. Metaclasses ------------------------------------------------------
    _section("3. Metaclasses")

    class App(metaclass=SingletonMeta):
        """App using SingletonMeta metaclass."""
        def __init__(self) -> None:
            print("    App.__init__ called")

    print("  SingletonMeta metaclass:")
    a1 = App()
    a2 = App()
    print(f"    Same instance? {a1 is a2}")

    # -- 4. Dataclasses ------------------------------------------------------
    _section("4. Dataclasses")

    t1 = Task(priority=Priority.HIGH, title="Fix critical bug", tags=["bugfix"])
    t2 = Task(priority=Priority.LOW, title="Write docs", tags=["docs"])
    t3 = Task(priority=Priority.HIGH, title="Fix critical bug", tags=["bugfix"])
    print(f"  Task t1: {t1}")
    print(f"  Task t2: {t2}")
    print(f"  t1 < t2 ? {t1 < t2}")
    print(f"  t1 == t3 ? {t1 == t3}")

    p1 = Point(1.0, 2.0, 3.0)
    p2 = Point(4.0, 6.0, 3.0)
    print(f"  Point p1: {p1}")
    print(f"  Point p2: {p2}")
    print(f"  Distance p1 -> p2: {p1.distance_to(p2):.4f}")
    print(f"  p1 is hashable: {hash(p1)}")

    # -- 5. ORM Descriptor Framework -----------------------------------------
    _section("5. ORM Descriptor Framework (metaclass + descriptors)")

    print("  User model fields:")
    for name, fld in User._fields.items():
        print(f"    {fld}")

    print("\n  User CREATE TABLE SQL:")
    print(User.create_table_sql())

    user = User(id=1, username="alice", email="alice@example.com")
    print(f"\n  User instance: {user}")
    print(f"  user.to_dict() = {user.to_dict()}")

    print("\n  StringField max_length validation:")
    try:
        User(id=2, username="b" * 100, email="ok@ok.com")
    except ValueError as exc:
        print(f"    Caught: {exc}")

    print("\n  Product CREATE TABLE SQL:")
    print(Product.create_table_sql())

    prod = Product(id=42, name="Widget", price=19.99)
    print(f"\n  Product instance: {prod}")
    print(f"  prod.to_dict() = {prod.to_dict()}")

    # -- 6. Validation Framework ---------------------------------------------
    _section("6. Validation Framework")

    form_ok = RegistrationForm(username="alice", email="alice@example.com", age=30)
    print(f"  Valid form: {form_ok}")
    errors = form_ok.validate()
    print(f"  Errors: {errors if errors else '(none)'}")

    form_bad = RegistrationForm(username="!!", email="not-an-email", age=200)
    print(f"\n  Invalid form: {form_bad}")
    errors = form_bad.validate()
    print(f"  Errors: {errors}")

    # -- 7. Mixin & SetOnceDict -----------------------------------------------
    _section("7. Mixin (SetOnceDict)")

    my_dict = SetOnceDict()
    my_dict["username"] = "jackfrued"
    print(f"  After first set: {my_dict}")
    try:
        my_dict["username"] = "hellokitty"
    except KeyError as exc:
        print(f"  Caught on duplicate key: {exc}")

    # -- 8. Weak references --------------------------------------------------
    _section("8. Weak References")

    class Node:
        def __init__(self, name: str) -> None:
            self.name = name
        def __repr__(self) -> str:
            return f"Node({self.name!r})"

    node = Node("A")
    holder = RefHolder(node)
    print(f"  Strong ref: {node}")
    print(f"  Weak proxy: {holder.target}")
    del node
    try:
        _ = holder.target
    except ReferenceError:
        print("  Node was garbage-collected; proxy is dead.")

    # -- 9. Show C++ comparison note ------------------------------------------
    _section("9. C++ Template Metaprogramming vs Python Metaclasses")
    print(
        "  See the module-level docstring and Section 3 comments for the\n"
        "  full comparison.  In short:\n"
        "    C++ TMP  = compile-time code generation (zero runtime cost)\n"
        "    Python   = runtime class-construction customisation (flexible)"
    )


if __name__ == "__main__":
    main()
