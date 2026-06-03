"""
Day 19 - Object-Oriented Programming (Advanced)
================================================

This file covers advanced OOP concepts in Python:
- Inheritance and Multiple Inheritance
- Method Resolution Order (MRO)
- Polymorphism
- Abstract Base Classes (ABC)
- Property Decorators
- __slots__ Magic
- Static Methods and Class Methods

Comparisons with C++ are included throughout to help developers
coming from a C++ background understand Python's OOP model.

Enterprise examples included:
  - Payment Method Hierarchy (strategy pattern with polymorphism)
  - Shape Hierarchy (abstract classes, property, math operations)
  - Logger Hierarchy (multiple inheritance, mixin pattern)
"""

from abc import ABC, abstractmethod
import math
from datetime import datetime


# =============================================================================
# SECTION 1: Visibility and Property Decorators
# =============================================================================
#
# C++ COMPARISON: Python @property vs C++ getters/setters
# --------------------------------------------------------
# In C++, you typically write explicit getter/setter methods:
#
#   class Student {
#   private:
#       std::string name;
#       int age;
#   public:
#       std::string getName() const { return name; }
#       void setName(const std::string& n) { name = n; }
#       int getAge() const { return age; }
#       void setAge(int a) { if (a > 0) age = a; }
#   };
#
# In Python, @property lets you expose attribute-like access while
# still running code behind the scenes. Callers never know the
# difference -- they just do `student.name` instead of `student.getName()`.
# =============================================================================

class Student:
    """Demonstrates Python naming conventions for visibility and @property.

    Python naming conventions:
        __name  -> "private" (name-mangled to _Student__name)
        _name   -> "protected" (convention only, no enforcement)
        name    -> public

    C++ has true access modifiers (private, protected, public) enforced
    by the compiler. Python relies on convention and name mangling.
    """

    __slots__ = ('_name', '_age', '_grades')  # Restricts attributes (see Section 6)

    def __init__(self, name: str, age: int):
        self._name = name    # "protected" by convention
        self._age = age
        self._grades = []

    @property
    def name(self) -> str:
        """Getter for name -- accessed like an attribute: student.name."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Setter with validation -- triggered by: student.name = 'X'."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Name must be a non-empty string.")
        self._name = value.strip()

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int):
        if not isinstance(value, int) or value < 0 or value > 150:
            raise ValueError(f"Invalid age: {value}")
        self._age = value

    @property
    def gpa(self) -> float:
        """Read-only computed property -- no setter defined."""
        if not self._grades:
            return 0.0
        return sum(self._grades) / len(self._grades)

    def add_grade(self, score: float):
        """Add a grade score to the student's record."""
        if not 0 <= score <= 100:
            raise ValueError("Score must be between 0 and 100.")
        self._grades.append(score)

    def study(self, course_name: str):
        print(f'  {self._name} is studying {course_name}.')


# =============================================================================
# SECTION 2: Inheritance
# =============================================================================
#
# Python inheritance is similar to C++ but simpler:
#   - No need for virtual keyword (methods are virtual by default)
#   - super() works cleanly without specifying the parent class name
#   - All classes implicitly inherit from object
# =============================================================================

class Person:
    """Base class demonstrating inheritance fundamentals.

    In C++ you would write: class Person { ... };
    In Python all classes implicitly inherit from object.
    """

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def eat(self):
        print(f'  {self.name} is eating.')

    def sleep(self):
        print(f'  {self.name} is sleeping.')

    def introduce(self):
        return f"Person(name={self.name}, age={self.age})"

    def __repr__(self):
        return self.introduce()


class StudentPerson(Person):
    """Student inherits from Person -- gains eat(), sleep(), etc.

    C++ equivalent: class Student : public Person { ... };
    Python equivalent: class Student(Person): ...
    """

    def __init__(self, name: str, age: int, student_id: str):
        super().__init__(name, age)  # Calls Person.__init__
        self.student_id = student_id
        self.courses = []

    def study(self, course_name: str):
        if course_name not in self.courses:
            self.courses.append(course_name)
        print(f'  {self.name} is studying {course_name}.')

    def introduce(self):
        return f"Student(name={self.name}, age={self.age}, id={self.student_id})"


