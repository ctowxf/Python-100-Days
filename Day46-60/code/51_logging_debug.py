"""
Day 51 - Logging and Debug Toolbar
===================================
Comprehensive demo of Python logging, Django logging configuration, and
debug toolbar integration. Includes enterprise patterns: structured logging,
request logging middleware, and error tracking.

C++ Comparison:
    Python logging  vs  C++ spdlog / boost::log
    ---------------------------------------------------------------
    Python's `logging` module is part of the standard library and provides
    a batteries-included, thread-safe, hierarchical logger system with
    pluggable handlers, formatters, and filters -- no third-party deps.

    In C++ the standard library has NO built-in logging facility.  Projects
    typically reach for:
      * spdlog       -- header-only, extremely fast (~10-50 ns/log line),
                        supports async sinks, rotating files, syslog, etc.
      * boost::log   -- heavier, highly configurable, compile-time filters,
                        expression-based formatting.

    Key differences:
    | Aspect            | Python logging            | C++ spdlog / boost::log      |
    |-------------------|---------------------------|-------------------------------|
    | Speed             | ~1-5 us/log line          | ~10-50 ns/log line            |
    | Config style      | dictConfig / fileConfig   | Template / builder C++ API    |
    | Async support     | QueueHandler (stdlib 3.2) | Built-in async logger         |
    | Structured (JSON) | Manual / pythonjsonlogger | spdlog has built-in json sink |
    | Thread safety     | Inherited from handlers   | Lock-free queues (spdlog)     |
    | Compile-time opt  | N/A (interpreted)         | #define SPDLOG_ACTIVE_LEVEL   |

    In practice Python logging is "fast enough" for web apps; the real
    advantage is the dictConfig system that lets Django describe logging
    entirely in a settings dict -- no code changes needed to switch from
    console to file to remote aggregation.
"""

from __future__ import annotations

import json
import logging
import logging.config
import logging.handlers
import os
import sys
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Generator, TypeVar

# ---------------------------------------------------------------------------
# 1. PYTHON LOGGING FUNDAMENTALS
# ---------------------------------------------------------------------------

# The six log levels (lowest to highest):
#   DEBUG(10) < INFO(20) < WARNING(30) < ERROR(40) < CRITICAL(50) < NOTSET(0)
#
# A logger will only process messages at or above its effective level.
# The effective level is the first explicitly set level walking up the
# logger hierarchy (dot-separated names like "app.db.query").

# -- Basic setup (programmatic, no dictConfig) ------------------------------

def setup_basic_logging(level: int = logging.DEBUG) -> logging.Logger:
    """Configure root logger with a console handler and return a child logger.

    This is the simplest approach -- fine for scripts and small utilities.
    For Django projects, prefer dictConfig (see section 3).
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Avoid adding duplicate handlers when called multiple times.
    if not root.handlers:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        fmt = logging.Formatter(
            "%(asctime)s %(levelname)-8s [%(process)d-%(threadName)s] "
            "%(module)s.%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console.setFormatter(fmt)
        root.addHandler(console)

    return logging.getLogger("demo")


# -- Handler showcase -------------------------------------------------------

def demonstrate_handlers() -> None:
    """Show the most commonly used logging handlers."""
    logger = logging.getLogger("demo.handlers")
    logger.setLevel(logging.DEBUG)

    # 1. StreamHandler -- writes to any file-like object (stdout/stderr).
    stream_h = logging.StreamHandler(sys.stderr)
    stream_h.setLevel(logging.WARNING)  # only warnings and above to stderr

    # 2. FileHandler -- appends to a file.
    file_h = logging.FileHandler("app.log", encoding="utf-8")
    file_h.setLevel(logging.INFO)

    # 3. RotatingFileHandler -- rolls over at a max size.
    rotating_h = logging.handlers.RotatingFileHandler(
        "rotating.log", maxBytes=1_048_576, backupCount=5, encoding="utf-8"
    )
    rotating_h.setLevel(logging.DEBUG)

    # 4. TimedRotatingFileHandler -- rolls over at timed intervals.
    #    Common in Django configs (see Django logging section).
    timed_h = logging.handlers.TimedRotatingFileHandler(
        "timed.log", when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    timed_h.setLevel(logging.INFO)

    # Assign a simple formatter to every handler.
    simple_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for h in (stream_h, file_h, rotating_h, timed_h):
        h.setFormatter(simple_fmt)
        logger.addHandler(h)

    logger.debug("This DEBUG message goes to file and rotating handlers only.")
    logger.info("This INFO message goes to file, rotating, and timed handlers.")
    logger.warning("This WARNING goes to all four handlers (including stderr).")

    # Clean up file handles for the demo.
    for h in (stream_h, file_h, rotating_h, timed_h):
        h.close()
        logger.removeHandler(h)


# -- Format placeholders reference ------------------------------------------

FORMAT_PLACEHOLDER_REFERENCE = """
Common LogRecord attributes usable in format strings:
    %(name)s        - Logger name
    %(levelno)s     - Numeric log level (e.g. 20)
    %(levelname)s   - Text log level   (e.g. 'INFO')
    %(pathname)s    - Full path of the source file
    %(filename)s    - Filename component only
    %(module)s      - Module name (filename without extension)
    %(funcName)s    - Function name
    %(lineno)d      - Source line number
    %(created)s     - LogRecord creation time (time.time())
    %(asctime)s     - Human-readable timestamp
    %(msecs)s       - Millisecond portion of creation time
    %(thread)d      - Thread ID
    %(threadName)s  - Thread name
    %(process)d     - Process ID
    %(message)s     - The logged message (result of msg % args)
