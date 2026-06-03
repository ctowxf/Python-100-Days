"""
Day 96 - Software Testing and Automated Testing
=================================================

Comprehensive demonstration of Python testing patterns using pytest.

Topics covered:
    - pytest basics and test discovery
    - Fixtures (setup/teardown, scoping, factory pattern)
    - Parametrize for data-driven testing
    - Mocking with unittest.mock and pytest-mock
    - Test coverage measurement
    - Integration testing patterns
    - Enterprise patterns: API testing, database testing, mock patterns

C++ Comparison: pytest vs Google Test / Catch2
----------------------------------------------
| Feature              | pytest               | Google Test          | Catch2               |
|----------------------|----------------------|----------------------|----------------------|
| Discovery            | Auto (naming conv.)  | Manual registration  | Auto (naming conv.)  |
| Fixtures             | @pytest.fixture      | TEST_F macro         | SECTION / fixture    |
| Parameterized        | @pytest.mark.parametrize | INSTANTIATE_TEST | TEMPLATE_TEST_CASE   |
| Assertion style      | Plain assert         | EXPECT_EQ / ASSERT_EQ| REQUIRE / CHECK      |
| Mock framework       | unittest.mock        | Google Mock          | trompeloeil / fakeit |
| Coverage             | pytest-cov           | gcov / lcov          | gcov / lcov          |
| Ecosystem            | 1000+ plugins        | Integrated w/ GMock  | Header-only, minimal |
| Setup complexity     | Low (pip install)    | Moderate (CMake)     | Low (single header)  |

pytest advantages over C++ test frameworks:
    1. Dynamic typing reduces boilerplate for test data
    2. Rich fixture dependency injection with automatic teardown
    3. Parametrize generates separate test cases declaratively
    4. Plugin ecosystem (pytest-cov, pytest-xdist, pytest-asyncio, etc.)
    5. Plain `assert` with introspective failure messages

C++ frameworks advantages:
    1. Compile-time type checking catches errors before execution
    2. Google Mock supports strict/nice/sequence-based expectations
    3. Zero-overhead when test code is stripped from release builds
    4. Catch2 is truly header-only with no external dependencies

Requirements:
    pip install pytest pytest-cov pytest-mock requests

Run all tests:
    pytest 96_testing.py -v

Run with coverage:
    pytest 96_testing.py -v --cov=. --cov-report=term-missing
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Generator, Optional, Protocol
from unittest.mock import MagicMock, Mock, patch

import pytest


# =============================================================================
# Section 1: Domain Models Under Test
# =============================================================================


@dataclass
class Product:
    """Represents a product in an e-commerce system."""

    product_id: int
    name: str
    price: float
    stock: int = 0

    def is_available(self) -> bool:
        """Check if product is in stock."""
        return self.stock > 0

    def apply_discount(self, percent: float) -> float:
        """Apply a discount percentage and return the new price.

        Args:
            percent: Discount percentage (0-100).

        Returns:
            Discounted price rounded to 2 decimal places.

        Raises:
            ValueError: If percent is not in range [0, 100].
        """
        if not 0 <= percent <= 100:
            raise ValueError(f"Discount percent must be 0-100, got {percent}")
        return round(self.price * (1 - percent / 100), 2)

    def reduce_stock(self, quantity: int) -> None:
        """Reduce stock by quantity.

        Raises:
            ValueError: If quantity exceeds available stock.
        """
        if quantity > self.stock:
            raise ValueError(
                f"Requested {quantity} but only {self.stock} in stock"
            )
        self.stock -= quantity


@dataclass
class OrderItem:
    """A single line item in an order."""

    product: Product
    quantity: int

    @property
    def subtotal(self) -> float:
        return round(self.product.price * self.quantity, 2)


@dataclass
class Order:
    """Represents a customer order."""

    order_id: int
    items: list[OrderItem] = field(default_factory=list)

    @property
    def total(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)

    def add_item(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        product.reduce_stock(quantity)
        self.items.append(OrderItem(product=product, quantity=quantity))


class InventoryError(Exception):
    """Raised when an inventory operation fails."""


# =============================================================================
# Section 2: Service Layer (what we will test with mocks)
# =============================================================================


class PaymentGateway(Protocol):
    """Protocol defining the payment gateway interface.

    In C++ this would be an abstract class with pure virtual methods.
    Python's Protocol provides structural (duck) typing instead.
    """

    def charge(self, amount: float, currency: str = "USD") -> dict[str, Any]:
        ...

    def refund(self, transaction_id: str) -> bool:
        ...


class EmailService(Protocol):
    """Protocol for email notification service."""

    def send_order_confirmation(self, order_id: int, email: str) -> bool:
        ...


class RealPaymentGateway:
    """Production payment gateway -- never called in tests."""

    def charge(self, amount: float, currency: str = "USD") -> dict[str, Any]:
        # In reality this would call Stripe, PayPal, etc.
        raise RuntimeError("Do not call real gateway in tests")

    def refund(self, transaction_id: str) -> bool:
        raise RuntimeError("Do not call real gateway in tests")


class OrderService:
    """Service that orchestrates order creation with payment and notification."""

    def __init__(
        self,
        payment_gateway: PaymentGateway,
        email_service: EmailService,
    ) -> None:
        self._gateway = payment_gateway
        self._email = email_service

    def place_order(
        self,
        order: Order,
        customer_email: str,
    ) -> dict[str, Any]:
        """Place an order: charge payment, then send confirmation.

        Returns:
            Dict with 'status', 'transaction_id', and 'total'.

        Raises:
            ValueError: If order has no items.
        """
        if not order.items:
            raise ValueError("Cannot place an empty order")

        result = self._gateway.charge(order.total)
        if result.get("status") != "success":
            raise PaymentError(f"Payment failed: {result.get('message')}")

        self._email.send_order_confirmation(order.order_id, customer_email)
        return {
            "status": "placed",
            "transaction_id": result["transaction_id"],
            "total": order.total,
        }


class PaymentError(Exception):
    """Raised when payment processing fails."""


# =============================================================================
# Section 3: Database Layer for Integration Testing
# =============================================================================


class ProductRepository:
    """SQLite-backed product repository."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def save(self, product: Product) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO products (id, name, price, stock) "
                "VALUES (?, ?, ?, ?)",
                (product.product_id, product.name, product.price, product.stock),
            )
            conn.commit()

    def find_by_id(self, product_id: int) -> Optional[Product]:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT id, name, price, stock FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
        if row is None:
            return None
        return Product(product_id=row[0], name=row[1], price=row[2], stock=row[3])

    def find_all(self) -> list[Product]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, name, price, stock FROM products"
            ).fetchall()
        return [
            Product(product_id=r[0], name=r[1], price=r[2], stock=r[3])
            for r in rows
        ]

    def delete_by_id(self, product_id: int) -> bool:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM products WHERE id = ?", (product_id,)
            )
            conn.commit()
            return cursor.rowcount > 0