class Teacher(Person):
    """Teacher inherits from Person."""

    def __init__(self, name: str, age: int, title: str):
        super().__init__(name, age)
        self.title = title

    def teach(self, course_name: str):
        print(f'  {self.name} ({self.title}) is teaching {course_name}.')

    def introduce(self):
        return f"Teacher(name={self.name}, age={self.age}, title={self.title})"


class GraduateStudent(StudentPerson):
    """Multi-level inheritance: GraduateStudent -> Student -> Person."""

    def __init__(self, name: str, age: int, student_id: str, advisor: str):
        super().__init__(name, age, student_id)
        self.advisor = advisor
        self.thesis_topic = None

    def set_thesis(self, topic: str):
        self.thesis_topic = topic
        print(f'  {self.name} thesis topic set to: {topic}')

    def introduce(self):
        return (f"GraduateStudent(name={self.name}, age={self.age}, "
                f"id={self.student_id}, advisor={self.advisor})")


# =============================================================================
# SECTION 3: Multiple Inheritance and MRO
# =============================================================================
#
# C++ COMPARISON: Python multiple inheritance vs C++ diamond problem
# -----------------------------------------------------------------
# C++ solves the diamond problem with virtual inheritance:
#
#   class A { public: int x; };
#   class B : virtual public A { };
#   class C : virtual public A { };
#   class D : public B, public C { };  // One copy of A::x
#
# Python uses the C3 Linearization algorithm (MRO) to resolve the
# diamond problem automatically. Every class has a single, predictable
# method resolution order accessible via ClassName.__mro__ or
# ClassName.mro().
#
#   A           In Python, D(B, C) resolves to MRO: D -> B -> C -> A -> object
#  / \          Each method is looked up in this linear order.
# B   C         No virtual keyword needed -- it just works.
#  \ /
#   D
# =============================================================================

class Animal:
    """Base class for the diamond hierarchy demo."""

    def __init__(self, name: str):
        self.name = name

    def speak(self) -> str:
        return f"{self.name} makes a sound."

    def move(self) -> str:
        return f"{self.name} moves."


class Flyable(Animal):
    """Mixin for flying animals."""

    def move(self) -> str:
        return f"{self.name} flies through the air."

    def fly(self) -> str:
        return f"{self.name} flaps wings."


class Swimmable(Animal):
    """Mixin for swimming animals."""

    def move(self) -> str:
        return f"{self.name} swims in the water."

    def swim(self) -> str:
        return f"{self.name} paddles."


class Duck(Flyable, Swimmable):
    """Duck inherits from both Flyable and Swimmable -- diamond problem.

    MRO: Duck -> Flyable -> Swimmable -> Animal -> object

    When duck.move() is called, Python follows the MRO:
      1. Check Duck (no move) -> 2. Check Flyable (has move!) -> use it
    """

    def speak(self) -> str:
        return f"{self.name} says quack!"


class FlyingFish(Flyable, Swimmable):
    """Another diamond inheritor -- same MRO pattern."""

    def speak(self) -> str:
        return f"{self.name} makes a subtle bubbling sound."


def demonstrate_mro():
    """Show the Method Resolution Order for diamond inheritance."""
    print("\n--- Multiple Inheritance & MRO ---")

    # Print MRO for Duck
    print(f"\n  Duck MRO: {[cls.__name__ for cls in Duck.__mro__]}")
    print(f"  FlyingFish MRO: {[cls.__name__ for cls in FlyingFish.__mro__]}")

    duck = Duck("Donald")
    print(f"\n  {duck.speak()}")
    print(f"  {duck.move()}")   # Resolved via Flyable (first in MRO)
    print(f"  {duck.fly()}")
    print(f"  {duck.swim()}")

    fish = FlyingFish("Nemo")
    print(f"\n  {fish.speak()}")
    print(f"  {fish.move()}")   # Also resolved via Flyable
    print(f"  {fish.fly()}")
    print(f"  {fish.swim()}")

    # Demonstrate that super() follows MRO
    print(f"\n  isinstance(duck, Animal): {isinstance(duck, Animal)}")
    print(f"  isinstance(duck, Flyable): {isinstance(duck, Flyable)}")
    print(f"  isinstance(duck, Swimmable): {isinstance(duck, Swimmable)}")


