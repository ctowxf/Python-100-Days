"""
Branch and Loop Structures - Comprehensive Practice
=====================================================
Covers all examples from the tutorial plus enterprise-grade patterns:
  1. Prime numbers (100以内素数)
  2. Fibonacci sequence (斐波那契数列)
  3. Narcissistic numbers (水仙花数)
  4. Number reversal (正整数反转)
  5. Hundred Chickens problem (百钱百鸡)
  6. CRAPS gambling game (CRAPS赌博游戏)
  7. Pattern printing (图案打印)
  8. Enterprise: Input validation loop
  9. Enterprise: Menu-driven CLI
 10. Enterprise: Data processing pipeline

Version: 2.0
"""

import random


# ===========================================================================
# Example 1: Prime Numbers within 100 (100以内的素数)
# ===========================================================================
#
# C++ equivalent:
#   for (int num = 2; num < 100; ++num) {
#       bool is_prime = true;
#       for (int i = 2; i <= static_cast<int>(sqrt(num)); ++i) {
#           if (num % i == 0) { is_prime = false; break; }
#       }
#       if (is_prime) std::cout << num << "\n";
#   }
#

def primes_below(limit: int) -> list[int]:
    """Return all prime numbers below *limit* using trial division.

    Time complexity : O(n * sqrt(n))
    Space complexity: O(n) for the result list.
    """
    result: list[int] = []
    for num in range(2, limit):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            result.append(num)
    return result


def demo_primes() -> None:
    """Print all primes below 100."""
    print("=" * 50)
    print("Example 1: Prime Numbers Below 100")
    print("=" * 50)
    primes = primes_below(100)
    print(f"Found {len(primes)} primes: {primes}\n")


# ===========================================================================
# Example 2: Fibonacci Sequence (斐波那契数列)
# ===========================================================================
#
# C++ equivalent:
#   int a = 0, b = 1;
#   for (int i = 0; i < 20; ++i) {
#       int temp = b;
#       b = a + b;
#       a = temp;
#       std::cout << a << "\n";
#   }
#

def fibonacci(n: int) -> list[int]:
    """Return the first *n* Fibonacci numbers.

    Uses Python's simultaneous assignment (tuple swap):
        a, b = b, a + b
    which avoids the need for a temporary variable.
    """
    seq: list[int] = []
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
        seq.append(a)
    return seq


def demo_fibonacci() -> None:
    """Print the first 20 Fibonacci numbers."""
    print("=" * 50)
    print("Example 2: Fibonacci Sequence (first 20)")
    print("=" * 50)
    seq = fibonacci(20)
    for idx, val in enumerate(seq, 1):
        print(f"  F({idx:>2}) = {val}")
    print()


# ===========================================================================
# Example 3: Narcissistic / Armstrong Numbers (水仙花数)
# ===========================================================================
#
# A narcissistic number of N digits equals the sum of each digit raised to
# the N-th power.  For 3-digit numbers: 153 = 1^3 + 5^3 + 3^3.
#
# C++ equivalent:
#   for (int num = 100; num < 1000; ++num) {
#       int low  = num % 10;
#       int mid  = num / 10 % 10;
#       int high = num / 100;
#       if (num == low*low*low + mid*mid*mid + high*high*high)
#           std::cout << num << "\n";
#   }
#

def is_narcissistic(num: int) -> bool:
    """Check whether *num* is a narcissistic (Armstrong) number."""
    digits = [int(d) for d in str(num)]
    n = len(digits)
    return num == sum(d ** n for d in digits)


def narcissistic_in_range(lo: int, hi: int) -> list[int]:
    """Find all narcissistic numbers in [lo, hi)."""
    return [n for n in range(lo, hi) if is_narcissistic(n)]


def demo_narcissistic() -> None:
    """Print narcissistic numbers in 100-999 and a broader scan."""
    print("=" * 50)
    print("Example 3: Narcissistic Numbers (水仙花数)")
    print("=" * 50)
    # 3-digit narcissistic numbers (classic textbook example)
    three_digit = narcissistic_in_range(100, 1000)
    print(f"  3-digit: {three_digit}")
    # All narcissistic numbers up to 6 digits (bonus)
    all_narc = [n for n in range(1, 1_000_000) if is_narcissistic(n)]
    print(f"  Up to 6 digits: {all_narc}\n")


