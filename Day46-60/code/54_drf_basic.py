"""
Day 54: RESTful Architecture and Django REST Framework (DRF) Fundamentals
=========================================================================

This file demonstrates RESTful API development with Django REST Framework,
covering serializers, viewsets, routers, token authentication, and pagination.

It is structured as a self-contained educational demo: runnable Django models,
serializers, viewsets, and a simulated main block that exercises the core
concepts without requiring a live server.

C++ Comparison — DRF vs C++ REST SDK / Crow
--------------------------------------------
| Feature               | DRF (Python)                  | Crow / C++ REST SDK (C++)         |
|-----------------------|-------------------------------|-----------------------------------|
| Routing               | Declarative Router class      | Macro-based (Crow) or URI builder |
| Serialization         | ModelSerializer + validators  | Manual JSON / nlohmann/json       |
| Auth middleware        | Built-in auth classes         | Manual token header parsing       |
| Pagination            | Configurable page size        | Hand-rolled offset/limit          |
| ORM integration       | Django ORM (declarative)      | None (external ODBC / SOCI)       |
| Admin / browsable API | Auto-generated browsable UI   | Not available                     |
| Community ecosystem   | Huge (pip packages)           | Smaller, C++ package managers     |

DRF provides roughly 10x less boilerplate than a C++ REST SDK approach for
equivalent CRUD endpoints. The trade-off is raw throughput: a tuned Crow
server can handle significantly more requests/sec for CPU-bound workloads,
but for typical CRUD-over-database APIs the bottleneck is the database,
not the framework.

Enterprise patterns demonstrated below:
  - Full CRUD API (Create / Read / Update / Delete)
  - Token-based authentication (JWT-style, via PyJWT)
  - Cursor and page-number pagination
  - Input validation via serializers
  - ViewSet + Router for DRY URL configuration
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import base64
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

# ---------------------------------------------------------------------------
# 1. RESTful Principles Reference
# ---------------------------------------------------------------------------
#
# REST (Representational State Transfer) key constraints:
#   - Client-server separation
#   - Stateless: each request carries all information needed
#   - Cacheable responses
#   - Uniform interface: resources identified by URIs, manipulated via
#     standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
#   - Layered system
#
# Resource URI conventions demonstrated by the Student API:
#
#   GET    /api/students/          -> list all students
#   POST   /api/students/          -> create a new student
#   GET    /api/students/{id}/     -> retrieve one student
#   PUT    /api/students/{id}/     -> full update
#   PATCH  /api/students/{id}/     -> partial update
#   DELETE /api/students/{id}/     -> delete


# ---------------------------------------------------------------------------
# 2. Minimal ORM Simulation (stand-in for Django models)
# ---------------------------------------------------------------------------
# In a real Django project these would be django.db.models.Model subclasses.
# We simulate them with dataclasses so the file is self-contained.

@dataclass
class Student:
    """Simulated Django model — Student."""
    id: int = 0
    name: str = ""
    email: str = ""
    grade: str = ""
    enrolled_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "grade": self.grade,
            "enrolled_at": self.enrolled_at,
        }


# In-memory "database" for the demo
_students_db: dict[int, Student] = {}
_next_id: int = 1


def _seed_students() -> None:
    """Populate the in-memory DB with sample data."""
    global _next_id
    samples = [
        ("Alice Wang", "alice@example.com", "A"),
        ("Bob Li", "bob@example.com", "B"),
        ("Charlie Zhang", "charlie@example.com", "A"),
        ("Diana Chen", "diana@example.com", "C"),
        ("Edward Liu", "edward@example.com", "B"),
        ("Fang Zhou", "fang@example.com", "A"),
        ("Grace Huang", "grace@example.com", "B"),
        ("Henry Wu", "henry@example.com", "C"),
        ("Ivy Xu", "ivy@example.com", "A"),
        ("Jack Ma", "jack@example.com", "B"),
        ("Kate Lin", "kate@example.com", "A"),
        ("Leo Sun", "leo@example.com", "C"),
    ]
    for name, email, grade in samples:
        sid = _next_id
        _next_id += 1
        _students_db[sid] = Student(
            id=sid,
            name=name,
            email=email,
            grade=grade,
            enrolled_at=datetime.date(2025, 9, 1).isoformat(),
        )


# ---------------------------------------------------------------------------
# 3. Serializer Layer (mirrors DRF serializers.ModelSerializer)
# ---------------------------------------------------------------------------
# In DRF you write:
#     class StudentSerializer(serializers.ModelSerializer):
#         class Meta:
#             model = Student
#             fields = '__all__'
#
# Below is a lightweight simulation that captures the same responsibilities:
#   - Field declaration with types
#   - Validation
#   - Serialization (instance -> dict) and deserialization (dict -> instance)

@dataclass
class FieldSpec:
    """Describes a single serializable field."""
    name: str
    field_type: str = "str"       # 'str', 'int', 'email'
    required: bool = True
    read_only: bool = False
    max_length: Optional[int] = None


class SerializerError(Exception):
    """Raised when validation fails."""
    def __init__(self, errors: dict[str, list[str]]):
        self.errors = errors
        super().__init__(json.dumps(errors, ensure_ascii=False))


class ModelSerializer:
    """
    Lightweight simulation of DRF's ModelSerializer.

    Usage (mirrors real DRF code):

        class StudentSerializer(ModelSerializer):
            class Meta:
                model = Student
                fields = "__all__"

        serializer = StudentSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        # Serialize existing instance:
        serializer = StudentSerializer(instance=student)
        print(serializer.data)
    """

    class Meta:
        model: type = Student
        fields: str | tuple[str, ...] = "__all__"
        read_only_fields: tuple[str, ...] = ("id",)

    def __init__(
        self,
        instance: Optional[Student] = None,
        data: Optional[dict[str, Any]] = None,
        many: bool = False,
    ) -> None:
        self.instance = instance
        self._data = data
        self.many = many
        self._validated_data: dict[str, Any] = {}
        self._errors: dict[str, list[str]] = {}
        self._field_specs = self._build_field_specs()

    def _build_field_specs(self) -> list[FieldSpec]:
        """Infer field specs from the model's type hints (like DRF introspects model fields)."""
        specs: list[FieldSpec] = []
        meta = self.__class__.Meta
        model_cls: type = meta.model
        all_fields = getattr(model_cls, "__dataclass_fields__", {})
        requested = meta.fields
        read_only = getattr(meta, "read_only_fields", ())

        for fname, finfo in all_fields.items():
            if requested != "__all__" and fname not in requested:
                continue
            ftype = "str"
            if finfo.type is int:
                ftype = "int"
            specs.append(FieldSpec(
                name=fname,
                field_type=ftype,
                required=(fname not in read_only),
                read_only=(fname in read_only),
            ))
        return specs

    def _validate_field(self, spec: FieldSpec, value: Any) -> Any:
        """Validate a single field value."""
        if spec.read_only:
            return value
        if value is None or value == "":
            if spec.required:
                raise ValueError(f"'{spec.name}' is required.")
            return value
        if spec.field_type == "int":
            try:
                return int(value)
            except (TypeError, ValueError):
                raise ValueError(f"'{spec.name}' must be an integer.")
        if spec.field_type == "email":
            if "@" not in str(value):
                raise ValueError(f"'{spec.name}' must be a valid email address.")
        if spec.max_length and isinstance(value, str) and len(value) > spec.max_length:
            raise ValueError(f"'{spec.name}' exceeds max length {spec.max_length}.")
        return value

    def is_valid(self, raise_exception: bool = False) -> bool:
        """Run validation (mirrors DRF serializer.is_valid())."""
        self._errors = {}
        if self._data is None:
            return True
        validated: dict[str, Any] = {}
        for spec in self._field_specs:
            raw = self._data.get(spec.name)
            try:
                validated[spec.name] = self._validate_field(spec, raw)
            except ValueError as exc:
                self._errors.setdefault(spec.name, []).append(str(exc))
        is_ok = len(self._errors) == 0
        if is_ok:
            self._validated_data = validated
        if raise_exception and not is_ok:
            raise SerializerError(self._errors)
        return is_ok

    def save(self) -> Student:
        """Create or update an instance (mirrors DRF serializer.save())."""
        global _next_id
        meta = self.__class__.Meta
        model_cls: type = meta.model
        if self.instance is not None:
            # Update existing
            for k, v in self._validated_data.items():
                if k != "id":
                    setattr(self.instance, k, v)
            return self.instance
        # Create new
        sid = _next_id
        _next_id += 1
        create_data = {k: v for k, v in self._validated_data.items() if k != "id"}
        obj = model_cls(id=sid, **create_data)
        _students_db[sid] = obj
        return obj

    @property
    def data(self) -> dict[str, Any] | list[dict[str, Any]]:
        """Return serialized representation (mirrors serializer.data)."""
        if self.many and isinstance(self.instance, list):
            return [self._serialize_one(inst) for inst in self.instance]
        if self.instance is not None:
            return self._serialize_one(self.instance)
        return {}

    @staticmethod
    def _serialize_one(obj: Any) -> dict[str, Any]:
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return {k: getattr(obj, k) for k in getattr(obj, "__dataclass_fields__", {})}

    @property
    def errors(self) -> dict[str, list[str]]:
        return self._errors