# =============================================================================
# SECTION 4: Polymorphism
# =============================================================================
#
# In C++, polymorphism requires:
#   1. Inheritance
#   2. Virtual keyword on the base class method
#   3. A pointer or reference to the base class
#
# In Python, polymorphism is implicit -- any object that has the
# required method can be used, regardless of its class. This is
# sometimes called "duck typing" (if it quacks like a duck...).
# =============================================================================

# --- Enterprise Example: Payment Method Hierarchy ---

class PaymentMethod(ABC):
    """Abstract base class for payment methods.

    C++ COMPARISON: Python ABC vs C++ pure virtual
    -----------------------------------------------
    C++ uses pure virtual functions:
        class PaymentMethod {
        public:
            virtual void pay(double amount) = 0;  // pure virtual
            virtual ~PaymentMethod() = default;
        };

    Python uses ABC + @abstractmethod:
        class PaymentMethod(ABC):
            @abstractmethod
            def pay(self, amount): ...

    Key differences:
    - C++ abstract classes can still have data members and
      non-virtual methods without any special syntax.
    - Python ABC is just a regular class that happens to
      inherit from ABC and use @abstractmethod.
    - C++ prevents instantiation at compile time; Python
      prevents it at runtime (raises TypeError).
    - Python doesn't have virtual destructors; it has __del__
      but garbage collection makes this less critical.
    """

    @abstractmethod
    def pay(self, amount: float) -> bool:
        """Process a payment. Returns True on success."""
        ...

    @abstractmethod
    def refund(self, amount: float) -> bool:
        """Process a refund. Returns True on success."""
        ...

    @property
    @abstractmethod
    def payment_type(self) -> str:
        """Return the type name of this payment method."""
        ...


class CreditCardPayment(PaymentMethod):
    """Concrete payment method: Credit Card."""

    def __init__(self, card_number: str, cardholder: str, expiry: str):
        self._card_number = card_number[-4:]  # Store only last 4 digits
        self._cardholder = cardholder
        self._expiry = expiry
        self._balance = 0.0

    @property
    def payment_type(self) -> str:
        return "Credit Card"

    def pay(self, amount: float) -> bool:
        if amount <= 0:
            print(f"  [CreditCard] Invalid amount: ${amount:.2f}")
            return False
        self._balance += amount
        print(f"  [CreditCard ****{self._card_number}] Charged ${amount:.2f} "
              f"for {self._cardholder}. Total: ${self._balance:.2f}")
        return True

    def refund(self, amount: float) -> bool:
        if amount > self._balance:
            print(f"  [CreditCard] Refund ${amount:.2f} exceeds balance.")
            return False
        self._balance -= amount
        print(f"  [CreditCard ****{self._card_number}] Refunded ${amount:.2f}. "
              f"Remaining: ${self._balance:.2f}")
        return True


class PayPalPayment(PaymentMethod):
    """Concrete payment method: PayPal."""

    def __init__(self, email: str):
        self._email = email
        self._balance = 0.0

    @property
    def payment_type(self) -> str:
        return "PayPal"

    def pay(self, amount: float) -> bool:
        if amount <= 0:
            print(f"  [PayPal] Invalid amount: ${amount:.2f}")
            return False
        self._balance += amount
        print(f"  [PayPal ({self._email})] Paid ${amount:.2f}. "
              f"Total: ${self._balance:.2f}")
        return True

    def refund(self, amount: float) -> bool:
        if amount > self._balance:
            print(f"  [PayPal] Refund ${amount:.2f} exceeds balance.")
            return False
        self._balance -= amount
        print(f"  [PayPal ({self._email})] Refunded ${amount:.2f}. "
              f"Remaining: ${self._balance:.2f}")
        return True


