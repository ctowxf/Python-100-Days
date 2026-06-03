"""
Day 18 - Object-Oriented Programming Fundamentals (面向对象编程入门)

This module covers the essential building blocks of OOP in Python:
  - Defining classes with the `class` keyword
  - The `__init__` initializer and the role of `self`
  - Instance methods, class attributes vs instance attributes
  - String representation via `__str__` and `__repr__`
  - Encapsulation: exposing a clean public interface while hiding internals

C++ developers will find comparison notes throughout the file that map
Python OOP idioms to their C++ counterparts (implicit this, constructors,
class definitions, etc.).
"""

import math
from datetime import datetime


# =============================================================================
# SECTION 1 - Basic Class Definition
# =============================================================================
#
# C++ COMPARISON: Python class vs C++ class
# ------------------------------------------
# C++:   class Student { public: void study(string course); };
# Python: class Student:
#             def study(self, course): ...
#
# Differences:
#   - Python has no explicit access specifiers (public/private/protected).
#   - Python uses indentation instead of braces.
#   - Python methods are defined with `def` inside the class body.
#   - In C++ you declare member variables separately from methods; in Python
#     both live in the class body. Instance attributes are typically created
#     inside __init__ by assigning to self.xxx.
#   - Python classes are themselves objects (type metaclass); C++ classes are
#     compile-time constructs.
# =============================================================================


class Student:
    """A simple Student class demonstrating basic class structure.

    This class shows how to define a class with instance attributes
    (name, age) and instance methods (study, play).
    """

    # --- class attribute (shared by ALL instances) ---
    school_name = "Python 100 Days Academy"

    # ------------------------------------------------------------------ #
    # C++ COMPARISON: Python __init__ vs C++ constructor
    # -------------------------------------------------
    # C++:   Student(string name, int age) : name_(name), age_(age) {}
    # Python:
    #        def __init__(self, name, age):
    #            self.name = name
    #            self.age  = age
    #
    # Key differences:
    #   - __init__ is NOT the constructor. The real constructor is __new__
    #     (allocates the object). __init__ is the *initializer* that sets
    #     up the already-created object, analogous to a C++ constructor body.
    #   - In C++, member initialization lists run before the constructor body.
    #     Python has no equivalent; all setup happens inside __init__.
    #   - Default parameter values in Python use the same syntax as regular
    #     functions (name="unknown"). C++ uses the declaration side.
    #   - Python does not support constructor overloading. Use default args,
    #     *args/**kwargs, or @classmethod factory methods instead.
    # ------------------------------------------------------------------ #

    def __init__(self, name: str, age: int):
        """Initialize a Student instance.

        Args:
            name: The student's name.
            age:  The student's age (must be positive).
        """
        self.name = name
        self.age = age

    # ------------------------------------------------------------------ #
    # C++ COMPARISON: Python self vs C++ implicit this
    # ------------------------------------------------
    # C++:   void study(string course) {
    #            cout << this->name_ << " is studying " << course;
    #        }
    # Python:
    #        def study(self, course):
    #            print(f'{self.name} is studying {course}.')
    #
    # Key differences:
    #   - In C++ `this` is an implicit pointer; you don't list it as a
    #     parameter. In Python, `self` is an EXPLICIT first parameter of
    #     every instance method. You MUST write it.
    #   - `self` is not a keyword -- it's a strong convention. You could
    #     name it anything, but always use `self`.
    #   - C++ uses `this->member` or implicitly resolves member names.
    #     Python ALWAYS requires `self.member` to access instance state.
    #   - In C++, calling obj.study("Python") is syntactic sugar for
    #     Student::study(&obj, "Python"). In Python, obj.study("Python")
    #     is syntactic sugar for Student.study(obj, "Python"). Both
    #     languages pass the receiver as the first argument under the hood.
    # ------------------------------------------------------------------ #

    def study(self, course_name: str) -> None:
        """Simulate the student studying a course."""
        print(f'{self.name} is studying {course_name}.')

    def play(self, game: str = "a video game") -> None:
        """Simulate the student playing."""
        print(f'{self.name} is playing {game}.')

    # ------------------------------------------------------------------ #
    # __str__  -  user-friendly string representation
    # __repr__ -  developer-friendly / unambiguous representation
    #
    # C++ analogy: __str__ is like operator<< for ostream (human-readable).
    #              __repr__ is like a debug dump or serialization that could
    #              ideally be used to reconstruct the object.
    # ------------------------------------------------------------------ #

    def __str__(self) -> str:
        """Return a human-readable string (used by print() and str())."""
        return f'Student(name={self.name}, age={self.age})'

    def __repr__(self) -> str:
        """Return an unambiguous string useful for debugging.

        Convention: return a string that looks like a valid Python expression
        for recreating the object.
        """
        return f'Student("{self.name}", {self.age})'


