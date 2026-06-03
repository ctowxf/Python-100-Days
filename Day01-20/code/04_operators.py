"""
Python Operators - Comprehensive Guide
=======================================
Covers: arithmetic, assignment, comparison, logical, bitwise, walrus operator
Includes: C++ comparisons, real-world examples, operator overloading preview

Version: 2.0
Based on: Day04 - Python语言中的运算符
"""

import math
from datetime import datetime


# =============================================================================
# SECTION 1: Arithmetic Operators (算术运算符)
# =============================================================================

def demonstrate_arithmetic_operators():
    """Demonstrate all arithmetic operators with examples."""
    print("=" * 60)
    print("SECTION 1: Arithmetic Operators (算术运算符)")
    print("=" * 60)

    a, b = 15, 4

    print(f"\nGiven: a = {a}, b = {b}")
    print("-" * 40)
    print(f"Addition:       a + b  = {a + b}")      # 19
    print(f"Subtraction:    a - b  = {a - b}")      # 11
    print(f"Multiplication: a * b  = {a * b}")      # 60
    print(f"Division:       a / b  = {a / b}")      # 3.75 (always returns float)
    print(f"Floor Division: a // b = {a // b}")     # 3 (rounds down)
    print(f"Modulus:        a % b  = {a % b}")      # 3 (remainder)
    print(f"Exponentiation: a ** b = {a ** b}")     # 50625

    # Operator precedence (运算符优先级)
    print("\n--- Operator Precedence ---")
    print(f"2 + 3 * 5        = {2 + 3 * 5}")          # 17 (multiplication first)
    print(f"(2 + 3) * 5      = {(2 + 3) * 5}")        # 25 (parentheses first)
    print(f"(2 + 3) * 5 ** 2 = {(2 + 3) * 5 ** 2}")   # 125 (exponent first)
    print(f"((2 + 3) * 5)**2 = {((2 + 3) * 5) ** 2}") # 625


# =============================================================================
# SECTION 2: C++ Comparison - Key Differences (C++ 对比)
# =============================================================================

def demonstrate_cpp_comparison():
    """Show key differences between Python and C++ operators."""
    print("\n" + "=" * 60)
    print("SECTION 2: Python vs C++ Key Differences")
    print("=" * 60)

    # --- Difference 1: Python ** vs C++ pow() ---
    print("\n--- Python ** vs C++ pow() ---")
    print("Python: result = 2 ** 10")
    result = 2 ** 10
    print(f"Result: {result}")
    print("\nC++ equivalent:")
    print("  #include <cmath>")
    print("  double result = pow(2, 10);  // Returns double, needs <cmath>")
    print("  // Or for integers: long long result = (long long)pow(2, 10);")
    print("\nKey difference: Python ** handles arbitrary precision integers natively!")
    print(f"Example: 2 ** 100 = {2 ** 100}")
    print("C++ would overflow with standard integer types for large exponents.")

    # --- Difference 2: Python // vs C++ / for integers ---
    print("\n--- Python // vs C++ / for integers ---")
    print("Python integer division (//) always floors toward negative infinity:")
    print(f"  7 // 2   = {7 // 2}")      # 3
    print(f"  -7 // 2  = {-7 // 2}")     # -4 (floors toward -infinity)
    print(f"  7 // -2  = {7 // -2}")     # -4 (floors toward -infinity)
    print(f"  -7 // -2 = {-7 // -2}")    # 3
    print("\nC++ integer division truncates toward zero:")
    print("  7 / 2   = 3")
    print("  -7 / 2  = -3  (truncates toward zero)")
    print("  7 / -2  = -3  (truncates toward zero)")
    print("\nThis is a CRITICAL difference for negative numbers!")

    # --- Difference 3: Python has no ++/-- ---
    print("\n--- Python has NO ++ or -- operators ---")
    counter = 10
    print(f"Python way: counter = {counter}")
    counter += 1  # Use += instead of ++
    print(f"After counter += 1: {counter}")
    counter -= 1  # Use -= instead of --
    print(f"After counter -= 1: {counter}")
    print("\nC++ has: counter++; counter--; ++counter; --counter;")
    print("Python explicitly does NOT support ++ or -- (by design philosophy)")


# =============================================================================
# SECTION 3: Assignment Operators (赋值运算符)
# =============================================================================