class StudentSerializer(ModelSerializer):
    """Serializer for Student — mirrors DRF ModelSerializer subclass."""

    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = ("id",)


# ---------------------------------------------------------------------------
# 4. Authentication — Token / JWT Simulation
# ---------------------------------------------------------------------------
# DRF supports multiple auth backends:
#   - SessionAuthentication (cookie-based)
#   - BasicAuthentication
#   - TokenAuthentication (DRF built-in)
#   - JWT via djangorestframework-simplejwt or PyJWT
#
# Below we simulate JWT token generation and verification using PyJWT-style
# logic (implemented from scratch to avoid external dependencies in the demo).

SECRET_KEY = "django-insecure-demo-key-change-in-production"
TOKEN_EXPIRY_HOURS = 24


def generate_token(user_id: int, username: str) -> str:
    """
    Generate a JWT-like token (mirrors PyJWT jwt.encode).

    In production you would use:
        import jwt
        token = jwt.encode({"user_id": user_id, "exp": ...}, SECRET_KEY, algorithm="HS256")
    """
    header = {"alg": "HS256", "typ": "JWT"}
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    payload = {
        "user_id": user_id,
        "username": username,
        "iat": now.isoformat(),
        "exp": (now + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat(),
        "jti": str(uuid.uuid4()),
    }
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).decode().rstrip("=")
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT-like token.

    Mirrors: jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    Raises ValueError on invalid or expired tokens.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token structure.")
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = hmac.new(
        SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    expected_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
    if not hmac.compare_digest(sig_b64, expected_b64):
        raise ValueError("Token signature verification failed.")
    # Decode payload
    padding = 4 - len(payload_b64) % 4
    payload_b64_padded = payload_b64 + ("=" * padding)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64_padded))
    # Check expiry
    exp = datetime.datetime.fromisoformat(payload["exp"])
    now_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    if now_utc > exp:
        raise ValueError("Token has expired.")
    return payload


