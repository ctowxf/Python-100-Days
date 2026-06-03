"""
56_cache_demo.py
================
Comprehensive caching demonstration for Python/Django applications.

Covers:
  1. Cache framework overview (Django cache abstraction layer)
  2. Redis cache with direct redis-py usage
  3. Memcached via pymemcache
  4. Custom cache decorators (function-level, TTL, key generation)
  5. Cache invalidation strategies (Cache Aside, Read/Write Through, Write Behind)
  6. Cache penetration / breakdown / avalanche protection

C++ comparison note:
    Django cache    -- high-level framework abstraction: configure once in
                      settings.py, then call cache.get/set or use @cache_page.
                      Serialisation, key-prefixing, connection pooling, and
                      cache-backend switching are all handled transparently.
    C++ Redis client -- you typically pick a library such as redis-plus-plus or
                      hiredis, manage connections and serialization yourself,
                      and write explicit get/set calls around every data access.
                      There is no built-in decorator or middleware; you must
                      integrate caching into your request pipeline manually.
                      Django's approach trades a small runtime overhead for
                      vastly less boilerplate and easier backend swapping.

Enterprise examples included:
  - Query cache   : expensive DB query results cached in Redis
  - Page cache    : full HTML/API responses cached by URL
  - API response cache: JSON endpoint cached with TTL + manual invalidation

Requirements (install only what you need):
    pip install django redis pymemcache

Usage:
    python 56_cache_demo.py
"""

from __future__ import annotations

import hashlib
import json
import time
import threading
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

# ---------------------------------------------------------------------------
# Try importing optional dependencies; fall back to stubs for demonstration.
# ---------------------------------------------------------------------------
try:
    import redis as _redis_mod
    HAS_REDIS: bool = True
except ImportError:
    HAS_REDIS = False
    _redis_mod = None  # type: ignore[assignment]

try:
    from pymemcache.client.base import Client as MemcachedClient
    HAS_MEMCACHED: bool = True
except ImportError:
    HAS_MEMCACHED = False
    MemcachedClient = None  # type: ignore[assignment,misc]

F = TypeVar("F", bound=Callable[..., Any])


# =========================================================================
#  1. SIMPLIFIED CACHE FRAMEWORK (mirrors Django's cache abstraction layer)
# =========================================================================