# =============================================================================
# Section 4: Pytest Fixtures
# =============================================================================
#
# Fixture scopes control how often a fixture is invoked:
#   function  - once per test function (default)
#   class     - once per test class
#   module    - once per module (file)
#   session   - once per entire test session
#
# In C++ Google Test, the equivalent is SetUp()/TearDown() in TEST_F,
# or global fixtures registered with testing::Environment.
# Catch2 uses SECTION blocks which re-run setup for each section.


@pytest.fixture
def sample_product() -> Product:
    """Create a single sample product for unit tests."""
    return Product(product_id=1, name="Widget", price=29.99, stock=100)


@pytest.fixture
def sample_products() -> list[Product]:
    """Create a list of sample products."""
    return [
        Product(product_id=1, name="Widget", price=29.99, stock=100),
        Product(product_id=2, name="Gadget", price=49.99, stock=50),
        Product(product_id=3, name="Gizmo", price=9.99, stock=0),
    ]


@pytest.fixture
def sample_order(sample_product: Product) -> Order:
    """Create a sample order with one item."""
    order = Order(order_id=1001)
    order.add_item(sample_product, quantity=2)
    return order


@pytest.fixture
def mock_payment_gateway() -> Mock:
    """Create a mock payment gateway that always succeeds.

    This is equivalent to Google Mock's NiceMock<MockPaymentGateway>.
    """
    gateway = Mock(spec=PaymentGateway)
    gateway.charge.return_value = {
        "status": "success",
        "transaction_id": "txn_abc123",
    }
    gateway.refund.return_value = True
    return gateway


