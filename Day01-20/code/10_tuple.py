"""
Python Tuples — Comprehensive Guide
=====================================
A tuple is an immutable, ordered collection of elements. Once created, its
contents cannot be added, removed, or modified. Tuples support indexing,
slicing, membership testing, concatenation, and comparison — the same
operations available on lists, but with the guarantee of immutability.

Topics covered
--------------
1. Tuple creation (literals, constructor, single-element trap)
2. Immutability and why it matters
3. Packing and unpacking (including star expressions)
4. Swapping variable values
5. Tuple vs list performance
6. Named tuples (collections.namedtuple / typing.NamedTuple)
7. Enterprise patterns: multi-value returns, coordinates, DB records
8. C++ comparison notes

Reference
---------
Source: Day01-20/10.常用数据结构之元组.md
"""

from collections import namedtuple
from typing import NamedTuple, Tuple
import timeit
import json


# ---------------------------------------------------------------------------
# 1. Tuple Creation
# ---------------------------------------------------------------------------

def demonstrate_creation():
    """Show the many ways to create tuples in Python."""
    print("=" * 60)
    print("1. TUPLE CREATION")
    print("=" * 60)

    # Literal syntax — the most common way
    t1 = (35, 12, 98)
    t2 = ("骆昊", 45, True, "四川成都")
    print(f"t1 = {t1}  type = {type(t1)}")
    print(f"t2 = {t2}  type = {type(t2)}")

    # The single-element trap: a trailing comma is REQUIRED
    not_a_tuple = ("hello")   # This is a str, not a tuple!
    is_a_tuple  = ("hello",)  # This IS a tuple
    print(f"\n('hello')  -> type = {type(not_a_tuple)}  # NOT a tuple!")
    print(f"('hello',) -> type = {type(is_a_tuple)}   # a 1-tuple")

    # Empty tuple
    empty = ()
    print(f"\n() -> type = {type(empty)}, len = {len(empty)}")

    # Using the tuple() constructor — converts any iterable
    from_list = tuple([10, 20, 30])
    from_range = tuple(range(1, 6))
    from_string = tuple("Python")
    print(f"\ntuple([10,20,30])   = {from_list}")
    print(f"tuple(range(1,6))   = {from_range}")
    print(f"tuple('Python')     = {from_string}")


# ---------------------------------------------------------------------------
# 2. Immutability
# ---------------------------------------------------------------------------

def demonstrate_immutability():
    """Prove that tuples are immutable and explain why that matters."""
    print("\n" + "=" * 60)
    print("2. IMMUTABILITY")
    print("=" * 60)

    t = (1, 2, 3)
    print(f"Original tuple: {t}")

    # Attempting modification raises TypeError
    try:
        t[0] = 99
    except TypeError as e:
        print(f"t[0] = 99  -> TypeError: {e}")

    try:
        t.append(4)
    except AttributeError as e:
        print(f"t.append(4) -> AttributeError: {e}")

    # Immutability means tuples are hashable (if all elements are hashable)
    # so they can be used as dictionary keys or set members.
    location_counts = {
        (40.7128, -74.0060): 150,   # New York
        (34.0522, -118.2437): 90,   # Los Angeles
    }
    print(f"\nTuples as dict keys: {location_counts}")

    # Immutability also makes tuples safe for concurrent / multithreaded code
    # without requiring locks — no thread can modify the contents.


# ---------------------------------------------------------------------------
# 3. Basic Operations (indexing, slicing, membership, concatenation, etc.)
# ---------------------------------------------------------------------------

def demonstrate_operations():
    """Indexing, slicing, membership, concatenation, comparison."""
    print("\n" + "=" * 60)
    print("3. BASIC OPERATIONS")
    print("=" * 60)

    t1 = (35, 12, 98)
    t2 = ("骆昊", 45, True, "四川成都")

    # Length
    print(f"len(t1) = {len(t1)}")
    print(f"len(t2) = {len(t2)}")

    # Indexing (supports negative indices)
    print(f"\nt1[0]  = {t1[0]}")
    print(f"t1[2]  = {t1[2]}")
    print(f"t2[-1] = {t2[-1]}")

    # Slicing
    print(f"\nt2[:2]  = {t2[:2]}")
    print(f"t2[::2] = {t2[::2]}")
    print(f"t2[::-1] = {t2[::-1]}")

    # Iteration
    print("\nIterating t1:", end=" ")
    for elem in t1:
        print(elem, end=" ")
    print()

    # Membership
    print(f"\n12 in t1          = {12 in t1}")
    print(f"99 in t1          = {99 in t1}")
    print(f"'Hao' not in t2   = {'Hao' not in t2}")

    # Concatenation
    t3 = t1 + t2
    print(f"\nt1 + t2 = {t3}")

    # Repetition
    print(f"t1 * 3  = {t1 * 3}")

    # Comparison (lexicographic)
    print(f"\nt1 == (35, 12, 98)   = {t1 == (35, 12, 98)}")
    print(f"t1 < (35, 11, 99)    = {t1 < (35, 11, 99)}")
    print(f"t1 <= (35, 12, 98)   = {t1 <= (35, 12, 98)}")