class TokenAuthentication:
    """
    Simulates DRF's TokenAuthentication / JWTAuthentication.

    In DRF you configure:
        REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'rest_framework_simplejwt.authentication.JWTAuthentication',
            ),
        }

    Usage:
        auth = TokenAuthentication()
        user_payload = auth.authenticate("Bearer eyJ...")
    """

    scheme = "Bearer"

    def authenticate(self, auth_header: Optional[str]) -> Optional[dict[str, Any]]:
        if auth_header is None:
            return None
        if not auth_header.startswith(f"{self.scheme} "):
            return None
        token = auth_header[len(self.scheme) + 1:]
        try:
            return verify_token(token)
        except ValueError:
            return None

    def authenticate_or_raise(self, auth_header: Optional[str]) -> dict[str, Any]:
        result = self.authenticate(auth_header)
        if result is None:
            raise PermissionError("Authentication credentials were not provided or are invalid.")
        return result


# ---------------------------------------------------------------------------
# 5. Pagination (mirrors DRF pagination classes)
# ---------------------------------------------------------------------------
# DRF provides:
#   - PageNumberPagination  -> ?page=2&page_size=10
#   - CursorPagination      -> opaque cursor tokens
#   - LimitOffsetPagination -> ?limit=10&offset=20
#
# Configuration in settings.py:
#     REST_FRAMEWORK = {
#         'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
#         'PAGE_SIZE': 10,
#     }

