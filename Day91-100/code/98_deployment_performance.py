"""
Day 98 - Deployment, Performance Tuning, and Monitoring
========================================================

Comprehensive demonstration of Python project deployment best practices,
performance profiling, load testing, caching strategies, database optimization,
and production monitoring.

Topics covered:
    - Deployment checklist and configuration
    - Performance profiling (cProfile, line_profiler, timeit)
    - Load testing with concurrent request simulation
    - Caching strategies (in-memory LRU, Redis-pattern cache, cache warming)
    - Database optimization (query profiling, connection pooling, indexing hints)
    - Application monitoring and health checks
    - Docker and process management (Supervisor/uWSGI concepts)

C++ Comparison: Python Deployment vs C++ Deployment Pipeline
-------------------------------------------------------------
| Aspect              | Python                          | C++                          |
|---------------------|---------------------------------|------------------------------|
| Packaging           | pip / wheel / poetry            | CMake / Conan / vcpkg        |
| Artifact            | .whl / source / container       | Binary executable / .so/.dll |
| Virtual env         | venv / virtualenv / conda       | Not needed (static linking)  |
| Interpreter         | CPython / PyPy needed at runtime| None (compiled to machine)   |
| Startup time        | Slower (module import, JIT warm)| Fast (native code entry)     |
| Runtime deps        | Python runtime + packages       | Shared libs or statically ld |
| Hot reload          | Yes (uwsgi --reload, gunicorn)  | No (recompile + restart)     |
| Container size      | Larger (base image + packages)  | Smaller (scratch + binary)   |
| CI/CD build         | Fast (no compilation)           | Slow (compile + link)        |
| Profiling tools     | cProfile, py-spy, line_profiler  | perf, gprof, Valgrind, gperftools |
| Debug               | pdb, remote-pdb                 | gdb, lldb, rr                |

Python deployment advantages:
    1. No compilation step -- faster iteration in CI/CD
    2. Hot-reload without downtime (Gunicorn preload + HUP signal)
    3. Rich ecosystem for WSGI/ASGI servers (uWSGI, Gunicorn, Uvicorn)
    4. Container images are reproducible via Dockerfile
    5. Dynamic nature allows runtime configuration injection

C++ deployment advantages:
    1. Single static binary simplifies distribution
    2. Lower memory footprint and startup latency
    3. Native performance eliminates interpreter overhead
    4. Compile-time optimization (LTO, PGO) for maximum throughput
    5. No need for a runtime environment on target machine

Requirements (optional, for live demos):
    pip install redis psutil

Run this file:
    python 98_deployment_performance.py
"""

from __future__ import annotations

import collections
import contextlib
import cProfile
import datetime
import functools
import hashlib
import io
import json
import logging
import math
import os
import pstats
import random
import sqlite3
import sys
import tempfile
import textwrap
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    Generator,
    List,
    NamedTuple,
    Optional,
    Protocol,
    Tuple,
    Union,
)

# ---------------------------------------------------------------------------
# 模块级日志配置
# ---------------------------------------------------------------------------
logger: Final = logging.getLogger(__name__)


# ===================================================================
# Section 1 -- 部署检查清单 (Deployment Checklist)
# ===================================================================


@dataclass
class DeploymentCheckItem:
    """部署检查清单中的一个条目。"""

    name: str
    description: str
    is_critical: bool = True
    checked: bool = False


class DeploymentChecklist:
    """项目上线前的部署检查清单管理器。

    涵盖Django项目上线前必须完成的安全和配置检查，
    参照Django官方的deploy检查命令 (manage.py check --deploy)。
    """

    def __init__(self) -> None:
        self._items: List[DeploymentCheckItem] = []

    def add(self, name: str, description: str, is_critical: bool = True) -> None:
        """添加一个检查项。"""
        self._items.append(
            DeploymentCheckItem(name=name, description=description, is_critical=is_critical)
        )

    def check(self, name: str) -> None:
        """标记某个检查项为已通过。"""
        for item in self._items:
            if item.name == name:
                item.checked = True
                return
        raise KeyError(f"Check item '{name}' not found")

    def unchecked_critical(self) -> List[DeploymentCheckItem]:
        """返回所有未通过的关键检查项。"""
        return [item for item in self._items if item.is_critical and not item.checked]

    def summary(self) -> Dict[str, int]:
        """返回检查清单的统计摘要。"""
        total = len(self._items)
        checked = sum(1 for i in self._items if i.is_critical and i.checked)
        critical = sum(1 for i in self._items if i.is_critical)
        return {"total": total, "critical": critical, "critical_checked": checked}

    def display(self) -> str:
        """生成可读的检查清单报告。"""
        lines = ["=" * 60, "部署检查清单 (Deployment Checklist)", "=" * 60]
        for item in self._items:
            status = "[OK]" if item.checked else "[!!]"
            severity = "(关键)" if item.is_critical else "(建议)"
            lines.append(f"  {status} {severity} {item.name}")
            lines.append(f"        {item.description}")
        summary = self.summary()
        lines.append(f"\n  总计: {summary['total']} 项, "
                      f"关键项: {summary['critical_checked']}/{summary['critical']} 已通过")
        return "\n".join(lines)


