"""
Comprehensive Branch Structure Examples in Python

Covers:
    - if / elif / else
    - Ternary operator (conditional expression)
    - match-case (Python 3.10+)
    - C++ comparison notes
    - Enterprise-grade examples

Version: 1.0
"""

# =============================================================================
# Section 1: if / elif / else Basics
# =============================================================================

def bmi_calculator(height_cm: float, weight_kg: float) -> str:
    """Calculate BMI and return a health assessment string.

    Demonstrates a classic if/elif/else chain with chained comparisons,
    which Python supports natively (unlike C++/Java).
    """
    bmi = weight_kg / (height_cm / 100) ** 2
    # Python allows chaining: 18.5 <= bmi < 24
    # In C++ you would write: bmi >= 18.5 && bmi < 24
    if bmi < 18.5:
        category = "underweight"
    elif bmi < 24:
        category = "normal"
    elif bmi < 27:
        category = "overweight"
    elif bmi < 30:
        category = "mildly obese"
    elif bmi < 35:
        category = "moderately obese"
    else:
        category = "severely obese"
    return f"BMI = {bmi:.1f} -> {category}"


# =============================================================================
# Section 2: Ternary Operator (Conditional Expression)
# =============================================================================
#
# C++ ternary:
#     int abs_val = (x < 0) ? -x : x;
#
# Python equivalent:
#     abs_val = -x if x < 0 else x
#
# Key difference: Python's ternary reads in natural language order
# ("abs_val = negative-x IF x < 0 ELSE x"), whereas C++ uses the
# traditional ? : symbol sequence.
# =============================================================================

def ternary_demo() -> None:
    """Demonstrate Python's ternary operator with side-by-side C++ comments."""

    x = -7

    # C++: int abs_val = (x < 0) ? -x : x;
    abs_val = -x if x < 0 else x
    print(f"abs({x}) = {abs_val}")

    # Nested ternary (use sparingly -- elif chain is usually clearer)
    # C++: const char* label = (score >= 90) ? "A" : (score >= 80) ? "B" : "C";
    score = 85
    label = "A" if score >= 90 else ("B" if score >= 80 else "C")
    print(f"score {score} -> grade {label}")

    # Ternary for default values
    username = ""
    display_name = username if username else "Anonymous"
    print(f"display_name = {display_name!r}")


# =============================================================================
# Section 3: match-case (Python 3.10+)
# =============================================================================
#
# C++ switch-case vs Python match-case
# ------------------------------------
# C++ switch:
#     switch (code) {
#         case 400: desc = "Bad Request"; break;
#         case 401: desc = "Unauthorized"; break;
#         // fall-through without break is a common C++ pitfall
#         default:  desc = "Unknown";      break;
#     }
#
# Python match-case:
#     match code:
#         case 400: desc = "Bad Request"
#         case 401: desc = "Unauthorized"
#         case _:   desc = "Unknown"       # _ is the wildcard (like default)
#
# Differences:
#   1. No fall-through in Python -- no "break" needed.
#   2. Python match-case supports structural pattern matching, not just
#      value comparison.  It can destructure tuples, dicts, and objects.
#   3. Python uses | (OR) to combine patterns in a single case arm.
#   4. Python case arms support "guards" (if conditions), similar in spirit
#      to C++17's if-constexpr or Rust's match guards.
# =============================================================================

def http_status_match(status_code: int) -> str:
    """Map HTTP status codes to descriptions using match-case with OR patterns."""
    match status_code:
        case 200:
            return "OK"
        case 301 | 302:
            return "Redirect"
        case 400 | 405:
            return "Invalid Request"
        case 401 | 403 | 404:
            return "Not Allowed"
        case 418:
            return "I am a teapot"
        case 429:
            return "Too Many Requests"
        case 500 | 502 | 503:
            return "Server Error"
        case _:
            return "Unknown Status Code"