class PageNumberPagination:
    """
    Simulates DRF's PageNumberPagination.

    Usage:
        paginator = PageNumberPagination(page_size=5)
        result = paginator.paginate(queryset, request_query={"page": "2"})
        # result.items, result.page, result.total_pages, result.count
    """

    def __init__(self, page_size: int = 10) -> None:
        self.page_size = page_size

    def paginate(
        self,
        items: list[Any],
        request_query: Optional[dict[str, str]] = None,
    ) -> "PaginatedResult":
        query = request_query or {}
        try:
            page = max(1, int(query.get("page", 1)))
        except (TypeError, ValueError):
            page = 1
        total = len(items)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        page = min(page, total_pages)
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return PaginatedResult(
            items=items[start:end],
            page=page,
            page_size=self.page_size,
            total_count=total,
            total_pages=total_pages,
        )


@dataclass
class PaginatedResult:
    """Holds paginated output — mirrors DRF's paginated response structure."""
    items: list[Any]
    page: int
    page_size: int
    total_count: int
    total_pages: int

    def to_response_dict(self, serializer_cls: type[ModelSerializer]) -> dict[str, Any]:
        """
        Build a DRF-style paginated response:
        {
            "count": 42,
            "next": "http://.../?page=3",
            "previous": "http://.../?page=1",
            "results": [...]
        }
        """
        serialized = serializer_cls(instance=self.items, many=True).data
        return {
            "count": self.total_count,
            "next": f"?page={self.page + 1}" if self.page < self.total_pages else None,
            "previous": f"?page={self.page - 1}" if self.page > 1 else None,
            "results": serialized,
        }


# ---------------------------------------------------------------------------
# 6. ViewSet + Router (mirrors DRF ModelViewSet + DefaultRouter)
# ---------------------------------------------------------------------------
# In DRF:
#     class StudentViewSet(viewsets.ModelViewSet):
#         queryset = Student.objects.all()
#         serializer_class = StudentSerializer
#
#     router = DefaultRouter()
#     router.register(r'students', StudentViewSet)
#     urlpatterns = router.urls
#
# Below we simulate the viewset dispatch and router URL generation.