@pytest.fixture
def mock_email_service() -> Mock:
    """Create a mock email service."""
    svc = Mock(spec=EmailService)
    svc.send_order_confirmation.return_value = True
    return svc


@pytest.fixture
def order_service(
    mock_payment_gateway: Mock,
    mock_email_service: Mock,
) -> OrderService:
    """Create an OrderService wired with mock dependencies."""
    return OrderService(
        payment_gateway=mock_payment_gateway,
        email_service=mock_email_service,
    )


# --- Database fixtures for integration tests ---


@pytest.fixture
def db_path(tmp_path: Path) -> Generator[str, None, None]:
    """Provide a temporary SQLite database path.

    Uses tmp_path (built-in pytest fixture) for automatic cleanup.
    Equivalent to Google Test SetUp/TearDown with a temp directory.
    """
    path = str(tmp_path / "test_products.db")
    yield path
    # tmp_path cleanup is automatic; explicit cleanup shown for clarity
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def product_repo(db_path: str) -> ProductRepository:
    """Provide an initialized ProductRepository with a temp database."""
    return ProductRepository(db_path)


@pytest.fixture
def seeded_repo(product_repo: ProductRepository) -> ProductRepository:
    """Provide a ProductRepository pre-loaded with sample data."""
    product_repo.save(Product(product_id=1, name="Widget", price=29.99, stock=100))
    product_repo.save(Product(product_id=2, name="Gadget", price=49.99, stock=50))
    product_repo.save(Product(product_id=3, name="Gizmo", price=9.99, stock=0))
    return product_repo


# =============================================================================
# Section 5: Basic Unit Tests
# =============================================================================


class TestProduct:
    """Unit tests for the Product dataclass.

    Equivalent in C++ Google Test:
        class ProductTest : public ::testing::Test { ... };
        TEST_F(ProductTest, IsAvailableWhenStockPositive) { ... }
    """

    def test_is_available_with_stock(self, sample_product: Product) -> None:
        """Product with stock > 0 should be available."""
        assert sample_product.is_available() is True

    def test_is_available_zero_stock(self) -> None:
        """Product with stock == 0 should not be available."""
        product = Product(product_id=99, name="Empty", price=1.0, stock=0)
        assert product.is_available() is False

    def test_apply_discount_valid(self, sample_product: Product) -> None:
        """Applying 10% discount to $29.99 product yields $26.99."""
        discounted = sample_product.apply_discount(10)
        assert discounted == 26.99

    def test_apply_discount_zero(self, sample_product: Product) -> None:
        """0% discount leaves price unchanged."""
        assert sample_product.apply_discount(0) == sample_product.price

    def test_apply_discount_full(self, sample_product: Product) -> None:
        """100% discount yields zero."""
        assert sample_product.apply_discount(100) == 0.0

    def test_apply_discount_out_of_range_raises(self, sample_product: Product) -> None:
        """Discount outside [0, 100] raises ValueError."""
        with pytest.raises(ValueError, match="Discount percent must be 0-100"):
            sample_product.apply_discount(150)

        with pytest.raises(ValueError, match="Discount percent must be 0-100"):
            sample_product.apply_discount(-10)

    def test_reduce_stock_success(self, sample_product: Product) -> None:
        """Reducing stock by a valid amount succeeds."""
        sample_product.reduce_stock(10)
        assert sample_product.stock == 90

    def test_reduce_stock_exceeds_raises(self, sample_product: Product) -> None:
        """Reducing stock beyond available raises ValueError."""
        with pytest.raises(ValueError, match="only 100 in stock"):
            sample_product.reduce_stock(200)


class TestOrder:
    """Unit tests for the Order class."""

    def test_empty_order_total_is_zero(self) -> None:
        order = Order(order_id=1)
        assert order.total == 0.0

    def test_order_total_after_adding_items(
        self, sample_product: Product
    ) -> None:
        order = Order(order_id=2)
        order.add_item(sample_product, quantity=3)
        assert order.total == round(29.99 * 3, 2)

    def test_add_item_reduces_stock(self, sample_product: Product) -> None:
        order = Order(order_id=3)
        order.add_item(sample_product, quantity=5)
        assert sample_product.stock == 95

    def test_add_item_zero_quantity_raises(
        self, sample_product: Product
    ) -> None:
        order = Order(order_id=4)
        with pytest.raises(ValueError, match="Quantity must be positive"):
            order.add_item(sample_product, quantity=0)