def build_django_deployment_checklist() -> DeploymentChecklist:
    """构建一个Django项目的标准部署检查清单。

    覆盖文档中提到的所有上线前检查项：
    - DEBUG = False
    - ALLOWED_HOSTS 配置
    - HTTPS / HSTS 安全头
    - 敏感信息外置（环境变量）
    - 静态文件收集
    """
    checklist = DeploymentChecklist()

    checklist.add(
        "DEBUG设置为False",
        "settings.py中DEBUG = False，避免泄露调试信息给终端用户",
    )
    checklist.add(
        "ALLOWED_HOSTS配置",
        "配置允许访问的域名/IP白名单，例如 ALLOWED_HOSTS = ['example.com']",
    )
    checklist.add(
        "HTTPS强制跳转",
        "SECURE_SSL_REDIRECT = True，所有HTTP请求自动重定向到HTTPS",
    )
    checklist.add(
        "HSTS安全头",
        "SECURE_HSTS_SECONDS = 3600, SECURE_HSTS_INCLUDE_SUBDOMAINS = True",
    )
    checklist.add(
        "安全Cookie配置",
        "SESSION_COOKIE_SECURE = True, CSRF_COOKIE_SECURE = True",
    )
    checklist.add(
        "XSS和内容嗅探保护",
        "SECURE_BROWSER_XSS_FILTER = True, SECURE_CONTENT_TYPE_NOSNIFF = True",
    )
    checklist.add(
        "防点击劫持",
        "X_FRAME_OPTIONS = 'DENY'，禁止iframe嵌入",
    )
    checklist.add(
        "SECRET_KEY外置",
        "通过环境变量或密钥管理服务加载SECRET_KEY，不硬编码在代码中",
    )
    checklist.add(
        "数据库凭据外置",
        "DB_USER / DB_PASS 等通过环境变量注入",
    )
    checklist.add(
        "静态文件收集",
        "执行 python manage.py collectstatic，配置STATIC_ROOT",
    )
    checklist.add(
        "日志配置",
        "配置生产环境日志级别和输出路径，确保错误可追踪",
    )
    checklist.add(
        "依赖锁定",
        "pip freeze > requirements.txt 或使用 poetry.lock 锁定版本",
    )

    return checklist


# ===================================================================
# Section 2 -- 性能分析器 (Performance Profiler)
# ===================================================================


class ProfileResult(NamedTuple):
    """性能分析结果。"""

    function_name: str
    total_calls: int
    total_time: float  # 秒
    per_call_time: float  # 秒
    top_functions: List[Tuple[str, float, int]]  # (name, cumtime, calls)


class PerformanceProfiler:
    """基于cProfile的性能分析工具。

    提供简单接口来分析函数的执行时间和调用频率，
    帮助开发者找到性能瓶颈。

    C++ 对比:
        - cProfile 对标 gprof / perf
        - Python的cProfile是确定性分析(deterministic profiling)
        - C++的perf是统计性采样(sampling profiler)
        - Python可以使用py-spy进行非侵入式采样分析，类似perf
    """

    @staticmethod
    def profile_function(func: Callable, *args: Any, **kwargs: Any) -> Tuple[Any, ProfileResult]:
        """对单个函数进行性能分析。

        Args:
            func: 要分析的函数
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数

        Returns:
            (函数返回值, 性能分析结果)
        """
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()

        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")

        # 提取top函数信息
        top_funcs: List[Tuple[str, float, int]] = []
        for key, value in stats.stats.items():
            filename, lineno, funcname = key
            cumtime = value[3]  # 累计时间
            calls = value[0]    # 调用次数
            top_funcs.append((funcname, cumtime, calls))
        top_funcs.sort(key=lambda x: x[1], reverse=True)

        profile_result = ProfileResult(
            function_name=func.__name__,
            total_calls=stats.total_calls,
            total_time=stats.total_tt,
            per_call_time=stats.total_tt / max(stats.total_calls, 1),
            top_functions=top_funcs[:10],
        )

        return result, profile_result

    @staticmethod
    def format_report(result: ProfileResult) -> str:
        """将性能分析结果格式化为可读报告。"""
        lines = [
            "=" * 60,
            f"性能分析报告: {result.function_name}",
            "=" * 60,
            f"  总调用次数 : {result.total_calls}",
            f"  总执行时间 : {result.total_time:.6f} 秒",
            f"  每次调用   : {result.per_call_time:.9f} 秒",
            "",
            "  Top 10 耗时函数:",
            "  " + "-" * 56,
        ]
        for name, cumtime, calls in result.top_functions:
            lines.append(f"    {name:<30s} {cumtime:>10.6f}s  ({calls} calls)")
        return "\n".join(lines)


# 模拟被分析的业务函数
def simulate_db_query(num_queries: int = 100) -> List[Dict[str, Any]]:
    """模拟数据库查询操作，用于性能分析演示。

    模拟了实际开发中常见的查询模式：
    - 逐条查询（存在N+1问题）
    - 无索引的全表扫描
    """
    results: List[Dict[str, Any]] = []
    for i in range(num_queries):
        # 模拟查询延迟
        time.sleep(0.0001)
        results.append({"id": i, "value": f"record_{i}", "score": random.random()})
    return results