# ---------------------------------------------------------------------------
# 4. Packing and Unpacking
# ---------------------------------------------------------------------------

def demonstrate_packing_unpacking():
    """Tuple packing, unpacking, and the star (extended) unpacking."""
    print("\n" + "=" * 60)
    print("4. PACKING AND UNPACKING")
    print("=" * 60)

    # --- Packing: multiple values assigned to one variable ---
    a = 1, 10, 100
    print(f"Packing: a = 1, 10, 100  ->  type = {type(a)}, value = {a}")

    # --- Unpacking: one tuple assigned to multiple variables ---
    i, j, k = a
    print(f"Unpacking: i, j, k = a  ->  i={i}, j={j}, k={k}")

    # --- Mismatched count raises ValueError ---
    a = (1, 10, 100, 1000)
    print(f"\nTuple: {a}")
    try:
        x, y, z = a  # too many values
    except ValueError as e:
        print(f"3 variables for 4 elements -> ValueError: {e}")

    # --- Star (extended) unpacking ---
    print("\nStar unpacking examples:")
    first, *rest = a
    print(f"first, *rest  = a  ->  first={first}, rest={rest}")

    first, *middle, last = a
    print(f"first, *mid, last = a  ->  first={first}, mid={middle}, last={last}")

    *head, last = a
    print(f"*head, last   = a  ->  head={head}, last={last}")

    # Star variable is always a list (possibly empty)
    p, q, r, *s = a
    print(f"p, q, r, *s   = a  ->  p={p}, q={q}, r={r}, s={s}")

    p, q, r, s, *t = a
    print(f"p, q, r, s, *t= a  ->  p={p}, q={q}, r={r}, s={s}, t={t}")

    # Unpacking works on any sequence
    x, y, *z = range(1, 10)
    print(f"\nrange unpacking:  x={x}, y={y}, z={z}")

    x, y, z = [10, 20, 30]
    print(f"list unpacking:   x={x}, y={y}, z={z}")

    a, *b, c = "hello"
    print(f"string unpacking: a={a}, b={b}, c={c}")


# ---------------------------------------------------------------------------
# 5. Swapping Variables
# ---------------------------------------------------------------------------

def demonstrate_swap():
    """Python's elegant variable swap uses tuple packing/unpacking."""
    print("\n" + "=" * 60)
    print("5. SWAPPING VARIABLE VALUES")
    print("=" * 60)

    a, b = 10, 20
    print(f"Before swap: a={a}, b={b}")
    a, b = b, a
    print(f"After swap:  a={a}, b={b}")

    # Three-way rotation
    a, b, c = 1, 2, 3
    print(f"\nBefore rotation: a={a}, b={b}, c={c}")
    a, b, c = b, c, a
    print(f"After rotation:  a={a}, b={b}, c={c}")

    # Note: Python's bytecode has ROT_TWO and ROT_THREE instructions
    # for 2- and 3-variable swaps, making them very efficient.
    # For 4+ variables, packing/unpacking is used under the hood.


# ---------------------------------------------------------------------------
# 6. Tuple vs List Performance
# ---------------------------------------------------------------------------

def demonstrate_performance():
    """Compare creation time of tuples vs lists."""
    print("\n" + "=" * 60)
    print("6. TUPLE vs LIST PERFORMANCE")
    print("=" * 60)

    n = 5_000_000
    list_time = timeit.timeit("[1, 2, 3, 4, 5, 6, 7, 8, 9]", number=n)
    tuple_time = timeit.timeit("(1, 2, 3, 4, 5, 6, 7, 8, 9)", number=n)

    print(f"Creating [1..9] list  x{n}: {list_time:.3f} seconds")
    print(f"Creating (1..9) tuple x{n}: {tuple_time:.3f} seconds")
    print(f"Tuple is ~{list_time / tuple_time:.1f}x faster to create")

    # Conversion between the two types
    infos = ("骆昊", 45, True, "四川成都")
    print(f"\ntuple -> list:  {list(infos)}")

    fruits = ["apple", "banana", "orange"]
    print(f"list -> tuple:  {tuple(fruits)}")