# =============================================================================
# Section 6: Parametrize -- Data-Driven Testing
# =============================================================================
#
# In C++ Google Test:
#     INSTANTIATE_TEST_SUITE_P(DiscountValues, ProductDiscountTest,
#         ::testing::Values(std::make_tuple(10, 26.99), ...));
#
# In C++ Catch2:
#     TEMPLATE_TEST_CASE("Discount", "[product]", float, 10.0f, 20.0f, 50.0f)


class TestParametrizedDiscount:
    """Parametrized tests for discount calculations.

    Each tuple defines (discount_percent, expected_result).
    pytest generates one test case per tuple automatically.
    """

    @pytest.mark.parametrize(
        "percent, expected",
        [
            (0, 29.99),
            (10, 26.99),
            (25, 22.49),
            (50, 15.0),
            (75, 7.5),
            (100, 0.0),
        ],
        ids=["no-discount", "10pct", "25pct", "50pct", "75pct", "full"],
    )
    def test_discount_values(
        self, percent: float, expected: float
    ) -> None:
        product = Product(product_id=1, name="Widget", price=29.99, stock=10)
        assert product.apply_discount(percent) == expected

    @pytest.mark.parametrize(
        "invalid_percent",
        [-1, -0.01, 100.01, 200, 999],
        ids=["neg-int", "neg-float", "just-over", "double", "large"],
    )
    def test_invalid_discount_raises(self, invalid_percent: float) -> None:
        product = Product(product_id=1, name="Widget", price=29.99, stock=10)
        with pytest.raises(ValueError):
            product.apply_discount(invalid_percent)


@pytest.mark.parametrize(
    "name, price, stock, expected_available",
    [
        ("InStock", 10.0, 1, True),
        ("ZeroStock", 10.0, 0, False),
        ("LargeStock", 10.0, 99999, True),
    ],
)
def test_product_availability_parametrized(
    name: str, price: float, stock: int, expected_available: bool
) -> None:
    """Standalone parametrized test (not inside a class)."""
    product = Product(product_id=1, name=name, price=price, stock=stock)
    assert product.is_available() == expected_available


# =============================================================================
# Section 7: Mocking Patterns
# =============================================================================
#
# C++ Google Mock:
#     class MockPaymentGateway : public PaymentGateway {
#     public:
#         MOCK_METHOD(ChargeResult, charge, (float, const std::string&));
#     };
#
# Python unittest.mock:
#     gateway = Mock(spec=PaymentGateway)
#     gateway.charge.return_value = {...}
#
# Key difference: Python mocks are runtime constructs; C++ mocks are
# compile-time generated via macros. Python offers patch() for monkey-patching
# module-level dependencies, which has no direct C++ equivalent.


class TestOrderServiceWithMocks:
    """Test OrderService using injected mock dependencies."""

    def test_place_order_success(
        self,
        order_service: OrderService,
        mock_payment_gateway: Mock,
        mock_email_service: Mock,
        sample_order: Order,
    ) -> None:
        """Successful order calls gateway and sends email."""
        result = order_service.place_order(sample_order, "customer@example.com")

        assert result["status"] == "placed"
        assert result["transaction_id"] == "txn_abc123"
        assert result["total"] == sample_order.total

        # Verify the mock was called with expected arguments
        mock_payment_gateway.charge.assert_called_once_with(sample_order.total)
        mock_email_service.send_order_confirmation.assert_called_once_with(
            sample_order.order_id, "customer@example.com"
        )

    def test_place_order_payment_failure(
        self,
        mock_payment_gateway: Mock,
        mock_email_service: Mock,
        sample_order: Order,
    ) -> None:
        """Failed payment raises PaymentError; email is never sent."""
        mock_payment_gateway.charge.return_value = {
            "status": "failure",
            "message": "Card declined",
        }
        service = OrderService(
            payment_gateway=mock_payment_gateway,
            email_service=mock_email_service,
        )

        with pytest.raises(PaymentError, match="Card declined"):
            service.place_order(sample_order, "customer@example.com")

        # Email should NOT have been called
        mock_email_service.send_order_confirmation.assert_not_called()

    def test_place_order_empty_order_raises(
        self,
        order_service: OrderService,
    ) -> None:
        """Empty order raises ValueError before any payment attempt."""
        empty_order = Order(order_id=9999)
        with pytest.raises(ValueError, match="empty order"):
            order_service.place_order(empty_order, "test@example.com")