"""


# ---------------------------------------------------------------------------
# 2. STRUCTURED (JSON) LOGGING -- ENTERPRISE PATTERN
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line.

    Structured logs are machine-parseable and play nicely with ELK,
    Datadog, CloudWatch Logs Insights, Splunk, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.thread,
        }

        # Attach extra fields passed via `logger.info("msg", extra={...})`.
        reserved = logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
        extras = {k: v for k, v in record.__dict__.items() if k not in reserved}
        if extras:
            log_entry["extra"] = extras

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_json_logging() -> logging.Logger:
    """Configure a JSON logger that writes to stdout (typical for containers)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger("app.structured")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# -- Log context (similar to C++ spdlog's spdlog::mdc / MDC in log4cxx) ----

class LogContext:
    """Thread-local context that is automatically merged into every log record.

    Comparable to Mapped Diagnostic Context (MDC) in Java/Log4j or
    spdlog::mdc in C++.
    """

    _context: dict[str, Any] = {}

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls._context[key] = value

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return cls._context.get(key, default)

    @classmethod
    def clear(cls) -> None:
        cls._context.clear()

    @classmethod
    def as_dict(cls) -> dict[str, Any]:
        return dict(cls._context)


class ContextFilter(logging.Filter):
    """Inject LogContext fields into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in LogContext.as_dict().items():
            setattr(record, key, value)
        return True


# ---------------------------------------------------------------------------
# 3. DJANGO LOGGING CONFIGURATION (dictConfig)
# ---------------------------------------------------------------------------
# The following dict mirrors what a real Django settings.py would contain.
# We demonstrate it here standalone so the file is self-contained.

DJANGO_LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,

    # -- Formatters --------------------------------------------------------
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(module)s.%(funcName)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": (
                "%(asctime)s %(levelname)s [%(process)d-%(threadName)s] "
                "%(module)s.%(funcName)s line %(lineno)d: %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "path.to.JSONFormatter",  # In a real project, point to actual class path.
        },
    },

    # -- Filters -----------------------------------------------------------
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },

    # -- Handlers ----------------------------------------------------------
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "formatter": "simple",
        },
        # Access log -- rotated weekly (W0 = Monday).
        "access_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/access.log",
            "when": "W0",
            "backupCount": 12,
            "formatter": "simple",
            "level": "INFO",
        },
        # Error log -- rotated daily.
        "error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/error.log",
            "when": "D",
            "backupCount": 31,
            "formatter": "verbose",
            "level": "WARNING",
        },
        # SQL log -- useful for ORM query debugging.
        "sql_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/sql.log",
            "maxBytes": 10_485_760,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
            "level": "DEBUG",
        },
        # Mail admins on critical errors (production).
        "mail_admins": {
            "class": "django.utils.log.AdminEmailHandler",
            "level": "ERROR",
            "include_html": True,
        },
    },

    # -- Loggers -----------------------------------------------------------
    "loggers": {
        "django": {
            "handlers": ["console", "access_file", "error_file"],
            "propagate": True,
            "level": "DEBUG",
        },
        "django.request": {
            "handlers": ["error_file", "mail_admins"],
            "propagate": False,
            "level": "ERROR",
        },
        "django.server": {
            "handlers": ["console", "access_file"],
            "propagate": False,
            "level": "INFO",
        },
        "django.db.backends": {
            "handlers": ["sql_file"],
            "propagate": False,
            "level": "DEBUG",  # Set to WARNING in production to suppress SQL logging.
        },
        "django.template": {
            "handlers": ["console"],
            "propagate": False,
            "level": "WARNING",
        },
    },

    # -- Root logger -------------------------------------------------------
    "root": {
        "handlers": ["console", "access_file", "error_file"],
        "level": "INFO",
    },
}


def explain_django_logging() -> None:
    """Print a human-readable walkthrough of the Django logging config."""
    print("=" * 72)
    print("DJANGO LOGGING CONFIGURATION WALKTHROUGH")
    print("=" * 72)

    print("\n--- Formatters ---")
    for name, fmt in DJANGO_LOGGING_CONFIG["formatters"].items():
        if "format" in fmt:
            print(f"  {name:12s} -> {fmt['format']}")

    print("\n--- Handlers ---")
    descriptions = {
        "console":     "StreamHandler -- stdout, only active when DEBUG=True",
        "access_file": "TimedRotatingFileHandler -- weekly rotation, INFO+",
        "error_file":  "TimedRotatingFileHandler -- daily rotation, WARNING+",
        "sql_file":    "RotatingFileHandler -- 10 MB limit, captures SQL queries",
        "mail_admins": "AdminEmailHandler -- emails ERROR+ to ADMINS",
    }
    for name in DJANGO_LOGGING_CONFIG["handlers"]:
        print(f"  {name:14s}: {descriptions.get(name, '')}")

    print("\n--- Loggers (built-in Django loggers) ---")
    logger_desc = {
        "django":              "All messages in the Django hierarchy",
        "django.request":      "5xx = ERROR, 4xx = WARNING (request lifecycle)",
        "django.server":       "runserver request logs (5xx=ERROR, 4xx=WARN, else INFO)",
        "django.db.backends":  "SQL queries -- invaluable for ORM debugging",
        "django.template":     "Template rendering messages",
    }
    for name, cfg in DJANGO_LOGGING_CONFIG["loggers"].items():
        level = cfg.get("level", "NOTSET")
        print(f"  {name:25s} level={level:8s}  {logger_desc.get(name, '')}")

    print("\n--- Effective level rule ---")
    print("  The effective log level = max(logger level, handler level).")
    print("  Example: logger=DEBUG + handler=INFO => only INFO+ is actually emitted.")


# ---------------------------------------------------------------------------
# 4. DJANGO DEBUG TOOLBAR CONFIGURATION
# ---------------------------------------------------------------------------

def show_debug_toolbar_config() -> None:
    """Display the typical django-debug-toolbar configuration steps."""
    print("\n" + "=" * 72)
    print("DJANGO-DEBUG-TOOLBAR SETUP")
    print("=" * 72)

    print("""
