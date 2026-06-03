"""
Day 94 - 网络API接口设计 (Network API Interface Design)

C++ Comparison:
    REST API design principles are language-agnostic. In C++, you would use
    frameworks like Crow, Pistache, or Boost.Beast to build HTTP servers,
    but the design principles -- resource-based URLs, proper HTTP methods,
    JSON responses, versioning, pagination, and rate limiting -- apply
    equally to any language. Python's advantage here is the rich ecosystem
    of frameworks (Flask, FastAPI, Django REST Framework) that provide
    batteries-included solutions for these concerns.

    Key parallels:
    - C++ Boost.JSON / nlohmann::json  <-->  Python json / pydantic
    - C++ Crow route handlers           <-->  Flask / FastAPI route decorators
    - C++ template metaprogramming      <-->  Python dataclasses / Pydantic models
    - C++ RAII for resource cleanup      <-->  Python context managers

Topics covered:
    1. RESTful API design with resource-based routing
    2. API versioning (URL path vs. header)
    3. Structured error handling with custom error codes
    4. Pagination (offset-based and cursor-based)
    5. Rate limiting (token bucket algorithm)
"""

from __future__ import annotations

import re
import time
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, IntEnum
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)
from urllib.parse import urlparse, parse_qs


# ============================================================================
# 1. Structured Error Codes and Error Response Builder
# ============================================================================


class ErrorCode(IntEnum):
    """
    Global API error/status codes.

    In enterprise APIs, these codes let clients programmatically handle
    responses without parsing human-readable messages. This mirrors the
    pattern described in the document (codes 10000-10004).
    """
    SUCCESS = 10000
    COMMENT_CREATED = 10001
    COMMENT_CREATION_FAILED = 10002
    COMMENT_DELETED = 10003
    INVALID_REQUEST = 20000
    UNAUTHORIZED = 20001
    FORBIDDEN = 20002
    NOT_FOUND = 20003
    RATE_LIMITED = 20004
    INTERNAL_ERROR = 30000
    SERVICE_UNAVAILABLE = 30001


# Human-readable messages mapped to each code.
ERROR_MESSAGES: Dict[ErrorCode, str] = {
    ErrorCode.SUCCESS: "获取成功",
    ErrorCode.COMMENT_CREATED: "创建评论成功",
    ErrorCode.COMMENT_CREATION_FAILED: "无法创建评论",
    ErrorCode.COMMENT_DELETED: "评论已被删除",
    ErrorCode.INVALID_REQUEST: "请求参数无效",
    ErrorCode.UNAUTHORIZED: "未授权，请提供有效的身份标识",
    ErrorCode.FORBIDDEN: "无权访问该资源",
    ErrorCode.NOT_FOUND: "请求的资源不存在",
    ErrorCode.RATE_LIMITED: "请求过于频繁，请稍后重试",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",
    ErrorCode.SERVICE_UNAVAILABLE: "服务暂不可用",
}


@dataclass(frozen=True)
class APIResponse:
    """
    Enterprise-grade: Error Response Builder.

    Every API response follows a consistent envelope:
        { "code": int, "message": str, "data": ..., "timestamp": str }

    This pattern is ubiquitous in production Chinese tech APIs (Alibaba,
    Tencent, Baidu). It ensures clients can always branch on `code`.
    """
    code: ErrorCode
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "code": self.code.value,
            "message": self.message,
            "timestamp": self.timestamp,
        }
        if self.data is not None:
            result["data"] = self.data
        return result

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def success(cls, data: Optional[Dict[str, Any]] = None,
                message: Optional[str] = None) -> APIResponse:
        return cls(
            code=ErrorCode.SUCCESS,
            message=message or ERROR_MESSAGES[ErrorCode.SUCCESS],
            data=data,
        )

    @classmethod
    def error(cls, code: ErrorCode,
              extra_message: Optional[str] = None) -> APIResponse:
        base = ERROR_MESSAGES.get(code, "未知错误")
        msg = f"{base}: {extra_message}" if extra_message else base
        return cls(code=code, message=msg)


# ============================================================================
# 2. API Version Manager
# ============================================================================


