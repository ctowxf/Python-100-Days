"""
Day 20: Object-Oriented Programming Applications
=================================================

This module demonstrates advanced OOP concepts in Python including:
- Enum types for symbolic constants
- Abstract base classes and polymorphism
- Operator overloading (magic methods)
- Dataclasses for clean data modeling
- Design patterns (Singleton, Factory, Observer)
- Context managers for resource management
- Enterprise patterns (connection pooling, event systems, configuration)

C++ Comparisons:
- Python dataclass vs C++ struct
- Python context manager vs C++ RAII
- Python enum vs C++ enum class
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from contextlib import contextmanager
import random
import time
import threading
from collections import defaultdict


# =============================================================================
# Section 1: Enum Types - Symbolic Constants
# =============================================================================
# C++ Comparison: Python enum vs C++ enum class
#
# Python Enum:
#   class Color(Enum):
#       RED = 1
#       GREEN = 2
#       BLUE = 3
#
# C++ enum class:
#   enum class Color {
#       RED = 1,
#       GREEN = 2,
#       BLUE = 3
#   };
#
# Key Differences:
# - Python Enum: Class-based, supports iteration, has .name and .value
# - C++ enum class: Scoped, type-safe, but no built-in iteration
# - Python enums can have methods and custom behavior
# - C++ enums are more lightweight but less flexible

class Suite(Enum):
    """Card suits (花色)"""
    SPADE = 0    # 黑桃 ♠
    HEART = 1    # 红心 ♥
    CLUB = 2     # 草花 ♣
    DIAMOND = 3  # 方块 ♦

    def __str__(self):
        symbols = {0: '♠', 1: '♥', 2: '♣', 3: '♦'}
        return symbols[self.value]


class CardRank(Enum):
    """Card ranks with auto() for automatic values"""
    ACE = auto()    # 1
    TWO = auto()    # 2
    THREE = auto()  # 3
    FOUR = auto()   # 4
    FIVE = auto()   # 5
    SIX = auto()    # 6
    SEVEN = auto()  # 7
    EIGHT = auto()  # 8
    NINE = auto()   # 9
    TEN = auto()    # 10
    JACK = auto()   # 11
    QUEEN = auto()  # 12
    KING = auto()   # 13

    def __str__(self):
        names = {
            1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
            8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K'
        }
        return names[self.value]


# =============================================================================
# Section 2: Poker Game - Card, Deck, and Player Classes
# =============================================================================

class Card:
    """
    Playing card with suite and face value.

    Demonstrates:
    - Operator overloading (__lt__, __eq__, __repr__)
    - Property-based access
    - Clean string representation
    """

    def __init__(self, suite: Suite, face: int):
        self.suite = suite
        self.face = face

    def __repr__(self) -> str:
        """String representation of the card"""
        faces = ['', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        return f'{self.suite}{faces[self.face]}'

    def __lt__(self, other: 'Card') -> bool:
        """Compare cards by suite, then by face value"""
        if self.suite == other.suite:
            return self.face < other.face
        return self.suite.value < other.suite.value

    def __eq__(self, other: object) -> bool:
        """Check equality of two cards"""
        if not isinstance(other, Card):
            return False
        return self.suite == other.suite and self.face == other.face

    def __hash__(self) -> int:
        """Make Card hashable for use in sets and dictionaries"""
        return hash((self.suite, self.face))


class Poker:
    """
    Standard 52-card deck with shuffle and deal operations.

    Demonstrates:
    - List comprehension for card generation
    - Property decorators
    - Iterator-like pattern
    """

    def __init__(self):
        self.cards = [
            Card(suite, face)
            for suite in Suite
            for face in range(1, 14)
        ]
        self.current = 0

    def shuffle(self) -> None:
        """Shuffle the deck"""
        self.current = 0
        random.shuffle(self.cards)

    def deal(self) -> Card:
        """Deal one card from the top"""
        if not self.has_next:
            raise ValueError("No more cards to deal")
        card = self.cards[self.current]
        self.current += 1
        return card

    @property
    def has_next(self) -> bool:
        """Check if there are more cards to deal"""
        return self.current < len(self.cards)

    @property
    def remaining(self) -> int:
        """Number of remaining cards"""
        return len(self.cards) - self.current


class Player:
    """
    Card game player with hand management.

    Demonstrates:
    - Object state management
    - Sorting with operator overloading
    - Clean object representation
    """

    def __init__(self, name: str):
        self.name = name
        self.cards: List[Card] = []

    def get_one(self, card: Card) -> None:
        """Receive a card"""
        self.cards.append(card)

    def arrange(self) -> None:
        """Sort cards in hand"""
        self.cards.sort()

    def __repr__(self) -> str:
        return f'Player({self.name})'


# =============================================================================
# Section 3: Dataclasses - Modern Python Data Modeling
# =============================================================================
# C++ Comparison: Python dataclass vs C++ struct
#
# Python dataclass:
#   @dataclass
#   class Point:
#       x: float
#       y: float
#
# C++ struct:
#   struct Point {
#       float x;
#       float y;
#   };
#
# Key Differences:
# - Python dataclass: Auto-generates __init__, __repr__, __eq__
# - C++ struct: Manual implementation or use aggregate initialization
# - Python: Supports default values, type hints, frozen instances
# - C++: More control over memory layout, no runtime overhead

@dataclass
class GameResult:
    """Immutable game result record"""
    winner: str
    score: int
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate data after initialization"""
        if self.score < 0:
            raise ValueError("Score cannot be negative")