Step 1: Install
    $ pip install django-debug-toolbar

Step 2: settings.py additions

    INSTALLED_APPS = [
        ...
        'debug_toolbar',
    ]

    MIDDLEWARE = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',  # as early as possible
        ...
    ]

    # Only show toolbar for internal IPs (or lambda x: True in dev).
    INTERNAL_IPS = ['127.0.0.1']

    DEBUG_TOOLBAR_CONFIG = {
        'JQUERY_URL': 'https://cdn.bootcss.com/jquery/3.3.1/jquery.min.js',
        'SHOW_COLLAPSED': True,
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,  # always show in dev
    }

Step 3: urls.py

    if settings.DEBUG:
        import debug_toolbar
        from django.urls import include, path
        urlpatterns.insert(0, path('__debug__/', include(debug_toolbar.urls)))

Panels provided:
    +----------------+-------------------------------------------------------+
    | Panel          | What it shows                                         |
    +----------------+-------------------------------------------------------+
    | Versions       | Django version info                                   |
    | Time           | View rendering time breakdown                         |
    | Settings       | All settings.py values                                |
    | Headers        | HTTP request / response headers                       |
    | Request        | GET/POST parameters, cookies, session data            |
    | StaticFiles    | Which static files were loaded                        |
    | Templates      | Templates used and their context                      |
    | Cache          | Cache hit/miss statistics                             |
    | Signals        | Django signals that fired                             |
    | Logging        | Messages recorded during the request                  |
    | SQL            | Every SQL query with execution time (N+1 detector!)   |
    +----------------+-------------------------------------------------------+