# =============================================================================
# SECTION 2 - Enterprise Examples with Proper Encapsulation
# =============================================================================

class User:
    """Represents an application user with proper encapsulation.

    Demonstrates:
      - Private attributes with name mangling (__password)
      - Read-only properties via @property
      - Validation inside setters
      - Both __str__ and __repr__
    """

    # class-level auto-incrementing ID counter
    _next_id = 1

    def __init__(self, username: str, email: str, password: str,
                 is_active: bool = True):
        self._user_id = User._next_id
        User._next_id += 1
        self.username = username
        self.email = email
        self.__password = password   # name-mangled: _User__password
        self._is_active = is_active
        self._created_at = datetime.now()

    # ---- properties (controlled access) ----

    @property
    def user_id(self) -> int:
        """Read-only property: the user's unique identifier."""
        return self._user_id

    @property
    def is_active(self) -> bool:
        """Whether the user account is active."""
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("is_active must be a boolean.")
        self._is_active = value

    @property
    def created_at(self) -> datetime:
        """Read-only: timestamp when the user was created."""
        return self._created_at

    # ---- business methods ----

    def deactivate(self) -> None:
        """Deactivate this user account."""
        self._is_active = False
        print(f'User "{self.username}" (id={self._user_id}) has been deactivated.')

    def activate(self) -> None:
        """Activate this user account."""
        self._is_active = True
        print(f'User "{self.username}" (id={self._user_id}) has been activated.')

    def check_password(self, password: str) -> bool:
        """Verify the given password against the stored one.

        In a real application, use bcrypt/argon2 hashing instead of
        plain-text comparison.
        """
        return self.__password == password

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change the password after verifying the old one.

        Returns True on success, False if the old password is wrong.
        """
        if self.__password != old_password:
            print("Password change failed: incorrect current password.")
            return False
        if len(new_password) < 6:
            print("Password change failed: new password too short (min 6 chars).")
            return False
        self.__password = new_password
        print(f'Password changed successfully for user "{self.username}".')
        return True

    def __str__(self) -> str:
        status = "active" if self._is_active else "inactive"
        return f'User({self.username}, {self.email}, {status})'

    def __repr__(self) -> str:
        return (f'User(username="{self.username}", email="{self.email}", '
                f'password="***", is_active={self._is_active})')


class Product:
    """Represents a product in a catalog.

    Demonstrates:
      - Validation logic in __init__ and property setters
      - Computed properties (discounted_price)
      - Class attribute for default currency
    """

    default_currency = "USD"

    def __init__(self, product_id: str, name: str, price: float,
                 stock: int = 0, discount: float = 0.0):
        if price < 0:
            raise ValueError("Price must be non-negative.")
        if stock < 0:
            raise ValueError("Stock must be non-negative.")
        if not (0.0 <= discount <= 1.0):
            raise ValueError("Discount must be between 0.0 and 1.0.")

        self._product_id = product_id
        self.name = name
        self._price = price
        self._stock = stock
        self._discount = discount

    # ---- properties ----

    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Price must be non-negative.")
        self._price = value

    @property
    def stock(self) -> int:
        return self._stock

    @property
    def discount(self) -> float:
        return self._discount

    @discount.setter
    def discount(self, value: float) -> None:
        if not (0.0 <= value <= 1.0):
            raise ValueError("Discount must be between 0.0 and 1.0.")
        self._discount = value

    @property
    def discounted_price(self) -> float:
        """Computed property: price after applying the discount."""
        return round(self._price * (1 - self._discount), 2)

    # ---- business methods ----

    def restock(self, quantity: int) -> None:
        """Add stock for this product."""
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive.")
        self._stock += quantity
        print(f'Restocked {quantity} units of "{self.name}". '
              f'New stock: {self._stock}.')

    def sell(self, quantity: int = 1) -> float:
        """Sell the given quantity. Returns the total cost.

        Raises ValueError if insufficient stock.
        """
        if quantity <= 0:
            raise ValueError("Sell quantity must be positive.")
        if quantity > self._stock:
            raise ValueError(
                f'Insufficient stock: requested {quantity}, '
                f'available {self._stock}.'
            )
        self._stock -= quantity
        total = round(self.discounted_price * quantity, 2)
        print(f'Sold {quantity} unit(s) of "{self.name}" for '
              f'{Product.default_currency} {total:.2f}.')
        return total

    def __str__(self) -> str:
        return (f'{self.name} (ID: {self._product_id}) - '
                f'{Product.default_currency} {self.discounted_price:.2f} '
                f'| In stock: {self._stock}')

    def __repr__(self) -> str:
        return (f'Product(product_id="{self._product_id}", '
                f'name="{self.name}", price={self._price}, '
                f'stock={self._stock}, discount={self._discount})')


class OrderItem:
    """A single line item within an order (product + quantity)."""

    def __init__(self, product: Product, quantity: int):
        if quantity <= 0:
            raise ValueError("Order item quantity must be positive.")
        self.product = product
        self.quantity = quantity

    @property
    def subtotal(self) -> float:
        """Line-item total after discount."""
        return round(self.product.discounted_price * self.quantity, 2)

    def __str__(self) -> str:
        return (f'{self.product.name} x{self.quantity} = '
                f'{Product.default_currency} {self.subtotal:.2f}')

    def __repr__(self) -> str:
        return (f'OrderItem(product={self.product!r}, '
                f'quantity={self.quantity})')


class Order:
    """Represents a customer order containing multiple items.

    Demonstrates:
      - Composition: Order "has" OrderItems, which "have" Products
      - Aggregate behavior (total calculation, checkout)
      - State machine with order status
    """

    VALID_STATUSES = ("pending", "confirmed", "shipped", "delivered", "cancelled")

    _next_order_id = 1000

    def __init__(self, customer: User):
        self._order_id = Order._next_order_id
        Order._next_order_id += 1
        self.customer = customer
        self._items: list[OrderItem] = []
        self._status = "pending"
        self._created_at = datetime.now()

    @property
    def order_id(self) -> int:
        return self._order_id

    @property
    def status(self) -> str:
        return self._status

    @property
    def total(self) -> float:
        """Aggregate total for all line items."""
        return round(sum(item.subtotal for item in self._items), 2)

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self._items)

    # ---- business methods ----

    def add_item(self, product: Product, quantity: int = 1) -> None:
        """Add a product to this order (or increase its quantity).

        If the product already exists in the order, increase its quantity
        rather than creating a duplicate line item.
        """
        if self._status != "pending":
            raise RuntimeError("Cannot modify a non-pending order.")
        for item in self._items:
            if item.product.product_id == product.product_id:
                item.quantity += quantity
                print(f'Updated "{product.name}" quantity to {item.quantity}.')
                return
        self._items.append(OrderItem(product, quantity))
        print(f'Added "{product.name}" x{quantity} to order #{self._order_id}.')

    def remove_item(self, product_id: str) -> None:
        """Remove a product entirely from the order."""
        if self._status != "pending":
            raise RuntimeError("Cannot modify a non-pending order.")
        self._items = [i for i in self._items
                       if i.product.product_id != product_id]
        print(f'Removed product {product_id} from order #{self._order_id}.')

    def checkout(self) -> None:
        """Confirm the order, deducting stock for every item.

        Changes status from 'pending' to 'confirmed'.
        """
        if self._status != "pending":
            raise RuntimeError("Only pending orders can be checked out.")
        if not self._items:
            raise RuntimeError("Cannot checkout an empty order.")

        # Deduct stock
        for item in self._items:
            item.product.sell(item.quantity)

        self._status = "confirmed"
        print(f'\nOrder #{self._order_id} confirmed! '
              f'Total: {Product.default_currency} {self.total:.2f}')

    def update_status(self, new_status: str) -> None:
        """Transition the order to a new status."""
        if new_status not in Order.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        self._status = new_status
        print(f'Order #{self._order_id} status -> {new_status}')

    def __str__(self) -> str:
        header = (f'Order #{self._order_id} | Customer: {self.customer.username} '
                  f'| Status: {self._status}')
        lines = [header, "-" * len(header)]
        for item in self._items:
            lines.append(f'  {item}')
        lines.append(f'  {"":->40}')
        lines.append(f'  Total: {Product.default_currency} {self.total:.2f}')
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (f'Order(order_id={self._order_id}, '
                f'customer={self.customer!r}, '
                f'items={self._items!r}, status="{self._status}")')


# =============================================================================
# SECTION 3 - Supplementary Examples from the Lesson
# =============================================================================

class Clock:
    """Digital clock demonstrating stateful instance methods.

    Attributes:
        hour, minute, second are instance attributes set in __init__.
    """

    def __init__(self, hour: int = 0, minute: int = 0, second: int = 0):
        self.hour = hour
        self.minute = minute
        self.second = second

    def tick(self) -> None:
        """Advance the clock by one second."""
        self.second += 1
        if self.second == 60:
            self.second = 0
            self.minute += 1
            if self.minute == 60:
                self.minute = 0
                self.hour = (self.hour + 1) % 24

    def show(self) -> str:
        """Return the current time as a formatted string."""
        return f'{self.hour:02d}:{self.minute:02d}:{self.second:02d}'

    def __str__(self) -> str:
        return self.show()

    def __repr__(self) -> str:
        return f'Clock(hour={self.hour}, minute={self.minute}, second={self.second})'


class Point:
    """A point on a 2-D plane.

    Demonstrates __str__, __repr__, and instance methods that operate
    on two objects (self and other).
    """

    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def distance_to(self, other: "Point") -> float:
        """Calculate the Euclidean distance to another Point."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def __str__(self) -> str:
        return f'({self.x}, {self.y})'

    def __repr__(self) -> str:
        return f'Point(x={self.x}, y={self.y})'