class VersionStrategy(Enum):
    """Supported versioning strategies."""
    URL_PATH = "url_path"          # /api/v1/comments
    QUERY_PARAM = "query_param"    # /api/comments?version=1
    HEADER = "header"              # Accept-Version: 1
    MEDIA_TYPE = "media_type"      # Accept: application/vnd.myapp.v1+json


@dataclass
class APIVersion:
    """Represents a single API version with its lifecycle metadata."""
    version: str
    released: datetime
    deprecated: Optional[datetime] = None
    sunset: Optional[datetime] = None  # date after which the version is removed
    changelog: str = ""

    @property
    def is_deprecated(self) -> bool:
        return self.deprecated is not None and datetime.now(timezone.utc) >= self.deprecated

    @property
    def is_active(self) -> bool:
        now = datetime.now(timezone.utc)
        if self.sunset and now >= self.sunset:
            return False
        return True


class APIVersionManager:
    """
    Enterprise example: API Version Manager.

    Manages multiple API versions, resolves the requested version from
    various strategies, and handles deprecation headers.

    Usage:
        vm = APIVersionManager(strategy=VersionStrategy.URL_PATH)
        vm.register(APIVersion("1.0", released=datetime(2024, 1, 1)))
        vm.register(APIVersion("2.0", released=datetime(2025, 6, 1)))
        version = vm.resolve("/api/v2/comments", headers={})
    """

    def __init__(self, strategy: VersionStrategy = VersionStrategy.URL_PATH,
                 default_version: str = "1.0") -> None:
        self._strategy = strategy
        self._default_version = default_version
        self._versions: Dict[str, APIVersion] = {}

    def register(self, version: APIVersion) -> None:
        self._versions[version.version] = version

    def resolve(self, path: str = "/", headers: Optional[Dict[str, str]] = None,
                query_params: Optional[Dict[str, str]] = None) -> Tuple[APIVersion, Optional[str]]:
        """
        Resolve the API version from the request context.

        Returns:
            Tuple of (APIVersion, deprecation_warning_or_None).
        """
        headers = headers or {}
        query_params = query_params or {}

        requested: Optional[str] = None

        if self._strategy == VersionStrategy.URL_PATH:
            # Parse version from URL: /api/v2/comments -> "2"
            parts = path.strip("/").split("/")
            for part in parts:
                if part.startswith("v") and part[1:].isdigit():
                    requested = self._find_latest_minor(part[1:])
                    break

        elif self._strategy == VersionStrategy.QUERY_PARAM:
            requested = self._find_latest_minor(
                query_params.get("version", "")
            )

        elif self._strategy == VersionStrategy.HEADER:
            requested = self._find_latest_minor(
                headers.get("Accept-Version", "")
            )

        elif self._strategy == VersionStrategy.MEDIA_TYPE:
            accept = headers.get("Accept", "")
            # Parse: application/vnd.myapp.v2+json
            for segment in accept.split(";"):
                if "vnd.myapp.v" in segment:
                    for part in segment.split("."):
                        if part.startswith("v") and part[1:].isdigit():
                            requested = self._find_latest_minor(part[1:])
                            break

        if requested is None:
            requested = self._default_version

        if requested not in self._versions:
            raise ValueError(f"API version '{requested}' is not registered")

        ver = self._versions[requested]
        warning: Optional[str] = None
        if ver.is_deprecated:
            sunset_str = ver.sunset.isoformat() if ver.sunset else "TBD"
            warning = (
                f"API version {ver.version} is deprecated. "
                f"Sunset date: {sunset_str}. Please migrate to a newer version."
            )
        return ver, warning

    def _find_latest_minor(self, version_str: str) -> Optional[str]:
        """Given a major version number, find the latest registered minor version."""
        if not version_str:
            return None
        # Exact match first
        if version_str in self._versions:
            return version_str
        # Try prefix match (e.g. "2" matches "2.1")
        candidates = [
            v for v in self._versions if v.startswith(version_str + ".") or v.startswith(version_str)
        ]
        if candidates:
            return sorted(candidates)[-1]
        return version_str  # return as-is; caller will validate

    def list_versions(self) -> List[Dict[str, Any]]:
        """List all registered versions with status info."""
        result = []
        for ver in sorted(self._versions.values(), key=lambda v: v.version):
            status = "active"
            if not ver.is_active:
                status = "sunset"
            elif ver.is_deprecated:
                status = "deprecated"
            result.append({
                "version": ver.version,
                "status": status,
                "released": ver.released.isoformat(),
                "deprecated": ver.deprecated.isoformat() if ver.deprecated else None,
                "sunset": ver.sunset.isoformat() if ver.sunset else None,
            })
        return result