""")


# ---------------------------------------------------------------------------
# 5. REQUEST LOGGING MIDDLEWARE -- ENTERPRISE PATTERN
# ---------------------------------------------------------------------------

@dataclass
class RequestLogEntry:
    """Structured representation of a single HTTP request log."""
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    method: str = "GET"
    path: str = "/"
    status_code: int = 200
    duration_ms: float = 0.0
    client_ip: str = "127.0.0.1"
    user_agent: str = ""
    user_id: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RequestLoggingMiddleware:
    """Django middleware that logs every request with timing and metadata.

    In a real Django project, add this to MIDDLEWARE:
        'myapp.middleware.RequestLoggingMiddleware'

    This demo shows the pattern without requiring a running Django server.
    """

    def __init__(self, get_response: Callable[..., Any]) -> None:
        self.get_response = get_response
        self.logger = logging.getLogger("django.request.custom")

    def __call__(self, request: Any) -> Any:
        # Assign a unique request ID (useful for distributed tracing).
        request_id = uuid.uuid4().hex[:12]
        LogContext.set("request_id", request_id)

        entry = RequestLogEntry(
            request_id=request_id,
            method=getattr(request, "method", "UNKNOWN"),
            path=getattr(request, "path", "/"),
            client_ip=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_AGENT", "")
            if hasattr(request, "META")
            else "",
        )

        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        entry.status_code = getattr(response, "status_code", 500)
        entry.duration_ms = round(elapsed_ms, 2)

        # Log at appropriate level based on status code.
        if entry.status_code >= 500:
            self.logger.error("Request completed", extra=asdict(entry))
        elif entry.status_code >= 400:
            self.logger.warning("Request completed", extra=asdict(entry))
        else:
            self.logger.info("Request completed", extra=asdict(entry))

        # Inject request ID into response headers for debugging.
        if hasattr(response, "X-Request-Id".replace("-", "_")):
            pass  # DRF or custom response
        return response

    @staticmethod
    def _get_client_ip(request: Any) -> str:
        """Extract client IP, respecting X-Forwarded-For behind a proxy."""
        if not hasattr(request, "META"):
            return "unknown"
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")


def demo_request_logging() -> None:
    """Simulate request logging without a real Django server."""
    logger = setup_json_logging()
    logger.name = "django.request.custom"
    LogContext.set("request_id", uuid.uuid4().hex[:12])
    logger.info("GET /api/v1/teachers/ 200 12.34ms client=192.168.1.100")
    LogContext.clear()


# ---------------------------------------------------------------------------
# 6. ERROR TRACKING -- ENTERPRISE PATTERN
# ---------------------------------------------------------------------------

@dataclass
class ErrorReport:
    """Machine-readable error report suitable for Sentry / ELK / Datadog."""
    error_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    level: str = "ERROR"
    exception_type: str = ""
    message: str = ""
    traceback: str = ""
    module: str = ""
    function: str = ""
    line: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class ErrorTracker:
    """Collects and reports errors in a structured format.

    In production you would forward ErrorReport instances to Sentry,
    Datadog, or a custom error aggregation service.  Here we store them
    in memory and provide a summary.
    """

    def __init__(self) -> None:
        self._reports: list[ErrorReport] = []
        self._logger = logging.getLogger("app.error_tracker")

    def capture_exception(
        self,
        exc: BaseException,
        *,
        extra: dict[str, Any] | None = None,
    ) -> ErrorReport:
        """Capture an exception with full traceback and context."""
        report = ErrorReport(
            exception_type=type(exc).__name__,
            message=str(exc),
            traceback=traceback.format_exc(),
            extra=extra or {},
        )

        # Walk the traceback to find the originating frame.
        tb = exc.__traceback__
        if tb is not None:
            while tb.tb_next is not None:
                tb = tb.tb_next
            frame = tb.tb_frame
            report.module = frame.f_globals.get("__name__", "<unknown>")
            report.function = frame.f_code.co_name
            report.line = tb.tb_lineno

        self._reports.append(report)

        # Also emit a structured log line.
        self._logger.error(
            "Unhandled exception: %s: %s",
            report.exception_type,
            report.message,
            extra={"error_id": report.error_id, **report.extra},
            exc_info=True,
        )

        return report

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of all captured errors."""
        by_type: dict[str, int] = {}
        for r in self._reports:
            by_type[r.exception_type] = by_type.get(r.exception_type, 0) + 1
        return {
            "total_errors": len(self._reports),
            "by_exception_type": by_type,
            "recent": [asdict(r) for r in self._reports[-5:]],
        }