@dataclass(frozen=True)
class Vector2D:
    """
    Immutable 2D vector.

    frozen=True makes it immutable (like const in C++)
    """
    x: float
    y: float

    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)

    def magnitude(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5


@dataclass
class Employee:
    """
    Base employee dataclass.

    Demonstrates:
    - Field with default factory
    - Type hints
    - Computed properties
    """
    name: str
    employee_id: str
    department: str = "General"
    hire_date: Optional[str] = None

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.employee_id})"


# =============================================================================
# Section 4: Abstract Base Classes and Polymorphism
# =============================================================================

class AbstractEmployee(ABC):
    """
    Abstract base class for different employee types.

    Demonstrates:
    - ABC (Abstract Base Class) usage
    - Abstract methods for polymorphism
    - Template method pattern
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_salary(self) -> float:
        """Calculate monthly salary - must be implemented by subclasses"""
        pass

    def get_details(self) -> Dict[str, Any]:
        """Get employee details - template method"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "salary": self.get_salary()
        }


class Manager(AbstractEmployee):
    """Department manager with fixed salary"""

    def __init__(self, name: str, department: str = "Management"):
        super().__init__(name)
        self.department = department

    def get_salary(self) -> float:
        return 15000.0


class Programmer(AbstractEmployee):
    """Programmer with hourly pay"""

    def __init__(self, name: str, hourly_rate: float = 200.0):
        super().__init__(name)
        self.hourly_rate = hourly_rate
        self.working_hours: float = 0

    def get_salary(self) -> float:
        return self.hourly_rate * self.working_hours


class Salesman(AbstractEmployee):
    """Salesman with base salary plus commission"""

    def __init__(self, name: str, base_salary: float = 1800.0, commission_rate: float = 0.05):
        super().__init__(name)
        self.base_salary = base_salary
        self.commission_rate = commission_rate
        self.sales_amount: float = 0

    def get_salary(self) -> float:
        return self.base_salary + self.sales_amount * self.commission_rate


# =============================================================================
# Section 5: Design Patterns
# =============================================================================