def simulate_data_processing(data_size: int = 10000) -> float:
    """模拟数据处理流程，用于性能分析演示。

    包含CPU密集型操作（排序、数学计算）和内存分配。
    """
    # 生成随机数据
    data = [random.gauss(0, 1) for _ in range(data_size)]
    # 排序操作
    sorted_data = sorted(data)
    # 统计计算
    mean_val = sum(sorted_data) / len(sorted_data)
    variance = sum((x - mean_val) ** 2 for x in sorted_data) / len(sorted_data)
    std_dev = math.sqrt(variance)
    return std_dev


# ===================================================================
# Section 3 -- 负载测试脚本 (Load Testing)
# ===================================================================


@dataclass
class LoadTestResult:
    """负载测试结果。"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float  # 总耗时(秒)
    avg_response_time: float  # 平均响应时间(秒)
    min_response_time: float
    max_response_time: float
    p95_response_time: float  # 95th百分位
    p99_response_time: float  # 99th百分位
    requests_per_second: float
    errors: List[str] = field(default_factory=list)


class LoadTester:
    """简单的负载测试工具。

    模拟并发请求来评估服务的吞吐量和响应时间。
    在生产环境中建议使用 locust 或 wrk 等专业工具。

    C++ 对比:
        - Python使用ThreadPoolExecutor实现并发
        - C++可使用 libcurl + std::thread 或 Boost.Asio
        - 专业工具: wrk (C), wrk2, vegeta (Go)
        - Python的GIL在I/O密集型负载测试中影响较小
          因为大部分时间花在等待网络响应上
    """

    def __init__(self, target_func: Callable[..., Any], num_requests: int = 100,
                 concurrency: int = 10) -> None:
        """初始化负载测试器。

        Args:
            target_func: 被测试的目标函数（模拟HTTP请求处理）
            num_requests: 总请求数
            concurrency: 并发数
        """
        self._target_func = target_func
        self._num_requests = num_requests
        self._concurrency = concurrency

    def run(self) -> LoadTestResult:
        """执行负载测试。"""
        response_times: List[float] = []
        errors: List[str] = []
        success_count = 0
        fail_count = 0

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=self._concurrency) as executor:
            futures = [
                executor.submit(self._execute_single_request, i)
                for i in range(self._num_requests)
            ]
            for future in as_completed(futures):
                try:
                    elapsed = future.result()
                    response_times.append(elapsed)
                    success_count += 1
                except Exception as exc:
                    fail_count += 1
                    errors.append(str(exc))

        total_time = time.perf_counter() - start_time

        # 计算统计数据
        if response_times:
            response_times.sort()
            avg_time = sum(response_times) / len(response_times)
            p95_idx = int(len(response_times) * 0.95)
            p99_idx = int(len(response_times) * 0.99)
        else:
            avg_time = 0.0
            p95_idx = 0
            p99_idx = 0

        return LoadTestResult(
            total_requests=self._num_requests,
            successful_requests=success_count,
            failed_requests=fail_count,
            total_time=total_time,
            avg_response_time=avg_time,
            min_response_time=response_times[0] if response_times else 0.0,
            max_response_time=response_times[-1] if response_times else 0.0,
            p95_response_time=response_times[p95_idx] if response_times else 0.0,
            p99_response_time=response_times[p99_idx] if response_times else 0.0,
            requests_per_second=(success_count / total_time) if total_time > 0 else 0.0,
            errors=errors[:10],  # 只保留前10个错误
        )

    def _execute_single_request(self, request_id: int) -> float:
        """执行单个请求并返回响应时间。"""
        start = time.perf_counter()
        self._target_func(request_id)
        return time.perf_counter() - start

    @staticmethod
    def format_report(result: LoadTestResult) -> str:
        """格式化负载测试报告。"""
        lines = [
            "=" * 60,
            "负载测试报告 (Load Test Report)",
            "=" * 60,
            f"  总请求数       : {result.total_requests}",
            f"  成功请求       : {result.successful_requests}",
            f"  失败请求       : {result.failed_requests}",
            f"  总耗时         : {result.total_time:.3f} 秒",
            f"  吞吐量(RPS)    : {result.requests_per_second:.1f} req/s",
            "",
            "  响应时间统计:",
            f"    平均         : {result.avg_response_time * 1000:.2f} ms",
            f"    最小         : {result.min_response_time * 1000:.2f} ms",
            f"    最大         : {result.max_response_time * 1000:.2f} ms",
            f"    P95          : {result.p95_response_time * 1000:.2f} ms",
            f"    P99          : {result.p99_response_time * 1000:.2f} ms",
        ]
        if result.errors:
            lines.append(f"\n  错误示例 (前{len(result.errors)}个):")
            for err in result.errors:
                lines.append(f"    - {err}")
        return "\n".join(lines)


# 模拟一个HTTP请求处理函数
def simulate_request_handler(request_id: int) -> Dict[str, Any]:
    """模拟Web应用的请求处理逻辑。

    包含: 参数解析 -> 业务逻辑 -> 数据库查询 -> 响应构建。
    """
    # 模拟参数解析（CPU密集）
    _ = hashlib.md5(f"request_{request_id}".encode()).hexdigest()

    # 模拟数据库查询（I/O等待）
    time.sleep(random.uniform(0.001, 0.005))

    # 模拟响应构建
    return {
        "request_id": request_id,
        "status": "ok",
        "timestamp": time.time(),
    }


# ===================================================================
# Section 4 -- 缓存策略 (Caching Strategies)
# ===================================================================


class CacheEntry(NamedTuple):
    """缓存条目，包含值和过期时间。"""

    value: Any
    expire_at: float  # Unix时间戳
    created_at: float


class MemoryCache:
    """带TTL(生存时间)的内存缓存。

    支持的功能:
    - 基于TTL的自动过期
    - 缓存统计（命中率、淘汰次数）
    - 线程安全
    - 最大容量限制（LRU淘汰）

    C++ 对比:
        - Python内存缓存对标C++的 std::unordered_map + 定时清理
        - 生产环境通常使用Redis/Memcached（C语言实现）
        - Python的GIL保证了简单操作的线程安全
        - C++需要手动使用 std::mutex 保护共享数据结构
    """

    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0) -> None:
        """初始化缓存。

        Args:
            max_size: 缓存最大条目数
            default_ttl: 默认过期时间(秒)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，如果不存在或已过期则返回None。"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None
            if time.time() > entry.expire_at:
                # 已过期，删除
                del self._cache[key]
                self._stats["misses"] += 1
                return None
            self._stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值。"""
        with self._lock:
            if len(self._cache) >= self._max_size and key not in self._cache:
                # LRU淘汰：删除最老的条目
                oldest_key = min(self._cache, key=lambda k: self._cache[k].created_at)
                del self._cache[oldest_key]
                self._stats["evictions"] += 1

            effective_ttl = ttl if ttl is not None else self._default_ttl
            now = time.time()
            self._cache[key] = CacheEntry(
                value=value,
                expire_at=now + effective_ttl,
                created_at=now,
            )

    def delete(self, key: str) -> bool:
        """删除缓存条目。"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """清空缓存，返回被清除的条目数。"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    @property
    def hit_rate(self) -> float:
        """缓存命中率。"""
        total = self._stats["hits"] + self._stats["misses"]
        return self._stats["hits"] / total if total > 0 else 0.0

    @property
    def stats(self) -> Dict[str, Any]:
        """返回缓存统计信息。"""
        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_rate": f"{self.hit_rate:.2%}",
        }


