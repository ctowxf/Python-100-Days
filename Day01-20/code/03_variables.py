"""
Python Variables and Types - Comprehensive Guide
=================================================

Covers: variable types (int, float, str, bool), type conversion, type checking,
        C++ comparisons, type hints (Python 3.10+), and enterprise patterns.

Based on: Day01-20/03.Python语言中的变量.md
Version: 2.0
"""


# =============================================================================
# Section 1: Variable Declaration - Python vs C++
# =============================================================================
# C++ requires explicit type declaration:
#   int x = 10;
#   float pi = 3.14f;
#   std::string name = "Alice";
#   bool flag = true;
#
# Python uses dynamic typing - no type declaration needed:
#   x = 10
#   pi = 3.14
#   name = "Alice"
#   flag = True
# =============================================================================


def demonstrate_variable_declaration():
    """Show Python's dynamic typing vs C++'s static typing."""
    print("=" * 60)
    print("Section 1: Variable Declaration")
    print("=" * 60)

    # Python: no type annotation required (dynamic typing)
    x = 10          # C++ equivalent: int x = 10;
    pi = 3.14       # C++ equivalent: double pi = 3.14;
    name = "Alice"  # C++ equivalent: std::string name = "Alice";
    flag = True     # C++ equivalent: bool flag = true;

    print(f"x = {x}, type = {type(x)}")
    print(f"pi = {pi}, type = {type(pi)}")
    print(f"name = {name}, type = {type(name)}")
    print(f"flag = {flag}, type = {type(flag)}")

    # Dynamic typing: same variable can change type
    # In C++, this would cause a compile error
    x = "now I'm a string"
    print(f"\nAfter reassignment: x = {x!r}, type = {type(x)}")


# =============================================================================
# Section 2: Python Built-in Types
# =============================================================================


def demonstrate_integer_types():
    """Integer types: Python supports arbitrary precision integers."""
    print("\n" + "=" * 60)
    print("Section 2a: Integer Types (int)")
    print("=" * 60)

    # Decimal
    decimal_val = 100
    # Binary
    binary_val = 0b100      # 4 in decimal
    # Octal
    octal_val = 0o100       # 64 in decimal
    # Hexadecimal
    hex_val = 0x100         # 256 in decimal

    print(f"Decimal 100     = {decimal_val}")
    print(f"Binary 0b100    = {binary_val}")
    print(f"Octal 0o100     = {octal_val}")
    print(f"Hex 0x100       = {hex_val}")

    # Python handles arbitrarily large integers
    # C++ would overflow with long long
    huge = 2 ** 100
    print(f"\n2^100 = {huge}")
    print(f"Digits in 2^100 = {len(str(huge))}")


def demonstrate_float_types():
    """Float types: scientific notation and precision."""
    print("\n" + "=" * 60)
    print("Section 2b: Float Types (float)")
    print("=" * 60)

    math_notation = 123.456
    scientific = 1.23456e2  # 1.23456 * 10^2

    print(f"Math notation: 123.456  = {math_notation}")
    print(f"Scientific: 1.23456e2   = {scientific}")
    print(f"Are they equal? {math_notation == scientific}")

    # Float precision caveat
    result = 0.1 + 0.2
    print(f"\n0.1 + 0.2 = {result}")
    print(f"0.1 + 0.2 == 0.3? {result == 0.3}")
    print(f"Use math.isclose(): {__import__('math').isclose(result, 0.3)}")


def demonstrate_string_types():
    """String types: creation and basic operations."""
    print("\n" + "=" * 60)
    print("Section 2c: String Types (str)")
    print("=" * 60)

    single_quoted = 'hello, world'
    double_quoted = "hello, world"
    multiline = """This is
a multiline string"""

    print(f"Single quoted: {single_quoted!r}")
    print(f"Double quoted: {double_quoted!r}")
    print(f"Multiline:\n{multiline}")

    # String operations
    name = "Python"
    print(f"\nlen('{name}') = {len(name)}")
    print(f"'{name}' * 3 = {name * 3}")
    print(f"'{name}'[0:3] = {name[0:3]}")


def demonstrate_bool_types():
    """Boolean types: True and False."""
    print("\n" + "=" * 60)
    print("Section 2d: Boolean Types (bool)")
    print("=" * 60)

    is_active = True
    is_deleted = False

    print(f"is_active  = {is_active}  (type: {type(is_active)})")
    print(f"is_deleted = {is_deleted} (type: {type(is_deleted)})")

    # bool is a subclass of int in Python
    print(f"\nTrue + True = {True + True}")    # 2
    print(f"True * 10  = {True * 10}")         # 10
    print(f"False + 5  = {False + 5}")         # 5
    print(f"isinstance(True, int) = {isinstance(True, int)}")