def http_status_if_else(status_code: int) -> str:
    """Equivalent logic using if/elif/else for comparison."""
    if status_code == 200:
        return "OK"
    elif status_code in (301, 302):
        return "Redirect"
    elif status_code in (400, 405):
        return "Invalid Request"
    elif status_code in (401, 403, 404):
        return "Not Allowed"
    elif status_code == 418:
        return "I am a teapot"
    elif status_code == 429:
        return "Too Many Requests"
    elif status_code in (500, 502, 503):
        return "Server Error"
    else:
        return "Unknown Status Code"


# =============================================================================
# Section 4: match-case with Guards
# =============================================================================
#
# Guards add an extra "if" condition after the pattern, enabling
# range-based or attribute-based filtering inside a case arm.
#
# C++ has no direct equivalent.  The closest analogues are:
#   - C++17 if-constexpr for compile-time branching
#   - Runtime if/else chains (which is what match-case guards replace)
#
# Rust has a similar feature: match arms with "if" guards.
# =============================================================================

def classify_number(value: int | float) -> str:
    """Classify a number using match-case with guards."""
    match value:
        case n if n < 0:
            return f"{n} is negative"
        case 0:
            return "zero"
        case n if n % 2 == 0:
            return f"{n} is a positive even number"
        case n:
            return f"{n} is a positive odd number"


def piecewise_function(x: float) -> float:
    """Evaluate the piecewise function from the lesson using match-case guards.

    y = 3x - 5   if x > 1
    y = x + 2     if -1 <= x <= 1
    y = 5x + 3    if x < -1
    """
    match x:
        case v if v > 1:
            return 3 * v - 5
        case v if v >= -1:
            return v + 2
        case v:
            return 5 * v + 3


# =============================================================================
# Section 5: Structural Pattern Matching (Advanced)
# =============================================================================
#
# match-case goes far beyond simple value matching.  It can destructure
# tuples, sequences, mappings, and even class instances.
# =============================================================================

def describe_point(point: tuple) -> str:
    """Match on tuple structure."""
    match point:
        case (0, 0):
            return "Origin"
        case (x, 0):
            return f"On x-axis at x={x}"
        case (0, y):
            return f"On y-axis at y={y}"
        case (x, y) if x == y:
            return f"On diagonal at ({x}, {y})"
        case (x, y):
            return f"Point at ({x}, {y})"


def handle_command(command: str) -> str:
    """Match on a sequence of words (split string)."""
    parts = command.lower().split()
    match parts:
        case ["quit" | "exit"]:
            return "Goodbye!"
        case ["hello", name]:
            return f"Hello, {name}!"
        case ["add", *numbers]:
            total = sum(int(n) for n in numbers)
            return f"Sum = {total}"
        case ["help"]:
            return "Commands: hello <name>, add <n1> <n2> ..., quit"
        case _:
            return f"Unknown command: {command!r}"


# =============================================================================
# Section 6: Enterprise Example -- Grade Calculator
# =============================================================================

class GradeCalculator:
    """Converts numeric scores to letter grades with +/- modifiers.

    Demonstrates nested if/elif/else and ternary usage.
    """

    # Grade boundaries: (lower_bound, letter)
    _BOUNDARIES = [
        (97, "A+"), (93, "A"), (90, "A-"),
        (87, "B+"), (83, "B"), (80, "B-"),
        (77, "C+"), (73, "C"), (70, "C-"),
        (67, "D+"), (63, "D"), (60, "D-"),
    ]

    @staticmethod
    def calculate(score: float) -> str:
        """Return a letter grade for the given numeric score (0-100)."""
        if not 0 <= score <= 100:
            raise ValueError(f"Score must be between 0 and 100, got {score}")

        for boundary, letter in GradeCalculator._BOUNDARIES:
            if score >= boundary:
                return letter
        return "F"

    @staticmethod
    def pass_or_fail(score: float) -> str:
        """Ternary example: return 'PASS' or 'FAIL'."""
        return "PASS" if score >= 60 else "FAIL"

    @staticmethod
    def calculate_match(score: float) -> str:
        """Same logic using match-case with guards (Python 3.10+)."""
        if not 0 <= score <= 100:
            raise ValueError(f"Score must be between 0 and 100, got {score}")
        match score:
            case s if s >= 97:
                return "A+"
            case s if s >= 93:
                return "A"
            case s if s >= 90:
                return "A-"
            case s if s >= 87:
                return "B+"
            case s if s >= 83:
                return "B"
            case s if s >= 80:
                return "B-"
            case s if s >= 77:
                return "C+"
            case s if s >= 73:
                return "C"
            case s if s >= 70:
                return "C-"
            case s if s >= 67:
                return "D+"
            case s if s >= 63:
                return "D"
            case s if s >= 60:
                return "D-"
            case _:
                return "F"