# ---------------------------------------------------------------------------
# 7. Named Tuples
# ---------------------------------------------------------------------------

# Using collections.namedtuple (classic style)
Point = namedtuple("Point", ["x", "y"])
Employee = namedtuple("Employee", "name age department salary")

# Using typing.NamedTuple (modern, class-based style with type hints)
class Coordinate(NamedTuple):
    """A geographic coordinate with latitude and longitude."""
    latitude: float
    longitude: float
    label: str = ""


class DatabaseRecord(NamedTuple):
    """Represents a row from a database query."""
    id: int
    name: str
    email: str
    is_active: bool


def demonstrate_named_tuples():
    """Named tuples give tuple elements meaningful names."""
    print("\n" + "=" * 60)
    print("7. NAMED TUPLES")
    print("=" * 60)

    # --- collections.namedtuple ---
    p = Point(3, 4)
    print(f"Point: {p}")
    print(f"  p.x = {p.x}, p.y = {p.y}")
    print(f"  Distance from origin: {(p.x**2 + p.y**2) ** 0.5:.2f}")

    emp = Employee("Alice", 30, "Engineering", 95000)
    print(f"\nEmployee: {emp}")
    print(f"  {emp.name} works in {emp.department}, earning ${emp.salary:,.0f}")

    # Named tuples are still tuples — immutable, indexable, iterable
    print(f"\n  emp[0] = {emp[0]}  (access by index)")
    print(f"  emp.name = {emp.name}  (access by name)")

    # _replace() returns a NEW tuple with one field changed
    emp_after_raise = emp._replace(salary=105000)
    print(f"\n  After raise: {emp_after_raise}")
    print(f"  Original unchanged: {emp.salary}")

    # _asdict() converts to an OrderedDict / dict
    print(f"\n  As dict: {emp._asdict()}")

    # --- typing.NamedTuple (modern style) ---
    coord = Coordinate(40.7128, -74.0060, "New York")
    print(f"\nCoordinate: {coord}")
    print(f"  Location: {coord.label} ({coord.latitude}, {coord.longitude})")

    # With default values, the label is optional
    coord2 = Coordinate(51.5074, -0.1278)
    print(f"  Unlabeled: {coord2}")


# ---------------------------------------------------------------------------
# 8. Enterprise Examples
# ---------------------------------------------------------------------------

def get_user_statistics(user_id: int) -> Tuple[str, int, float]:
    """
    Enterprise pattern: function returning multiple values via a tuple.

    In real applications this might query a database, but here we simulate it.
    Returns (username, login_count, avg_session_minutes).
    """
    # Simulated database lookup
    mock_data = {
        1: ("alice_w", 342, 45.6),
        2: ("bob_dev", 189, 32.1),
        3: ("carol_m", 507, 61.3),
    }
    return mock_data.get(user_id, ("unknown", 0, 0.0))


def process_sensor_reading(raw: tuple) -> dict:
    """
    Enterprise pattern: processing structured records from sensors.

    Input tuple format: (sensor_id, timestamp, temperature, humidity, pressure)
    Returns a formatted dictionary.
    """
    sensor_id, timestamp, temp, humidity, pressure = raw  # unpacking
    return {
        "sensor": sensor_id,
        "time": timestamp,
        "temperature_f": temp,
        "temperature_c": round((temp - 32) * 5 / 9, 2),
        "humidity_pct": humidity,
        "pressure_hpa": round(pressure * 33.8639, 2),
    }


def coordinate_transform(point: Tuple[float, float], dx: float, dy: float) -> Tuple[float, float]:
    """
    Enterprise pattern: coordinate system transformation.

    Translates a 2D point by (dx, dy). Returns a new tuple (tuples are
    immutable so we create a new one rather than modifying the input).
    """
    x, y = point
    return (x + dx, y + dy)