# ===========================================================================
# Example 3b: Integer Reversal (正整数反转)
# ===========================================================================
#
# C++ equivalent:
#   int reversed_num = 0;
#   while (num > 0) {
#       reversed_num = reversed_num * 10 + num % 10;
#       num /= 10;
#   }
#

def reverse_integer(num: int) -> int:
    """Reverse a positive integer using // and % operators."""
    reversed_num = 0
    while num > 0:
        reversed_num = reversed_num * 10 + num % 10
        num //= 10
    return reversed_num


def demo_reverse() -> None:
    """Demo integer reversal with several test values."""
    print("=" * 50)
    print("Example 3b: Integer Reversal (正整数反转)")
    print("=" * 50)
    test_values = [12389, 100, 7, 987654321]
    for val in test_values:
        print(f"  reverse({val}) = {reverse_integer(val)}")
    print()


# ===========================================================================
# Example 4: Hundred Chickens Problem (百钱百鸡)
# ===========================================================================
#
# Ancient Chinese math puzzle:
#   - Rooster: 5 yuan each
#   - Hen:     3 yuan each
#   - Chickens: 1 yuan for 3
#   Spend exactly 100 yuan to buy exactly 100 chickens.
#
# Version 1.0 uses triple-nested loops (brute-force / exhaustive search).
# Version 1.1 eliminates the innermost loop by computing z = 100 - x - y.
#
# C++ equivalent (optimized):
#   for (int x = 0; x <= 20; ++x)
#       for (int y = 0; y <= 33; ++y) {
#           int z = 100 - x - y;
#           if (z % 3 == 0 && 5*x + 3*y + z/3 == 100)
#               printf("Rooster: %d, Hen: %d, Chick: %d\n", x, y, z);
#       }
#


def hundred_chickens_v1() -> list[tuple[int, int, int]]:
    """Brute-force with 3 nested loops (version 1.0)."""
    results: list[tuple[int, int, int]] = []
    for x in range(0, 21):           # roosters:  0..20
        for y in range(0, 34):       # hens:      0..33
            for z in range(0, 100, 3):  # chicks: multiples of 3
                if x + y + z == 100 and 5 * x + 3 * y + z // 3 == 100:
                    results.append((x, y, z))
    return results


def hundred_chickens_v2() -> list[tuple[int, int, int]]:
    """Optimized with 2 nested loops (version 1.1)."""
    results: list[tuple[int, int, int]] = []
    for x in range(0, 21):
        for y in range(0, 34):
            z = 100 - x - y
            if z % 3 == 0 and 5 * x + 3 * y + z // 3 == 100:
                results.append((x, y, z))
    return results


def demo_hundred_chickens() -> None:
    """Compare brute-force vs optimized solutions."""
    print("=" * 50)
    print("Example 4: Hundred Chickens Problem (百钱百鸡)")
    print("=" * 50)
    print("  Brute-force (v1.0, 3 nested loops):")
    for rooster, hen, chick in hundred_chickens_v1():
        print(f"    Rooster={rooster}, Hen={hen}, Chick={chick}")
    print("  Optimized (v1.1, 2 nested loops):")
    for rooster, hen, chick in hundred_chickens_v2():
        print(f"    Rooster={rooster}, Hen={hen}, Chick={chick}")
    print()


# ===========================================================================
# Example 5: CRAPS Dice Game (CRAPS赌博游戏)
# ===========================================================================
#
# Simplified CRAPS rules:
#   - First roll: 7 or 11 -> player wins; 2, 3, or 12 -> house wins.
#   - Otherwise the first roll becomes the "point".  Keep rolling:
#       * 7        -> house wins
#       * == point -> player wins
#       * else     -> roll again
#
# This is a self-contained interactive game.  It will NOT auto-run in the
# demo suite; call play_craps() explicitly if you want to play.
#