def demonstrate_assignment_operators():
    """Demonstrate assignment and augmented assignment operators."""
    print("\n" + "=" * 60)
    print("SECTION 3: Assignment Operators (赋值运算符)")
    print("=" * 60)

    # Basic assignment
    x = 10
    print(f"\nBasic assignment: x = {x}")

    # Augmented assignment operators (复合赋值运算符)
    print("\n--- Augmented Assignment Operators ---")
    x = 20
    print(f"Initial: x = {x}")

    x += 5   # x = x + 5
    print(f"x += 5  -> x = {x}")    # 25

    x -= 3   # x = x - 3
    print(f"x -= 3  -> x = {x}")    # 22

    x *= 2   # x = x * 2
    print(f"x *= 2  -> x = {x}")    # 44

    x /= 4   # x = x / 4
    print(f"x /= 4  -> x = {x}")    # 11.0

    x //= 3  # x = x // 3
    print(f"x //= 3 -> x = {x}")    # 3.0

    x **= 4  # x = x ** 4
    print(f"x **= 4 -> x = {x}")    # 81.0

    x %= 10  # x = x % 10
    print(f"x %= 10 -> x = {x}")    # 1.0

    # Multiple assignment (多重赋值)
    print("\n--- Multiple Assignment ---")
    a, b, c = 1, 2, 3
    print(f"a, b, c = {a}, {b}, {c}")

    # Swap values (交换值) - Pythonic way
    a, b = b, a
    print(f"After swap: a, b = {a}, {b}")

    # Chain assignment (链式赋值)
    x = y = z = 100
    print(f"Chain assignment: x = y = z = {x}")


# =============================================================================
# SECTION 4: Walrus Operator (海象运算符 :=)
# =============================================================================

def demonstrate_walrus_operator():
    """Demonstrate the walrus operator (:=) introduced in Python 3.8."""
    print("\n" + "=" * 60)
    print("SECTION 4: Walrus Operator (海象运算符 :=)")
    print("=" * 60)

    print("\nThe walrus operator (:=) assigns AND returns a value.")
    print("It looks like a walrus: :=  (eyes and tusks!)")
    print("\nC++ does NOT have an equivalent operator!")

    # --- Basic usage ---
    print("\n--- Basic Usage ---")
    # Regular assignment doesn't return a value
    # print(x = 10)  # SyntaxError!

    # Walrus operator assigns AND returns
    print(f"print(y := 10) -> ", end="")
    print((y := 10))  # Assigns 10 to y and prints it

    # --- Practical use in while loops ---
    print("\n--- Practical: Reading input in while loop ---")
    print("Without walrus operator:")
    print("  line = input('Enter: ')")
    print("  while line != 'quit':")
    print("      process(line)")
    print("      line = input('Enter: ')")
    print("\nWith walrus operator (cleaner!):")
    print("  while (line := input('Enter: ')) != 'quit':")
    print("      process(line)")

    # --- Practical use in list comprehensions ---
    print("\n--- Practical: Filtering with computation ---")
    # Without walrus: compute twice
    data = [1, 5, 12, 3, 18, 7, 25]
    print(f"Original data: {data}")

    # With walrus: compute once, use twice
    results = [y for x in data if (y := x ** 2) > 50]
    print(f"Squares > 50 (using walrus): {results}")

    # --- Practical use in if statements ---
    print("\n--- Practical: if statement with assignment ---")
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    if (n := len(numbers)) > 5:
        print(f"List has {n} elements, which is more than 5")

    # --- Practical: Avoiding repeated function calls ---
    print("\n--- Avoiding Repeated Expensive Calls ---")
    import random
    expensive_data = [random.randint(1, 100) for _ in range(10)]
    print(f"Data: {expensive_data}")

    # Without walrus: call len() twice
    # if len(expensive_data) > 5:
    #     print(f"Processing {len(expensive_data)} items")

    # With walrus: call len() once
    if (count := len(expensive_data)) > 5:
        print(f"Processing {count} items (computed once)")


# =============================================================================
# SECTION 5: Comparison Operators (比较运算符)
# =============================================================================