def demonstrate_enterprise_patterns():
    """Real-world patterns where tuples shine."""
    print("\n" + "=" * 60)
    print("8. ENTERPRISE PATTERNS")
    print("=" * 60)

    # --- Pattern A: Functions returning multiple values ---
    print("\n[Pattern A] Function returning multiple values")
    for uid in [1, 2, 3]:
        name, logins, avg_session = get_user_statistics(uid)
        print(f"  User {name}: {logins} logins, avg session {avg_session} min")

    # --- Pattern B: Database-like records ---
    print("\n[Pattern B] Database records as named tuples")
    records = [
        DatabaseRecord(1, "Alice", "alice@example.com", True),
        DatabaseRecord(2, "Bob", "bob@example.com", False),
        DatabaseRecord(3, "Carol", "carol@example.com", True),
    ]
    active_users = [r for r in records if r.is_active]
    for r in active_users:
        print(f"  Active: {r.name} <{r.email}>")

    # --- Pattern C: Sensor data processing ---
    print("\n[Pattern C] Sensor data processing")
    raw_readings = [
        ("SENS-001", "2026-01-15 08:00", 72.5, 45.2, 29.92),
        ("SENS-002", "2026-01-15 08:00", 68.1, 52.8, 29.88),
    ]
    for reading in raw_readings:
        result = process_sensor_reading(reading)
        print(f"  {result['sensor']}: {result['temperature_f']}F "
              f"({result['temperature_c']}C), humidity {result['humidity_pct']}%")

    # --- Pattern D: Coordinate systems ---
    print("\n[Pattern D] Coordinate system transformations")
    origin = (0.0, 0.0)
    waypoints = [(1.0, 2.0), (3.5, 4.5), (6.0, 1.0)]

    offset_x, offset_y = 100.0, 200.0
    print(f"  Applying offset ({offset_x}, {offset_y}):")
    for wp in waypoints:
        transformed = coordinate_transform(wp, offset_x, offset_y)
        print(f"    {wp} -> {transformed}")

    # Using named tuples for geographic coordinates
    cities = [
        Coordinate(40.7128, -74.0060, "New York"),
        Coordinate(34.0522, -118.2437, "Los Angeles"),
        Coordinate(41.8781, -87.6298, "Chicago"),
    ]
    print(f"\n  City coordinates:")
    for c in cities:
        print(f"    {c.label}: ({c.latitude}, {c.longitude})")


# ---------------------------------------------------------------------------
# 9. C++ Comparison Notes
# ---------------------------------------------------------------------------

def print_cpp_comparison():
    """
    Print a structured comparison of Python tuples vs C++ equivalents.

    Python tuple vs C++ std::tuple
    ------------------------------
    - Python tuples are heterogeneous (like C++ std::tuple) but far more
      ergonomic: no template parameter lists, no std::get<N>, no
      std::make_tuple needed.
    - Python tuples are immutable; C++ std::tuple elements are mutable
      by default (unless the element type is const).
    - Python tuples support len(), indexing, slicing, iteration directly.
      C++ std::tuple requires std::tuple_size, std::get, and structured
      bindings for similar functionality.
    - Python tuples are hashable (if elements are hashable); C++ std::tuple
      has no built-in hash unless you provide one.

    Python tuple unpacking vs C++ structured bindings (C++17)
    ---------------------------------------------------------
    - Python:  a, b, c = my_tuple
    - C++17:   auto [a, b, c] = my_tuple;
    - Python's star unpacking (*rest) has no direct C++ equivalent.
    - Python unpacking works on any iterable (list, string, range, ...);
      C++17 structured bindings work on tuple-like types, arrays, and
      structs with public members.
    - Both languages evaluate the right-hand side once, then distribute
      values to the left-hand side variables.
    """
    print("\n" + "=" * 60)
    print("9. C++ COMPARISON")
    print("=" * 60)

    cpp_notes = """
    +-----------------------------------+------------------------------------+
    |        Python tuple               |     C++ std::tuple (C++11)         |
    +-----------------------------------+------------------------------------+
    | t = (1, "hi", 3.14)              | auto t = std::make_tuple(          |
    |                                   |     1, "hi", 3.14);               |
    +-----------------------------------+------------------------------------+
    | x = t[0]                          | auto x = std::get<0>(t);          |
    |                                   | // index must be compile-time     |
    +-----------------------------------+------------------------------------+
    | len(t)                            | std::tuple_size<decltype(t)>::value|
    +-----------------------------------+------------------------------------+
    | for item in t: ...                | std::apply([](auto&... args){     |
    |                                   |   ((std::cout << args), ...);     |
    |                                   | }, t);                            |
    +-----------------------------------+------------------------------------+
    | t is immutable (can't modify)     | Elements are mutable by default   |
    +-----------------------------------+------------------------------------+
    | Usable as dict key / set member   | No built-in hash support          |
    +-----------------------------------+------------------------------------+

    +-----------------------------------+------------------------------------+
    |  Python unpacking                 |  C++17 Structured Bindings         |
    +-----------------------------------+------------------------------------+
    | a, b, c = (1, 2, 3)              | auto [a, b, c] =                  |
    |                                   |     std::make_tuple(1, 2, 3);    |
    +-----------------------------------+------------------------------------+
    | first, *rest = seq               | No direct equivalent              |
    | // rest is a list                 | // would need manual decomposition|
    +-----------------------------------+------------------------------------+
    | Works on any sequence type        | Works on tuple-like, arrays,      |
    | (list, str, range, ...)           | and aggregates (struct w/ public  |
    |                                   | members)                          |
    +-----------------------------------+------------------------------------+
    | a, b = b, a  (swap)              | auto [a, b] = std::tie(b, a);    |
    | // uses ROT_TWO bytecode          | // or std::swap(a, b);           |
    +-----------------------------------+------------------------------------+
    """
    print(cpp_notes)

    # Demonstrate the Python side
    print("Python example:")
    t = (1, "hello", 3.14, True)
    a, b, *rest = t
    print(f"  Unpacking (1, 'hello', 3.14, True):")
    print(f"    a = {a}, b = {b}, rest = {rest}")

    # Swap demo
    x, y = 10, 20
    print(f"\n  Swap: x={x}, y={y} -> ", end="")
    x, y = y, x
    print(f"x={x}, y={y}")

    print("\n  Equivalent C++17 code would be:")
    print('    auto [a, b, c, d] = std::make_tuple(1, "hello", 3.14, true);')
    print("    // No star-unpacking; must know the exact number of elements")
    print('    auto [x2, y2] = std::make_tuple(y, x);  // or std::swap(x, y)')