# ============================================================================
# 3. Pagination Helpers
# ============================================================================


T = TypeVar("T")


@dataclass
class PageRequest:
    """Offset-based pagination request parameters."""
    page: int = 1
    size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            self.page = 1
        if self.size < 1:
            self.size = 1
        if self.size > 100:
            self.size = 100

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


@dataclass
class CursorPageRequest:
    """Cursor-based pagination request (for large/infinite datasets)."""
    cursor: Optional[str] = None
    size: int = 20

    def __post_init__(self) -> None:
        if self.size < 1:
            self.size = 1
        if self.size > 100:
            self.size = 100


class Paginator(Generic[T]):
    """
    Enterprise example: Pagination Helper.

    Supports both offset-based and cursor-based pagination.

    Offset-based is simpler but has performance issues at high page numbers
    (the database must scan and discard all prior rows). Cursor-based uses
    the last item's identifier to fetch the next page efficiently.

    Usage:
        paginator = Paginator()
        page_result = paginator.paginate_offset(
            data=all_items,
            page_request=PageRequest(page=2, size=10),
            total_count=350,
        )
    """

    def paginate_offset(
        self,
        data: Sequence[T],
        page_request: PageRequest,
        total_count: int,
    ) -> Dict[str, Any]:
        """
        Build an offset-based pagination response.

        The response format matches the document's comment API spec:
        { "page": 1, "size": 10, "totalPage": 35, "contents": [...] }
        """
        total_pages = max(1, (total_count + page_request.size - 1) // page_request.size)
        return {
            "page": page_request.page,
            "size": page_request.size,
            "totalPage": total_pages,
            "totalCount": total_count,
            "hasNext": page_request.page < total_pages,
            "hasPrev": page_request.page > 1,
            "contents": list(data),
        }

    def paginate_cursor(
        self,
        data: Sequence[T],
        page_request: CursorPageRequest,
        get_cursor: Callable[[T], str],
    ) -> Dict[str, Any]:
        """
        Build a cursor-based pagination response.

        Args:
            data: The items for this page.
            page_request: The original request with cursor and size.
            get_cursor: A function that extracts a cursor string from an item.
        """
        next_cursor: Optional[str] = None
        if len(data) == page_request.size:
            # There might be more items
            next_cursor = get_cursor(data[-1])
        return {
            "size": page_request.size,
            "nextCursor": next_cursor,
            "hasNext": next_cursor is not None,
            "contents": list(data),
        }


# ============================================================================
# 4. Rate Limiter (Token Bucket Algorithm)
# ============================================================================


@dataclass
class _Bucket:
    """Internal state for a single rate-limit bucket."""
    tokens: float
    last_refill: float


class RateLimiter:
    """
    Token-bucket rate limiter.

    Each client identified by a key (e.g., API key, IP address) gets a
    bucket with a maximum capacity and a refill rate. Each request consumes
    one token. When the bucket is empty, the request is rejected.

    In C++, this same algorithm would be implemented with std::chrono and
    std::unordered_map; the logic is identical.

    Usage:
        limiter = RateLimiter(max_tokens=100, refill_rate=10)  # 100 burst, 10/sec sustained
        allowed, remaining, retry_after = limiter.allow("client_api_key")
        if not allowed:
            return APIResponse.error(ErrorCode.RATE_LIMITED)
    """

    def __init__(self, max_tokens: int = 100, refill_rate: float = 10.0) -> None:
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate  # tokens per second
        self._buckets: Dict[str, _Bucket] = {}

    def allow(self, key: str) -> Tuple[bool, int, Optional[float]]:
        """
        Check if a request from `key` is allowed.

        Returns:
            Tuple of (allowed, remaining_tokens, retry_after_seconds).
            retry_after is None when the request is allowed.
        """
        now = time.monotonic()

        if key not in self._buckets:
            self._buckets[key] = _Bucket(tokens=float(self._max_tokens), last_refill=now)

        bucket = self._buckets[key]

        # Refill tokens based on elapsed time
        elapsed = now - bucket.last_refill
        bucket.tokens = min(
            float(self._max_tokens),
            bucket.tokens + elapsed * self._refill_rate,
        )
        bucket.last_refill = now

        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True, int(bucket.tokens), None
        else:
            # Calculate how long until 1 token is available
            deficit = 1.0 - bucket.tokens
            retry_after = deficit / self._refill_rate
            return False, 0, retry_after

    def reset(self, key: str) -> None:
        """Reset the bucket for a given key (e.g., after plan upgrade)."""
        self._buckets.pop(key, None)


# ============================================================================
# 5. Authentication Helpers
# ============================================================================


@dataclass(frozen=True)
class AuthContext:
    """Parsed authentication context from a request."""
    user_id: str
    api_key: str
    roles: Tuple[str, ...] = ()

    def has_role(self, role: str) -> bool:
        return role in self.roles


class Authenticator:
    """
    Validates API keys and builds an AuthContext.

    In production, this would consult a database or external auth service.
    """

    def __init__(self) -> None:
        # Simulated user store: api_key -> user_info
        self._users: Dict[str, Dict[str, Any]] = {
            "key_alice": {"user_id": "1700095", "roles": ("user",)},
            "key_bob": {"user_id": "1995322", "roles": ("user", "admin")},
        }

    def authenticate(self, api_key: Optional[str]) -> Optional[AuthContext]:
        if api_key is None:
            return None
        user_info = self._users.get(api_key)
        if user_info is None:
            return None
        return AuthContext(
            user_id=user_info["user_id"],
            api_key=api_key,
            roles=tuple(user_info["roles"]),
        )


# ============================================================================
# 6. RESTful Resource Router (Simplified)
# ============================================================================


@dataclass
class Route:
    """A single registered route."""
    method: str
    path_pattern: str
    handler: Callable[..., APIResponse]
    version: Optional[str] = None

    def matches(self, method: str, path: str) -> Optional[Dict[str, str]]:
        """Check if this route matches the given method and path, extracting params."""
        if method.upper() != self.method.upper():
            return None
        pattern_parts = self.path_pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")
        if len(pattern_parts) != len(path_parts):
            return None
        params: Dict[str, str] = {}
        for pattern_seg, path_seg in zip(pattern_parts, path_parts):
            if pattern_seg.startswith("{") and pattern_seg.endswith("}"):
                param_name = pattern_seg[1:-1]
                params[param_name] = path_seg
            elif pattern_seg != path_seg:
                return None
        return params


class RESTRouter:
    """
    A minimal RESTful router demonstrating resource-based URL design.

    The document emphasizes: design APIs around business entities, not UI
    operations. This router follows that principle.

    Usage:
        router = RESTRouter()
        router.add("GET", "/articles/{article_id}/comments", list_comments)
        router.add("POST", "/articles/{article_id}/comments", create_comment)
        router.add("DELETE", "/articles/{article_id}/comments/{comment_id}", delete_comment)
    """

    def __init__(self) -> None:
        self._routes: List[Route] = []

    def add(self, method: str, path: str,
            handler: Callable[..., APIResponse],
            version: Optional[str] = None) -> None:
        self._routes.append(Route(method=method, path_pattern=path,
                                   handler=handler, version=version))

    def dispatch(self, method: str, path: str,
                 body: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None,
                 query: Optional[Dict[str, str]] = None) -> APIResponse:
        """Find a matching route and invoke its handler."""
        for route in self._routes:
            params = route.matches(method, path)
            if params is not None:
                try:
                    return route.handler(
                        path_params=params,
                        body=body or {},
                        headers=headers or {},
                        query=query or {},
                    )
                except ValueError as exc:
                    return APIResponse.error(ErrorCode.INVALID_REQUEST, str(exc))
                except PermissionError as exc:
                    return APIResponse.error(ErrorCode.FORBIDDEN, str(exc))
                except Exception as exc:
                    return APIResponse.error(ErrorCode.INTERNAL_ERROR, str(exc))
        return APIResponse.error(ErrorCode.NOT_FOUND, f"No route matches {method} {path}")


# ============================================================================
# 7. Sample Business Logic (Comment Resource)
# ============================================================================


# In-memory data store for demonstration purposes.
_comments_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "article_id": "100",
        "user_id": "1700095",
        "nickname": "王大锤",
        "content": "小编是不是有病呀",
        "pub_date": "2018-07-31T00:00:00Z",
    },
    {
        "id": 2,
        "article_id": "100",
        "user_id": "1995322",
        "nickname": "白元芳",
        "content": "楼上说得好",
        "pub_date": "2018-08-02T00:00:00Z",
    },
    {
        "id": 3,
        "article_id": "100",
        "user_id": "1700095",
        "nickname": "王大锤",
        "content": "再顶一次",
        "pub_date": "2018-08-05T00:00:00Z",
    },
]
_next_id = 4