class TestMockPatterns:
    """Demonstrates various mock patterns useful in enterprise testing."""

    def test_side_effect_for_sequential_responses(self) -> None:
        """Mock can return different values on successive calls.

        Equivalent to Google Mock:
            EXPECT_CALL(mock, charge)
                .WillOnce(Return(fail))
                .WillOnce(Return(success));
        """
        gateway = Mock(spec=PaymentGateway)
        gateway.charge.side_effect = [
            {"status": "failure", "message": "Timeout"},
            {"status": "success", "transaction_id": "txn_retry_1"},
        ]

        # First call fails
        result1 = gateway.charge(100.0)
        assert result1["status"] == "failure"

        # Second call succeeds
        result2 = gateway.charge(100.0)
        assert result2["status"] == "success"
        assert gateway.charge.call_count == 2

    def test_side_effect_with_exception(self) -> None:
        """Mock raises an exception to simulate network errors."""
        gateway = Mock(spec=PaymentGateway)
        gateway.charge.side_effect = ConnectionError("Network unreachable")

        with pytest.raises(ConnectionError, match="Network unreachable"):
            gateway.charge(50.0)

    def test_side_effect_function(self) -> None:
        """Mock delegates to a function for dynamic behavior."""

        def custom_charge(amount: float, currency: str = "USD") -> dict[str, Any]:
            if amount > 1000:
                return {"status": "failure", "message": "Over limit"}
            return {"status": "success", "transaction_id": f"txn_{int(amount)}"}

        gateway = Mock(spec=PaymentGateway)
        gateway.charge.side_effect = custom_charge

        assert gateway.charge(500.0)["status"] == "success"
        assert gateway.charge(2000.0)["status"] == "failure"

    @patch("time.time", return_value=1700000000.0)
    def test_patch_module_level_dependency(self, mock_time: Mock) -> None:
        """patch() replaces a module-level name for the test duration.

        This has no direct equivalent in C++ testing. In C++ you would
        inject a clock interface; Python allows monkey-patching.
        """
        assert time.time() == 1700000000.0
        mock_time.assert_called()

    def test_assert_called_with_matching_args(self) -> None:
        """Verify mock calls with specific argument matchers."""
        gateway = Mock(spec=PaymentGateway)
        gateway.charge(42.50, currency="EUR")

        # Exact match
        gateway.charge.assert_called_once_with(42.50, currency="EUR")

    def test_mock_attribute_access(self) -> None:
        """Mock supports attribute and item access for complex objects."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"id": 1, "name": "Test"}
        response.headers.__getitem__ = Mock(return_value="application/json")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test"


# =============================================================================
# Section 8: Integration Testing -- Database Layer
# =============================================================================
#
# Integration tests verify that multiple components work together correctly.
# Here we test the ProductRepository against a real SQLite database.
#
# In a C++ project, integration tests might link against a real database
# library and use Google Test's test environment for setup/teardown.


class TestProductRepositoryIntegration:
    """Integration tests for ProductRepository with SQLite.

    These tests use a real database (in temp dir) rather than mocks,
    verifying that SQL queries, schema, and data mapping all work together.
    """

    def test_save_and_find_by_id(self, product_repo: ProductRepository) -> None:
        """Saved product can be retrieved by ID."""
        product = Product(product_id=1, name="Widget", price=29.99, stock=100)
        product_repo.save(product)

        found = product_repo.find_by_id(1)
        assert found is not None
        assert found.name == "Widget"
        assert found.price == 29.99
        assert found.stock == 100

    def test_find_by_id_not_found(self, product_repo: ProductRepository) -> None:
        """Querying a non-existent ID returns None."""
        assert product_repo.find_by_id(9999) is None

    def test_save_replaces_on_conflict(
        self, product_repo: ProductRepository
    ) -> None:
        """Saving with the same ID replaces the existing record."""
        product_repo.save(Product(product_id=1, name="V1", price=10.0, stock=5))
        product_repo.save(Product(product_id=1, name="V2", price=20.0, stock=15))

        found = product_repo.find_by_id(1)
        assert found is not None
        assert found.name == "V2"
        assert found.price == 20.0

    def test_find_all(self, seeded_repo: ProductRepository) -> None:
        """find_all returns all products."""
        products = seeded_repo.find_all()
        assert len(products) == 3
        names = {p.name for p in products}
        assert names == {"Widget", "Gadget", "Gizmo"}

    def test_delete_existing_product(
        self, seeded_repo: ProductRepository
    ) -> None:
        """Deleting an existing product returns True."""
        assert seeded_repo.delete_by_id(1) is True
        assert seeded_repo.find_by_id(1) is None

    def test_delete_nonexistent_product(
        self, product_repo: ProductRepository
    ) -> None:
        """Deleting a non-existent product returns False."""
        assert product_repo.delete_by_id(9999) is False

    def test_full_lifecycle(self, product_repo: ProductRepository) -> None:
        """End-to-end lifecycle: create, read, update, delete."""
        # Create
        product = Product(product_id=42, name="Lifecycle", price=99.99, stock=10)
        product_repo.save(product)

        # Read
        found = product_repo.find_by_id(42)
        assert found is not None
        assert found.name == "Lifecycle"

        # Update (via INSERT OR REPLACE)
        updated = Product(product_id=42, name="Lifecycle v2", price=79.99, stock=20)
        product_repo.save(updated)
        found = product_repo.find_by_id(42)
        assert found is not None
        assert found.name == "Lifecycle v2"
        assert found.price == 79.99

        # Delete
        assert product_repo.delete_by_id(42) is True
        assert product_repo.find_by_id(42) is None


# =============================================================================
# Section 9: Integration Testing -- API-Like Service Layer
# =============================================================================
#
# Enterprise pattern: test the full service stack with real DB but mocked
# external services (payment gateway, email). This is a "narrow integration
# test" -- it tests our code end-to-end but stubs third-party boundaries.


class TestOrderServiceIntegration:
    """Integration tests for OrderService wired to real DB + mocked externals."""

    @pytest.fixture
    def integrated_service(
        self,
        seeded_repo: ProductRepository,
        mock_payment_gateway: Mock,
        mock_email_service: Mock,
    ) -> tuple[OrderService, ProductRepository]:
        """Wire OrderService with a real repo and mocked externals."""
        service = OrderService(
            payment_gateway=mock_payment_gateway,
            email_service=mock_email_service,
        )
        return service, seeded_repo

    def test_place_order_with_real_stock_reduction(
        self,
        integrated_service: tuple[OrderService, ProductRepository],
    ) -> None:
        """Place an order and verify stock is actually reduced in the DB."""
        service, repo = integrated_service
        product = repo.find_by_id(1)
        assert product is not None
        original_stock = product.stock

        order = Order(order_id=5001)
        order.add_item(product, quantity=3)

        result = service.place_order(order, "buyer@example.com")
        assert result["status"] == "placed"

        # Verify stock was physically reduced
        updated = repo.find_by_id(1)
        # Note: product object stock was reduced by add_item, but the DB
        # was not updated in this demo (ProductRepository.save() would be
        # called by a real service layer). Here we verify the object state.
        assert product.stock == original_stock - 3

    def test_order_cannot_exceed_stock(
        self,
        integrated_service: tuple[OrderService, ProductRepository],
    ) -> None:
        """Order exceeding stock raises before payment is attempted."""
        service, repo = integrated_service
        product = repo.find_by_id(3)  # Gizmo has stock=0
        assert product is not None

        order = Order(order_id=5002)
        with pytest.raises(ValueError, match="only 0 in stock"):
            order.add_item(product, quantity=1)


# =============================================================================
# Section 10: Marks, Skipping, and Expected Failures
# =============================================================================
#
# pytest marks let you selectively run tests:
#     pytest -m slow       -- only slow tests
#     pytest -m "not slow" -- skip slow tests


@pytest.mark.slow
def test_slow_performance_benchmark() -> None:
    """Example of a test marked as slow (for selective execution)."""
    time.sleep(0.1)  # Simulate slow operation
    result = sum(range(100000))
    assert result == 4999950000


@pytest.mark.skip(reason="Feature not yet implemented")
def test_future_feature() -> None:
    """This test is skipped until the feature is built."""
    pass


@pytest.mark.xfail(reason="Known bug #1234, not yet fixed")
def test_known_failure() -> None:
    """Expected to fail; pytest reports xfail instead of FAIL."""
    assert 1 + 1 == 3  # Known incorrect behavior


# =============================================================================
# Section 11: Fixtures with yield (Teardown Pattern)
# =============================================================================


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary config file and clean it up after the test.

    In C++ Google Test, this is equivalent to:
        void SetUp() override { createTempFile(); }
        void TearDown() override { removeTempFile(); }
    """
    config_path = tmp_path / "config.json"
    config_data = {"api_url": "https://api.example.com", "timeout": 30}
    config_path.write_text(json.dumps(config_data), encoding="utf-8")
    yield config_path
    # Teardown: file is auto-cleaned by tmp_path, but you could add
    # explicit cleanup logic here (e.g., deregistering a service)