# =============================================================================
# Section 7: Enterprise Example -- Permission Checker
# =============================================================================

from enum import IntFlag


class Permission(IntFlag):
    """Bitflag permissions, similar to how C++ codebases often define them."""
    NONE    = 0
    READ    = 1 << 0   # 1
    WRITE   = 1 << 1   # 2
    EXECUTE = 1 << 2   # 4
    DELETE  = 1 << 3   # 8
    ADMIN   = READ | WRITE | EXECUTE | DELETE  # 15


class PermissionChecker:
    """Checks user permissions using different branch strategies."""

    _ROLE_PERMISSIONS: dict[str, Permission] = {
        "viewer":   Permission.READ,
        "editor":   Permission.READ | Permission.WRITE,
        "developer": Permission.READ | Permission.WRITE | Permission.EXECUTE,
        "admin":    Permission.ADMIN,
    }

    @staticmethod
    def get_permissions(role: str) -> Permission:
        """Look up permissions for a role using match-case."""
        match role.lower():
            case "viewer":
                return Permission.READ
            case "editor":
                return Permission.READ | Permission.WRITE
            case "developer":
                return Permission.READ | Permission.WRITE | Permission.EXECUTE
            case "admin":
                return Permission.ADMIN
            case _:
                return Permission.NONE

    @staticmethod
    def check_access(role: str, required: Permission) -> str:
        """Check whether a role has the required permissions."""
        perms = PermissionChecker.get_permissions(role)
        has_access = (perms & required) == required
        # Ternary for concise status message
        status = "GRANTED" if has_access else "DENIED"
        return f"[{role.upper()}] {required.name} -> {status}"

    @staticmethod
    def describe_permission(perm: Permission) -> str:
        """Use match-case with guards to describe a permission level."""
        match perm:
            case p if p == Permission.NONE:
                return "No permissions"
            case p if p == Permission.ADMIN:
                return "Full admin access"
            case p if Permission.WRITE in p and Permission.EXECUTE in p:
                return "Read-Write-Execute access"
            case p if Permission.WRITE in p:
                return "Read-Write access"
            case p if Permission.READ in p:
                return "Read-only access"
            case _:
                return f"Custom permissions: {perm}"


# =============================================================================
# Section 8: Enterprise Example -- Order Status Handler
# =============================================================================

class OrderStatus:
    """Encapsulates order state transitions using branch structures."""

    VALID_STATUSES = {
        "pending", "confirmed", "processing",
        "shipped", "delivered", "cancelled", "refunded",
    }

    def __init__(self, order_id: str, status: str = "pending"):
        self.order_id = order_id
        self.status = status.lower()

    def transition(self, action: str) -> str:
        """Advance the order to its next state based on the given action.

        Uses match-case on (current_status, action) tuples -- a pattern
        that is very hard to express cleanly in C++ switch-case.
        """
        key = (self.status, action.lower())
        match key:
            case ("pending", "confirm"):
                self.status = "confirmed"
            case ("confirmed", "process"):
                self.status = "processing"
            case ("processing", "ship"):
                self.status = "shipped"
            case ("shipped", "deliver"):
                self.status = "delivered"
            case ("pending" | "confirmed", "cancel"):
                self.status = "cancelled"
            case ("delivered", "refund"):
                self.status = "refunded"
            case (current, act):
                return (
                    f"Invalid transition: cannot '{act}' from "
                    f"'{current}' state for order {self.order_id}"
                )
        return f"Order {self.order_id}: transitioned to '{self.status}'"

    def get_eta_message(self) -> str:
        """Return an estimated-time-of-arrival message based on status."""
        match self.status:
            case "pending":
                return "Awaiting confirmation. ETA: TBD."
            case "confirmed":
                return "Order confirmed. Processing will begin shortly."
            case "processing":
                return "Being prepared. Estimated 1-2 business days."
            case "shipped":
                return "In transit. Estimated 3-5 business days."
            case "delivered":
                return "Delivered. Thank you for your purchase!"
            case "cancelled":
                return "This order has been cancelled."
            case "refunded":
                return "Refund has been processed."
            case _:
                return "Unknown status."

    def __repr__(self) -> str:
        return f"OrderStatus(order_id={self.order_id!r}, status={self.status!r})"