# =============================================================================
# Section 3: Type Checking - type() vs C++ typeid
# =============================================================================
# C++ uses typeid for runtime type identification:
#   #include <typeinfo>
#   int x = 10;
#   std::cout << typeid(x).name();  // Output: "i" (compiler-specific)
#
# Python uses type() which returns the actual class:
#   x = 10
#   print(type(x))  # Output: <class 'int'>
# =============================================================================


def demonstrate_type_checking():
    """Type checking with type() and isinstance()."""
    print("\n" + "=" * 60)
    print("Section 3: Type Checking")
    print("=" * 60)

    values: list[int | float | str | bool] = [100, 123.45, "hello", True]

    for val in values:
        print(f"value={val!r:>10}, type()={type(val).__name__:<6}, "
              f"isinstance int={isinstance(val, int):<5}, "
              f"isinstance str={isinstance(val, str)}")

    # type() vs isinstance() difference with inheritance
    print(f"\n--- type() vs isinstance() with bool/int ---")
    print(f"type(True) is bool:        {type(True) is bool}")
    print(f"isinstance(True, bool):    {isinstance(True, bool)}")
    print(f"isinstance(True, int):     {isinstance(True, int)}")  # True: bool inherits int


# =============================================================================
# Section 4: Type Conversion
# =============================================================================


def demonstrate_type_conversion():
    """Type conversion using built-in functions."""
    print("\n" + "=" * 60)
    print("Section 4: Type Conversion")
    print("=" * 60)

    a = 100
    b = 123.45
    c = "123"
    d = "100"
    e = "123.45"
    f = "hello, world"
    g = True

    # int -> float
    print(f"float({a})         = {float(a)}")          # 100.0

    # float -> int (truncates, does not round)
    print(f"int({b})           = {int(b)}")            # 123

    # str -> int with base
    print(f"int('{c}')         = {int(c)}")            # 123
    print(f"int('{c}', base=16) = {int(c, base=16)}")  # 291
    print(f"int('{d}', base=2)  = {int(d, base=2)}")   # 4

    # str -> float
    print(f"float('{e}')       = {float(e)}")          # 123.45

    # str -> bool (non-empty = True)
    print(f"bool('{f}') = {bool(f)}")                  # True
    print(f"bool('')    = {bool('')}")                  # False

    # bool -> int
    print(f"int(True)  = {int(True)}")                 # 1
    print(f"int(False) = {int(False)}")                # 0

    # chr / ord
    print(f"\nchr(100)  = {chr(100)}")                 # 'd'
    print(f"ord('d')  = {ord('d')}")                   # 100

    # Hex, octal, binary string conversions
    print(f"\nint('ff', 16) = {int('ff', 16)}")        # 255
    print(f"hex(255)       = {hex(255)}")               # '0xff'
    print(f"oct(64)        = {oct(64)}")                # '0o100'
    print(f"bin(4)         = {bin(4)}")                 # '0b100'


# =============================================================================
# Section 5: Type Hints (Python 3.10+ with | syntax)
# =============================================================================


def demonstrate_type_hints():
    """Modern type hints using Python 3.10+ union syntax."""
    print("\n" + "=" * 60)
    print("Section 5: Type Hints (Python 3.10+)")
    print("=" * 60)

    # Basic type hints
    name: str = "Alice"
    age: int = 30
    height: float = 1.75
    is_student: bool = False

    # Union types using | (Python 3.10+)
    # Old way: Union[int, str] from typing module
    # New way: int | str
    user_id: int | str = "U-12345"
    print(f"user_id = {user_id!r} (type: {type(user_id).__name__})")
    user_id = 12345
    print(f"user_id = {user_id!r} (type: {type(user_id).__name__})")

    # Optional types: int | None is equivalent to Optional[int]
    result: int | None = None
    print(f"result = {result} (type: {type(result).__name__})")

    # Generic types
    scores: list[float] = [98.5, 87.3, 92.1]
    config: dict[str, int | str] = {"port": 8080, "host": "localhost"}
    print(f"scores = {scores}")
    print(f"config = {config}")


# =============================================================================
# Section 6: Enterprise Patterns
# =============================================================================


def parse_config(raw: dict[str, str]) -> dict[str, int | str | bool]:
    """
    Enterprise pattern: Config parsing with type coercion.

    Parses string-typed config values into their proper Python types.
    Common in web frameworks (Django settings, Flask config, etc.)
    """
    type_map: dict[str, type] = {
        "port": int,
        "debug": bool,
        "max_connections": int,
    }

    parsed: dict[str, int | str | bool] = {}

    for key, value in raw.items():
        if key in type_map:
            target_type = type_map[key]
            if target_type is bool:
                # Handle string booleans from config files
                parsed[key] = value.lower() in ("true", "1", "yes", "on")
            else:
                parsed[key] = target_type(value)
        else:
            parsed[key] = value

    return parsed