# Shared instances
_authenticator = Authenticator()
_rate_limiter = RateLimiter(max_tokens=50, refill_rate=5.0)
_paginator = Paginator[Dict[str, Any]]()


def _require_auth(headers: Dict[str, str]) -> AuthContext:
    """Extract and validate auth from headers, raise PermissionError on failure."""
    api_key = headers.get("X-API-Key") or headers.get("key")
    ctx = _authenticator.authenticate(api_key)
    if ctx is None:
        raise PermissionError("Invalid or missing API key")
    return ctx


def _check_rate_limit(ctx: AuthContext) -> Optional[APIResponse]:
    """Return an error response if rate-limited, else None."""
    allowed, remaining, retry_after = _rate_limiter.allow(ctx.api_key)
    if not allowed:
        resp = APIResponse.error(ErrorCode.RATE_LIMITED)
        # In a real framework, you'd also set the Retry-After header.
        return resp
    return None


def list_comments(
    path_params: Dict[str, str],
    body: Dict[str, Any],
    headers: Dict[str, str],
    query: Dict[str, str],
) -> APIResponse:
    """
    GET /articles/{article_id}/comments

    Retrieves comments for an article with offset-based pagination.
    """
    ctx = _require_auth(headers)
    rate_resp = _check_rate_limit(ctx)
    if rate_resp:
        return rate_resp

    article_id = path_params["article_id"]
    page_req = PageRequest(
        page=int(query.get("page", 1)),
        size=int(query.get("size", 20)),
    )

    # Filter by article
    article_comments = [c for c in _comments_db if c["article_id"] == article_id]
    total = len(article_comments)
    start = page_req.offset
    end = start + page_req.limit
    page_data = article_comments[start:end]

    page_result = _paginator.paginate_offset(page_data, page_req, total)

    return APIResponse(
        code=ErrorCode.SUCCESS,
        message=ERROR_MESSAGES[ErrorCode.SUCCESS],
        data=page_result,
    )