# --- Pattern 1: Singleton ---
class SingletonMeta(type):
    """
    Singleton metaclass.

    Ensures only one instance of a class exists.
    Thread-safe implementation with lock.
    """
    _instances: Dict[type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class DatabaseConnection(metaclass=SingletonMeta):
    """
    Singleton database connection.

    Demonstrates:
    - Singleton pattern via metaclass
    - Resource management
    - Connection state tracking
    """

    def __init__(self, host: str = "localhost", port: int = 5432):
        self.host = host
        self.port = port
        self._connected = False
        self._query_count = 0

    def connect(self) -> None:
        """Establish connection"""
        if not self._connected:
            print(f"Connecting to {self.host}:{self.port}...")
            self._connected = True

    def disconnect(self) -> None:
        """Close connection"""
        if self._connected:
            print(f"Disconnecting from {self.host}:{self.port}...")
            self._connected = False

    def execute(self, query: str) -> str:
        """Execute a query"""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        self._query_count += 1
        return f"Result of: {query}"

    @property
    def is_connected(self) -> bool:
        return self._connected


# --- Pattern 2: Factory ---
class Animal(ABC):
    """Abstract animal class"""

    @abstractmethod
    def speak(self) -> str:
        pass

    @abstractmethod
    def get_type(self) -> str:
        pass


class Dog(Animal):
    def speak(self) -> str:
        return "Woof!"

    def get_type(self) -> str:
        return "Dog"


class Cat(Animal):
    def speak(self) -> str:
        return "Meow!"

    def get_type(self) -> str:
        return "Cat"


class Bird(Animal):
    def speak(self) -> str:
        return "Tweet!"

    def get_type(self) -> str:
        return "Bird"


class AnimalFactory:
    """
    Factory pattern for creating animals.

    Demonstrates:
    - Factory pattern
    - Encapsulated object creation
    - Easy extensibility
    """

    _creators: Dict[str, Callable[[], Animal]] = {}

    @classmethod
    def register(cls, animal_type: str, creator: Callable[[], Animal]) -> None:
        """Register a new animal type"""
        cls._creators[animal_type.lower()] = creator

    @classmethod
    def create(cls, animal_type: str) -> Animal:
        """Create an animal by type"""
        creator = cls._creators.get(animal_type.lower())
        if not creator:
            raise ValueError(f"Unknown animal type: {animal_type}")
        return creator()


# Register animal types
AnimalFactory.register("dog", Dog)
AnimalFactory.register("cat", Cat)
AnimalFactory.register("bird", Bird)


# --- Pattern 3: Observer ---
class Event:
    """Simple event data container"""

    def __init__(self, event_type: str, data: Any = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = time.time()


class EventEmitter:
    """
    Observer pattern implementation.

    Demonstrates:
    - Observer/Pub-Sub pattern
    - Event-driven architecture
    - Loose coupling between components
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Event], None]]] = defaultdict(list)

    def on(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Register an event listener"""
        self._listeners[event_type].append(callback)

    def off(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Remove an event listener"""
        if event_type in self._listeners:
            self._listeners[event_type].remove(callback)

    def emit(self, event_type: str, data: Any = None) -> None:
        """Emit an event to all listeners"""
        event = Event(event_type, data)
        for callback in self._listeners.get(event_type, []):
            callback(event)

    def listener_count(self, event_type: str) -> int:
        """Get number of listeners for an event type"""
        return len(self._listeners.get(event_type, []))


# =============================================================================
# Section 6: Context Managers
# =============================================================================
# C++ Comparison: Python context manager vs C++ RAII
#
# Python context manager:
#   class FileHandler:
#       def __init__(self, filename):
#           self.filename = filename
#       def __enter__(self):
#           self.file = open(self.filename)
#           return self.file
#       def __exit__(self, exc_type, exc_val, exc_tb):
#           self.file.close()
#
#   with FileHandler("data.txt") as f:
#       data = f.read()
#
# C++ RAII:
#   class FileHandler {
#       std::fstream file;
#   public:
#       FileHandler(const std::string& filename)
#           : file(filename) {}
#       ~FileHandler() { file.close(); }
#   };
#
#   {
#       FileHandler handler("data.txt");
#       // use handler
#   } // destructor called automatically
#
# Key Differences:
# - Python: Explicit with statement, __enter__ and __exit__ methods
# - C++: Deterministic destruction via RAII, no explicit scope needed
# - Python: More flexible (can return different objects from __enter__)
# - C++: More predictable lifetime, no garbage collection delays

class FileManager:
    """
    Context manager for file operations.

    Demonstrates:
    - Context manager protocol (__enter__, __exit__)
    - Exception handling in context managers
    - Resource cleanup guarantee
    """

    def __init__(self, filename: str, mode: str = 'r'):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        """Enter the context - open the file"""
        print(f"Opening file: {self.filename}")
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context - close the file"""
        if self.file:
            print(f"Closing file: {self.filename}")
            self.file.close()
        if exc_type:
            print(f"Exception occurred: {exc_val}")
        return False  # Don't suppress exceptions


class Timer:
    """
    Context manager for timing code blocks.

    Demonstrates:
    - Context manager for cross-cutting concerns
    - Performance measurement
    - Clean resource management
    """

    def __init__(self, label: str = "Operation"):
        self.label = label
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        """Start timing"""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and report"""
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time
        print(f"{self.label} took {self.elapsed:.6f} seconds")
        return False

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if self.elapsed is None:
            raise RuntimeError("Timer not yet completed")
        return self.elapsed


@contextmanager
def managed_resource(name: str):
    """
    Generator-based context manager using @contextmanager decorator.

    Demonstrates:
    - @contextmanager decorator
    - Generator-based context managers
    - Simplified context manager creation
    """
    print(f"Acquiring resource: {name}")
    resource = {"name": name, "acquired": True}
    try:
        yield resource
    except Exception as e:
        print(f"Error with resource {name}: {e}")
        raise
    finally:
        print(f"Releasing resource: {name}")
        resource["acquired"] = False


# =============================================================================
# Section 7: Enterprise Patterns
# =============================================================================

# --- Pattern: Database Connection Pool ---
class ConnectionPool:
    """
    Database connection pool implementation.

    Demonstrates:
    - Object pooling pattern
    - Thread-safe resource management
    - Context manager integration
    """

    def __init__(self, max_size: int = 5, host: str = "localhost", port: int = 5432):
        self.max_size = max_size
        self.host = host
        self.port = port
        self._pool: List[DatabaseConnection] = []
        self._in_use: List[DatabaseConnection] = []
        self._lock = threading.Lock()

    def _create_connection(self) -> DatabaseConnection:
        """Create a new database connection"""
        conn = DatabaseConnection(self.host, self.port)
        conn.connect()
        return conn

    def acquire(self) -> DatabaseConnection:
        """Acquire a connection from the pool"""
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._in_use.append(conn)
                return conn
            elif len(self._in_use) < self.max_size:
                conn = self._create_connection()
                self._in_use.append(conn)
                return conn
            else:
                raise RuntimeError("Connection pool exhausted")

    def release(self, conn: DatabaseConnection) -> None:
        """Release a connection back to the pool"""
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                self._pool.append(conn)

    @contextmanager
    def connection(self):
        """Context manager for automatic connection management"""
        conn = self.acquire()
        try:
            yield conn
        finally:
            self.release(conn)

    @property
    def available(self) -> int:
        """Number of available connections"""
        return len(self._pool)

    @property
    def in_use(self) -> int:
        """Number of connections in use"""
        return len(self._in_use)


# --- Pattern: Event System ---
class EventSystem:
    """
    Enterprise event system with event bus.

    Demonstrates:
    - Event-driven architecture
    - Decoupled communication
    - Event filtering and routing
    """

    def __init__(self):
        self._emitter = EventEmitter()
        self._event_history: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type"""
        self._emitter.on(event_type, handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type"""
        self._emitter.off(event_type, handler)

    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event"""
        event = Event(event_type, data)
        self._event_history.append(event)
        self._emitter.emit(event_type, data)

    def get_history(self, event_type: Optional[str] = None) -> List[Event]:
        """Get event history, optionally filtered by type"""
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type]
        return self._event_history.copy()

    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()


# --- Pattern: Configuration Management ---
class Configuration:
    """
    Application configuration manager.

    Demonstrates:
    - Singleton-like behavior
    - Hierarchical configuration
    - Environment-based configuration
    - Type-safe access
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_file: Optional[str] = None):
        if Configuration._initialized:
            return
        Configuration._initialized = True

        self._config: Dict[str, Any] = {}
        self._config_file = config_file
        self._load_defaults()

        if config_file:
            self._load_from_file(config_file)

    def _load_defaults(self) -> None:
        """Load default configuration values"""
        self._config = {
            "app.name": "Enterprise App",
            "app.version": "1.0.0",
            "database.host": "localhost",
            "database.port": 5432,
            "database.pool_size": 10,
            "logging.level": "INFO",
            "logging.format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }

    def _load_from_file(self, filename: str) -> None:
        """Load configuration from file (simplified)"""
        # In real implementation, this would read from JSON/YAML/INI
        print(f"Loading configuration from: {filename}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self._config[key] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all configuration values for a section"""
        return {
            k.split('.', 1)[1]: v
            for k, v in self._config.items()
            if k.startswith(f"{section}.")
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return self._config.copy()


# =============================================================================
# Section 8: Poker Game Demonstration
# =============================================================================

def demonstrate_poker_game():
    """Demonstrate the poker card game with 4 players"""
    print("\n" + "=" * 60)
    print("POKER GAME DEMONSTRATION")
    print("=" * 60)

    # Create and shuffle deck
    poker = Poker()
    poker.shuffle()

    # Create players
    players = [
        Player("Alice"),
        Player("Bob"),
        Player("Charlie"),
        Player("David")
    ]

    # Deal cards
    for _ in range(13):
        for player in players:
            player.get_one(poker.deal())

    # Arrange and display hands
    for player in players:
        player.arrange()
        print(f"{player.name}: {player.cards}")

    print(f"\nRemaining cards: {poker.remaining}")


# =============================================================================
# Section 9: Design Patterns Demonstration
# =============================================================================

def demonstrate_singleton():
    """Demonstrate Singleton pattern"""
    print("\n" + "=" * 60)
    print("SINGLETON PATTERN - Database Connection")
    print("=" * 60)

    # Both variables point to the same instance
    db1 = DatabaseConnection("localhost", 5432)
    db2 = DatabaseConnection("localhost", 5432)

    print(f"db1 is db2: {db1 is db2}")  # True
    print(f"Same object: {id(db1) == id(db2)}")

    db1.connect()
    print(f"db2 is connected: {db2.is_connected}")  # True - same instance


def demonstrate_factory():
    """Demonstrate Factory pattern"""
    print("\n" + "=" * 60)
    print("FACTORY PATTERN - Animal Creation")
    print("=" * 60)

    animal_types = ["dog", "cat", "bird"]

    for animal_type in animal_types:
        animal = AnimalFactory.create(animal_type)
        print(f"{animal.get_type()}: {animal.speak()}")


def demonstrate_observer():
    """Demonstrate Observer pattern"""
    print("\n" + "=" * 60)
    print("OBSERVER PATTERN - Event System")
    print("=" * 60)

    # Create event system
    event_system = EventSystem()

    # Define event handlers
    def on_user_login(event: Event):
        print(f"User logged in: {event.data}")

    def on_user_logout(event: Event):
        print(f"User logged out: {event.data}")

    def log_all_events(event: Event):
        print(f"[LOG] Event: {event.event_type} at {event.timestamp}")

    # Subscribe to events
    event_system.subscribe("user.login", on_user_login)
    event_system.subscribe("user.logout", on_user_logout)
    event_system.subscribe("user.login", log_all_events)

    # Emit events
    event_system.publish("user.login", "alice")
    event_system.publish("user.logout", "alice")

    # Show history
    print(f"\nEvent history: {len(event_system.get_history())} events")


# =============================================================================
# Section 10: Context Managers Demonstration
# =============================================================================

def demonstrate_context_managers():
    """Demonstrate context managers"""
    print("\n" + "=" * 60)
    print("CONTEXT MANAGERS")
    print("=" * 60)

    # Timer context manager
    print("\n1. Timer Context Manager:")
    with Timer("Calculation") as timer:
        # Simulate some work
        total = sum(range(1000000))
        print(f"   Sum result: {total}")

    # Resource manager
    print("\n2. Resource Manager:")
    with managed_resource("database_pool") as resource:
        print(f"   Using resource: {resource['name']}")
        print(f"   Acquired: {resource['acquired']}")

    # Connection pool
    print("\n3. Connection Pool:")
    pool = ConnectionPool(max_size=3)

    with pool.connection() as conn:
        result = conn.execute("SELECT * FROM users")
        print(f"   Query result: {result}")
        print(f"   Available connections: {pool.available}")
        print(f"   In-use connections: {pool.in_use}")


# =============================================================================
# Section 11: Enterprise Patterns Demonstration
# =============================================================================

def demonstrate_enterprise_patterns():
    """Demonstrate enterprise patterns"""
    print("\n" + "=" * 60)
    print("ENTERPRISE PATTERNS")
    print("=" * 60)

    # Configuration management
    print("\n1. Configuration Management:")
    config = Configuration()
    print(f"   App name: {config.get('app.name')}")
    print(f"   DB host: {config.get('database.host')}")
    print(f"   DB config: {config.get_section('database')}")

    # Modify configuration
    config.set("database.host", "192.168.1.100")
    print(f"   Updated DB host: {config.get('database.host')}")

    # Employee system
    print("\n2. Employee Salary System:")
    employees = [
        Manager("Alice"),
        Programmer("Bob"),
        Salesman("Charlie"),
    ]

    # Set working hours/sales for non-managers
    for emp in employees:
        if isinstance(emp, Programmer):
            emp.working_hours = 160
        elif isinstance(emp, Salesman):
            emp.sales_amount = 50000

    # Display salaries (polymorphism in action)
    for emp in employees:
        print(f"   {emp.name} ({emp.__class__.__name__}): ${emp.get_salary():,.2f}")


# =============================================================================
# Section 12: Dataclass Demonstration
# =============================================================================

def demonstrate_dataclasses():
    """Demonstrate dataclass features"""
    print("\n" + "=" * 60)
    print("DATACLASSES")
    print("=" * 60)

    # Create dataclass instances
    result = GameResult(winner="Alice", score=95)
    print(f"\n1. Game Result: {result}")
    print(f"   Winner: {result.winner}")
    print(f"   Score: {result.score}")

    # Immutable vector
    v1 = Vector2D(3.0, 4.0)
    v2 = Vector2D(1.0, 2.0)
    v3 = v1 + v2

    print(f"\n2. Vector Operations:")
    print(f"   v1: {v1}")
    print(f"   v2: {v2}")
    print(f"   v1 + v2 = {v3}")
    print(f"   |v1| = {v1.magnitude():.2f}")

    # Employee dataclass
    emp = Employee("Alice", "EMP001", "Engineering")
    print(f"\n3. Employee: {emp.display_name}")


# =============================================================================
# Section 13: Enum Demonstration
# =============================================================================

def demonstrate_enums():
    """Demonstrate enum features"""
    print("\n" + "=" * 60)
    print("ENUMERATIONS")
    print("=" * 60)

    # Suite enum
    print("\n1. Card Suits:")
    for suite in Suite:
        print(f"   {suite.name}: {suite} (value={suite.value})")

    # CardRank enum
    print("\n2. Card Ranks (first 5):")
    for rank in list(CardRank)[:5]:
        print(f"   {rank.name}: {rank}")

    # Using enums
    print("\n3. Creating Cards:")
    cards = [
        Card(Suite.SPADE, 1),   # Ace of Spades
        Card(Suite.HEART, 13),  # King of Hearts
        Card(Suite.DIAMOND, 7), # Seven of Diamonds
    ]
    for card in cards:
        print(f"   {card}")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    print("Python Object-Oriented Programming - Day 20 Practice")
    print("=" * 60)

    # Run all demonstrations
    demonstrate_enums()
    demonstrate_dataclasses()
    demonstrate_poker_game()
    demonstrate_singleton()
    demonstrate_factory()
    demonstrate_observer()
    demonstrate_context_managers()
    demonstrate_enterprise_patterns()

    print("\n" + "=" * 60)
    print("All demonstrations completed!")
    print("=" * 60)