def demonstrate_comparison_operators():
    """Demonstrate comparison operators and their behavior."""
    print("\n" + "=" * 60)
    print("SECTION 5: Comparison Operators (比较运算符)")
    print("=" * 60)

    a, b = 10, 20

    print(f"\nGiven: a = {a}, b = {b}")
    print("-" * 40)
    print(f"a == b  : {a == b}")    # False
    print(f"a != b  : {a != b}")    # True
    print(f"a < b   : {a < b}")     # True
    print(f"a > b   : {a > b}")     # False
    print(f"a <= b  : {a <= b}")    # True
    print(f"a >= b  : {a >= b}")    # False

    # Chained comparisons (链式比较) - Pythonic feature
    print("\n--- Chained Comparisons (Python-specific!) ---")
    x = 15
    print(f"x = {x}")
    print(f"10 < x < 20  : {10 < x < 20}")    # True
    print(f"10 < x < 12  : {10 < x < 12}")    # False
    print(f"1 <= x <= 100: {1 <= x <= 100}")   # True

    # Identity vs Equality
    print("\n--- Identity (is) vs Equality (==) ---")
    list1 = [1, 2, 3]
    list2 = [1, 2, 3]
    list3 = list1

    print(f"list1 == list2 : {list1 == list2}")   # True (same value)
    print(f"list1 is list2 : {list1 is list2}")   # False (different object)
    print(f"list1 is list3 : {list1 is list3}")   # True (same object)

    # Membership operators
    print("\n--- Membership Operators (in, not in) ---")
    fruits = ['apple', 'banana', 'cherry']
    print(f"fruits = {fruits}")
    print(f"'apple' in fruits     : {'apple' in fruits}")      # True
    print(f"'grape' in fruits     : {'grape' in fruits}")      # False
    print(f"'grape' not in fruits : {'grape' not in fruits}")  # True


# =============================================================================
# SECTION 6: Logical Operators (逻辑运算符)
# =============================================================================

def demonstrate_logical_operators():
    """Demonstrate logical operators and short-circuit evaluation."""
    print("\n" + "=" * 60)
    print("SECTION 6: Logical Operators (逻辑运算符)")
    print("=" * 60)

    print("\nTruth Table for 'and':")
    print("-" * 30)
    print(f"True  and True  = {True and True}")
    print(f"True  and False = {True and False}")
    print(f"False and True  = {False and True}")
    print(f"False and False = {False and False}")

    print("\nTruth Table for 'or':")
    print("-" * 30)
    print(f"True  or True  = {True or True}")
    print(f"True  or False = {True or False}")
    print(f"False or True  = {False or True}")
    print(f"False or False = {False or False}")

    print("\nTruth Table for 'not':")
    print("-" * 30)
    print(f"not True  = {not True}")
    print(f"not False = {not False}")

    # Short-circuit evaluation (短路求值)
    print("\n--- Short-circuit Evaluation ---")
    print("'and' stops at first False:")
    result = False and print("not executed")
    print(f"False and print('not executed') = {result}")

    print("\n'or' stops at first True:")
    result = True or print("not executed")
    print(f"True or print('not executed') = {result}")

    # Practical: Default values
    print("\n--- Practical: Default Values ---")
    username = "" or "Anonymous"
    print(f"username = '' or 'Anonymous' -> {username}")

    username = "Alice" or "Anonymous"
    print(f"username = 'Alice' or 'Anonymous' -> {username}")


# =============================================================================
# SECTION 7: Bitwise Operators (位运算符)
# =============================================================================

def demonstrate_bitwise_operators():
    """Demonstrate bitwise operators with practical examples."""
    print("\n" + "=" * 60)
    print("SECTION 7: Bitwise Operators (位运算符)")
    print("=" * 60)

    a, b = 0b1100, 0b1010  # Binary: 12 and 10
    print(f"\nGiven: a = {a} (binary: {bin(a)})")
    print(f"       b = {b} (binary: {bin(b)})")
    print("-" * 40)

    # Bitwise AND
    result = a & b
    print(f"a & b  (AND)      = {result:4d} (binary: {bin(result)})")

    # Bitwise OR
    result = a | b
    print(f"a | b  (OR)       = {result:4d} (binary: {bin(result)})")

    # Bitwise XOR
    result = a ^ b
    print(f"a ^ b  (XOR)      = {result:4d} (binary: {bin(result)})")

    # Bitwise NOT
    result = ~a
    print(f"~a     (NOT)      = {result:4d} (flips all bits)")

    # Left shift
    result = a << 2
    print(f"a << 2 (LEFT)     = {result:4d} (binary: {bin(result)})")

    # Right shift
    result = a >> 2
    print(f"a >> 2 (RIGHT)    = {result:4d} (binary: {bin(result)})")

    # --- Practical Examples ---
    print("\n--- Practical: Permission System ---")
    READ = 0b100    # 4
    WRITE = 0b010   # 2
    EXECUTE = 0b001 # 1

    user_perm = READ | WRITE  # Grant read and write
    print(f"User permissions: {bin(user_perm)}")

    has_read = bool(user_perm & READ)
    has_write = bool(user_perm & WRITE)
    has_execute = bool(user_perm & EXECUTE)
    print(f"Has read:    {has_read}")
    print(f"Has write:   {has_write}")
    print(f"Has execute: {has_execute}")

    # Toggle permission
    user_perm ^= EXECUTE  # Toggle execute
    print(f"After toggle execute: {bin(user_perm)}")

    # --- Practical: Check even/odd ---
    print("\n--- Practical: Check Even/Odd (faster than %) ---")
    for num in [7, 12, 25, 42]:
        is_odd = bool(num & 1)
        print(f"{num} is {'odd' if is_odd else 'even'}")