def create_comment(
    path_params: Dict[str, str],
    body: Dict[str, Any],
    headers: Dict[str, str],
    query: Dict[str, str],
) -> APIResponse:
    """
    POST /articles/{article_id}/comments

    Creates a new comment on an article.
    """
    global _next_id
    ctx = _require_auth(headers)
    rate_resp = _check_rate_limit(ctx)
    if rate_resp:
        return rate_resp

    article_id = path_params["article_id"]
    content = body.get("content", "").strip()
    if not content:
        return APIResponse.error(ErrorCode.INVALID_REQUEST, "评论内容不能为空")
    if len(content) > 500:
        return APIResponse.error(ErrorCode.INVALID_REQUEST, "评论内容不能超过500字")

    # Simulate content moderation
    forbidden_words = ["spam", "广告"]
    if any(word in content for word in forbidden_words):
        return APIResponse.error(ErrorCode.COMMENT_CREATION_FAILED, "评论包含违禁内容")

    comment: Dict[str, Any] = {
        "id": _next_id,
        "article_id": article_id,
        "user_id": ctx.user_id,
        "nickname": body.get("nickname", "匿名用户"),
        "content": content,
        "pub_date": datetime.now(timezone.utc).isoformat(),
    }
    _next_id += 1
    _comments_db.append(comment)

    return APIResponse(
        code=ErrorCode.COMMENT_CREATED,
        message=ERROR_MESSAGES[ErrorCode.COMMENT_CREATED],
        data={"comment": comment},
    )