def validate_input(data: dict[str, str]) -> dict[str, int | str]:
    """
    Enterprise pattern: Input validation with type checking.

    Validates and converts user input, raising clear errors on failure.
    Common in API endpoints and form processing.
    """
    schema: dict[str, tuple[type, bool]] = {
        "age": (int, True),         # required
        "name": (str, True),        # required
        "score": (float, False),    # optional
    }

    validated: dict[str, int | str | float] = {}

    for field, (expected_type, required) in schema.items():
        raw_value = data.get(field)

        if raw_value is None:
            if required:
                raise ValueError(f"Missing required field: {field}")
            continue

        try:
            if expected_type is bool:
                validated[field] = raw_value.lower() in ("true", "1", "yes")
            else:
                validated[field] = expected_type(raw_value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid type for '{field}': expected {expected_type.__name__}, "
                f"got {raw_value!r}"
            ) from e

    return validated


def safe_type_convert(value: str, target: type, default=None) -> int | float | str | None:
    """
    Enterprise pattern: Safe type coercion with fallback.

    Converts a string value to the target type, returning default on failure.
    Useful for parsing environment variables, CLI args, database rows, etc.
    """
    converters: dict[type, callable] = {
        int: int,
        float: float,
        str: str,
        bool: lambda v: v.lower() in ("true", "1", "yes", "on"),
    }

    converter = converters.get(target)
    if converter is None:
        return default

    try:
        return converter(value)
    except (ValueError, TypeError):
        return default


def demonstrate_enterprise_patterns():
    """Show enterprise-grade type handling patterns."""
    print("\n" + "=" * 60)
    print("Section 6: Enterprise Patterns")
    print("=" * 60)

    # Pattern 1: Config parsing
    print("\n--- Config Parsing ---")
    raw_config = {
        "host": "localhost",
        "port": "8080",
        "debug": "true",
        "max_connections": "100",
    }
    parsed = parse_config(raw_config)
    print(f"Raw config:    {raw_config}")
    print(f"Parsed config: {parsed}")
    for key, val in parsed.items():
        print(f"  {key}: {val!r} ({type(val).__name__})")

    # Pattern 2: Input validation
    print("\n--- Input Validation ---")
    valid_input = {"name": "Alice", "age": "30", "score": "95.5"}
    invalid_input = {"name": "Bob", "age": "not_a_number"}

    try:
        result = validate_input(valid_input)
        print(f"Valid input result: {result}")
    except ValueError as e:
        print(f"Validation error: {e}")

    try:
        validate_input(invalid_input)
    except ValueError as e:
        print(f"Expected error for invalid input: {e}")

    # Pattern 3: Safe type coercion
    print("\n--- Safe Type Coercion ---")
    test_cases = [
        ("42", int, None),
        ("3.14", float, 0.0),
        ("not_a_number", int, -1),
        ("true", bool, False),
        ("", int, 0),
    ]
    for value, target, default in test_cases:
        result = safe_type_convert(value, target, default)
        print(f"  safe_type_convert({value!r}, {target.__name__}, "
              f"default={default}) = {result!r}")


# =============================================================================
# Section 7: Variable Naming Conventions
# =============================================================================


def demonstrate_naming_conventions():
    """Python variable naming rules and conventions."""
    print("\n" + "=" * 60)
    print("Section 7: Variable Naming Conventions")
    print("=" * 60)

    # Good: lowercase with underscores (PEP 8)
    user_name = "Alice"
    max_retry_count = 3
    is_valid = True

    # Convention: single underscore prefix for "protected"
    _internal_cache = {}

    # Convention: double underscore prefix for "private" (name mangling)
    # class MyClass:
    #     def __init__(self):
    #         self.__secret = 42

    # Convention: UPPER_CASE for constants
    MAX_CONNECTIONS = 100
    DEFAULT_TIMEOUT = 30
    API_BASE_URL = "https://api.example.com"

    print("Naming examples:")
    print(f"  user_name = {user_name!r}")
    print(f"  max_retry_count = {max_retry_count}")
    print(f"  is_valid = {is_valid}")
    print(f"  MAX_CONNECTIONS = {MAX_CONNECTIONS}")
    print(f"  API_BASE_URL = {API_BASE_URL}")


# =============================================================================
# Main Entry Point
# =============================================================================


if __name__ == "__main__":
    demonstrate_variable_declaration()
    demonstrate_integer_types()
    demonstrate_float_types()
    demonstrate_string_types()
    demonstrate_bool_types()
    demonstrate_type_checking()
    demonstrate_type_conversion()
    demonstrate_type_hints()
    demonstrate_enterprise_patterns()
    demonstrate_naming_conventions()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("""
Key takeaways:
  1. Python uses dynamic typing - no explicit type declaration needed
  2. Core types: int, float, str, bool
  3. type() returns the exact class; isinstance() respects inheritance
  4. Built-in converters: int(), float(), str(), bool(), chr(), ord()
  5. Python 3.10+ type hints use | instead of Union[]
  6. Enterprise code benefits from safe type coercion and validation
""")