def test_config_file_contents(temp_config_file: Path) -> None:
    """Verify the fixture-created config file has expected contents."""
    data = json.loads(temp_config_file.read_text(encoding="utf-8"))
    assert data["api_url"] == "https://api.example.com"
    assert data["timeout"] == 30


# =============================================================================
# Section 12: Fixture Factory Pattern
# =============================================================================
#
# When you need different configurations per test, use a factory fixture.
# The fixture returns a callable; each test calls it with custom params.


@pytest.fixture
def make_product() -> Callable[..., Product]:
    """Factory fixture: returns a function that creates products with defaults."""

    def _make(
        product_id: int = 1,
        name: str = "Default",
        price: float = 10.0,
        stock: int = 10,
    ) -> Product:
        return Product(
            product_id=product_id, name=name, price=price, stock=stock
        )

    return _make


def test_factory_fixture_creates_custom_products(
    make_product: Callable[..., Product],
) -> None:
    """Use the factory to create products with custom parameters."""
    cheap = make_product(price=1.99, stock=1000)
    expensive = make_product(name="Premium", price=999.99, stock=1)

    assert cheap.price == 1.99
    assert cheap.stock == 1000
    assert expensive.name == "Premium"
    assert expensive.price == 999.99


# =============================================================================
# Section 13: pytest Configuration Note
# =============================================================================
#
# In a real project, you would add a pyproject.toml or pytest.ini:
#
#     [tool.pytest.ini_options]
#     testpaths = ["tests"]
#     markers = ["slow: marks tests as slow"]
#     addopts = "-v --tb=short"
#
# To measure coverage:
#     pytest --cov=mymodule --cov-report=html
#
# C++ equivalent: gcov + lcov for GCC/Clang, or OpenCppCoverage on Windows.
#
# To run tests in parallel (like C++ parallel test execution):
#     pip install pytest-xdist
#     pytest -n auto