class CryptoPayment(PaymentMethod):
    """Concrete payment method: Cryptocurrency."""

    def __init__(self, wallet_address: str, currency: str = "BTC"):
        self._wallet = wallet_address[:8] + "..."  # Truncated for display
        self._currency = currency
        self._balance = 0.0

    @property
    def payment_type(self) -> str:
        return f"Crypto ({self._currency})"

    def pay(self, amount: float) -> bool:
        if amount <= 0:
            print(f"  [Crypto] Invalid amount: ${amount:.2f}")
            return False
        self._balance += amount
        print(f"  [Crypto {self._wallet}] Paid ${amount:.2f} {self._currency}. "
              f"Total: ${self._balance:.2f}")
        return True

    def refund(self, amount: float) -> bool:
        if amount > self._balance:
            print(f"  [Crypto] Refund ${amount:.2f} exceeds balance.")
            return False
        self._balance -= amount
        print(f"  [Crypto {self._wallet}] Refunded ${amount:.2f}. "
              f"Remaining: ${self._balance:.2f}")
        return True


def process_order(payment: PaymentMethod, amount: float):
    """Process an order -- demonstrates POLYMORPHISM.

    This function doesn't care what kind of payment method is passed.
    As long as it implements pay() and refund(), it works.
    This is duck typing: if it has pay() and refund(), it's a payment.

    In C++, this would require a base class pointer/reference:
        void processOrder(PaymentMethod* payment, double amount) {
            payment->pay(amount);
        }
    """
    print(f"\n  Processing ${amount:.2f} order via {payment.payment_type}...")
    success = payment.pay(amount)
    if success:
        print(f"  Order processed successfully!")
    else:
        print(f"  Order failed!")


def demonstrate_polymorphism():
    """Show polymorphism with payment methods."""
    print("\n--- Polymorphism: Payment Method Hierarchy ---")

    # Create different payment methods
    credit_card = CreditCardPayment("4111111112345678", "Alice Smith", "12/27")
    paypal = PayPalPayment("alice@example.com")
    crypto = CryptoPayment("0xABCDEF1234567890", "ETH")

    # Polymorphism: same function, different behaviors
    payments = [credit_card, paypal, crypto]

    for payment in payments:
        process_order(payment, 99.99)

    # Demonstrate refunds
    print("\n  --- Refunds ---")
    credit_card.refund(49.99)
    paypal.refund(99.99)

    # Demonstrate ABC enforcement: cannot instantiate abstract class
    print("\n  --- ABC Enforcement ---")
    try:
        # This will raise TypeError at runtime
        PaymentMethod("test")
    except TypeError as e:
        print(f"  Cannot instantiate abstract class: {e}")

    # isinstance checks work with ABCs
    print(f"\n  isinstance(credit_card, PaymentMethod): "
          f"{isinstance(credit_card, PaymentMethod)}")
    print(f"  isinstance(paypal, CreditCardPayment): "
          f"{isinstance(paypal, CreditCardPayment)}")


# =============================================================================
# SECTION 5: Shape Hierarchy (Abstract Classes + Property + Math)
# =============================================================================

class Shape(ABC):
    """Abstract shape with computed properties.

    Demonstrates @property combined with @abstractmethod.
    In C++, this would use pure virtual getters.
    """

    @property
    @abstractmethod
    def area(self) -> float:
        """Computed area -- read-only property."""
        ...

    @property
    @abstractmethod
    def perimeter(self) -> float:
        """Computed perimeter -- read-only property."""
        ...

    @abstractmethod
    def scale(self, factor: float) -> 'Shape':
        """Return a new scaled shape."""
        ...

    def __repr__(self):
        return (f"{self.__class__.__name__}(area={self.area:.2f}, "
                f"perimeter={self.perimeter:.2f})")

    def __eq__(self, other):
        if not isinstance(other, Shape):
            return NotImplemented
        return (self.__class__ == other.__class__ and
                math.isclose(self.area, other.area, rel_tol=1e-9) and
                math.isclose(self.perimeter, other.perimeter, rel_tol=1e-9))