# =============================================================================
# Section 9: Enterprise Example -- Tax Calculator
# =============================================================================

class TaxCalculator:
    """Progressive tax calculator using bracket-based branching.

    Demonstrates if/elif/else, ternary, and match-case with guards
    applied to a real-world financial calculation.
    """

    # US-style simplified brackets for demonstration
    _BRACKETS = [
        (11_000,  0.10),
        (44_725,  0.12),
        (95_375,  0.22),
        (182_100, 0.24),
        (231_250, 0.32),
        (578_125, 0.35),
        (float("inf"), 0.37),
    ]

    def __init__(self, filing_status: str = "single"):
        self.filing_status = filing_status.lower()

    def _get_standard_deduction(self) -> float:
        """Return the standard deduction based on filing status."""
        match self.filing_status:
            case "single":
                return 13_850
            case "married":
                return 27_700
            case "head":
                return 20_800
            case _:
                return 13_850

    def calculate_tax(self, gross_income: float) -> dict:
        """Calculate federal tax owed using progressive brackets."""
        deduction = self._get_standard_deduction()
        taxable = max(gross_income - deduction, 0)
        remaining = taxable
        tax = 0.0
        bracket_details: list[dict] = []
        prev_limit = 0

        for limit, rate in self._BRACKETS:
            if remaining <= 0:
                break
            bracket_size = limit - prev_limit
            taxed_in_bracket = min(remaining, bracket_size)
            tax_in_bracket = taxed_in_bracket * rate
            bracket_details.append({
                "bracket": f"${prev_limit:,.0f}-${limit:,.0f}",
                "rate": f"{rate:.0%}",
                "taxable_amount": taxed_in_bracket,
                "tax": tax_in_bracket,
            })
            tax += tax_in_bracket
            remaining -= taxed_in_bracket
            prev_limit = limit

        effective_rate = (tax / gross_income * 100) if gross_income > 0 else 0
        # Ternary for a concise summary string
        status = "taxable" if taxable > 0 else "no taxable income"

        return {
            "gross_income": gross_income,
            "deduction": deduction,
            "taxable_income": taxable,
            "total_tax": round(tax, 2),
            "effective_rate": f"{effective_rate:.2f}%",
            "status": status,
            "brackets": bracket_details,
        }

    def get_tax_category(self, tax: float) -> str:
        """Classify total tax burden using match-case with guards."""
        match tax:
            case t if t == 0:
                return "No tax owed"
            case t if t < 5_000:
                return "Low tax burden"
            case t if t < 20_000:
                return "Moderate tax burden"
            case t if t < 50_000:
                return "High tax burden"
            case _:
                return "Very high tax burden"


# =============================================================================
# Section 10: Main Demo
# =============================================================================

def demo_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