def demo_error_tracking() -> None:
    """Demonstrate the ErrorTracker with intentional exceptions."""
    logger = setup_json_logging()
    logger.name = "app.error_tracker"

    tracker = ErrorTracker()

    # Simulate a ValueError.
    try:
        result = int("not_a_number")
    except ValueError as exc:
        tracker.capture_exception(exc, extra={"input": "not_a_number"})

    # Simulate a ZeroDivisionError.
    try:
        _ = 1 / 0
    except ZeroDivisionError as exc:
        tracker.capture_exception(exc, extra={"operation": "division"})

    # Simulate a custom application error.
    class InsufficientFundsError(Exception):
        def __init__(self, balance: float, amount: float) -> None:
            self.balance = balance
            self.amount = amount
            super().__init__(
                f"Cannot withdraw {amount:.2f} from balance {balance:.2f}"
            )

    try:
        raise InsufficientFundsError(balance=50.00, amount=120.00)
    except InsufficientFundsError as exc:
        tracker.capture_exception(
            exc, extra={"account_id": "ACC-001", "currency": "USD"}
        )

    print("\n--- Error Tracker Summary ---")
    summary = tracker.get_summary()
    print(json.dumps(summary, indent=2, default=str))


# ---------------------------------------------------------------------------
# 7. DJANGO ORM QUERY LOGGING (N+1 DETECTION)
# ---------------------------------------------------------------------------

def explain_n_plus_one_problem() -> None:
    """Explain the N+1 query problem and how logging helps detect it.

    In Django, when you iterate over a queryset that has a ForeignKey
    relation, the ORM fires a separate query for EACH related object.
    This is the classic N+1 problem.

    SQL logged (without select_related):
        SELECT ... FROM tb_teacher;                    -- 1 query
        SELECT ... FROM tb_subject WHERE no = 101;     -- N queries (one per teacher)
        SELECT ... FROM tb_subject WHERE no = 101;
        SELECT ... FROM tb_subject WHERE no = 103;

    Fix with select_related (generates a JOIN):
        SELECT ... FROM tb_teacher
        INNER JOIN tb_subject ON tb_teacher.sno = tb_subject.no;
    """
    print("\n" + "=" * 72)
    print("N+1 QUERY PROBLEM AND ORM OPTIMIZATION")
    print("=" * 72)
    print("""
    Problem:  Teacher.objects.all()  => 1 query + N queries for subjects
    Solution: Teacher.objects.all().select_related('subject')  => 1 JOIN query

    Other useful QuerySet methods for optimization:

    only('name', 'good_count', 'bad_count')
        => SELECT name, good_count, bad_count FROM tb_teacher
        (projection -- fetch only the columns you need)

    defer('detail', 'photo')
        => SELECT no, name, good_count, bad_count, ... FROM tb_teacher
        (defer loading large columns until accessed)

    values('subject__name').annotate(good=Avg('good_count'), bad=Avg('bad_count'))
        => SELECT subject.name, AVG(good_count), AVG(bad_count)
           FROM tb_teacher GROUP BY subject.name
        (aggregation at the database level)

    How logging helps:
        - Enable 'django.db.backends' logger at DEBUG level.
        - Every SQL query is logged with execution time.
        - Django Debug Toolbar's SQL panel shows the same with EXPLAIN.
        - Watch for repeated identical queries -- that is the N+1 signal.
""")


# ---------------------------------------------------------------------------
# 8. PERFORMANCE TIMING WITH LOGGING
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def log_execution_time(
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
) -> Callable[[F], F]:
    """Decorator that logs the execution time of a function.

    Usage:
        @log_execution_time()
        def slow_function():
            ...

    Comparable to C++ spdlog pattern:
        auto start = std::chrono::high_resolution_clock::now();
        // ... work ...
        spdlog::info("slow_function took {} ms", elapsed_ms);
    """
    _logger = logger or logging.getLogger("app.perf")

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                _logger.log(
                    level,
                    "%s executed in %.2f ms",
                    func.__qualname__,
                    elapsed_ms,
                )
        return wrapper  # type: ignore[return-value]
    return decorator