# =============================================================================
# SECTION 8: Real-World Examples (实际应用示例)
# =============================================================================

def temperature_converter():
    """Convert between Fahrenheit and Celsius."""
    print("\n" + "=" * 60)
    print("REAL-WORLD EXAMPLE 1: Temperature Converter")
    print("=" * 60)

    # Fahrenheit to Celsius: C = (F - 32) / 1.8
    # Celsius to Fahrenheit: F = C * 1.8 + 32

    test_temps_f = [32, 72, 98.6, 212, -40]
    print("\nFahrenheit to Celsius:")
    print("-" * 30)
    for f in test_temps_f:
        c = (f - 32) / 1.8
        print(f"{f:>6.1f}°F = {c:>6.1f}°C")

    test_temps_c = [0, 20, 37, 100, -40]
    print("\nCelsius to Fahrenheit:")
    print("-" * 30)
    for c in test_temps_c:
        f = c * 1.8 + 32
        print(f"{c:>6.1f}°C = {f:>6.1f}°F")


def bmi_calculator():
    """Calculate BMI and provide health category."""
    print("\n" + "=" * 60)
    print("REAL-WORLD EXAMPLE 2: BMI Calculator")
    print("=" * 60)

    # BMI = weight(kg) / height(m)^2
    print("\nBMI Categories:")
    print("  Underweight:   BMI < 18.5")
    print("  Normal weight: 18.5 <= BMI < 24.9")
    print("  Overweight:    25 <= BMI < 29.9")
    print("  Obese:         BMI >= 30")

    # Sample data: (name, weight_kg, height_m)
    people = [
        ("Alice", 55, 1.65),
        ("Bob", 85, 1.80),
        ("Charlie", 70, 1.75),
        ("Diana", 45, 1.60),
        ("Eve", 95, 1.70),
    ]

    print("\nResults:")
    print("-" * 50)
    for name, weight, height in people:
        bmi = weight / (height ** 2)  # Using ** operator

        # Using comparison and logical operators
        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi < 24.9:
            category = "Normal weight"
        elif 25 <= bmi < 29.9:
            category = "Overweight"
        else:
            category = "Obese"

        print(f"{name:>8}: {weight}kg, {height}m -> BMI = {bmi:.1f} ({category})")