def delete_comment(
    path_params: Dict[str, str],
    body: Dict[str, Any],
    headers: Dict[str, str],
    query: Dict[str, str],
) -> APIResponse:
    """
    DELETE /articles/{article_id}/comments/{comment_id}

    Deletes a comment. Only the author or an admin can delete.
    """
    ctx = _require_auth(headers)
    rate_resp = _check_rate_limit(ctx)
    if rate_resp:
        return rate_resp

    comment_id = int(path_params["comment_id"])
    comment = next((c for c in _comments_db if c["id"] == comment_id), None)
    if comment is None:
        return APIResponse.error(ErrorCode.NOT_FOUND, "评论不存在")

    if comment["user_id"] != ctx.user_id and not ctx.has_role("admin"):
        return APIResponse.error(ErrorCode.FORBIDDEN, "只能删除自己的评论")

    _comments_db.remove(comment)
    return APIResponse(
        code=ErrorCode.COMMENT_DELETED,
        message=ERROR_MESSAGES[ErrorCode.COMMENT_DELETED],
    )


def get_system_info(
    path_params: Dict[str, str],
    body: Dict[str, Any],
    headers: Dict[str, str],
    query: Dict[str, str],
) -> APIResponse:
    """
    GET /system/info

    Returns system update information -- the document mentions designing an
    API that clients call first to check for updates.
    """
    return APIResponse.success(
        data={
            "latest_version": "3.2.0",
            "min_supported_version": "2.5.0",
            "update_url": "https://example.com/download",
            "changelog": "修复已知问题，提升用户体验",
        },
        message="获取系统信息成功",
    )


# ============================================================================
# 8. Application Assembly and Demonstration
# ============================================================================


def build_router() -> RESTRouter:
    """Assemble the REST router with all resource routes."""
    router = RESTRouter()

    # Resource-based routes (entity-centric, not operation-centric)
    router.add("GET", "/articles/{article_id}/comments", list_comments)
    router.add("POST", "/articles/{article_id}/comments", create_comment)
    router.add("DELETE", "/articles/{article_id}/comments/{comment_id}", delete_comment)
    router.add("GET", "/system/info", get_system_info)

    return router


def build_version_manager() -> APIVersionManager:
    """Set up the API version manager with multiple versions."""
    vm = APIVersionManager(strategy=VersionStrategy.URL_PATH, default_version="2.0")

    vm.register(APIVersion(
        version="1.0",
        released=datetime(2024, 1, 1, tzinfo=timezone.utc),
        deprecated=datetime(2025, 1, 1, tzinfo=timezone.utc),
        sunset=datetime(2026, 1, 1, tzinfo=timezone.utc),
        changelog="Initial release",
    ))
    vm.register(APIVersion(
        version="2.0",
        released=datetime(2025, 6, 1, tzinfo=timezone.utc),
        changelog="Added cursor-based pagination, improved error codes",
    ))
    vm.register(APIVersion(
        version="2.1",
        released=datetime(2026, 3, 1, tzinfo=timezone.utc),
        changelog="Added rate limiting headers, batch endpoints",
    ))

    return vm


def _simulate_request(
    router: RESTRouter,
    version_manager: APIVersionManager,
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    query: Optional[Dict[str, str]] = None,
) -> None:
    """Simulate a full API request lifecycle and print the result."""
    headers = headers or {}
    query = query or {}

    print(f"\n{'='*70}")
    print(f"Request: {method} {path}")
    if body:
        print(f"Body:    {json.dumps(body, ensure_ascii=False)}")
    if headers:
        print(f"Headers: {headers}")
    if query:
        print(f"Query:   {query}")

    # Version resolution
    try:
        version, warning = version_manager.resolve(path, headers, query)
        print(f"Version: {version.version} ({'deprecated' if version.is_deprecated else 'active'})")
        if warning:
            print(f"WARNING: {warning}")
    except ValueError as exc:
        resp = APIResponse.error(ErrorCode.NOT_FOUND, str(exc))
        print(f"\nResponse:\n{resp.to_json()}")
        return

    # Route dispatch -- strip version prefix so route patterns match
    dispatch_path = re.sub(r"/api/v[\d]+", "", path) or path

    resp = router.dispatch(method, dispatch_path, body=body, headers=headers, query=query)
    print(f"\nResponse:\n{resp.to_json()}")