def demo_performance_logging() -> None:
    """Show how to combine logging with performance measurement."""
    logger = logging.getLogger("app.perf")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)

    @log_execution_time(logger)
    def compute_sum(n: int) -> int:
        """Deliberately slow computation for demo purposes."""
        total = 0
        for i in range(n):
            total += i
        return total

    result = compute_sum(1_000_000)
    logger.info("Result: %d", result)

    logger.removeHandler(handler)
    handler.close()


# ---------------------------------------------------------------------------
# 9. CENTRALIZED LOGGING CONFIGURATION FACTORY
# ---------------------------------------------------------------------------

def build_logging_config(
    *,
    app_name: str = "myapp",
    log_dir: str = "logs",
    console_level: int = logging.DEBUG,
    file_level: int = logging.INFO,
    json_format: bool = False,
) -> dict[str, Any]:
    """Build a logging config dict suitable for logging.config.dictConfig().

    This is a reusable factory -- call it once at application startup with
    environment-specific parameters (dev/staging/prod).
    """
    os.makedirs(log_dir, exist_ok=True)

    formatter_name = "json" if json_format else "standard"
    formatters: dict[str, Any] = {
        "standard": {
            "format": (
                "%(asctime)s %(levelname)-8s [%(name)s] "
                "%(module)s.%(funcName)s:%(lineno)d - %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    if json_format:
        formatters["json"] = {"()": JSONFormatter}

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": console_level,
                "formatter": formatter_name,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": file_level,
                "formatter": formatter_name,
                "filename": os.path.join(log_dir, f"{app_name}.log"),
                "when": "midnight",
                "backupCount": 30,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": logging.ERROR,
                "formatter": formatter_name,
                "filename": os.path.join(log_dir, f"{app_name}_error.log"),
                "maxBytes": 10_485_760,
                "backupCount": 10,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            app_name: {
                "handlers": ["console", "file", "error_file"],
                "level": logging.DEBUG,
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console", "error_file"],
            "level": logging.WARNING,
        },
    }


# ---------------------------------------------------------------------------
# 10. MAIN -- RUN ALL DEMONSTRATIONS
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations in sequence."""
    # Clean up any leftover log files from previous runs.
    for fname in ("app.log", "rotating.log", "timed.log"):
        if os.path.exists(fname):
            os.remove(fname)

    print("=" * 72)
    print(" DAY 51 -- LOGGING AND DEBUG TOOLBAR DEMO")
    print("=" * 72)

    # 1. Basic logging
    print("\n--- 1. Basic Logging Setup ---")
    logger = setup_basic_logging()
    logger.debug("DEBUG: detailed diagnostic information")
    logger.info("INFO: confirmation that things are working")
    logger.warning("WARNING: something unexpected happened")
    logger.error("ERROR: a serious problem occurred")
    logger.critical("CRITICAL: the program may not be able to continue")

    # 2. Handler showcase
    print("\n--- 2. Handler Showcase ---")
    demonstrate_handlers()

    # 3. Structured JSON logging
    print("\n--- 3. Structured JSON Logging ---")
    json_logger = setup_json_logging()
    json_logger.info("User login", extra={"user_id": "U-12345", "ip": "10.0.0.1"})
    json_logger.warning("Rate limit approaching", extra={"current_rps": 95, "limit": 100})

    # 4. Django logging configuration walkthrough
    explain_django_logging()

    # 5. Django Debug Toolbar
    show_debug_toolbar_config()

    # 6. Request logging demo
    print("--- 6. Request Logging Middleware ---")
    demo_request_logging()

    # 7. Error tracking demo
    print("\n--- 7. Error Tracking ---")
    demo_error_tracking()

    # 8. N+1 query explanation
    explain_n_plus_one_problem()

    # 9. Performance logging
    print("\n--- 9. Performance Logging ---")
    demo_performance_logging()

    # 10. Centralized config factory
    print("\n--- 10. Centralized Logging Config Factory ---")
    dev_config = build_logging_config(app_name="myapp", json_format=False)
    prod_config = build_logging_config(
        app_name="myapp", log_dir="/var/log/myapp", json_format=True,
        console_level=logging.WARNING, file_level=logging.INFO,
    )
    print(f"  Dev config handlers : {list(dev_config['handlers'].keys())}")
    print(f"  Prod config handlers: {list(prod_config['handlers'].keys())}")
    print(f"  Prod uses JSON format: {'json' in prod_config['formatters']}")

    # Clean up demo log files.
    for fname in ("app.log", "rotating.log", "timed.log"):
        if os.path.exists(fname):
            os.remove(fname)

    print("\n" + "=" * 72)
    print(" DEMO COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