def play_craps(starting_money: int = 1000) -> None:
    """Run an interactive CRAPS session until the player goes bankrupt."""
    money = starting_money
    print("\n" + "=" * 50)
    print("  Welcome to CRAPS!  Starting funds: ${}".format(money))
    print("=" * 50)

    while money > 0:
        print(f"\nYour balance: ${money}")
        # --- input validation loop (also demonstrates a common pattern) ---
        while True:
            try:
                bet = int(input("Place your bet: "))
                if 0 < bet <= money:
                    break
                print(f"  Bet must be between 1 and {money}.")
            except ValueError:
                print("  Please enter a valid integer.")

        first_point = random.randrange(1, 7) + random.randrange(1, 7)
        print(f"  You rolled {first_point}")

        if first_point in (7, 11):
            print("  Player wins!\n")
            money += bet
        elif first_point in (2, 3, 12):
            print("  House wins!\n")
            money -= bet
        else:
            # Keep rolling until resolved
            while True:
                current = random.randrange(1, 7) + random.randrange(1, 7)
                print(f"  You rolled {current}")
                if current == 7:
                    print("  House wins!\n")
                    money -= bet
                    break
                elif current == first_point:
                    print("  Player wins!\n")
                    money += bet
                    break

    print("You went bankrupt.  Game over!")


# ===========================================================================
# Example 6: Pattern Printing (图案打印)
# ===========================================================================
#
# Common interview / practice exercises for nested loops.
# C++ comparison shown in comments for the first pattern.
#

def print_right_triangle(rows: int = 5) -> None:
    """Print a right-angled triangle of asterisks.

    *
    **
    ***
    ****
    *****

    C++ equivalent:
        for (int i = 1; i <= rows; ++i) {
            for (int j = 0; j < i; ++j) std::cout << "*";
            std::cout << "\n";
        }
    """
    print("  Right Triangle:")
    for i in range(1, rows + 1):
        print("    " + "*" * i)


def print_inverted_triangle(rows: int = 5) -> None:
    """Print an inverted triangle.

    *****
    ****
    ***
    **
    *
    """
    print("  Inverted Triangle:")
    for i in range(rows, 0, -1):
        print("    " + "*" * i)


def print_centered_pyramid(rows: int = 5) -> None:
    """Print a centered pyramid.

        *
       ***
      *****
     *******
    *********
    """
    print("  Centered Pyramid:")
    for i in range(1, rows + 1):
        spaces = " " * (rows - i)
        stars = "*" * (2 * i - 1)
        print(f"    {spaces}{stars}")


def print_diamond(rows: int = 5) -> None:
    """Print a diamond shape (pyramid + inverted pyramid)."""
    print("  Diamond:")
    # Top half
    for i in range(1, rows + 1):
        spaces = " " * (rows - i)
        stars = "*" * (2 * i - 1)
        print(f"    {spaces}{stars}")
    # Bottom half
    for i in range(rows - 1, 0, -1):
        spaces = " " * (rows - i)
        stars = "*" * (2 * i - 1)
        print(f"    {spaces}{stars}")


def print_multiplication_table(size: int = 9) -> None:
    """Print a multiplication table (九九乘法表).

    C++ equivalent uses nested for-loops with printf formatting.
    """
    print("  Multiplication Table:")
    for i in range(1, size + 1):
        row = "    "
        for j in range(1, i + 1):
            row += f"{j}x{i}={i*j:<4}"
        print(row)


def demo_patterns() -> None:
    """Run all pattern-printing demos."""
    print("=" * 50)
    print("Example 6: Pattern Printing (图案打印)")
    print("=" * 50)
    print_right_triangle()
    print()
    print_inverted_triangle()
    print()
    print_centered_pyramid()
    print()
    print_diamond()
    print()
    print_multiplication_table()
    print()


# ===========================================================================
# Enterprise Example A: Input Validation Loop (输入验证循环)
# ===========================================================================
#
# Demonstrates a robust, reusable pattern for collecting validated user input.
# In production systems this is essential for CLI tools, configuration
# wizards, and any interactive interface.
#

def validated_input(
    prompt: str,
    validator=None,
    error_msg: str = "Invalid input. Please try again.",
    max_attempts: int = 5,
) -> str | None:
    """Prompt the user for input, validating with *validator*.

    Parameters
    ----------
    prompt : str
        The prompt string shown to the user.
    validator : callable or None
        A function that takes the raw string and returns True if valid.
        If None, any non-empty string is accepted.
    error_msg : str
        Message displayed on validation failure.
    max_attempts : int
        Give up after this many failed attempts (returns None).

    Returns
    -------
    str or None
        The validated input, or None if max attempts exceeded.
    """
    for attempt in range(1, max_attempts + 1):
        raw = input(prompt).strip()
        if validator is None:
            if raw:
                return raw
        elif validator(raw):
            return raw
        remaining = max_attempts - attempt
        print(f"  {error_msg}  ({remaining} attempt(s) remaining)")
    print("  Max attempts exceeded.")
    return None