def main() -> None:
    """
    Demonstrate the full API design system.

    This runs a series of simulated requests to show:
    - Resource-based routing (GET/POST/DELETE comments)
    - API version resolution and deprecation warnings
    - Pagination (offset-based)
    - Rate limiting
    - Structured error handling
    """
    router = build_router()
    version_manager = build_version_manager()

    auth_headers = {"X-API-Key": "key_alice"}
    admin_headers = {"X-API-Key": "key_bob"}

    print("=" * 70)
    print("  Day 94 - Network API Interface Design Demo")
    print("  RESTful API design, versioning, error handling,")
    print("  pagination, and rate limiting")
    print("=" * 70)

    # Show registered API versions
    print("\n--- Registered API Versions ---")
    for ver_info in version_manager.list_versions():
        print(f"  v{ver_info['version']}: {ver_info['status']} "
              f"(released {ver_info['released']})")

    # 1. System info endpoint
    _simulate_request(router, version_manager, "GET", "/api/v2/system/info",
                      headers=auth_headers)

    # 2. List comments with pagination
    _simulate_request(router, version_manager, "GET", "/api/v2/articles/100/comments",
                      headers=auth_headers, query={"page": "1", "size": "2"})

    # 3. Create a new comment
    _simulate_request(router, version_manager, "POST", "/api/v2/articles/100/comments",
                      headers=auth_headers,
                      body={"content": "这篇文章写得很好！", "nickname": "小明"})

    # 4. Create a comment with forbidden content
    _simulate_request(router, version_manager, "POST", "/api/v2/articles/100/comments",
                      headers=auth_headers,
                      body={"content": "这是一条spam广告"})

    # 5. Create a comment without auth
    _simulate_request(router, version_manager, "POST", "/api/v2/articles/100/comments",
                      body={"content": "无权发言"})

    # 6. Delete a comment (as admin)
    _simulate_request(router, version_manager, "DELETE",
                      "/api/v2/articles/100/comments/2",
                      headers=admin_headers)

    # 7. Delete another user's comment (as admin -- succeeds due to admin role)
    _simulate_request(router, version_manager, "DELETE",
                      "/api/v2/articles/100/comments/1",
                      headers={"X-API-Key": "key_bob"})

    # 8. Route not found
    _simulate_request(router, version_manager, "GET", "/api/v2/users/123/profile",
                      headers=auth_headers)

    # 9. Old API version with deprecation warning
    _simulate_request(router, version_manager, "GET", "/api/v1/articles/100/comments",
                      headers=auth_headers, query={"page": "1", "size": "5"})

    # 10. Rate limiting demo -- burst requests
    print(f"\n{'='*70}")
    print("Rate Limiting Demo (burst of 15 rapid requests):")
    print("=" * 70)
    limiter = RateLimiter(max_tokens=5, refill_rate=2.0)  # small bucket for demo
    for i in range(1, 16):
        allowed, remaining, retry_after = limiter.allow("demo_client")
        status = f"ALLOWED (remaining={remaining})" if allowed else f"BLOCKED (retry after {retry_after:.2f}s)"
        print(f"  Request {i:2d}: {status}")

    # 11. Cursor-based pagination example
    print(f"\n{'='*70}")
    print("Cursor-Based Pagination Example:")
    print("=" * 70)
    all_items = [
        {"id": i, "title": f"Article {i}"} for i in range(1, 52)
    ]
    cursor_paginator = Paginator[Dict[str, Any]]()

    # Simulate fetching 3 pages
    cursor: Optional[str] = None
    for page_num in range(1, 4):
        req = CursorPageRequest(cursor=cursor, size=10)
        # In a real app, the cursor would be used to query the database.
        # Here we simulate by slicing.
        start_idx = (page_num - 1) * 10
        page_items = all_items[start_idx:start_idx + 10]
        result = cursor_paginator.paginate_cursor(
            page_items, req, get_cursor=lambda item: str(item["id"])
        )
        cursor = result["nextCursor"]
        print(f"  Page {page_num}: {len(result['contents'])} items, "
              f"hasNext={result['hasNext']}, nextCursor={result['nextCursor']}")

    print(f"\n{'='*70}")
    print("Demo complete. All core API design patterns demonstrated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