# ---------------------------------------------------------------------------
# 10. Useful Tuple Methods and Patterns
# ---------------------------------------------------------------------------

def demonstrate_advanced_patterns():
    """Additional tuple patterns useful in real code."""
    print("\n" + "=" * 60)
    print("10. ADVANCED PATTERNS")
    print("=" * 60)

    # Counting and finding
    data = (1, 2, 3, 2, 4, 2, 5)
    print(f"Data: {data}")
    print(f"  data.count(2) = {data.count(2)}")
    print(f"  data.index(4) = {data.index(4)}")

    # Nested tuples (tuples can contain other tuples / lists / any object)
    matrix = (
        (1, 2, 3),
        (4, 5, 6),
        (7, 8, 9),
    )
    print(f"\nNested tuple (matrix): {matrix}")
    print(f"  matrix[1][2] = {matrix[1][2]}")  # row 1, col 2 -> 6

    # Tuples as lightweight "structs" for grouping related data
    HTTP_STATUS = {
        (200,): "OK",
        (301,): "Moved Permanently",
        (404,): "Not Found",
        (500,): "Internal Server Error",
    }
    # More natural: use a single int as key, but tuples work for composite keys
    CACHE_KEY = ("user", 42, "profile")
    cache = {CACHE_KEY: {"name": "Alice", "age": 30}}
    print(f"\nCache lookup {CACHE_KEY}: {cache[CACHE_KEY]}")

    # zip with tuples for parallel iteration
    names = ("Alice", "Bob", "Carol")
    scores = (95, 87, 92)
    print("\nParallel iteration with zip:")
    for name, score in zip(names, scores):
        print(f"  {name}: {score}")

    # Unpacking in function calls (* operator)
    point = (3, 4)
    print(f"\nPoint: {point}")
    print(f"  math.dist from origin: {(*point, 0, 0)}")  # extends tuple
    # Use * to unpack as function arguments
    print(f"  max(*point) = {max(*point)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demonstrate_creation()
    demonstrate_immutability()
    demonstrate_operations()
    demonstrate_packing_unpacking()
    demonstrate_swap()
    demonstrate_performance()
    demonstrate_named_tuples()
    demonstrate_enterprise_patterns()
    print_cpp_comparison()
    demonstrate_advanced_patterns()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
    Tuples are immutable, ordered sequences. Key takeaways:

    - Creation: (1, 2, 3) or tuple(iterable).
      Single-element tuples MUST have a trailing comma: (42,).

    - Immutability: no append/remove/modify after creation.
      Tuples are hashable (when elements are), safe as dict keys.

    - Packing/Unpacking:
        a, b, c = (1, 2, 3)          # unpacking
        x = 1, 2, 3                   # packing
        first, *rest = seq            # star unpacking (rest is a list)

    - Swap:  a, b = b, a  (efficient bytecode-level operation)

    - Named tuples: give fields names for readability.
        Point = namedtuple("Point", ["x", "y"])

    - Performance: tuples are faster to create than lists (~8x in tests).

    - C++ comparison:
        Python tuple       <->  C++ std::tuple
        Python unpacking   <->  C++17 structured bindings (auto [a, b] = ...)
        Python *rest       <->  No direct C++ equivalent
    """)