class CacheWarmer:
    """缓存预热工具。

    在应用启动时预先加载热点数据到缓存中，
    避免冷启动时大量缓存穿透打到数据库。

    Enterprise Pattern:
        电商系统启动时预热商品详情、类目树、配置信息等。
        API网关预热路由表和限流规则。
    """

    def __init__(self, cache: MemoryCache) -> None:
        self._cache = cache
        self._warm_tasks: List[Tuple[str, Callable[[], Any], float]] = []

    def register(self, key: str, data_loader: Callable[[], Any],
                 ttl: Optional[float] = None) -> None:
        """注册一个缓存预热任务。

        Args:
            key: 缓存键
            data_loader: 数据加载函数（模拟从DB加载）
            ttl: 缓存过期时间
        """
        self._warm_tasks.append((key, data_loader, ttl or 300.0))

    def execute(self) -> Dict[str, float]:
        """执行所有预热任务，返回每个任务的耗时。"""
        results: Dict[str, float] = {}
        for key, loader, ttl in self._warm_tasks:
            start = time.perf_counter()
            try:
                data = loader()
                self._cache.set(key, data, ttl=ttl)
                elapsed = time.perf_counter() - start
                results[key] = elapsed
                logger.info("缓存预热: %s 完成 (%.4fs)", key, elapsed)
            except Exception as exc:
                logger.error("缓存预热失败: %s - %s", key, exc)
                results[key] = -1.0
        return results


def simulate_db_data_loader(key: str) -> Dict[str, Any]:
    """模拟从数据库加载数据（有延迟）。"""
    time.sleep(0.01)  # 模拟DB查询延迟
    return {"key": key, "data": f"cached_value_for_{key}", "loaded_at": time.time()}


# ===================================================================
# Section 5 -- 数据库优化 (Database Optimization)
# ===================================================================


class QueryProfile(NamedTuple):
    """SQL查询性能分析结果。"""

    query: str
    execution_time: float  # 秒
    rows_affected: int
    uses_index: bool