class Circle(Shape):
    """Circle shape."""

    def __init__(self, radius: float):
        if radius <= 0:
            raise ValueError("Radius must be positive.")
        self._radius = radius

    @property
    def radius(self) -> float:
        return self._radius

    @property
    def area(self) -> float:
        return math.pi * self._radius ** 2

    @property
    def perimeter(self) -> float:
        return 2 * math.pi * self._radius

    def scale(self, factor: float) -> 'Circle':
        return Circle(self._radius * factor)


class Rectangle(Shape):
    """Rectangle shape."""

    def __init__(self, width: float, height: float):
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive.")
        self._width = width
        self._height = height

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    @property
    def area(self) -> float:
        return self._width * self._height

    @property
    def perimeter(self) -> float:
        return 2 * (self._width + self._height)

    def scale(self, factor: float) -> 'Rectangle':
        return Rectangle(self._width * factor, self._height * factor)


class Triangle(Shape):
    """Triangle shape using Heron's formula for area."""

    def __init__(self, a: float, b: float, c: float):
        if a <= 0 or b <= 0 or c <= 0:
            raise ValueError("Side lengths must be positive.")
        if not (a + b > c and b + c > a and a + c > b):
            raise ValueError(
                f"Sides ({a}, {b}, {c}) cannot form a valid triangle.")
        self._a = a
        self._b = b
        self._c = c

    @staticmethod
    def is_valid(a: float, b: float, c: float) -> bool:
        """Check if three sides can form a valid triangle (static method)."""
        return a + b > c and b + c > a and a + c > b

    @property
    def area(self) -> float:
        s = self.perimeter / 2
        return math.sqrt(s * (s - self._a) * (s - self._b) * (s - self._c))

    @property
    def perimeter(self) -> float:
        return self._a + self._b + self._c

    def scale(self, factor: float) -> 'Triangle':
        return Triangle(self._a * factor, self._b * factor, self._c * factor)


class RegularPolygon(Shape):
    """Regular polygon (all sides and angles equal)."""

    def __init__(self, n_sides: int, side_length: float):
        if n_sides < 3:
            raise ValueError("Polygon must have at least 3 sides.")
        if side_length <= 0:
            raise ValueError("Side length must be positive.")
        self._n = n_sides
        self._side = side_length

    @property
    def area(self) -> float:
        return ((self._n * self._side ** 2) /
                (4 * math.tan(math.pi / self._n)))

    @property
    def perimeter(self) -> float:
        return self._n * self._side

    def scale(self, factor: float) -> 'RegularPolygon':
        return RegularPolygon(self._n, self._side * factor)


def total_area(shapes: list) -> float:
    """Sum the areas of a list of shapes -- polymorphism in action.

    Each shape's .area property is computed differently, but this
    function doesn't care. It just sums them up.
    """
    return sum(shape.area for shape in shapes)


def demonstrate_shapes():
    """Show the Shape hierarchy with polymorphism."""
    print("\n--- Shape Hierarchy: Abstract Classes + Properties ---")

    shapes = [
        Circle(5),
        Rectangle(4, 6),
        Triangle(3, 4, 5),
        RegularPolygon(6, 2),     # Hexagon
        RegularPolygon(3, 4),     # Equilateral triangle
    ]

    for shape in shapes:
        print(f"  {shape}")

    print(f"\n  Total area of all shapes: {total_area(shapes):.2f}")

    # Demonstrate scale
    c = Circle(10)
    c2 = c.scale(2)
    print(f"\n  Original: {c}")
    print(f"  Scaled 2x: {c2}")

    # Demonstrate Triangle.is_valid (static method)
    print(f"\n  Triangle.is_valid(3, 4, 5): {Triangle.is_valid(3, 4, 5)}")
    print(f"  Triangle.is_valid(1, 2, 10): {Triangle.is_valid(1, 2, 10)}")


# =============================================================================
# SECTION 6: __slots__ Magic
# =============================================================================
#
# __slots__ restricts which attributes an instance can have.
# Benefits:
#   1. Memory savings -- no __dict__ per instance
#   2. Slightly faster attribute access
#   3. Prevents accidental attribute creation (catches typos)
#
# C++ doesn't need this because class members are declared at
# compile time. Python's __slots__ brings similar rigidity.
# =============================================================================