def financial_calculator():
    """Financial calculations demonstrating operator usage."""
    print("\n" + "=" * 60)
    print("REAL-WORLD EXAMPLE 3: Financial Calculator")
    print("=" * 60)

    # Compound interest: A = P(1 + r/n)^(nt)
    print("\n--- Compound Interest Calculator ---")
    principal = 10000      # Initial investment
    annual_rate = 0.05     # 5% annual interest rate
    compounds_per_year = 12  # Monthly compounding
    years = 10

    # Using ** for exponentiation
    amount = principal * (1 + annual_rate / compounds_per_year) ** (compounds_per_year * years)
    interest = amount - principal

    print(f"Principal:           ${principal:>12,.2f}")
    print(f"Annual Rate:         {annual_rate * 100:>11.1f}%")
    print(f"Compounding:         {'Monthly':>11}")
    print(f"Years:               {years:>11}")
    print(f"Final Amount:        ${amount:>12,.2f}")
    print(f"Interest Earned:     ${interest:>12,.2f}")

    # Loan payment calculation
    print("\n--- Monthly Loan Payment ---")
    loan_amount = 250000    # $250,000 mortgage
    monthly_rate = 0.04 / 12  # 4% annual rate
    num_payments = 30 * 12    # 30-year mortgage

    # Payment formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
    payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
              ((1 + monthly_rate) ** num_payments - 1)
    total_paid = payment * num_payments
    total_interest = total_paid - loan_amount

    print(f"Loan Amount:         ${loan_amount:>12,.2f}")
    print(f"Interest Rate:       {'4.0%':>11}")
    print(f"Loan Term:           {'30 years':>11}")
    print(f"Monthly Payment:     ${payment:>12,.2f}")
    print(f"Total Paid:          ${total_paid:>12,.2f}")
    print(f"Total Interest:      ${total_interest:>12,.2f}")

    # Percentage calculations
    print("\n--- Percentage Calculations ---")
    salary = 75000
    tax_rate = 0.22
    insurance_rate = 0.05
    savings_rate = 0.15

    taxes = salary * tax_rate
    insurance = salary * insurance_rate
    savings = salary * savings_rate
    take_home = salary - taxes - insurance - savings

    print(f"Gross Salary:    ${salary:>10,.2f}")
    print(f"Taxes ({tax_rate*100:.0f}%):     ${taxes:>10,.2f}")
    print(f"Insurance ({insurance_rate*100:.0f}%): ${insurance:>10,.2f}")
    print(f"Savings ({savings_rate*100:.0f}%):   ${savings:>10,.2f}")
    print(f"Take Home:       ${take_home:>10,.2f}")


# =============================================================================
# SECTION 9: Operator Overloading Preview (运算符重载预览)
# =============================================================================

class Vector:
    """
    A 2D Vector class demonstrating operator overloading.
    This is a preview of OOP concepts covered later in the course.

    In enterprise applications, operator overloading makes custom classes
    work naturally with Python's syntax.
    """

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other):
        """Overload + operator for vector addition."""
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """Overload - operator for vector subtraction."""
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        """Overload * operator for scalar multiplication."""
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        """Support scalar * vector (right multiplication)."""
        return self.__mul__(scalar)

    def __abs__(self):
        """Overload abs() to return vector magnitude."""
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __eq__(self, other):
        """Overload == operator for equality check."""
        return self.x == other.x and self.y == other.y

    def __lt__(self, other):
        """Overload < operator to compare magnitudes."""
        return abs(self) < abs(other)

    def __repr__(self):
        """String representation for debugging."""
        return f"Vector({self.x}, {self.y})"

    def __str__(self):
        """Human-readable string representation."""
        return f"({self.x}, {self.y})"

    def dot(self, other):
        """Calculate dot product."""
        return self.x * other.x + self.y * other.y


class Money:
    """
    Money class for financial calculations.
    Demonstrates enterprise-grade operator overloading.
    """

    def __init__(self, amount: float, currency: str = "USD"):
        self.amount = round(amount, 2)  # Avoid floating point issues
        self.currency = currency

    def __add__(self, other):
        """Add money amounts (same currency only)."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other):
        """Subtract money amounts."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor):
        """Multiply by a factor (e.g., for interest calculation)."""
        return Money(self.amount * factor, self.currency)

    def __gt__(self, other):
        """Compare if greater than."""
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount > other.amount

    def __eq__(self, other):
        """Check equality."""
        return self.amount == other.amount and self.currency == other.currency

    def __repr__(self):
        return f"Money({self.amount}, '{self.currency}')"

    def __str__(self):
        return f"{self.currency} {self.amount:,.2f}"