class DatabaseOptimizer:
    """数据库优化工具。

    提供查询性能分析、索引建议和连接池模拟。

    优化策略:
    1. 使用EXPLAIN分析查询计划
    2. 合理创建索引（避免全表扫描）
    3. 批量操作代替逐条操作（避免N+1问题）
    4. 使用连接池减少连接创建开销
    5. 读写分离（主库写，从库读）

    C++ 对比:
        - Python ORM (SQLAlchemy/Django ORM) 会引入额外开销
        - C++直接使用libpq/libmysql可以更精确控制SQL
        - Python的数据库连接池库: SQLAlchemy QueuePool, psycopg2 pool
        - C++连接池: 自行实现或使用sqlpp11等库
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._query_profiles: List[QueryProfile] = []
        self._init_sample_db()

    def _init_sample_db(self) -> None:
        """初始化示例数据库。"""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DROP TABLE IF EXISTS products")
            conn.execute("""
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            # 插入测试数据
            categories = ["电子", "服装", "食品", "图书", "家居"]
            rows = []
            for i in range(1000):
                rows.append((
                    i + 1,
                    f"商品_{i + 1}",
                    random.choice(categories),
                    round(random.uniform(10, 1000), 2),
                    random.randint(0, 500),
                    datetime.datetime.now().isoformat(),
                ))
            conn.executemany(
                "INSERT INTO products (id, name, category, price, stock, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()

    def profile_query(self, query: str, params: Optional[Tuple] = None) -> QueryProfile:
        """分析单条SQL查询的执行时间。"""
        with sqlite3.connect(self._db_path) as conn:
            start = time.perf_counter()
            cursor = conn.execute(query, params or ())
            rows = cursor.fetchall()
            elapsed = time.perf_counter() - start

            profile = QueryProfile(
                query=query,
                execution_time=elapsed,
                rows_affected=len(rows),
                uses_index=False,  # 简化：实际需要EXPLAIN分析
            )
            self._query_profiles.append(profile)
            return profile

    def demonstrate_n_plus_one_problem(self) -> Tuple[float, float]:
        """演示N+1查询问题及其优化方案。

        N+1问题: 先查询N条记录，然后对每条记录再执行1次查询。
        优化方案: 使用JOIN或IN子查询一次性获取所有数据。

        Returns:
            (N+1方案耗时, 优化方案耗时)
        """
        # 方案1: N+1查询（不推荐）
        start_n1 = time.perf_counter()
        with sqlite3.connect(self._db_path) as conn:
            categories = conn.execute(
                "SELECT DISTINCT category FROM products"
            ).fetchall()
            for (cat,) in categories:
                conn.execute(
                    "SELECT * FROM products WHERE category = ? LIMIT 5",
                    (cat,),
                ).fetchall()
        n_plus_one_time = time.perf_counter() - start_n1

        # 方案2: 优化查询（推荐）
        start_optimized = time.perf_counter()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                SELECT * FROM products
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (
                            PARTITION BY category ORDER BY id
                        ) as rn
                        FROM products
                    ) WHERE rn <= 5
                )
            """).fetchall()
        optimized_time = time.perf_counter() - start_optimized

        return n_plus_one_time, optimized_time

    def add_index_and_compare(self) -> Tuple[float, float]:
        """演示索引对查询性能的影响。

        Returns:
            (无索引查询耗时, 有索引查询耗时)
        """
        # 无索引查询
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DROP INDEX IF EXISTS idx_category")
            conn.commit()

        start_no_idx = time.perf_counter()
        with sqlite3.connect(self._db_path) as conn:
            for _ in range(50):
                conn.execute(
                    "SELECT * FROM products WHERE category = ?", ("电子",)
                ).fetchall()
        no_index_time = time.perf_counter() - start_no_idx

        # 创建索引
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON products(category)")
            conn.commit()

        # 有索引查询
        start_with_idx = time.perf_counter()
        with sqlite3.connect(self._db_path) as conn:
            for _ in range(50):
                conn.execute(
                    "SELECT * FROM products WHERE category = ?", ("电子",)
                ).fetchall()
        with_index_time = time.perf_counter() - start_with_idx

        return no_index_time, with_index_time

    @staticmethod
    def format_comparison(label_a: str, time_a: float,
                          label_b: str, time_b: float) -> str:
        """格式化两个方案的对比报告。"""
        speedup = time_a / time_b if time_b > 0 else float("inf")
        lines = [
            "  " + "-" * 50,
            f"  {label_a:<25s}: {time_a * 1000:>10.3f} ms",
            f"  {label_b:<25s}: {time_b * 1000:>10.3f} ms",
            f"  性能提升: {speedup:.2f}x",
        ]
        return "\n".join(lines)


# ===================================================================
# Section 6 -- 应用监控仪表板 (Application Monitoring)
# ===================================================================


@dataclass
class HealthCheckResult:
    """健康检查结果。"""

    service_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time: float  # 毫秒
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class SystemMetrics:
    """系统指标收集器。

    收集应用运行时的关键指标：
    - 请求计数和错误率
    - 响应时间统计
    - 内存使用情况
    - 自定义业务指标
    """

    def __init__(self) -> None:
        self._request_count: int = 0
        self._error_count: int = 0
        self._response_times: collections.deque[float] = collections.deque(maxlen=10000)
        self._custom_metrics: Dict[str, List[float]] = collections.defaultdict(list)
        self._start_time: float = time.time()

    def record_request(self, response_time: float, is_error: bool = False) -> None:
        """记录一个请求。"""
        self._request_count += 1
        self._response_times.append(response_time)
        if is_error:
            self._error_count += 1

    def record_metric(self, name: str, value: float) -> None:
        """记录一个自定义业务指标。"""
        self._custom_metrics[name].append(value)

    @property
    def uptime(self) -> float:
        """应用运行时间(秒)。"""
        return time.time() - self._start_time

    @property
    def error_rate(self) -> float:
        """错误率。"""
        return self._error_count / max(self._request_count, 1)

    def get_response_time_stats(self) -> Dict[str, float]:
        """获取响应时间统计。"""
        if not self._response_times:
            return {"min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        times = sorted(self._response_times)
        n = len(times)
        return {
            "min": times[0] * 1000,
            "max": times[-1] * 1000,
            "avg": (sum(times) / n) * 1000,
            "p50": times[n // 2] * 1000,
            "p95": times[int(n * 0.95)] * 1000,
            "p99": times[int(n * 0.99)] * 1000,
        }

    def dashboard(self) -> str:
        """生成监控仪表板文本。"""
        rt_stats = self.get_response_time_stats()
        lines = [
            "=" * 60,
            "应用监控仪表板 (Application Monitoring Dashboard)",
            "=" * 60,
            f"  运行时间     : {self.uptime:.0f} 秒",
            f"  总请求数     : {self._request_count}",
            f"  错误数       : {self._error_count}",
            f"  错误率       : {self.error_rate:.2%}",
            "",
            "  响应时间 (ms):",
            f"    最小       : {rt_stats['min']:.2f}",
            f"    最大       : {rt_stats['max']:.2f}",
            f"    平均       : {rt_stats['avg']:.2f}",
            f"    P50        : {rt_stats['p50']:.2f}",
            f"    P95        : {rt_stats['p95']:.2f}",
            f"    P99        : {rt_stats['p99']:.2f}",
        ]
        if self._custom_metrics:
            lines.append("\n  自定义指标:")
            for name, values in self._custom_metrics.items():
                if values:
                    lines.append(
                        f"    {name:<20s}: avg={sum(values)/len(values):.2f}, "
                        f"count={len(values)}"
                    )
        return "\n".join(lines)


class HealthChecker:
    """应用健康检查器。

    检查各个服务组件的可用性：
    - 数据库连接
    - 缓存服务
    - 外部API
    - 磁盘空间
    """

    def __init__(self) -> None:
        self._checks: Dict[str, Callable[[], HealthCheckResult]] = {}

    def register(self, name: str, check_func: Callable[[], HealthCheckResult]) -> None:
        """注册一个健康检查项。"""
        self._checks[name] = check_func

    def run_all(self) -> List[HealthCheckResult]:
        """执行所有健康检查。"""
        results: List[HealthCheckResult] = []
        for name, check_func in self._checks.items():
            try:
                result = check_func()
                results.append(result)
            except Exception as exc:
                results.append(HealthCheckResult(
                    service_name=name,
                    status="unhealthy",
                    response_time=0.0,
                    details={"error": str(exc)},
                ))
        return results

    def overall_status(self, results: List[HealthCheckResult]) -> str:
        """根据所有检查结果返回总体状态。"""
        statuses = {r.status for r in results}
        if "unhealthy" in statuses:
            return "unhealthy"
        if "degraded" in statuses:
            return "degraded"
        return "healthy"


def check_database_health() -> HealthCheckResult:
    """模拟数据库健康检查。"""
    start = time.perf_counter()
    # 模拟执行一个简单查询
    time.sleep(0.001)
    elapsed = (time.perf_counter() - start) * 1000
    return HealthCheckResult(
        service_name="database",
        status="healthy",
        response_time=elapsed,
        details={"connection_pool_size": 10, "active_connections": 3},
    )


def check_cache_health() -> HealthCheckResult:
    """模拟缓存服务健康检查。"""
    start = time.perf_counter()
    time.sleep(0.0005)
    elapsed = (time.perf_counter() - start) * 1000
    return HealthCheckResult(
        service_name="cache",
        status="healthy",
        response_time=elapsed,
        details={"hit_rate": "95.2%", "memory_used_mb": 128},
    )


# ===================================================================
# Section 7 -- 主从复制路由 (Master-Slave Router)
# ===================================================================


class MasterSlaveRouter:
    """Django主从复制数据库路由。

    实现读写分离：写操作路由到主库，读操作路由到从库。
    参照文档中Django的DATABASE_ROUTERS配置。

    在Django的settings.py中配置:
        DATABASE_ROUTERS = ['common.routers.MasterSlaveRouter']

    C++ 对比:
        - C++中通常在应用层手动指定连接
        - Django的Router是声明式的，自动根据操作类型路由
        - C++ ORM (如ODB) 也有类似的读写分离支持
    """

    def __init__(self, master: str = "default",
                 slaves: Optional[List[str]] = None) -> None:
        self._master = master
        self._slaves = slaves or ["slave1", "slave2", "slave3"]

    def db_for_read(self, model: Any, **hints: Any) -> str:
        """读操作路由到从库（随机负载均衡）。"""
        return random.choice(self._slaves)

    def db_for_write(self, model: Any, **hints: Any) -> str:
        """写操作路由到主库。"""
        return self._master

    def allow_relation(self, obj1: Any, obj2: Any, **hints: Any) -> Optional[bool]:
        """允许同一数据库中的对象建立关系。"""
        db_set = {self._master} | set(self._slaves)
        if hasattr(obj1, "_state") and hasattr(obj2, "_state"):
            if obj1._state.db in db_set and obj2._state.db in db_set:
                return True
        return None

    def allow_migrate(self, db: str, app_label: str,
                      model_name: Optional[str] = None, **hints: Any) -> bool:
        """数据库迁移只在主库执行。"""
        return db == self._master


# ===================================================================
# Section 8 -- 综合演示 (Full Demonstration)
# ===================================================================


def demonstrate_deployment_checklist() -> None:
    """演示部署检查清单。"""
    print("=" * 60)
    print("1. 部署检查清单演示")
    print("=" * 60)

    checklist = build_django_deployment_checklist()

    # 模拟部分检查项已通过
    checklist.check("DEBUG设置为False")
    checklist.check("ALLOWED_HOSTS配置")
    checklist.check("SECRET_KEY外置")
    checklist.check("静态文件收集")
    checklist.check("依赖锁定")

    print(checklist.display())
    print()


def demonstrate_profiler() -> None:
    """演示性能分析器。"""
    print("=" * 60)
    print("2. 性能分析器演示")
    print("=" * 60)

    profiler = PerformanceProfiler()

    # 分析数据处理函数
    _, result = profiler.profile_function(simulate_data_processing, 5000)
    print(profiler.format_report(result))
    print()


def demonstrate_load_testing() -> None:
    """演示负载测试。"""
    print("=" * 60)
    print("3. 负载测试演示")
    print("=" * 60)

    tester = LoadTester(
        target_func=simulate_request_handler,
        num_requests=200,
        concurrency=20,
    )
    result = tester.run()
    print(LoadTester.format_report(result))
    print()


def demonstrate_caching() -> None:
    """演示缓存策略和缓存预热。"""
    print("=" * 60)
    print("4. 缓存策略演示")
    print("=" * 60)

    cache = MemoryCache(max_size=100, default_ttl=5.0)

    # --- 缓存预热 ---
    print("\n  [缓存预热]")
    warmer = CacheWarmer(cache)
    warmer.register("config:app", lambda: {"name": "MyApp", "version": "2.0"})
    warmer.register("config:db", lambda: {"pool_size": 20, "timeout": 30})
    warmer.register("hot:categories", lambda: ["电子", "服装", "食品", "图书", "家居"])

    warm_times = warmer.execute()
    for key, elapsed in warm_times.items():
        print(f"    预热 {key}: {elapsed * 1000:.2f} ms")

    # --- 缓存读写测试 ---
    print("\n  [缓存读写测试]")
    # 命中
    for key in ["config:app", "config:db", "hot:categories"]:
        value = cache.get(key)
        print(f"    GET {key}: {'命中' if value is not None else '未命中'}")

    # 未命中
    miss_value = cache.get("nonexistent_key")
    print(f"    GET nonexistent_key: {'命中' if miss_value is not None else '未命中'}")

    # 写入新数据
    cache.set("user:1001", {"name": "Alice", "role": "admin"}, ttl=60.0)
    print(f"    SET user:1001 -> {cache.get('user:1001')}")

    # --- 缓存统计 ---
    print(f"\n  [缓存统计]")
    stats = cache.stats
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # --- TTL过期演示 ---
    print("\n  [TTL过期演示]")
    cache.set("temp_key", "temp_value", ttl=0.1)
    print(f"    刚设置: GET temp_key = {cache.get('temp_key')}")
    time.sleep(0.15)
    print(f"    0.15秒后: GET temp_key = {cache.get('temp_key')}")
    print()


def demonstrate_database_optimization() -> None:
    """演示数据库优化。"""
    print("=" * 60)
    print("5. 数据库优化演示")
    print("=" * 60)

    # 使用临时数据库
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    try:
        optimizer = DatabaseOptimizer(db_path)

        # --- 索引优化 ---
        print("\n  [索引优化]")
        no_idx, with_idx = optimizer.add_index_and_compare()
        print(DatabaseOptimizer.format_comparison(
            "无索引查询", no_idx,
            "有索引查询", with_idx,
        ))

        # --- N+1问题 ---
        print("\n  [N+1查询问题]")
        n1_time, opt_time = optimizer.demonstrate_n_plus_one_problem()
        print(DatabaseOptimizer.format_comparison(
            "N+1查询方案", n1_time,
            "优化方案(窗口函数)", opt_time,
        ))

        # --- 主从复制路由演示 ---
        print("\n  [主从复制路由]")
        router = MasterSlaveRouter()
        for i in range(6):
            read_db = router.db_for_read(None)
            write_db = router.db_for_write(None)
            print(f"    读操作 -> {read_db}, 写操作 -> {write_db}")

    finally:
        # Windows上SQLite可能持有文件锁，等待释放后再删除
        import gc
        gc.collect()
        for _attempt in range(3):
            try:
                os.unlink(db_path)
                break
            except PermissionError:
                time.sleep(0.1)
    print()


def demonstrate_monitoring() -> None:
    """演示应用监控。"""
    print("=" * 60)
    print("6. 应用监控演示")
    print("=" * 60)

    # --- 系统指标收集 ---
    metrics = SystemMetrics()

    # 模拟一些请求
    for _ in range(100):
        response_time = random.uniform(0.001, 0.05)
        is_error = random.random() < 0.05  # 5%错误率
        metrics.record_request(response_time, is_error)

    # 记录自定义业务指标
    for _ in range(50):
        metrics.record_metric("orders_per_minute", random.randint(10, 100))
        metrics.record_metric("cache_hit_rate", random.uniform(0.85, 0.99))

    print(metrics.dashboard())

    # --- 健康检查 ---
    print("\n  [健康检查]")
    checker = HealthChecker()
    checker.register("database", check_database_health)
    checker.register("cache", check_cache_health)

    results = checker.run_all()
    for r in results:
        print(f"    {r.service_name}: {r.status} ({r.response_time:.2f}ms)")
    print(f"    总体状态: {checker.overall_status(results)}")
    print()


# ===================================================================
# Section 9 -- 最佳实践总结
# ===================================================================


DEPLOYMENT_BEST_PRACTICES: Final[List[Dict[str, str]]] = [
    {
        "category": "部署配置",
        "practice": "DEBUG=False，配置ALLOWED_HOSTS白名单",
    },
    {
        "category": "部署配置",
        "practice": "敏感信息（密钥、密码）通过环境变量注入，不硬编码",
    },
    {
        "category": "部署配置",
        "practice": "强制HTTPS，配置HSTS安全头",
    },
    {
        "category": "Web服务器",
        "practice": "使用Nginx + uWSGI/Gunicorn，实现动静分离",
    },
    {
        "category": "Web服务器",
        "practice": "Nginx配置负载均衡(WRR/ip_hash)和反向代理",
    },
    {
        "category": "Web服务器",
        "practice": "Keepalived实现Nginx主备热切换，保证高可用",
    },
    {
        "category": "容器化",
        "practice": "使用Docker容器化部署，Dockerfile分层构建减小镜像",
    },
    {
        "category": "容器化",
        "practice": "Docker Compose编排多服务（Web, DB, Redis, Celery）",
    },
    {
        "category": "进程管理",
        "practice": "使用Supervisor/Circus管理进程，支持自动重启",
    },
    {
        "category": "数据库",
        "practice": "MySQL主从复制实现读写分离，写主库读从库",
    },
    {
        "category": "数据库",
        "practice": "合理创建索引，使用EXPLAIN分析慢查询",
    },
    {
        "category": "数据库",
        "practice": "使用连接池减少连接开销，避免N+1查询",
    },
    {
        "category": "缓存",
        "practice": "Redis/Memcached缓存热点数据，设置合理TTL",
    },
    {
        "category": "缓存",
        "practice": "应用启动时缓存预热，避免冷启动穿透",
    },
    {
        "category": "性能调优",
        "practice": "先用cProfile/py-spy定位瓶颈，再有针对性优化",
    },
    {
        "category": "性能调优",
        "practice": "I/O密集型用asyncio/多线程，CPU密集型用多进程",
    },
    {
        "category": "监控",
        "practice": "配置日志收集（ELK/EFK）和应用性能监控(APM)",
    },
    {
        "category": "监控",
        "practice": "实现健康检查端点，接入Nagios/Zabbix/Prometheus",
    },
    {
        "category": "安全",
        "practice": "定期更新依赖，使用pip-audit扫描安全漏洞",
    },
    {
        "category": "CI/CD",
        "practice": "自动化CI/CD流水线：代码检查->测试->构建->部署",
    },
]


def print_deployment_best_practices() -> None:
    """打印部署最佳实践。"""
    by_category: Dict[str, List[str]] = {}
    for entry in DEPLOYMENT_BEST_PRACTICES:
        by_category.setdefault(entry["category"], []).append(entry["practice"])

    lines = ["=" * 60, "部署与性能调优最佳实践", "=" * 60]
    for category, practices in by_category.items():
        lines.append(f"\n  [{category}]")
        for i, p in enumerate(practices, 1):
            lines.append(f"    {i}. {p}")
    lines.append("")
    print("\n".join(lines))


# ===================================================================
# Main Entry Point
# ===================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stderr,
    )

    print("Day 98 - 部署上线与性能调优")
    print()

    demonstrate_deployment_checklist()
    demonstrate_profiler()
    demonstrate_load_testing()
    demonstrate_caching()
    demonstrate_database_optimization()
    demonstrate_monitoring()
    print_deployment_best_practices()

    print("=" * 60)
    print("所有演示完成!")
    print("=" * 60)
    print(textwrap.dedent("""\
        关键要点:
          * 上线前严格执行检查清单，安全配置不可遗漏
          * 性能优化要先测量(cProfile/py-spy)后优化，避免过早优化
          * 合理使用缓存(Redis/内存)减少数据库压力
          * Nginx + uWSGI/Gunicorn 是Python Web应用的标准部署方案
          * Docker容器化简化环境配置和多节点部署
          * MySQL主从复制实现读写分离，提升数据库吞吐量
          * 监控和日志是生产环境的生命线
          * CI/CD自动化保证代码质量和部署效率

        进一步学习:
          - Gunicorn/uWSGI调优: worker数、超时、缓冲区
          - Redis高级用法: Pipeline、Lua脚本、集群模式
          - Prometheus + Grafana监控体系搭建
          - Kubernetes容器编排和自动扩缩容
          - 分布式追踪: Jaeger / Zipkin / OpenTelemetry
    """))