class BaseCache:
    """Abstract base cache -- mirrors Django's ``django.core.cache.backends.base``."""

    def __init__(self, default_timeout: int = 300) -> None:
        self._default_timeout = default_timeout

    def get(self, key: str) -> Any:
        raise NotImplementedError

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        raise NotImplementedError

    def has_key(self, key: str) -> bool:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class InMemoryCache(BaseCache):
    """Thread-safe in-memory cache (similar to Django's LocMemCache)."""

    def __init__(self, default_timeout: int = 300) -> None:
        super().__init__(default_timeout)
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires = entry
            if expires and time.time() > expires:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        ttl = timeout if timeout is not None else self._default_timeout
        expires = time.time() + ttl if ttl > 0 else 0.0
        with self._lock:
            self._store[key] = (value, expires)

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def has_key(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


class CacheManager:
    """
    Manages multiple named cache backends (mirrors Django's ``caches`` object).

    Usage:
        caches = CacheManager()
        caches.register('default', InMemoryCache())
        caches.register('redis', RedisCache(...))
        caches['default'].set('key', 'value')
    """

    def __init__(self) -> None:
        self._backends: dict[str, BaseCache] = {}

    def register(self, alias: str, backend: BaseCache) -> None:
        self._backends[alias] = backend

    def __getitem__(self, alias: str) -> BaseCache:
        try:
            return self._backends[alias]
        except KeyError:
            raise ValueError(f"Cache backend '{alias}' is not registered.")

    @property
    def default(self) -> BaseCache:
        return self["default"]


# =========================================================================
#  2. REDIS CACHE
# =========================================================================

class RedisCache(BaseCache):
    """
    Production-grade Redis cache wrapper.

    In a Django project this role is played by ``django_redis.cache.RedisCache``
    configured via the ``CACHES`` setting:

        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': ['redis://127.0.0.1:6379/0'],
                'KEY_PREFIX': 'myapp',
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'CONNECTION_POOL_KWARGS': {'max_connections': 512},
                    'PASSWORD': 'foobared',
                },
            },
        }
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "",
        default_timeout: int = 300,
    ) -> None:
        super().__init__(default_timeout)
        if not HAS_REDIS:
            raise ImportError("Install 'redis' package:  pip install redis")
        self._client: _redis_mod.Redis = _redis_mod.Redis(
            host=host, port=port, db=db, password=password, decode_responses=True,
        )
        self._prefix = key_prefix

    def _make_key(self, key: str) -> str:
        return f"{self._prefix}{key}" if self._prefix else key

    def get(self, key: str) -> Any:
        raw: Optional[str] = self._client.get(self._make_key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        ttl = timeout if timeout is not None else self._default_timeout
        serialized = json.dumps(value, ensure_ascii=False)
        if ttl > 0:
            self._client.setex(self._make_key(key), ttl, serialized)
        else:
            self._client.set(self._make_key(key), serialized)

    def delete(self, key: str) -> bool:
        return bool(self._client.delete(self._make_key(key)))

    def has_key(self, key: str) -> bool:
        return bool(self._client.exists(self._make_key(key)))

    def clear(self) -> None:
        self._client.flushdb()

    # -- Enterprise helpers ---------------------------------------------------

    def cache_aside(
        self, key: str, loader: Callable[[], Any], timeout: Optional[int] = None,
    ) -> Any:
        """
        Cache Aside pattern (Lazy Loading).
        1. Read from cache.
        2. On miss, call ``loader()`` to fetch from DB, write result to cache.
        """
        data = self.get(key)
        if data is not None:
            return data
        data = loader()
        self.set(key, data, timeout=timeout)
        return data

    def invalidate_with_update(
        self, key: str, updater: Callable[[], Any], new_value: Any,
    ) -> None:
        """
        Cache Aside pattern (write path).
        1. Update database via ``updater()``.
        2. Delete the cache key (NOT update it -- avoids stale race).
        """
        updater()
        self.delete(key)


# =========================================================================
#  3. MEMCACHED CACHE
# =========================================================================

class MemcachedCache(BaseCache):
    """
    Cache backend backed by Memcached via pymemcache.

    Django's built-in ``django.core.cache.backends.memcached.PyMemcacheCache``
    does the same thing when configured:

        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
                'LOCATION': '127.0.0.1:11211',
            },
        }
    """

    def __init__(
        self,
        server: str = "127.0.0.1",
        port: int = 11211,
        default_timeout: int = 300,
    ) -> None:
        super().__init__(default_timeout)
        if not HAS_MEMCACHED:
            raise ImportError(
                "Install 'pymemcache' package:  pip install pymemcache"
            )
        self._client = MemcachedClient((server, port))

    def get(self, key: str) -> Any:
        raw = self._client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        ttl = timeout if timeout is not None else self._default_timeout
        self._client.set(key, json.dumps(value, ensure_ascii=False), expire=ttl)

    def delete(self, key: str) -> bool:
        return self._client.delete(key)

    def has_key(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        self._client.flush_all()


# =========================================================================
#  4. CACHE DECORATORS
# =========================================================================

def cache_result(
    cache: BaseCache,
    key_prefix: str = "",
    timeout: int = 300,
    key_builder: Optional[Callable[..., str]] = None,
) -> Callable[[F], F]:
    """
    Generic decorator that caches the return value of a function.

    Works with *any* BaseCache backend (InMemory, Redis, Memcached).

    Parameters
    ----------
    cache : BaseCache
        The cache backend instance to use.
    key_prefix : str
        Prefix for the cache key.
    timeout : int
        TTL in seconds.
    key_builder : callable, optional
        ``(func_name, *args, **kwargs) -> str``  Custom key generator.

    Example::

        @cache_result(cache=my_cache, timeout=600)
        def get_subjects():
            return list(Subject.objects.all())
    """

    def _default_key_builder(func_name: str, *args: Any, **kwargs: Any) -> str:
        raw = f"{key_prefix}:{func_name}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(raw.encode()).hexdigest()

    builder = key_builder or _default_key_builder

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = builder(func.__name__, *args, **kwargs)
            cached = cache.get(cache_key)
            if cached is not None:
                print(f"  [cache HIT]  key={cache_key}")
                return cached
            print(f"  [cache MISS] key={cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def cache_page(cache: BaseCache, timeout: int = 300) -> Callable[[F], F]:
    """
    Page / API response cache decorator.

    Caches the entire response payload keyed by the request path/params.
    Mirrors Django's ``@cache_page`` but works outside of Django for demo.

    Example::

        @cache_page(cache=my_cache, timeout=3600)
        def api_subjects(request_path: str, **params):
            # expensive DB + serialization work
            return {"code": 20000, "subjects": [...]}
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            raw_key = f"page:{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(raw_key.encode()).hexdigest()
            cached = cache.get(cache_key)
            if cached is not None:
                print(f"  [page cache HIT]  key={cache_key}")
                return cached
            print(f"  [page cache MISS] key={cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


# =========================================================================
#  5. CACHE INVALIDATION STRATEGIES
# =========================================================================

@dataclass
class CacheAsideDemo:
    """
    Cache Aside Pattern (Lazy Invalidation).
    - Read :  check cache -> miss -> load from DB -> populate cache.
    - Write:  update DB -> delete cache (never update cache directly).
    """

    cache: BaseCache
    _fake_db: dict[str, Any] = field(default_factory=lambda: {
        "user:1": {"name": "Alice", "score": 95},
        "user:2": {"name": "Bob", "score": 88},
    })

    def read(self, key: str) -> Any:
        data = self.cache.get(key)
        if data is not None:
            print(f"  [CacheAside READ] cache hit  -> {key}")
            return data
        print(f"  [CacheAside READ] cache miss -> loading from DB")
        data = self._fake_db.get(key)
        if data is not None:
            self.cache.set(key, data, timeout=60)
        return data

    def write(self, key: str, value: Any) -> None:
        """Step 1: update DB.  Step 2: invalidate cache."""
        print(f"  [CacheAside WRITE] updating DB -> {key}")
        self._fake_db[key] = value
        print(f"  [CacheAside WRITE] deleting cache -> {key}")
        self.cache.delete(key)


@dataclass
class ReadWriteThroughCache:
    """
    Read/Write Through Pattern.
    The cache layer itself is responsible for loading from and syncing to
    the backing store, so the caller only interacts with the cache.

    Read Through  : cache miss triggers automatic DB load.
    Write Through : write goes to cache first, then synchronously to DB.
    """

    cache: BaseCache
    _fake_db: dict[str, Any] = field(default_factory=lambda: {
        "product:101": {"name": "Widget", "price": 29.99},
    })

    def _load_from_db(self, key: str) -> Any:
        print(f"    (ReadThrough) loading '{key}' from DB")
        return self._fake_db.get(key)

    def read_through(self, key: str) -> Any:
        """Transparent read: caller doesn't know if data came from cache or DB."""
        data = self.cache.get(key)
        if data is not None:
            print(f"  [ReadThrough] cache hit  -> {key}")
            return data
        data = self._load_from_db(key)
        if data is not None:
            self.cache.set(key, data, timeout=120)
        return data

    def write_through(self, key: str, value: Any) -> None:
        """Synchronous write: cache then DB."""
        print(f"  [WriteThrough] writing to cache -> {key}")
        self.cache.set(key, value, timeout=120)
        print(f"  [WriteThrough] writing to DB    -> {key}")
        self._fake_db[key] = value


@dataclass
class WriteBehindCache:
    """
    Write Behind (Write Back) Pattern.
    Writes go to cache immediately; a background worker periodically flushes
    dirty entries to the database.
    Trade-off: higher throughput but eventual consistency.
    """

    cache: BaseCache
    _fake_db: dict[str, Any] = field(default_factory=dict)
    _dirty_keys: list[str] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def write_behind(self, key: str, value: Any) -> None:
        print(f"  [WriteBehind] writing to cache only -> {key}")
        self.cache.set(key, value, timeout=300)
        with self._lock:
            if key not in self._dirty_keys:
                self._dirty_keys.append(key)

    def flush_to_db(self) -> None:
        """Simulate background flush (called periodically)."""
        with self._lock:
            keys = list(self._dirty_keys)
            self._dirty_keys.clear()
        for key in keys:
            value = self.cache.get(key)
            print(f"  [WriteBehind FLUSH] '{key}' -> DB")
            self._fake_db[key] = value


# =========================================================================
#  6. CACHE PROBLEM SOLVERS
# =========================================================================

class CacheProblemSolver:
    """Solutions for cache penetration, breakdown, and avalanche."""

    def __init__(self, cache: BaseCache, default_ttl: int = 300) -> None:
        self.cache = cache
        self.default_ttl = default_ttl
        self._mutexes: dict[str, bool] = {}
        self._mutex_lock = threading.Lock()

    # -- Cache Penetration: cache null results with short TTL -----------------

    def get_or_load_penetration_safe(
        self, key: str, loader: Callable[[], Any], null_ttl: int = 60,
    ) -> Any:
        """
        If the DB returns None/empty, cache the empty result with a short TTL
        to prevent repeated hits on the database for non-existent data.
        """
        data = self.cache.get(key)
        if data is not None:
            return None if data == "__NULL__" else data
        data = loader()
        if data is None or data == []:
            print(f"  [Penetration] caching NULL for '{key}' (TTL={null_ttl}s)")
            self.cache.set(key, "__NULL__", timeout=null_ttl)
            return None
        self.cache.set(key, data, timeout=self.default_ttl)
        return data

    # -- Cache Breakdown: mutex lock to prevent stampede ----------------------

    def get_or_load_with_mutex(
        self, key: str, loader: Callable[[], Any],
    ) -> Any:
        """
        When a hot key expires, only one thread loads from DB (others wait).
        """
        data = self.cache.get(key)
        if data is not None:
            return data

        lock_key = f"mutex:{key}"
        acquired = False
        with self._mutex_lock:
            if not self._mutexes.get(lock_key, False):
                self._mutexes[lock_key] = True
                acquired = True

        if acquired:
            try:
                print(f"  [Breakdown] acquired mutex for '{key}', loading from DB")
                data = loader()
                self.cache.set(key, data, timeout=self.default_ttl)
                return data
            finally:
                with self._mutex_lock:
                    self._mutexes[lock_key] = False
        else:
            # Another thread is loading; wait and retry.
            print(f"  [Breakdown] waiting for mutex on '{key}'...")
            for _ in range(50):
                time.sleep(0.05)
                data = self.cache.get(key)
                if data is not None:
                    return data
            return loader()

    # -- Cache Avalanche: jittered TTL ----------------------------------------

    def set_with_jitter(self, key: str, value: Any, base_ttl: Optional[int] = None) -> None:
        """
        Add a random jitter (0-60s) to the TTL to prevent many keys from
        expiring at the same time (cache avalanche).
        """
        import random
        ttl = (base_ttl or self.default_ttl) + random.randint(0, 60)
        print(f"  [Avalanche] setting '{key}' with jittered TTL={ttl}s")
        self.cache.set(key, value, timeout=ttl)


# =========================================================================
#  7. ENTERPRISE EXAMPLE: QUERY CACHE / PAGE CACHE / API RESPONSE CACHE
# =========================================================================

class EnterpriseCacheExamples:
    """Real-world caching patterns seen in production Django apps."""

    def __init__(self, cache: BaseCache) -> None:
        self.cache = cache

    # -- Query Cache ----------------------------------------------------------

    @staticmethod
    def _simulate_expensive_query(sql: str) -> list[dict[str, Any]]:
        """Simulates a slow database query."""
        print(f"    Executing SQL: {sql}")
        time.sleep(0.05)  # simulate latency
        return [
            {"id": 1, "name": "Computer Science", "intro": "CS dept"},
            {"id": 2, "name": "Mathematics", "intro": "Math dept"},
            {"id": 3, "name": "Physics", "intro": "Physics dept"},
        ]

    def query_cache_demo(self) -> list[dict[str, Any]]:
        """
        Cache expensive query results by SQL fingerprint.

        Django equivalent (programming style):
            redis_cli = get_redis_connection()
            data = redis_cli.get('polls:subjects')
            if data:
                data = json.loads(data)
            else:
                queryset = Subject.objects.all()
                data = SubjectSerializer(queryset, many=True).data
                redis_cli.set('polls:subjects', json.dumps(data), ex=86400)
        """
        sql = "SELECT * FROM tb_subject"
        cache_key = f"query:{hashlib.md5(sql.encode()).hexdigest()}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            print("  [QueryCache] hit")
            return cached
        print("  [QueryCache] miss -> querying DB")
        result = self._simulate_expensive_query(sql)
        self.cache.set(cache_key, result, timeout=3600)
        return result

    # -- Page Cache (full HTML / JSON response) -------------------------------

    def page_cache_demo(self, page_url: str) -> dict[str, Any]:
        """
        Cache full page responses keyed by URL.

        Django declarative equivalent (FBV):
            @api_view(['GET'])
            @cache_page(timeout=86400, cache='default')
            def show_subjects(request):
                ...

        Django declarative equivalent (CBV):
            @method_decorator(cache_page(timeout=86400), name='get')
            class SubjectView(ListAPIView):
                ...
        """
        cache_key = f"page:{hashlib.md5(page_url.encode()).hexdigest()}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            print(f"  [PageCache] hit  for {page_url}")
            return cached
        print(f"  [PageCache] miss for {page_url}")
        payload = {
            "code": 20000,
            "url": page_url,
            "subjects": self._simulate_expensive_query("SELECT * FROM tb_subject"),
            "rendered_at": time.time(),
        }
        self.cache.set(cache_key, payload, timeout=86400)
        return payload

    # -- API Response Cache with manual invalidation --------------------------

    def api_response_cache_demo(
        self, endpoint: str, params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Cache API responses; invalidate on data mutation.

        Typical flow:
            GET  /api/subjects/  ->  check cache -> return
            POST /api/subjects/  ->  write DB -> invalidate cache key
        """
        cache_key = f"api:{endpoint}:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            print(f"  [APIResponse] hit  {endpoint}")
            return cached
        print(f"  [APIResponse] miss {endpoint} -> computing")
        result = {
            "endpoint": endpoint,
            "params": params,
            "data": self._simulate_expensive_query(f"SELECT * FROM {endpoint}"),
        }
        self.cache.set(cache_key, result, timeout=1800)
        return result

    def api_invalidate(self, endpoint: str) -> None:
        """Invalidate all cached responses for an endpoint."""
        # In production, track keys in a set or use Redis SCAN with pattern.
        print(f"  [APIResponse] invalidating cache for {endpoint}")


# =========================================================================
#  MAIN DEMONSTRATION
# =========================================================================

def main() -> None:
    print("=" * 72)
    print("  CACHING DEMO -- Python 100 Days (Day 56)")
    print("=" * 72)

    # Always available -- no external dependencies needed.
    local_cache = InMemoryCache(default_timeout=120)
    caches = CacheManager()
    caches.register("default", local_cache)

    # ---- 1. Cache Framework Basics -----------------------------------------
    print("\n--- 1. Cache Framework (InMemoryCache) ---")
    caches.default.set("greeting", "hello", timeout=10)
    print(f"  get('greeting') -> {caches.default.get('greeting')}")
    caches.default.delete("greeting")
    print(f"  after delete    -> {caches.default.get('greeting')}")

    # ---- 2. Redis Cache ----------------------------------------------------
    print("\n--- 2. Redis Cache ---")
    if HAS_REDIS:
        try:
            redis_cache = RedisCache(
                host="127.0.0.1", port=6379, db=0, key_prefix="demo:", default_timeout=60,
            )
            caches.register("redis", redis_cache)
            redis_cache.set("subject:1", {"name": "Computer Science"})
            print(f"  Redis get -> {redis_cache.get('subject:1')}")
            redis_cache.delete("subject:1")
            print("  Redis delete OK")
        except Exception as exc:
            print(f"  Redis unavailable ({exc}), using InMemoryCache as fallback")
    else:
        print("  'redis' package not installed -- pip install redis")
        print("  (Django config example shown in docstring of RedisCache class)")

    # ---- 3. Memcached Cache ------------------------------------------------
    print("\n--- 3. Memcached Cache ---")
    if HAS_MEMCACHED:
        try:
            mc_cache = MemcachedCache("127.0.0.1", 11211)
            caches.register("memcached", mc_cache)
            mc_cache.set("product:1", {"name": "Widget", "price": 9.99})
            print(f"  Memcached get -> {mc_cache.get('product:1')}")
        except Exception as exc:
            print(f"  Memcached unavailable ({exc})")
    else:
        print("  'pymemcache' package not installed -- pip install pymemcache")

    # ---- 4. Cache Decorators -----------------------------------------------
    print("\n--- 4. Cache Decorators ---")
    mem_cache = caches.default  # use in-memory for demo

    @cache_result(cache=mem_cache, key_prefix="subjects", timeout=60)
    def get_all_subjects() -> list[dict[str, str]]:
        print("    (loading subjects from database...)")
        return [
            {"id": "1", "name": "Computer Science"},
            {"id": "2", "name": "Mathematics"},
            {"id": "3", "name": "Physics"},
        ]

    result1 = get_all_subjects()
    result2 = get_all_subjects()  # should hit cache
    print(f"  Same object? {result1 is result2}")

    @cache_page(cache=mem_cache, timeout=300)
    def render_subjects_page(path: str) -> dict[str, Any]:
        print(f"    (rendering page for {path})")
        return {"html": "<h1>Subjects</h1>", "path": path}

    page1 = render_subjects_page("/api/subjects/")
    page2 = render_subjects_page("/api/subjects/")
    print(f"  Same page object? {page1 is page2}")

    # ---- 5. Cache Invalidation Strategies ----------------------------------
    print("\n--- 5a. Cache Aside Pattern ---")
    aside = CacheAsideDemo(cache=mem_cache)
    aside.cache.clear()
    u1 = aside.read("user:1")
    print(f"  First read:  {u1}")
    u1_again = aside.read("user:1")
    print(f"  Second read: {u1_again} (from cache)")
    aside.write("user:1", {"name": "Alice", "score": 100})
    u1_after = aside.read("user:1")
    print(f"  After write: {u1_after} (re-loaded from DB)")

    print("\n--- 5b. Read/Write Through Pattern ---")
    rwt = ReadWriteThroughCache(cache=InMemoryCache())
    p = rwt.read_through("product:101")
    print(f"  First read:  {p}")
    p2 = rwt.read_through("product:101")
    print(f"  Second read: {p2} (from cache)")
    rwt.write_through("product:101", {"name": "Super Widget", "price": 39.99})
    p3 = rwt.read_through("product:101")
    print(f"  After write: {p3}")

    print("\n--- 5c. Write Behind Pattern ---")
    wb = WriteBehindCache(cache=InMemoryCache())
    wb.write_behind("order:9001", {"item": "Laptop", "qty": 2})
    wb.write_behind("order:9002", {"item": "Mouse", "qty": 5})
    print(f"  DB before flush: {wb._fake_db}")
    wb.flush_to_db()
    print(f"  DB after flush:  {wb._fake_db}")

    # ---- 6. Cache Problem Solvers ------------------------------------------
    print("\n--- 6a. Cache Penetration (null caching) ---")
    solver = CacheProblemSolver(cache=InMemoryCache(), default_ttl=300)
    val = solver.get_or_load_penetration_safe(
        "nonexistent", lambda: None, null_ttl=30,
    )
    print(f"  Result for missing key: {val}")
    val2 = solver.get_or_load_penetration_safe(
        "nonexistent", lambda: None, null_ttl=30,
    )
    print(f"  Second call (cached NULL): {val2}")

    print("\n--- 6b. Cache Breakdown (mutex/stampede) ---")
    breakdown_cache = InMemoryCache()
    bd_solver = CacheProblemSolver(cache=breakdown_cache, default_ttl=1)
    results: list[Any] = []

    def slow_loader() -> list[int]:
        time.sleep(0.1)
        return [1, 2, 3]

    def reader() -> None:
        results.append(bd_solver.get_or_load_with_mutex("hot_key", slow_loader))

    # Simulate concurrent access to an expired hot key.
    breakdown_cache.set("hot_key", [1, 2, 3], timeout=0)  # expire immediately
    threads = [threading.Thread(target=reader) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"  All threads got: {results}")

    print("\n--- 6c. Cache Avalanche (jittered TTL) ---")
    av_solver = CacheProblemSolver(cache=InMemoryCache(), default_ttl=300)
    for i in range(5):
        av_solver.set_with_jitter(f"key:{i}", f"value:{i}")

    # ---- 7. Enterprise Examples --------------------------------------------
    print("\n--- 7. Enterprise Examples ---")
    ent = EnterpriseCacheExamples(cache=InMemoryCache())

    print("\n  [Query Cache]")
    q1 = ent.query_cache_demo()
    q2 = ent.query_cache_demo()
    print(f"  Same result? {q1 is q2}")

    print("\n  [Page Cache]")
    pg1 = ent.page_cache_demo("/subjects/")
    pg2 = ent.page_cache_demo("/subjects/")
    print(f"  Same page? {pg1 is pg2}")

    print("\n  [API Response Cache]")
    ar1 = ent.api_response_cache_demo("/api/v1/subjects", {"page": 1})
    ar2 = ent.api_response_cache_demo("/api/v1/subjects", {"page": 1})
    print(f"  Same response? {ar1 is ar2}")
    ent.api_invalidate("/api/v1/subjects")

    # ---- Summary -----------------------------------------------------------
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print("""
    Cache Framework       : BaseCache -> InMemoryCache / RedisCache / MemcachedCache
    CacheManager          : Named backends, Django-like caches['alias'] access
    Decorators            : @cache_result (generic), @cache_page (response)
    Invalidation          : Cache Aside (delete-on-write), Read/Write Through,
                            Write Behind (async flush)
    Penetration defence   : Cache null/empty results with short TTL
    Breakdown defence     : Mutex lock on cache miss (only 1 thread loads)
    Avalanche defence     : Jittered TTL = base_ttl + random(0..60)s

    Django integration    :
      - Config CACHES{} in settings.py (Redis / Memcached / LocMem)
      - @cache_page(timeout=86400, cache='default') on FBV or CBV
      - get_redis_connection() for full Redis access (programming style)
      - cache.get() / cache.set() for framework-level cache ops
    """)
    print("=" * 72)


if __name__ == "__main__":
    main()