def demonstrate_operator_overloading():
    """Demonstrate operator overloading with practical examples."""
    print("\n" + "=" * 60)
    print("SECTION 9: Operator Overloading Preview (运算符重载预览)")
    print("=" * 60)

    # --- Vector Example ---
    print("\n--- 2D Vector Operations ---")
    v1 = Vector(3, 4)
    v2 = Vector(1, 2)

    print(f"v1 = {v1}")
    print(f"v2 = {v2}")
    print(f"v1 + v2 = {v1 + v2}")        # Uses __add__
    print(f"v1 - v2 = {v1 - v2}")        # Uses __sub__
    print(f"v1 * 2  = {v1 * 2}")         # Uses __mul__
    print(f"2 * v1  = {2 * v1}")         # Uses __rmul__
    print(f"|v1|    = {abs(v1):.2f}")    # Uses __abs__
    print(f"v1 == v2: {v1 == v2}")       # Uses __eq__
    print(f"v1 > v2 : {v1 > v2}")        # Uses __lt__ (compares magnitude)
    print(f"v1 . v2 = {v1.dot(v2)}")     # Dot product

    # --- Money Example ---
    print("\n--- Financial Money Operations ---")
    salary = Money(5000.00)
    bonus = Money(1000.00)
    expenses = Money(3500.00)

    print(f"Monthly Salary:  {salary}")
    print(f"Monthly Bonus:   {bonus}")
    print(f"Monthly Expenses:{expenses}")

    total_income = salary + bonus
    savings = total_income - expenses
    annual_savings = savings * 12

    print(f"\nTotal Income:    {total_income}")
    print(f"Monthly Savings: {savings}")
    print(f"Annual Savings:  {annual_savings}")
    print(f"Income > Expenses: {total_income > expenses}")

    # Demonstrate error handling
    print("\n--- Currency Safety ---")
    usd = Money(100, "USD")
    eur = Money(100, "EUR")
    try:
        result = usd + eur  # This will raise ValueError
    except ValueError as e:
        print(f"Error: {e}")

    print("\nWhy Operator Overloading Matters in Enterprise:")
    print("-" * 50)
    print("1. Natural syntax: money1 + money2 instead of money1.add(money2)")
    print("2. Type safety: Custom classes enforce business rules")
    print("3. Readability: Code reads like the problem domain")
    print("4. Pythonic: Leverages Python's dynamic typing")


# =============================================================================
# SECTION 10: Leap Year Example (闰年判断)
# =============================================================================

def demonstrate_leap_year():
    """Demonstrate leap year calculation using logical operators."""
    print("\n" + "=" * 60)
    print("SECTION 10: Leap Year Calculator (闰年判断)")
    print("=" * 60)

    print("\nRules:")
    print("1. Year divisible by 4 is a leap year")
    print("2. EXCEPT years divisible by 100 are NOT leap years")
    print("3. EXCEPT years divisible by 400 ARE leap years")

    test_years = [2000, 2020, 2024, 1900, 2100, 2023, 2025]
    print("\nResults:")
    print("-" * 40)

    for year in test_years:
        # Complex logical expression
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        print(f"{year}: {'Leap Year' if is_leap else 'Not Leap Year'}")

    # Verify with datetime module
    print("\nVerification using datetime module:")
    print("-" * 40)
    for year in test_years[:3]:
        try:
            datetime(year, 2, 29)
            print(f"{year}: Confirmed as leap year")
        except ValueError:
            print(f"{year}: Not a leap year")


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    print("PYTHON OPERATORS - COMPREHENSIVE GUIDE")
    print("=" * 60)
    print("This file demonstrates all Python operators with")
    print("C++ comparisons and real-world examples.")
    print("=" * 60)

    # Run all demonstrations
    demonstrate_arithmetic_operators()
    demonstrate_cpp_comparison()
    demonstrate_assignment_operators()
    demonstrate_walrus_operator()
    demonstrate_comparison_operators()
    demonstrate_logical_operators()
    demonstrate_bitwise_operators()

    # Real-world examples
    temperature_converter()
    bmi_calculator()
    financial_calculator()

    # Advanced topics
    demonstrate_operator_overloading()
    demonstrate_leap_year()

    print("\n" + "=" * 60)
    print("SUMMARY OF KEY DIFFERENCES FROM C++")
    print("=" * 60)
    print("""
    1. Python ** vs C++ pow()
       - Python: 2 ** 10 (built-in operator, arbitrary precision)
       - C++:    pow(2, 10) (needs <cmath>, returns double)

    2. Python // vs C++ / for integers
       - Python //: Floors toward -infinity (-7 // 2 = -4)
       - C++ /:     Truncates toward zero (-7 / 2 = -3)

    3. Python has NO ++ or -- operators
       - Use += 1 or -= 1 instead
       - This is by design (explicit is better than implicit)

    4. Walrus Operator (:=) - Python 3.8+
       - Assigns AND returns value in expressions
       - C++ has no equivalent

    5. Chained Comparisons
       - Python: 1 < x < 10 (single expression)
       - C++:    x > 1 && x < 10 (two comparisons)

    6. Operator Overloading
       - Python: __add__, __mul__, etc.
       - C++:    operator+, operator*, etc.
    """)

    print("=" * 60)
    print("End of Python Operators Guide")
    print("=" * 60)