class Point2D:
    """A 2D point using __slots__ for memory efficiency.

    Without __slots__, each instance has a __dict__ (~100+ bytes).
    With __slots__, attributes are stored in a fixed-size structure.
    """

    __slots__ = ('_x', '_y')

    def __init__(self, x: float, y: float):
        self._x = x
        self._y = y

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    def distance_to(self, other: 'Point2D') -> float:
        return math.sqrt((self._x - other._x) ** 2 +
                         (self._y - other._y) ** 2)

    def __repr__(self):
        return f"Point2D({self._x}, {self._y})"

    def __eq__(self, other):
        if not isinstance(other, Point2D):
            return NotImplemented
        return math.isclose(self._x, other._x) and \
               math.isclose(self._y, other._y)

    def __hash__(self):
        return hash((round(self._x, 9), round(self._y, 9)))


class ColorPoint(Point2D):
    """Demonstrates __slots__ inheritance.

    Note: subclass must also define __slots__ for new attributes,
    otherwise it gets a __dict__ and defeats the purpose.
    """

    __slots__ = ('_color',)  # Only new attributes

    def __init__(self, x: float, y: float, color: str):
        super().__init__(x, y)
        self._color = color

    @property
    def color(self) -> str:
        return self._color

    def __repr__(self):
        return f"ColorPoint({self._x}, {self._y}, '{self._color}')"


def demonstrate_slots():
    """Show __slots__ behavior and restrictions."""
    print("\n--- __slots__ Magic ---")

    p = Point2D(3.0, 4.0)
    print(f"  Point: {p}")
    print(f"  Has __dict__: {hasattr(p, '__dict__')}")
    print(f"  Has __slots__: {hasattr(Point2D, '__slots__')}")
    print(f"  Allowed attributes: {Point2D.__slots__}")

    # Cannot add arbitrary attributes
    try:
        p.z = 5.0
    except AttributeError as e:
        print(f"  Cannot add 'z' to Point2D: {e}")

    # ColorPoint inherits slots correctly
    cp = ColorPoint(1.0, 2.0, "red")
    print(f"\n  ColorPoint: {cp}")
    print(f"  ColorPoint has __dict__: {hasattr(cp, '__dict__')}")
    print(f"  ColorPoint.__slots__: {ColorPoint.__slots__}")

    # Distance calculation
    p1 = Point2D(0, 0)
    p2 = Point2D(3, 4)
    print(f"\n  Distance from {p1} to {p2}: {p1.distance_to(p2):.2f}")

    # Memory comparison (conceptual)
    regular_point_count = 10000
    print(f"\n  Memory benefit: __slots__ eliminates per-instance __dict__")
    print(f"  For {regular_point_count} points, this saves significant memory.")


# =============================================================================
# SECTION 7: Logger Hierarchy (Multiple Inheritance + Mixin Pattern)
# =============================================================================
#
# Mixins are a common pattern in Python that leverage multiple
# inheritance to compose behavior. A mixin is a class that provides
# a specific capability but is not meant to stand alone.
#
# C++ COMPARISON:
#   C++ achieves similar composition through:
#     - Multiple inheritance (allowed but tricky)
#     - CRTP (Curiously Recurring Template Pattern)
#     - Template-based policy classes
#   Python's mixin pattern is simpler and more idiomatic.
# =============================================================================

class LoggerMixin:
    """Mixin that adds logging capability to any class.

    Mixins should:
    - Provide a single, focused capability
    - Not have their own __init__ (or be cooperative with super())
    - Not be instantiated on their own
    """

    def log(self, level: str, message: str):
        """Log a message with timestamp and class name."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        class_name = self.__class__.__name__
        print(f"  [{timestamp}] [{level:5s}] {class_name}: {message}")


class SerializableMixin:
    """Mixin that adds serialization capability."""

    def to_dict(self) -> dict:
        """Convert object attributes to a dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            # Skip private attributes (starting with _)
            if not key.startswith('_'):
                result[key] = value
        return result

    def to_json_string(self) -> str:
        """Simple JSON-like string representation."""
        parts = [f'"{k}": "{v}"' for k, v in self.to_dict().items()]
        return "{" + ", ".join(parts) + "}"