if __name__ == "__main__":

    # --- BMI Calculator ---
    demo_section("BMI Calculator (if/elif/else with chained comparisons)")
    test_cases = [(175, 68), (175, 95), (175, 50)]
    for h, w in test_cases:
        print(f"  height={h}cm, weight={w}kg -> {bmi_calculator(h, w)}")

    # --- Ternary Operator ---
    demo_section("Ternary Operator (C++ ? : vs Python if/else)")
    ternary_demo()

    # --- match-case vs if-else ---
    demo_section("match-case vs if-else (HTTP status codes)")
    codes = [200, 301, 400, 403, 418, 429, 500, 999]
    for code in codes:
        m = http_status_match(code)
        i = http_status_if_else(code)
        assert m == i, f"Mismatch at {code}: {m} != {i}"
        print(f"  HTTP {code}: {m}")

    # --- match-case with Guards ---
    demo_section("match-case with Guards (number classification)")
    for n in [-5, 0, 3, 8, 11]:
        print(f"  {n}: {classify_number(n)}")

    demo_section("match-case with Guards (piecewise function)")
    for x_val in [-2.0, -1.0, 0.0, 1.0, 2.0]:
        print(f"  x={x_val:+.1f} -> y={piecewise_function(x_val):.1f}")

    # --- Structural Pattern Matching ---
    demo_section("Structural Pattern Matching (tuple destructuring)")
    points = [(0, 0), (3, 0), (0, -2), (4, 4), (7, 3)]
    for pt in points:
        print(f"  {pt}: {describe_point(pt)}")

    demo_section("Structural Pattern Matching (command parsing)")
    commands = ["hello Alice", "add 10 20 30", "help", "quit", "dance"]
    for cmd in commands:
        print(f"  '{cmd}' -> {handle_command(cmd)}")

    # --- Grade Calculator ---
    demo_section("Enterprise: Grade Calculator")
    scores = [98, 95, 91, 88, 84, 79, 72, 65, 55]
    for s in scores:
        g1 = GradeCalculator.calculate(s)
        g2 = GradeCalculator.calculate_match(s)
        pf = GradeCalculator.pass_or_fail(s)
        assert g1 == g2, f"Mismatch at {s}: {g1} != {g2}"
        print(f"  Score {s:>3} -> {g1} ({pf})")

    # --- Permission Checker ---
    demo_section("Enterprise: Permission Checker")
    roles = ["viewer", "editor", "developer", "admin", "guest"]
    required_perms = [Permission.READ, Permission.WRITE, Permission.EXECUTE]
    for role in roles:
        for perm in required_perms:
            print(f"  {PermissionChecker.check_access(role, perm)}")
        desc = PermissionChecker.describe_permission(
            PermissionChecker.get_permissions(role)
        )
        print(f"    -> {desc}")
        print()

    # --- Order Status Handler ---
    demo_section("Enterprise: Order Status Handler (tuple-based matching)")
    order = OrderStatus("ORD-2024-001")
    actions = ["confirm", "process", "ship", "deliver"]
    print(f"  {order}")
    print(f"  ETA: {order.get_eta_message()}")
    for action in actions:
        result = order.transition(action)
        print(f"  {result}")
        print(f"  ETA: {order.get_eta_message()}")

    # Demonstrate invalid transition
    print(f"  {order.transition('cancel')}")
    print()

    # Demonstrate cancellation path
    order2 = OrderStatus("ORD-2024-002")
    order2.transition("confirm")
    print(f"  {order2}")
    print(f"  {order2.transition('cancel')}")
    print(f"  {order2.transition('refund')}")  # invalid: cancelled -> refund

    # --- Tax Calculator ---
    demo_section("Enterprise: Tax Calculator (progressive brackets)")
    tax_calc = TaxCalculator(filing_status="single")
    incomes = [25_000, 50_000, 100_000, 250_000, 1_000_000]
    for income in incomes:
        result = tax_calc.calculate_tax(income)
        category = tax_calc.get_tax_category(result["total_tax"])
        print(
            f"  Income ${income:>10,} | "
            f"Tax ${result['total_tax']:>10,.2f} | "
            f"Effective {result['effective_rate']:>7} | "
            f"{category}"
        )
        print(f"    Deduction: ${result['deduction']:,.0f} | "
              f"Taxable: ${result['taxable_income']:,.0f}")

    print(f"\n{'=' * 60}")
    print("  All demos completed successfully.")
    print(f"{'=' * 60}")