def demo_input_validation() -> None:
    """Demo the validated_input helper with a few validators."""
    print("=" * 50)
    print("Enterprise Example A: Input Validation Loop")
    print("=" * 50)

    # --- Validate an integer in a range ---
    def is_valid_age(s: str) -> bool:
        try:
            val = int(s)
            return 0 < val < 150
        except ValueError:
            return False

    # Simulated input (since this is a non-interactive demo)
    # In a real scenario: age = validated_input("Enter age: ", is_valid_age, ...)
    print("  [Simulated] Validated input pattern for age (0 < age < 150):")
    test_inputs = ["abc", "-5", "0", "200", "25"]
    for val in test_inputs:
        ok = is_valid_age(val)
        status = "VALID" if ok else "INVALID"
        print(f"    Input '{val}' -> {status}")

    # --- Validate email format (basic) ---
    def is_valid_email(s: str) -> bool:
        return "@" in s and "." in s.split("@")[-1]

    print("\n  [Simulated] Validated input pattern for email:")
    test_emails = ["", "foo", "foo@", "foo@bar", "foo@bar.com"]
    for val in test_emails:
        ok = is_valid_email(val)
        status = "VALID" if ok else "INVALID"
        print(f"    Input '{val}' -> {status}")
    print()


# ===========================================================================
# Enterprise Example B: Menu-Driven CLI (菜单驱动的命令行界面)
# ===========================================================================
#
# A common pattern in enterprise tools: present a numbered menu, accept user
# choice, dispatch to a handler, repeat until quit.
#

class MenuDrivenApp:
    """A minimal, extensible menu-driven CLI framework.

    Subclass or modify *register_commands()* to add your own commands.
    """

    def __init__(self, title: str = "Main Menu"):
        self.title = title
        self._commands: dict[str, tuple[str, callable]] = {}
        self._running = False

    # -- registration -------------------------------------------------------
    def register(self, key: str, label: str, handler: callable) -> None:
        self._commands[key] = (label, handler)

    # -- main loop ----------------------------------------------------------
    def run(self) -> None:
        self._running = True
        while self._running:
            self._show_menu()
            choice = input("  Enter choice: ").strip()
            if choice in self._commands:
                label, handler = self._commands[choice]
                print(f"\n  >> [{label}]\n")
                handler()
            elif choice.lower() in ("q", "quit", "exit"):
                self._running = False
            else:
                print("  Unknown option. Try again.\n")

    def stop(self) -> None:
        self._running = False

    def _show_menu(self) -> None:
        print(f"\n{'=' * 40}")
        print(f"  {self.title}")
        print(f"{'=' * 40}")
        for key, (label, _) in self._commands.items():
            print(f"  [{key}] {label}")
        print(f"  [q] Quit")
        print(f"{'=' * 40}")


# -- Demo command handlers ------------------------------------------------

def _cmd_hello() -> None:
    print("  Hello, World!")


def _cmd_fib() -> None:
    n = 10
    print(f"  First {n} Fibonacci numbers: {fibonacci(n)}")


def _cmd_primes() -> None:
    print(f"  Primes below 50: {primes_below(50)}")


def demo_menu_cli() -> None:
    """Demo the MenuDrivenApp (non-interactive simulation)."""
    print("=" * 50)
    print("Enterprise Example B: Menu-Driven CLI")
    print("=" * 50)
    app = MenuDrivenApp(title="Demo Tool")
    app.register("1", "Say Hello", _cmd_hello)
    app.register("2", "Fibonacci", _cmd_fib)
    app.register("3", "Primes", _cmd_primes)

    # Instead of running interactively, show what the menu looks like
    # and simulate executing each command.
    app._show_menu()
    print("\n  Simulating command dispatch:")
    for key, (label, handler) in app._commands.items():
        print(f"\n  >> [{label}]")
        handler()
    print()


# ===========================================================================
# Enterprise Example C: Data Processing Pipeline (数据处理管道)
# ===========================================================================
#
# Demonstrates a composable, testable pipeline pattern commonly used in
# ETL (Extract-Transform-Load) systems, log processors, and data wrangling
# scripts.
#
# Each stage is a plain function: data_in -> data_out.
# Stages are composed with the Pipeline class.
#