# =============================================================================
# SECTION 4 - __main__ guard
# =============================================================================

if __name__ == "__main__":

    print("=" * 70)
    print("  SECTION 1 - Basic Class & Instance Methods")
    print("=" * 70)

    # Create Student objects
    stu1 = Student("Alice", 20)
    stu2 = Student("Bob", 22)

    # Both calling styles (explicit class call vs implicit self-binding)
    Student.study(stu1, "Python Programming")   # class.method(instance, ...)
    stu2.play("table tennis")                   # instance.method(...)

    # str() and repr() demonstrations
    print(f'\nstr(stu1)  -> {str(stu1)}')
    print(f'repr(stu1) -> {repr(stu1)}')
    print(f'Class attribute (school_name): {Student.school_name}')

    # Each instance is a distinct object in memory
    print(f'\nid(stu1) = {hex(id(stu1))}')
    print(f'id(stu2) = {hex(id(stu2))}')
    print(f'stu1 is stu2: {stu1 is stu2}')
    print(f'type(stu1): {type(stu1)}')

    print()
    print("=" * 70)
    print("  SECTION 2 - Enterprise Examples")
    print("=" * 70)

    # ---- Users ----
    print("\n--- User Management ---")
    admin = User("admin", "admin@example.com", "s3cur3P@ss")
    guest = User("guest", "guest@example.com", "guest123")
    print(admin)
    print(guest)

    # Property access and validation
    print(f'\nadmin.user_id   = {admin.user_id}')
    print(f'admin.is_active  = {admin.is_active}')
    print(f'admin.created_at = {admin.created_at}')

    admin.deactivate()
    print(f'admin.is_active after deactivation: {admin.is_active}')
    admin.activate()

    # Password operations (encapsulated via name-mangling)
    print(f'\nPassword check (correct):   {admin.check_password("s3cur3P@ss")}')
    print(f'Password check (wrong):     {admin.check_password("wrong")}')
    admin.change_password("s3cur3P@ss", "N3w$ecurePass!")

    print(f'\nrepr(admin) -> {repr(admin)}')  # password masked

    # ---- Products ----
    print("\n--- Product Catalog ---")
    laptop = Product("P001", "Laptop Pro 16", 1299.99, stock=50, discount=0.10)
    mouse = Product("P002", "Ergonomic Mouse", 49.99, stock=200)
    keyboard = Product("P003", "Mechanical Keyboard", 129.99, stock=100,
                       discount=0.15)

    print(laptop)
    print(mouse)
    print(keyboard)
    print(f'\nOriginal laptop price:  {Product.default_currency} {laptop.price:.2f}')
    print(f'Discounted laptop price: {Product.default_currency} {laptop.discounted_price:.2f}')

    # Sell some products
    laptop.sell(2)
    mouse.sell(5)
    keyboard.sell(3)
    print()

    # Restock
    laptop.restock(10)

    # ---- Orders (composition) ----
    print("\n--- Order Processing ---")
    order = Order(admin)
    order.add_item(laptop, 1)
    order.add_item(mouse, 2)
    order.add_item(keyboard, 1)

    print(f'\nItems in order: {order.item_count}')
    print(order)

    # Checkout (deducts stock, transitions status)
    print()
    order.checkout()
    print(f'\nOrder status after checkout: {order.status}')

    order.update_status("shipped")
    order.update_status("delivered")
    print(f'\nFinal order status: {order.status}')

    print(f'\nrepr(order) -> {repr(order)}')

    print()
    print("=" * 70)
    print("  SECTION 3 - Supplementary Examples (Clock & Point)")
    print("=" * 70)

    # Clock demo (tick 3 times from 23:59:58 to show rollover)
    print("\n--- Clock ---")
    clock = Clock(23, 59, 58)
    for _ in range(4):
        print(f'  {clock.show()}')
        clock.tick()

    # Point demo
    print("\n--- Point Distance ---")
    p1 = Point(3, 5)
    p2 = Point(6, 9)
    print(f'  p1 = {p1}')
    print(f'  p2 = {p2}')
    print(f'  Distance p1 -> p2 = {p1.distance_to(p2):.4f}')

    # repr vs str
    print(f'\n  str(p1)  -> {str(p1)}')
    print(f'  repr(p1) -> {repr(p1)}')

    print()
    print("=" * 70)
    print("  SECTION 4 - C++ Comparison Summary")
    print("=" * 70)
    print("""
  +-----------------------------+----------------------------------------------+
  |        C++                   |         Python                               |
  +-----------------------------+----------------------------------------------+
  | class Foo {                  | class Foo:                                   |
  |   int x_;                   |     def __init__(self, x):                   |
  | public:                      |         self.x = x                           |
  |   Foo(int x) : x_(x) {}    |                                              |
  | };                          |                                              |
  +-----------------------------+----------------------------------------------+
  | this->x_  (implicit this)   | self.x  (explicit self, first param)         |
  +-----------------------------+----------------------------------------------+
  | Constructor overloads       | Default args / @classmethod factories        |
  +-----------------------------+----------------------------------------------+
  | ostream& operator<<         | __str__ (user-facing) / __repr__ (debug)     |
  +-----------------------------+----------------------------------------------+
  | public / private / protected| _single (convention) / __double (mangling)   |
  +-----------------------------+----------------------------------------------+
    """)

    print("All examples completed successfully.")