# =============================================================================
# Section 14: conftest.py Pattern (Demonstrated Inline)
# =============================================================================
#
# In a real project, fixtures shared across test files go in conftest.py.
# pytest auto-discovers conftest.py at each directory level.
#
# Project structure:
#     myproject/
#     |-- conftest.py          # shared fixtures (db_path, app_client, etc.)
#     |-- tests/
#     |   |-- conftest.py      # test-specific fixtures
#     |   |-- test_products.py
#     |   |-- test_orders.py
#     |   |-- integration/
#     |       |-- conftest.py  # integration-specific fixtures
#     |       |-- test_api.py
#     |-- src/
#         |-- myproject/
#             |-- __init__.py
#             |-- models.py
#             |-- services.py
#
# This is analogous to Google Test's test environment or a shared fixture
# base class, but pytest's conftest.py is more flexible because it uses
# dependency injection rather than class inheritance.


# =============================================================================
# Main Guard -- Demonstrates running tests programmatically
# =============================================================================

if __name__ == "__main__":
    # Running this file directly invokes pytest on itself.
    # This is convenient for quick development iteration.
    #
    # In production CI/CD (Jenkins, GitHub Actions, etc.), you would run:
    #     pytest tests/ -v --cov=src --cov-report=xml --junitxml=results.xml
    #
    # Equivalent C++ CI command:
    #     cmake --build . && ctest --output-on-failure

    import sys

    sys.exit(
        pytest.main(
            [
                __file__,
                "-v",
                "--tb=short",
                "-x",  # stop on first failure
            ]
        )
    )