class ValidatableMixin:
    """Mixin that adds validation capability."""

    _validators = {}

    def validate(self) -> list:
        """Run all registered validations. Returns list of errors."""
        errors = []
        for attr, rules in self._validators.items():
            value = getattr(self, attr, None)
            for rule_name, rule_check in rules.items():
                if not rule_check(value):
                    errors.append(f"{attr}: failed '{rule_name}' check")
        return errors


class AppConfig(LoggerMixin, SerializableMixin):
    """Application configuration with logging and serialization.

    Combines capabilities from two mixins via multiple inheritance.
    """

    def __init__(self, app_name: str, version: str, debug: bool = False):
        self.app_name = app_name
        self.version = version
        self.debug = debug
        self.log("INFO", f"Configuration created for {app_name} v{version}")

    def update(self, **kwargs):
        """Update configuration values with logging."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                old_value = getattr(self, key)
                setattr(self, key, value)
                self.log("INFO", f"Config '{key}': {old_value} -> {value}")
            else:
                self.log("WARN", f"Unknown config key: {key}")


class DatabaseConfig(LoggerMixin, SerializableMixin):
    """Database configuration with multiple mixin capabilities."""

    def __init__(self, host: str, port: int, database: str):
        self.host = host
        self.port = port
        self.database = database
        self.log("INFO", f"Database config: {host}:{port}/{database}")

    def get_connection_string(self) -> str:
        conn_str = f"postgresql://{self.host}:{self.port}/{self.database}"
        self.log("DEBUG", f"Connection string generated")
        return conn_str


def demonstrate_logger_hierarchy():
    """Show multiple inheritance with mixins."""
    print("\n--- Logger Hierarchy: Multiple Inheritance + Mixins ---")

    # AppConfig uses LoggerMixin + SerializableMixin
    config = AppConfig("MyApp", "2.1.0", debug=True)
    print(f"\n  Config as dict: {config.to_dict()}")
    print(f"  Config as JSON: {config.to_json_string()}")

    config.update(debug=False, version="2.1.1")

    # DatabaseConfig uses the same mixins
    db_config = DatabaseConfig("localhost", 5432, "mydb")
    print(f"\n  DB Config as dict: {db_config.to_dict()}")
    print(f"  Connection: {db_config.get_connection_string()}")

    # Show MRO for the mixin-based classes
    print(f"\n  AppConfig MRO: "
          f"{[cls.__name__ for cls in AppConfig.__mro__]}")
    print(f"  DatabaseConfig MRO: "
          f"{[cls.__name__ for cls in DatabaseConfig.__mro__]}")


# =============================================================================
# SECTION 8: Static Methods and Class Methods
# =============================================================================

class MathUtils:
    """Demonstrates static methods and class methods.

    Static methods: don't receive self or cls. Just utility functions
        that logically belong to the class namespace.

    Class methods: receive cls (the class itself). Often used for
        alternative constructors or factory methods.

    C++ comparison:
        - static methods in C++ are similar to Python @staticmethod
        - C++ has no direct equivalent of @classmethod
        - Python class methods are often used where C++ would use
          overloaded constructors or static factory methods
    """

    _pi_approximations = {
        1: 3.0,
        2: 3.1,
        5: 3.14159,
        10: 3.1415926535,
    }

    @staticmethod
    def is_even(n: int) -> bool:
        """Static method -- no self or cls needed."""
        return n % 2 == 0

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp a value between min and max."""
        return max(min_val, min(value, max_val))

    @classmethod
    def get_pi(cls, precision: int = 5) -> float:
        """Class method -- uses cls to access class-level data."""
        return cls._pi_approximations.get(precision, math.pi)

    @classmethod
    def from_degrees(cls, degrees: float) -> float:
        """Class method as a factory-like helper."""
        return degrees * math.pi / 180