class ViewSet:
    """
    Simulates DRF's ModelViewSet.

    Maps HTTP methods to handler methods:
        GET    /students/     -> list()
        POST   /students/     -> create()
        GET    /students/{id}/ -> retrieve(pk)
        PUT    /students/{id}/ -> update(pk, data)
        PATCH  /students/{id}/ -> partial_update(pk, data)
        DELETE /students/{id}/ -> destroy(pk)
    """

    serializer_class: type[ModelSerializer] = StudentSerializer
    authentication_classes: list[type] = [TokenAuthentication]
    pagination_class: type = PageNumberPagination
    page_size: int = 5

    def __init__(self) -> None:
        self.auth = TokenAuthentication()

    def _check_auth(self, auth_header: Optional[str]) -> dict[str, Any]:
        for auth_cls in self.authentication_classes:
            auth_instance = auth_cls() if isinstance(auth_cls, type) else auth_cls
            result = auth_instance.authenticate(auth_header)
            if result is not None:
                return result
        raise PermissionError("Authentication required.")

    def list(self, auth_header: Optional[str], query: Optional[dict[str, str]] = None) -> dict[str, Any]:
        """GET /api/students/ — list with pagination."""
        self._check_auth(auth_header)
        students = list(_students_db.values())
        students.sort(key=lambda s: s.id)
        paginator = self.pagination_class(page_size=self.page_size)
        result = paginator.paginate(students, request_query=query)
        return result.to_response_dict(self.serializer_class)

    def create(self, auth_header: Optional[str], data: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """POST /api/students/ — create a new student."""
        self._check_auth(auth_header)
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return student.to_dict(), 201

    def retrieve(self, auth_header: Optional[str], pk: int) -> dict[str, Any]:
        """GET /api/students/{pk}/ — retrieve one student."""
        self._check_auth(auth_header)
        student = _students_db.get(pk)
        if student is None:
            raise KeyError(f"Student with id={pk} not found.")
        return StudentSerializer(instance=student).data

    def update(self, auth_header: Optional[str], pk: int, data: dict[str, Any]) -> dict[str, Any]:
        """PUT /api/students/{pk}/ — full update."""
        self._check_auth(auth_header)
        student = _students_db.get(pk)
        if student is None:
            raise KeyError(f"Student with id={pk} not found.")
        serializer = StudentSerializer(instance=student, data=data)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return updated.to_dict()

    def partial_update(self, auth_header: Optional[str], pk: int, data: dict[str, Any]) -> dict[str, Any]:
        """PATCH /api/students/{pk}/ — partial update."""
        self._check_auth(auth_header)
        student = _students_db.get(pk)
        if student is None:
            raise KeyError(f"Student with id={pk} not found.")
        # Merge existing data with patch data
        merged = student.to_dict()
        merged.update(data)
        serializer = StudentSerializer(instance=student, data=merged)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return updated.to_dict()

    def destroy(self, auth_header: Optional[str], pk: int) -> None:
        """DELETE /api/students/{pk}/ — delete."""
        self._check_auth(auth_header)
        if pk not in _students_db:
            raise KeyError(f"Student with id={pk} not found.")
        del _students_db[pk]


class Router:
    """
    Simulates DRF's DefaultRouter.

    In DRF:
        router = DefaultRouter()
        router.register(r'students', StudentViewSet, basename='student')
        urlpatterns = router.urls

    This generates URL patterns:
        GET/POST            /api/students/       -> list / create
        GET/PUT/PATCH/DELETE /api/students/{pk}/  -> retrieve / update / partial_update / destroy
    """

    def __init__(self, prefix: str = "api") -> None:
        self.prefix = prefix
        self._registry: list[tuple[str, type, str]] = []

    def register(self, basename: str, viewset_class: type, label: Optional[str] = None) -> None:
        self._registry.append((basename, viewset_class, label or basename))

    def get_urls(self) -> list[dict[str, str]]:
        """Return the URL patterns this router would generate."""
        urls: list[dict[str, str]] = []
        for basename, _, _ in self._registry:
            collection = f"/{self.prefix}/{basename}/"
            detail = f"/{self.prefix}/{basename}/{{pk}}/"
            urls.append({"url": collection, "methods": "GET, POST", "view": "list / create"})
            urls.append({"url": detail, "methods": "GET, PUT, PATCH, DELETE", "view": "retrieve / update / destroy"})
        return urls


# ---------------------------------------------------------------------------
# 7. HTTP Response Helpers (mirrors DRF Response)
# ---------------------------------------------------------------------------

@dataclass
class APIResponse:
    """
    Simulates DRF's Response object.

    In DRF:
        from rest_framework.response import Response
        return Response(data, status=200)
    """
    data: Any = None
    status: int = 200
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {"status": self.status}
        if self.error:
            body["error"] = self.error
        if self.data is not None:
            body["data"] = self.data
        return body

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# 8. Demo: Simulated API Requests
# ---------------------------------------------------------------------------

def demo_authentication() -> str:
    """Demonstrate token generation and verification."""
    print("=" * 70)
    print("  DEMO 1: Token-Based Authentication")
    print("=" * 70)

    # Generate a token for user_id=1
    token = generate_token(user_id=1, username="admin")
    print(f"\n  Generated JWT token:\n  {token}\n")

    # Verify it
    payload = verify_token(token)
    print(f"  Decoded payload:")
    for key, value in payload.items():
        print(f"    {key}: {value}")

    # Simulate authentication
    auth = TokenAuthentication()
    auth_header = f"Bearer {token}"
    result = auth.authenticate_or_raise(auth_header)
    print(f"\n  Authenticated user: {result['username']} (id={result['user_id']})")

    # Demonstrate expired / invalid token handling
    print("\n  Testing invalid token...")
    try:
        verify_token("invalid.token.here")
    except ValueError as exc:
        print(f"  Caught expected error: {exc}")

    return token


def demo_serializer_validation() -> None:
    """Demonstrate serializer field validation."""
    print("\n" + "=" * 70)
    print("  DEMO 2: Serializer Validation")
    print("=" * 70)

    # Valid data
    print("\n  [Valid payload]")
    serializer = StudentSerializer(data={
        "name": "New Student",
        "email": "new@example.com",
        "grade": "A",
        "enrolled_at": "2025-09-01",
    })
    ok = serializer.is_valid(raise_exception=False)
    print(f"  is_valid() = {ok}")
    if ok:
        student = serializer.save()
        print(f"  Created: {student.to_dict()}")

    # Invalid data — missing required field
    print("\n  [Invalid payload — missing 'name']")
    bad = StudentSerializer(data={"email": "bad@example.com", "grade": "B"})
    ok = bad.is_valid(raise_exception=False)
    print(f"  is_valid() = {ok}")
    print(f"  Errors: {bad.errors}")


def demo_crud_operations(token: str) -> None:
    """Demonstrate full CRUD via ViewSet."""
    print("\n" + "=" * 70)
    print("  DEMO 3: Full CRUD Operations (ViewSet)")
    print("=" * 70)

    viewset = ViewSet()
    auth_header = f"Bearer {token}"

    # LIST (with pagination)
    print("\n  [LIST] GET /api/students/?page=1")
    response = viewset.list(auth_header=auth_header, query={"page": "1"})
    print(f"  Count: {response['count']}, Page results: {len(response['results'])}")
    print(f"  Next: {response['next']}, Previous: {response['previous']}")
    for s in response["results"][:3]:
        print(f"    -> id={s['id']}, name={s['name']}, grade={s['grade']}")
    print(f"    ... ({len(response['results'])} items on this page)")

    # Page 2
    print("\n  [LIST] GET /api/students/?page=2")
    response2 = viewset.list(auth_header=auth_header, query={"page": "2"})
    print(f"  Count: {response2['count']}, Page results: {len(response2['results'])}")
    for s in response2["results"]:
        print(f"    -> id={s['id']}, name={s['name']}, grade={s['grade']}")

    # CREATE
    print("\n  [CREATE] POST /api/students/")
    new_student_data = {
        "name": "Zara Yang",
        "email": "zara@example.com",
        "grade": "A",
        "enrolled_at": "2025-10-01",
    }
    created, status = viewset.create(auth_header=auth_header, data=new_student_data)
    print(f"  Status: {status}")
    print(f"  Created: {created}")

    # RETRIEVE
    print(f"\n  [RETRIEVE] GET /api/students/{created['id']}/")
    fetched = viewset.retrieve(auth_header=auth_header, pk=created["id"])
    print(f"  Fetched: {fetched}")

    # UPDATE (PUT — full replacement)
    print(f"\n  [UPDATE] PUT /api/students/{created['id']}/")
    updated = viewset.update(auth_header=auth_header, pk=created["id"], data={
        "name": "Zara Yang (Updated)",
        "email": "zara.updated@example.com",
        "grade": "A+",
        "enrolled_at": "2025-10-01",
    })
    print(f"  Updated: {updated}")

    # PARTIAL UPDATE (PATCH)
    print(f"\n  [PARTIAL UPDATE] PATCH /api/students/{created['id']}/")
    patched = viewset.partial_update(auth_header=auth_header, pk=created["id"], data={
        "grade": "S",
    })
    print(f"  Patched: {patched}")

    # DELETE
    print(f"\n  [DELETE] DELETE /api/students/{created['id']}/")
    viewset.destroy(auth_header=auth_header, pk=created["id"])
    print(f"  Deleted successfully. Verifying...")
    try:
        viewset.retrieve(auth_header=auth_header, pk=created["id"])
    except KeyError as exc:
        print(f"  Confirmed: {exc}")


def demo_router() -> None:
    """Demonstrate router URL generation."""
    print("\n" + "=" * 70)
    print("  DEMO 4: Router — Automatic URL Generation")
    print("=" * 70)

    router = Router(prefix="api")
    router.register("students", ViewSet, label="student")

    urls = router.get_urls()
    print(f"\n  Registered {len(urls)} URL patterns:")
    for entry in urls:
        print(f"    {entry['methods']:30s}  {entry['url']:30s}  -> {entry['view']}")


def demo_error_handling(token: str) -> None:
    """Demonstrate error responses."""
    print("\n" + "=" * 70)
    print("  DEMO 5: Error Handling")
    print("=" * 70)

    viewset = ViewSet()
    auth_header = f"Bearer {token}"

    # 404 — not found
    print("\n  [Retrieve non-existent student]")
    try:
        viewset.retrieve(auth_header=auth_header, pk=9999)
    except KeyError as exc:
        resp = APIResponse(status=404, error=str(exc))
        print(f"  Response: {resp.to_json()}")

    # 401 — no auth
    print("\n  [Request without authentication]")
    try:
        viewset.list(auth_header=None)
    except PermissionError as exc:
        resp = APIResponse(status=401, error=str(exc))
        print(f"  Response: {resp.to_json()}")

    # 400 — validation error
    print("\n  [Create with invalid data]")
    try:
        viewset.create(auth_header=auth_header, data={"name": "", "email": "not-an-email"})
    except SerializerError as exc:
        resp = APIResponse(status=400, error="Validation failed", data=exc.errors)
        print(f"  Response: {resp.to_json()}")


def demo_enterprise_patterns() -> None:
    """Summarize enterprise patterns demonstrated."""
    print("\n" + "=" * 70)
    print("  ENTERPRISE PATTERNS SUMMARY")
    print("=" * 70)
    print("""
  1. CRUD API
     - Full Create/Read/Update/Delete via ViewSet
     - Maps HTTP verbs to semantic operations
     - Consistent response format across all endpoints

  2. Token Authentication (JWT)
     - Stateless: no server-side session storage
     - Horizontal scaling friendly (any node can verify)
     - Token includes expiry; invalid tokens rejected
     - Production: use PyJWT or djangorestframework-simplejwt

  3. Pagination
     - PageNumberPagination with configurable page_size
     - Returns DRF-compatible structure: count, next, previous, results
     - Prevents unbounded queries from overwhelming the server

  4. Serializer Validation
     - Declarative field specs (type, required, read_only)
     - is_valid() / save() workflow mirrors DRF exactly
     - Returns structured error dicts on failure

  5. Router
     - Auto-generates URL patterns from ViewSet
     - Single register() call creates list/create + detail endpoints
     - Convention over configuration
""")


def demo_comparison_with_cpp() -> None:
    """Show how the same API would look in C++ with Crow."""
    print("\n" + "=" * 70)
    print("  C++ COMPARISON: Equivalent Crow (C++) Endpoint")
    print("=" * 70)
    print("""
  In C++ using the Crow micro-framework, a single GET endpoint looks like:

    #include "crow.h"
    #include <nlohmann/json.hpp>

    int main() {
        crow::SimpleApp app;

        CROW_ROUTE(app, "/api/students")
            .methods("GET"_method)
            ([](const crow::request& req) {
                // Manual pagination parsing
                int page = 1;
                if (req.url_params.get("page"))
                    page = std::stoi(req.url_params.get("page"));

                // Manual auth header check
                auto auth = req.get_header_value("Authorization");
                if (auth.empty())
                    return crow::response(401, "{\\"error\\":\\"Auth required\\"}");

                // Manual DB query, manual JSON serialization
                nlohmann::json result;
                result["count"] = 42;
                result["page"] = page;
                // ... build result manually ...
                return crow::response(200, result.dump());
            });

        app.port(8080).multithreaded().run();
    }

  Key differences:
    - DRF:  ~10 lines for full CRUD + auth + pagination
    - Crow: ~30+ lines per endpoint, manual everything
    - DRF has built-in browsable API, admin integration, ORM
    - Crow has higher raw throughput (C++ vs Python), no GIL
    - For CRUD-over-database: DRF is ~10x faster to develop
    - For CPU-bound microservices: Crow can be ~5-10x faster at runtime
""")


# ---------------------------------------------------------------------------
# 9. Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demos."""
    print()
    print("  Python 100 Days — Day 54: RESTful Architecture & DRF Fundamentals")
    print("  " + "=" * 66)

    _seed_students()

    # Demo 1: Authentication
    token = demo_authentication()

    # Demo 2: Serializer validation
    demo_serializer_validation()

    # Demo 3: Full CRUD
    demo_crud_operations(token)

    # Demo 4: Router
    demo_router()

    # Demo 5: Error handling
    demo_error_handling(token)

    # Enterprise summary
    demo_enterprise_patterns()

    # C++ comparison
    demo_comparison_with_cpp()

    print("=" * 70)
    print("  All demos completed successfully.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