from typing import Any, Callable


class Pipeline:
    """Compose a sequence of processing stages.

    Usage:
        pipe = Pipeline(stage1, stage2, stage3)
        result = pipe(data)
    """

    def __init__(self, *stages: Callable):
        self._stages = list(stages)

    def add(self, stage: Callable) -> "Pipeline":
        self._stages.append(stage)
        return self

    def __call__(self, data: Any) -> Any:
        for stage in self._stages:
            data = stage(data)
        return data


# -- Sample pipeline stages ------------------------------------------------

def stage_read_raw() -> list[dict]:
    """Simulate reading raw data (e.g., from CSV or database)."""
    return [
        {"name": " Alice ", "age": "30", "salary": "70000"},
        {"name": "Bob", "age": "25", "salary": "55000"},
        {"name": "  Charlie", "age": "invalid", "salary": "80000"},
        {"name": "Diana", "age": "28", "salary": "62000"},
        {"name": "", "age": "35", "salary": "90000"},
    ]


def stage_clean_strings(records: list[dict]) -> list[dict]:
    """Strip whitespace from all string fields."""
    return [
        {k: v.strip() if isinstance(v, str) else v for k, v in rec.items()}
        for rec in records
    ]


def stage_filter_valid(records: list[dict]) -> list[dict]:
    """Remove records with missing name or non-numeric age."""
    def is_valid(rec: dict) -> bool:
        if not rec.get("name"):
            return False
        try:
            int(rec["age"])
            return True
        except ValueError:
            return False
    return [r for r in records if is_valid(r)]


def stage_cast_types(records: list[dict]) -> list[dict]:
    """Convert age and salary to integers."""
    result = []
    for rec in records:
        result.append({
            "name": rec["name"],
            "age": int(rec["age"]),
            "salary": int(rec["salary"]),
        })
    return result


def stage_add_tax(records: list[dict]) -> list[dict]:
    """Add a computed 'tax' field (20% of salary)."""
    for rec in records:
        rec["tax"] = int(rec["salary"] * 0.20)
    return records


def stage_sort_by_salary(records: list[dict]) -> list[dict]:
    """Sort records descending by salary."""
    return sorted(records, key=lambda r: r["salary"], reverse=True)


def stage_summary(records: list[dict]) -> dict:
    """Produce a summary dict from the processed records."""
    if not records:
        return {"count": 0, "avg_salary": 0, "avg_tax": 0}
    return {
        "count": len(records),
        "avg_salary": sum(r["salary"] for r in records) // len(records),
        "avg_tax": sum(r["tax"] for r in records) // len(records),
        "top_earner": records[0]["name"],
        "records": records,
    }


def demo_pipeline() -> None:
    """Run the full data processing pipeline and show results."""
    print("=" * 50)
    print("Enterprise Example C: Data Processing Pipeline")
    print("=" * 50)

    # Build the pipeline by composing stages
    pipe = Pipeline(
        stage_read_raw,
        stage_clean_strings,
        stage_filter_valid,
        stage_cast_types,
        stage_add_tax,
        stage_sort_by_salary,
        stage_summary,
    )

    result = pipe(None)  # stage_read_raw ignores its input

    print(f"\n  Processed {result['count']} valid records.")
    print(f"  Average salary: ${result['avg_salary']:,}")
    print(f"  Average tax:    ${result['avg_tax']:,}")
    print(f"  Top earner:     {result['top_earner']}")
    print("\n  All records (sorted by salary desc):")
    for rec in result["records"]:
        print(
            f"    {rec['name']:>10}  age={rec['age']:>3}  "
            f"salary=${rec['salary']:>7,}  tax=${rec['tax']:>6,}"
        )
    print()


# ===========================================================================
# Main Entry Point
# ===========================================================================

def main() -> None:
    """Run all non-interactive demos.

    The CRAPS game (Example 5) is interactive and skipped by default.
    Call play_craps() directly to play.
    """
    demo_primes()
    demo_fibonacci()
    demo_narcissistic()
    demo_reverse()
    demo_hundred_chickens()
    # play_craps()  # Uncomment to play the interactive CRAPS game
    demo_patterns()
    demo_input_validation()
    demo_menu_cli()
    demo_pipeline()

    print("=" * 50)
    print("All demos complete.")
    print("=" * 50)


if __name__ == "__main__":
    main()