def demonstrate_static_class_methods():
    """Show static and class methods."""
    print("\n--- Static Methods and Class Methods ---")

    # Static methods -- called on the class, no instance needed
    print(f"  MathUtils.is_even(4): {MathUtils.is_even(4)}")
    print(f"  MathUtils.is_even(7): {MathUtils.is_even(7)}")
    print(f"  MathUtils.clamp(15, 0, 10): {MathUtils.clamp(15, 0, 10)}")

    # Class methods -- receive the class itself
    print(f"\n  MathUtils.get_pi(5): {MathUtils.get_pi(5)}")
    print(f"  MathUtils.get_pi(2): {MathUtils.get_pi(2)}")
    print(f"  MathUtils.from_degrees(180): {MathUtils.from_degrees(180):.6f}")
    print(f"  MathUtils.from_degrees(90): {MathUtils.from_degrees(90):.6f}")


# =============================================================================
# SECTION 9: Demonstrating Everything
# =============================================================================

def demonstrate_inheritance_and_polymorphism():
    """Comprehensive demo of single inheritance and polymorphism."""
    print("\n--- Inheritance and Polymorphism ---")

    # Create objects
    person = Person("Alice", 30)
    student = StudentPerson("Bob", 20, "STU-001")
    teacher = Teacher("Dr. Smith", 45, "Professor")
    grad_student = GraduateStudent("Charlie", 25, "GRAD-001", "Dr. Smith")

    # Demonstrate inherited methods
    print("\n  Inherited behaviors:")
    person.eat()
    student.eat()      # Inherited from Person
    teacher.sleep()    # Inherited from Person
    grad_student.eat() # Inherited through two levels

    # Demonstrate specialized methods
    print("\n  Specialized behaviors:")
    student.study("Python Programming")
    teacher.teach("Data Structures")
    grad_student.set_thesis("Advanced Machine Learning")

    # Polymorphism: same method, different results
    print("\n  Polymorphism (introduce method):")
    entities = [person, student, teacher, grad_student]
    for entity in entities:
        print(f"    {entity.introduce()}")

    # isinstance and issubclass checks
    print("\n  Type checking:")
    print(f"    isinstance(student, Person): {isinstance(student, Person)}")
    print(f"    isinstance(grad_student, StudentPerson): "
          f"{isinstance(grad_student, StudentPerson)}")
    print(f"    issubclass(GraduateStudent, Person): "
          f"{issubclass(GraduateStudent, Person)}")


# =============================================================================
# SECTION 10: Main Execution
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("  Day 19: Object-Oriented Programming (Advanced)")
    print("=" * 70)

    # 1. Inheritance and Polymorphism basics
    demonstrate_inheritance_and_polymorphism()

    # 2. Multiple Inheritance and MRO
    demonstrate_mro()

    # 3. Abstract Classes and Polymorphism (Payment Hierarchy)
    demonstrate_polymorphism()

    # 4. Shape Hierarchy (Abstract + Property + Math)
    demonstrate_shapes()

    # 5. __slots__
    demonstrate_slots()

    # 6. Logger Hierarchy (Mixins)
    demonstrate_logger_hierarchy()

    # 7. Static and Class Methods
    demonstrate_static_class_methods()

    # Summary
    print("\n" + "=" * 70)
    print("  Key Takeaways:")
    print("=" * 70)
    print("""
  1. @property: Python's elegant alternative to C++ getters/setters.
     Access computed values like attributes, not method calls.

  2. ABC: Python's answer to C++ pure virtual functions.
     Use @abstractmethod to enforce method implementation.

  3. Multiple Inheritance: Python uses C3 MRO to resolve the
     diamond problem automatically (no virtual keyword needed).

  4. Polymorphism: Python uses duck typing -- if it has the method,
     it works. No base class pointer required (unlike C++).

  5. __slots__: Restricts attributes for memory efficiency.
     Similar to C++ compile-time member declaration.

  6. Mixins: Compose behavior via multiple inheritance.
     Simpler than C++ template-based policy classes.

  7. Static/Class Methods: @staticmethod for utility functions,
     @classmethod for alternative constructors/factories.
""")
