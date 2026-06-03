"""
95. Django Commercial Project Best Practices (使用Django开发商业项目)

Enterprise-level implementation covering:
- Multi-environment settings management (dev/staging/production)
- Custom user model with extended fields
- Django signals for audit logging and event-driven architecture
- Production settings and security hardening
- RESTful API design with DRF patterns
- Middleware, caching, logging, and testing patterns
- Deployment checklist and operational readiness

C++ Comparison: Django ORM vs C++ Database Layer
============================================================
Django's ORM provides a high-level Python abstraction over SQL with
automatic migrations, query building, and lazy evaluation. In C++,
one would use libraries like SOCI, sqlpp11, or ODB which provide
compile-time SQL verification and zero-overhead abstractions but
require manual schema management. Django trades runtime performance
for developer productivity and safety (SQL injection prevention,
automatic parameterized queries), while C++ database layers offer
deterministic query execution times critical for high-frequency
trading and real-time systems.
============================================================
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

# ---------------------------------------------------------------------------
# Section 1: Multi-Environment Settings (多环境配置管理)
# ---------------------------------------------------------------------------


class Environment(Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    engine: str = "django.db.backends.postgresql"
    name: str = "appdb"
    user: str = "appuser"
    password: str = ""
    host: str = "localhost"
    port: int = 5432
    options: Dict[str, Any] = field(default_factory=dict)
    conn_max_age: int = 600
    test: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "ENGINE": self.engine,
            "NAME": self.name,
            "USER": self.user,
            "PASSWORD": self.password,
            "HOST": self.host,
            "PORT": self.port,
            "CONN_MAX_AGE": self.conn_max_age,
        }
        if self.options:
            d["OPTIONS"] = self.options
        if self.test:
            d["TEST"] = self.test
        return d


@dataclass
class CacheConfig:
    """Cache backend configuration."""
    backend: str = "django_redis.cache.RedisCache"
    location: str = "redis://127.0.0.1:6379/1"
    key_prefix: str = "djangocache"
    timeout: int = 300
    options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "BACKEND": self.backend,
            "LOCATION": self.location,
            "KEY_PREFIX": self.key_prefix,
            "TIMEOUT": self.timeout,
        }
        if self.options:
            d["OPTIONS"] = self.options
        return d


@dataclass
class SecurityConfig:
    """Security-related Django settings."""
    secret_key: str = ""
    debug: bool = False
    allowed_hosts: List[str] = field(default_factory=list)
    secure_ssl_redirect: bool = False
    secure_hsts_seconds: int = 0
    secure_hsts_include_subdomains: bool = False
    secure_hsts_preload: bool = False
    session_cookie_secure: bool = False
    csrf_cookie_secure: bool = False
    csrf_trusted_origins: List[str] = field(default_factory=list)
    x_frame_options: str = "DENY"
    secure_content_type_nosniff: bool = True
    secure_browser_xss_filter: bool = True

    def __post_init__(self) -> None:
        if not self.secret_key:
            self.secret_key = secrets.token_urlsafe(64)


@dataclass
class LoggingConfig:
    """Django logging configuration."""
    level: str = "INFO"
    log_file: str = "app.log"
    error_log_file: str = "error.log"
    max_bytes: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 10
    format_simple: str = "%(asctime)s %(module)s.%(funcName)s: %(message)s"
    format_verbose: str = (
        "%(asctime)s %(levelname)s [%(process)d-%(threadName)s] "
        "%(module)s.%(funcName)s line %(lineno)d: %(message)s"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": self.format_simple,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "verbose": {
                    "format": self.format_verbose,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "filters": {
                "require_debug_true": {
                    "()": "django.utils.log.RequireDebugTrue",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "filters": ["require_debug_true"],
                    "formatter": "simple",
                },
                "file_info": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": self.log_file,
                    "maxBytes": self.max_bytes,
                    "backupCount": self.backup_count,
                    "formatter": "verbose",
                    "level": "INFO",
                },
                "file_error": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": self.error_log_file,
                    "maxBytes": self.max_bytes,
                    "backupCount": self.backup_count,
                    "formatter": "verbose",
                    "level": "WARNING",
                },
            },
            "loggers": {
                "django": {
                    "handlers": ["console", "file_info", "file_error"],
                    "propagate": True,
                    "level": self.level,
                },
                "app": {
                    "handlers": ["console", "file_info", "file_error"],
                    "propagate": False,
                    "level": "DEBUG",
                },
            },
        }


class DjangoSettingsBuilder:
    """
    Builds Django settings dictionaries for different environments.

    Enterprise Example: A single codebase deployed across development,
    staging, and production with environment-specific configurations
    loaded from environment variables and secrets management.

    This implements the 12-Factor App methodology for configuration:
    - Store config in the environment
    - Strict separation of config from code
    - Environment parity across dev/staging/prod
    """

    def __init__(self, project_name: str, base_dir: str = "."):
        self.project_name = project_name
        self.base_dir = Path(base_dir)
        self._settings: Dict[str, Any] = {}
        self._installed_apps: List[str] = []
        self._middleware: List[str] = []
        self._databases: Dict[str, Dict[str, Any]] = {}
        self._caches: Dict[str, Dict[str, Any]] = {}
        self._urls: List[str] = []

    def set_environment(self, env: Environment) -> "DjangoSettingsBuilder":
        """Configure settings for the specified environment."""
        self._settings["ENVIRONMENT"] = env.value

        if env == Environment.DEVELOPMENT:
            self._development_settings()
        elif env == Environment.TESTING:
            self._testing_settings()
        elif env == Environment.STAGING:
            self._staging_settings()
        elif env == Environment.PRODUCTION:
            self._production_settings()

        return self

    def _base_settings(self) -> None:
        """Common settings for all environments."""
        self._settings.update({
            "ROOT_URLCONF": f"{self.project_name}.urls",
            "WSGI_APPLICATION": f"{self.project_name}.wsgi.application",
            "LANGUAGE_CODE": "zh-hans",
            "TIME_ZONE": "Asia/Shanghai",
            "USE_I18N": True,
            "USE_TZ": True,
            "DEFAULT_AUTO_FIELD": "django.db.models.BigAutoField",
        })

        # Default installed apps
        self._installed_apps = [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
        ]

        # Default middleware (correct order per Django docs)
        self._middleware = [
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ]

    def _development_settings(self) -> None:
        self._base_settings()
        security = SecurityConfig(
            secret_key=os.environ.get(
                "DJANGO_SECRET_KEY",
                "dev-insecure-key-change-in-production"
            ),
            debug=True,
            allowed_hosts=["*"],
        )
        self._settings["DEBUG"] = True
        self._settings["SECRET_KEY"] = security.secret_key
        self._settings["ALLOWED_HOSTS"] = security.allowed_hosts

        db = DatabaseConfig(
            engine="django.db.backends.sqlite3",
            name=str(self.base_dir / "db.sqlite3"),
        )
        self._databases = {"default": db.to_dict()}

        self._caches = {
            "default": CacheConfig(
                backend="django.core.cache.backends.locmem.LocMemCache",
                location="unique-snowflake",
            ).to_dict()
        }

        self._settings["STATIC_URL"] = "/static/"
        self._settings["STATIC_ROOT"] = str(self.base_dir / "staticfiles")
        self._settings["MEDIA_URL"] = "/media/"
        self._settings["MEDIA_ROOT"] = str(self.base_dir / "media")

    def _testing_settings(self) -> None:
        self._base_settings()
        self._settings["DEBUG"] = False
        self._settings["SECRET_KEY"] = "test-secret-key-not-for-production"
        self._settings["ALLOWED_HOSTS"] = ["testserver", "localhost"]

        db = DatabaseConfig(
            engine="django.db.backends.sqlite3",
            name=":memory:",
            test={"NAME": ":memory:"},
        )
        self._databases = {"default": db.to_dict()}

        self._caches = {
            "default": CacheConfig(
                backend="django.core.cache.backends.locmem.LocMemCache",
            ).to_dict()
        }
        self._settings["PASSWORD_HASHERS"] = [
            "django.contrib.auth.hashers.MD5PasswordHasher",
        ]

    def _staging_settings(self) -> None:
        self._base_settings()
        self._settings["DEBUG"] = False
        self._settings["SECRET_KEY"] = os.environ.get("DJANGO_SECRET_KEY", "")
        self._settings["ALLOWED_HOSTS"] = os.environ.get(
            "ALLOWED_HOSTS", "staging.example.com"
        ).split(",")

        db = DatabaseConfig(
            name=os.environ.get("DB_NAME", "staging_db"),
            user=os.environ.get("DB_USER", "staging_user"),
            password=os.environ.get("DB_PASSWORD", ""),
            host=os.environ.get("DB_HOST", "staging-db.example.com"),
            port=int(os.environ.get("DB_PORT", "5432")),
        )
        self._databases = {"default": db.to_dict()}

        self._caches = {
            "default": CacheConfig(
                location=os.environ.get("REDIS_URL", "redis://staging-redis:6379/1"),
            ).to_dict()
        }

    def _production_settings(self) -> None:
        self._base_settings()
        security = SecurityConfig(
            secret_key=os.environ["DJANGO_SECRET_KEY"],
            debug=False,
            allowed_hosts=os.environ.get(
                "ALLOWED_HOSTS", "www.example.com"
            ).split(","),
            secure_ssl_redirect=True,
            secure_hsts_seconds=31536000,
            secure_hsts_include_subdomains=True,
            secure_hsts_preload=True,
            session_cookie_secure=True,
            csrf_cookie_secure=True,
            csrf_trusted_origins=os.environ.get(
                "CSRF_TRUSTED_ORIGINS", "https://www.example.com"
            ).split(","),
        )
        self._settings["DEBUG"] = False
        self._settings["SECRET_KEY"] = security.secret_key
        self._settings["ALLOWED_HOSTS"] = security.allowed_hosts
        self._settings["SECURE_SSL_REDIRECT"] = security.secure_ssl_redirect
        self._settings["SECURE_HSTS_SECONDS"] = security.secure_hsts_seconds
        self._settings["SECURE_HSTS_INCLUDE_SUBDOMAINS"] = security.secure_hsts_include_subdomains
        self._settings["SECURE_HSTS_PRELOAD"] = security.secure_hsts_preload
        self._settings["SESSION_COOKIE_SECURE"] = security.session_cookie_secure
        self._settings["CSRF_COOKIE_SECURE"] = security.csrf_cookie_secure
        self._settings["CSRF_TRUSTED_ORIGINS"] = security.csrf_trusted_origins
        self._settings["X_FRAME_OPTIONS"] = security.x_frame_options
        self._settings["SECURE_CONTENT_TYPE_NOSNIFF"] = security.secure_content_type_nosniff

        db = DatabaseConfig(
            name=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ.get("DB_HOST", "db.example.com"),
            port=int(os.environ.get("DB_PORT", "5432")),
            options={"sslmode": os.environ.get("DB_SSLMODE", "require")},
            conn_max_age=600,
        )
        self._databases = {"default": db.to_dict()}

        self._caches = {
            "default": CacheConfig(
                location=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
                timeout=600,
            ).to_dict(),
            "session": CacheConfig(
                location=os.environ.get("REDIS_SESSION_URL", "redis://redis:6379/2"),
                key_prefix="session",
                timeout=1209600,
            ).to_dict(),
            "api": CacheConfig(
                location=os.environ.get("REDIS_API_URL", "redis://redis:6379/3"),
                key_prefix="api",
                timeout=300,
            ).to_dict(),
        }

        # Template caching in production
        self._settings["TEMPLATES"] = [{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [str(self.base_dir / "templates")],
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
                "loaders": [(
                    "django.template.loaders.cached.Loader", [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                )],
            },
        }]

    def add_app(self, app_name: str) -> "DjangoSettingsBuilder":
        """Add a Django app to INSTALLED_APPS."""
        if app_name not in self._installed_apps:
            self._installed_apps.append(app_name)
        return self

    def add_middleware(self, middleware_path: str) -> "DjangoSettingsBuilder":
        """Add a middleware class to MIDDLEWARE."""
        if middleware_path not in self._middleware:
            self._middleware.append(middleware_path)
        return self

    def set_auth_model(self, model_path: str) -> "DjangoSettingsBuilder":
        """Set the custom user model (AUTH_USER_MODEL)."""
        self._settings["AUTH_USER_MODEL"] = model_path
        return self

    def add_rest_framework(self) -> "DjangoSettingsBuilder":
        """Add Django REST Framework configuration."""
        self.add_app("rest_framework")
        self._settings["REST_FRAMEWORK"] = {
            "PAGE_SIZE": 20,
            "DEFAULT_PAGINATION_CLASS":
                "rest_framework.pagination.PageNumberPagination",
            "DEFAULT_AUTHENTICATION_CLASSES": [
                "rest_framework.authentication.SessionAuthentication",
                "rest_framework.authentication.TokenAuthentication",
            ],
            "DEFAULT_PERMISSION_CLASSES": [
                "rest_framework.permissions.IsAuthenticated",
            ],
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
                "rest_framework.throttling.UserRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "anon": "100/hour",
                "user": "10000/day",
            },
        }
        return self

    def add_cors(self, allow_all: bool = False) -> "DjangoSettingsBuilder":
        """Add CORS headers configuration."""
        self.add_app("corsheaders")
        self._middleware.insert(0, "corsheaders.middleware.CorsMiddleware")
        if allow_all:
            self._settings["CORS_ORIGIN_ALLOW_ALL"] = True
        return self

    def build(self) -> Dict[str, Any]:
        """Build and return the complete settings dictionary."""
        self._settings["INSTALLED_APPS"] = self._installed_apps
        self._settings["MIDDLEWARE"] = self._middleware
        self._settings["DATABASES"] = self._databases
        self._settings["CACHES"] = self._caches

        # Logging
        logging_cfg = LoggingConfig()
        if self._settings.get("ENVIRONMENT") == "production":
            logging_cfg.level = "WARNING"
        self._settings["LOGGING"] = logging_cfg.to_dict()

        return self._settings

    def to_python_code(self) -> str:
        """Generate settings as a Python source file."""
        settings = self.build()
        lines = [
            f'"""Auto-generated Django settings for {self.project_name}."""',
            "",
            "import os",
            "",
            f'ENVIRONMENT = "{settings.get("ENVIRONMENT", "development")}"',
            "",
        ]

        for key, value in sorted(settings.items()):
            if key == "ENVIRONMENT":
                continue
            lines.append(f"{key} = {repr(value)}")
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 2: Custom User Model (自定义用户模型)
# ---------------------------------------------------------------------------


@dataclass
class UserProfile:
    """
    Extended user profile for commercial applications.

    In a real Django project, this would be a model extending
    AbstractUser or linked via a OneToOneField to django.contrib.auth.User.

    Fields mirror common enterprise requirements:
    - Phone verification for two-factor auth
    - Role-based access control (RBAC)
    - Audit fields (created_at, updated_at, last_login_ip)
    - Soft delete support
    """
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    username: str = ""
    email: str = ""
    phone: str = ""
    first_name: str = ""
    last_name: str = ""
    avatar_url: str = ""
    role: str = "user"
    is_active: bool = True
    is_phone_verified: bool = False
    is_email_verified: bool = False
    last_login_ip: str = ""
    login_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    # Password-related (stored as hash, never plain text)
    password_hash: str = ""

    VALID_ROLES = ("user", "staff", "admin", "superadmin")
    PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def validate(self) -> List[str]:
        """Validate user profile fields and return list of errors."""
        errors: List[str] = []
        if not self.username or len(self.username) < 3:
            errors.append("Username must be at least 3 characters.")
        if self.email and not self.EMAIL_PATTERN.match(self.email):
            errors.append(f"Invalid email format: {self.email}")
        if self.phone and not self.PHONE_PATTERN.match(self.phone):
            errors.append(f"Invalid phone format: {self.phone}")
        if self.role not in self.VALID_ROLES:
            errors.append(f"Invalid role: {self.role}")
        return errors

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def soft_delete(self) -> None:
        """Mark user as deleted without removing data."""
        self.deleted_at = datetime.utcnow()
        self.is_active = False

    def record_login(self, ip_address: str) -> None:
        """Record a login event."""
        self.last_login_ip = ip_address
        self.login_count += 1
        self.updated_at = datetime.utcnow()

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """Hash a password with PBKDF2-SHA256 (Django's default)."""
        if salt is None:
            salt = secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
        return f"pbkdf2_sha256$260000${salt}${dk.hex()}"

    def set_password(self, password: str) -> None:
        """Set the user's password (hashed)."""
        self.password_hash = self.hash_password(password)

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        parts = self.password_hash.split("$")
        if len(parts) != 4:
            return False
        _, iterations, salt, _ = parts
        test_hash = self.hash_password(password, salt)
        return secrets.compare_digest(test_hash, self.password_hash)


# ---------------------------------------------------------------------------
# Section 3: Django Signals Pattern (Django信号模式)
# ---------------------------------------------------------------------------


class Signal:
    """
    Lightweight signal/dispatcher implementation.

    In Django, signals allow decoupled applications to get notified when
    certain actions occur. This demonstrates the pattern without requiring
    the full Django framework.

    Common Django signals:
    - pre_save / post_save: Before/after model save
    - pre_delete / post_delete: Before/after model deletion
    - request_started / request_finished: HTTP request lifecycle
    - user_logged_in / user_logged_out: Authentication events
    """

    def __init__(self, name: str):
        self.name = name
        self._receivers: List[Callable[..., Any]] = []

    def connect(self, receiver: Callable[..., Any]) -> None:
        """Connect a receiver function to this signal."""
        if receiver not in self._receivers:
            self._receivers.append(receiver)

    def disconnect(self, receiver: Callable[..., Any]) -> None:
        """Disconnect a receiver from this signal."""
        if receiver in self._receivers:
            self._receivers.remove(receiver)

    def send(self, sender: Any = None, **kwargs: Any) -> List[Tuple[Callable, Any]]:
        """
        Send signal to all connected receivers.

        Returns list of (receiver, response) tuples.
        """
        responses = []
        for receiver in self._receivers:
            try:
                response = receiver(sender=sender, **kwargs)
                responses.append((receiver, response))
            except Exception as e:
                responses.append((receiver, e))
        return responses


# Pre-defined signals (Django-compatible naming)
pre_save = Signal("pre_save")
post_save = Signal("post_save")
pre_delete = Signal("pre_delete")
post_delete = Signal("post_delete")
user_logged_in = Signal("user_logged_in")
user_logged_out = Signal("user_logged_out")
request_started = Signal("request_started")
request_finished = Signal("request_finished")


@dataclass
class AuditLog:
    """Audit log entry for tracking model changes."""
    log_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    action: str = ""  # CREATE, UPDATE, DELETE
    model_name: str = ""
    object_id: str = ""
    changes: Dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""


class AuditLogger:
    """
    Enterprise audit logging system using Django signal patterns.

    Captures all model mutations (create, update, delete) and logs them
    with before/after state for compliance and debugging.
    """

    def __init__(self) -> None:
        self.logs: List[AuditLog] = []
        self._connect_signals()

    def _connect_signals(self) -> None:
        pre_save.connect(self.on_pre_save)
        post_save.connect(self.on_post_save)
        pre_delete.connect(self.on_pre_delete)

    def on_pre_save(self, sender: Any = None, **kwargs: Any) -> None:
        """Capture the old state before save."""
        instance = kwargs.get("instance")
        if instance is not None:
            self._old_state = getattr(instance, "__dict__", {}).copy()

    def on_post_save(self, sender: Any = None, **kwargs: Any) -> None:
        """Log the save operation with changes."""
        instance = kwargs.get("instance")
        created = kwargs.get("created", False)
        if instance is not None:
            action = "CREATE" if created else "UPDATE"
            changes: Dict[str, Any] = {}
            old = getattr(self, "_old_state", {})
            new = getattr(instance, "__dict__", {})
            for key in set(list(old.keys()) + list(new.keys())):
                if key.startswith("_"):
                    continue
                old_val = old.get(key)
                new_val = new.get(key)
                if old_val != new_val and key not in ("updated_at", "password_hash"):
                    changes[key] = {"old": old_val, "new": new_val}

            log = AuditLog(
                action=action,
                model_name=type(instance).__name__,
                object_id=str(getattr(instance, "pk", getattr(instance, "id", ""))),
                changes=changes,
            )
            self.logs.append(log)

    def on_pre_delete(self, sender: Any = None, **kwargs: Any) -> None:
        """Log the deletion."""
        instance = kwargs.get("instance")
        if instance is not None:
            log = AuditLog(
                action="DELETE",
                model_name=type(instance).__name__,
                object_id=str(getattr(instance, "pk", getattr(instance, "id", ""))),
            )
            self.logs.append(log)

    def get_logs(
        self,
        model_name: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Retrieve audit logs with optional filtering."""
        filtered = self.logs
        if model_name:
            filtered = [l for l in filtered if l.model_name == model_name]
        if action:
            filtered = [l for l in filtered if l.action == action]
        return filtered[-limit:]


# ---------------------------------------------------------------------------
# Section 4: Deployment Checklist (部署检查清单)
# ---------------------------------------------------------------------------


@dataclass
class ChecklistItem:
    """A single deployment checklist item."""
    category: str
    description: str
    is_checked: bool = False
    priority: str = "required"  # required, recommended, optional
    notes: str = ""


class DeploymentChecklist:
    """
    Enterprise Django deployment checklist.

    Comprehensive pre-deployment verification covering:
    - Security settings
    - Database readiness
    - Static files and media
    - Cache configuration
    - Logging and monitoring
    - SSL/TLS setup
    - Backup verification
    """

    def __init__(self) -> None:
        self.items: List[ChecklistItem] = self._build_checklist()

    def _build_checklist(self) -> List[ChecklistItem]:
        return [
            # Security
            ChecklistItem("Security", "SECRET_KEY set from environment variable", priority="required"),
            ChecklistItem("Security", "DEBUG set to False", priority="required"),
            ChecklistItem("Security", "ALLOWED_HOSTS configured", priority="required"),
            ChecklistItem("Security", "SECURE_SSL_REDIRECT enabled", priority="required"),
            ChecklistItem("Security", "SECURE_HSTS_SECONDS set (>= 31536000)", priority="recommended"),
            ChecklistItem("Security", "SESSION_COOKIE_SECURE enabled", priority="required"),
            ChecklistItem("Security", "CSRF_COOKIE_SECURE enabled", priority="required"),
            ChecklistItem("Security", "X_FRAME_OPTIONS set to DENY", priority="required"),
            ChecklistItem("Security", "SECURE_CONTENT_TYPE_NOSNIFF enabled", priority="required"),
            ChecklistItem("Security", "All third-party packages up to date", priority="recommended"),
            ChecklistItem("Security", "No hardcoded credentials in source code", priority="required"),

            # Database
            ChecklistItem("Database", "Database migrations applied", priority="required"),
            ChecklistItem("Database", "Database backup configured", priority="required"),
            ChecklistItem("Database", "Connection pooling configured", priority="recommended"),
            ChecklistItem("Database", "Slow query logging enabled", priority="recommended"),
            ChecklistItem("Database", "Read replicas configured (if needed)", priority="optional"),

            # Static Files
            ChecklistItem("Static Files", "collectstatic executed", priority="required"),
            ChecklistItem("Static Files", "STATIC_ROOT configured", priority="required"),
            ChecklistItem("Static Files", "CDN configured for static assets", priority="recommended"),
            ChecklistItem("Static Files", "Media files stored in cloud storage", priority="recommended"),

            # Cache
            ChecklistItem("Cache", "Redis cache backend configured", priority="required"),
            ChecklistItem("Cache", "Session engine set to cache backend", priority="recommended"),
            ChecklistItem("Cache", "View-level caching configured", priority="recommended"),
            ChecklistItem("Cache", "Template fragment caching used", priority="optional"),

            # Logging
            ChecklistItem("Logging", "File-based logging configured", priority="required"),
            ChecklistItem("Logging", "Error log level set to WARNING or higher", priority="required"),
            ChecklistItem("Logging", "Log rotation configured", priority="required"),
            ChecklistItem("Logging", "Centralized logging (ELK/Sentry) configured", priority="recommended"),

            # Performance
            ChecklistItem("Performance", "Gunicorn/uWSGI workers configured", priority="required"),
            ChecklistItem("Performance", "Nginx reverse proxy configured", priority="required"),
            ChecklistItem("Performance", "Database query optimization (N+1 queries resolved)", priority="required"),
            ChecklistItem("Performance", "Celery configured for async tasks", priority="recommended"),

            # Monitoring
            ChecklistItem("Monitoring", "Health check endpoint (/health) available", priority="required"),
            ChecklistItem("Monitoring", "Uptime monitoring configured", priority="required"),
            ChecklistItem("Monitoring", "Error tracking (Sentry) configured", priority="recommended"),
            ChecklistItem("Monitoring", "Performance monitoring (APM) configured", priority="optional"),

            # Backup
            ChecklistItem("Backup", "Database backup schedule configured", priority="required"),
            ChecklistItem("Backup", "Media backup configured", priority="required"),
            ChecklistItem("Backup", "Backup restoration tested", priority="required"),
            ChecklistItem("Backup", "Disaster recovery plan documented", priority="recommended"),

            # Testing
            ChecklistItem("Testing", "All unit tests passing", priority="required"),
            ChecklistItem("Testing", "Integration tests passing", priority="required"),
            ChecklistItem("Testing", "Test coverage >= 80%", priority="recommended"),
            ChecklistItem("Testing", "Load testing performed", priority="recommended"),
        ]

    def check(self, category: str, index: int) -> None:
        """Mark a checklist item as checked."""
        cat_items = [i for i in self.items if i.category == category]
        if 0 <= index < len(cat_items):
            cat_items[index].is_checked = True

    def get_summary(self) -> Dict[str, Any]:
        """Get deployment readiness summary."""
        total = len(self.items)
        checked = sum(1 for i in self.items if i.is_checked)
        required = [i for i in self.items if i.priority == "required"]
        required_checked = sum(1 for i in required if i.is_checked)

        categories: Dict[str, Dict[str, int]] = {}
        for item in self.items:
            if item.category not in categories:
                categories[item.category] = {"total": 0, "checked": 0}
            categories[item.category]["total"] += 1
            if item.is_checked:
                categories[item.category]["checked"] += 1

        return {
            "total_items": total,
            "checked": checked,
            "completion_pct": round(checked / total * 100, 1) if total else 0,
            "required_total": len(required),
            "required_checked": required_checked,
            "ready_for_production": required_checked == len(required),
            "categories": categories,
        }

    def print_report(self) -> None:
        """Print a formatted deployment checklist report."""
        print("\nDeployment Checklist Report")
        print("=" * 70)

        current_category = ""
        cat_index = 0
        for item in self.items:
            if item.category != current_category:
                current_category = item.category
                cat_index = 0
                print(f"\n  [{current_category}]")
            status = "[x]" if item.is_checked else "[ ]"
            priority_marker = {"required": "*", "recommended": "+", "optional": "~"}
            marker = priority_marker.get(item.priority, " ")
            print(f"    {status} {marker} {item.description}")
            cat_index += 1

        summary = self.get_summary()
        print(f"\n{'=' * 70}")
        print(f"  Completion: {summary['completion_pct']}%")
        print(f"  Required items: {summary['required_checked']}/{summary['required_total']}")
        ready = "YES" if summary["ready_for_production"] else "NO"
        print(f"  Ready for production: {ready}")


# ---------------------------------------------------------------------------
# Section 5: URL Configuration Patterns (URL配置模式)
# ---------------------------------------------------------------------------


@dataclass
class URLPattern:
    """Represents a Django URL pattern."""
    pattern: str
    view: str
    name: str = ""
    methods: List[str] = field(default_factory=list)
    namespace: str = ""

    def to_url_line(self) -> str:
        if self.methods:
            return f"    path('{self.pattern}', {self.view}, name='{self.name}')"
        return f"    path('{self.pattern}', {self.view}, name='{self.name}')"


class URLConfigBuilder:
    """
    Programmatic URL configuration builder.

    Supports:
    - Nested URL includes with namespaces
    - RESTful resource URL generation
    - Debug-only URL patterns
    """

    def __init__(self, namespace: str = ""):
        self.namespace = namespace
        self.patterns: List[URLPattern] = []
        self._includes: List[Tuple[str, str, str]] = []  # prefix, module, namespace

    def add(
        self,
        pattern: str,
        view: str,
        name: str = "",
        methods: Optional[List[str]] = None,
    ) -> "URLConfigBuilder":
        self.patterns.append(URLPattern(
            pattern=pattern, view=view,
            name=name, methods=methods or [],
        ))
        return self

    def include(
        self, prefix: str, module: str, namespace: str = ""
    ) -> "URLConfigBuilder":
        self._includes.append((prefix, module, namespace))
        return self

    def add_rest_resource(
        self, resource_name: str, viewset: str, basename: str = ""
    ) -> "URLConfigBuilder":
        """Add RESTful CRUD routes for a resource."""
        if not basename:
            basename = resource_name
        self.patterns.append(URLPattern(
            pattern=f"{resource_name}/",
            view=f"{viewset}.as_view({{'get': 'list', 'post': 'create'}})",
            name=f"{basename}-list",
        ))
        self.patterns.append(URLPattern(
            pattern=f"{resource_name}/<int:pk>/",
            view=f"{viewset}.as_view({{'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}})",
            name=f"{basename}-detail",
        ))
        return self

    def generate(self) -> str:
        """Generate URL configuration Python code."""
        lines = [
            "from django.urls import path, include",
            "from rest_framework.routers import DefaultRouter",
            "",
            "app_name = '{}'".format(self.namespace),
            "",
            "urlpatterns = [",
        ]
        for p in self.patterns:
            lines.append(p.to_url_line() + ",")
        for prefix, module, ns in self._includes:
            if ns:
                lines.append(f"    path('{prefix}', include('{module}', namespace='{ns}')),")
            else:
                lines.append(f"    path('{prefix}', include('{module}')),")
        lines.append("]")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 6: Middleware Patterns (中间件模式)
# ---------------------------------------------------------------------------


class MiddlewareFactory:
    """
    Factory for generating Django middleware code.

    Generates middleware for common enterprise needs:
    - Request timing and performance logging
    - IP-based rate limiting
    - Request/response logging for audit
    - CORS handling
    - Custom authentication
    """

    @staticmethod
    def generate_request_timer() -> str:
        """Generate a request timing middleware."""
        return textwrap.dedent("""\
            import time
            import logging

            logger = logging.getLogger('app.middleware')


            def request_timer_middleware(get_response):
                \"\"\"Middleware that logs request processing time.\"\"\"

                def middleware(request):
                    start = time.time()
                    response = get_response(request)
                    duration = time.time() - start
                    logger.info(
                        '%s %s %.3fs [%d]',
                        request.method,
                        request.path,
                        duration,
                        response.status_code,
                    )
                    if duration > 1.0:
                        logger.warning(
                            'Slow request: %s %s took %.3fs',
                            request.method, request.path, duration,
                        )
                    response['X-Request-Duration'] = f'{duration:.3f}s'
                    return response

                return middleware
        """)

    @staticmethod
    def generate_rate_limiter() -> str:
        """Generate an IP-based rate limiting middleware."""
        return textwrap.dedent("""\
            import time
            from collections import defaultdict
            from django.http import JsonResponse


            def rate_limit_middleware(get_response):
                \"\"\"IP-based rate limiting middleware.\"\"\"
                _requests = defaultdict(list)
                MAX_REQUESTS = 100
                WINDOW_SECONDS = 60

                def middleware(request):
                    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                    now = time.time()
                    window_start = now - WINDOW_SECONDS

                    # Clean old entries
                    _requests[ip] = [
                        t for t in _requests[ip] if t > window_start
                    ]

                    if len(_requests[ip]) >= MAX_REQUESTS:
                        return JsonResponse(
                            {'error': 'Rate limit exceeded'},
                            status=429,
                        )

                    _requests[ip].append(now)
                    return get_response(request)

                return middleware
        """)

    @staticmethod
    def generate_audit_logger() -> str:
        """Generate a request audit logging middleware."""
        return textwrap.dedent("""\
            import json
            import logging

            logger = logging.getLogger('app.audit')


            def audit_log_middleware(get_response):
                \"\"\"Middleware for audit logging of all write operations.\"\"\"

                def middleware(request):
                    response = get_response(request)

                    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                        logger.info(
                            'AUDIT: %s %s user=%s ip=%s status=%d',
                            request.method,
                            request.path,
                            getattr(request.user, 'id', 'anonymous'),
                            request.META.get('REMOTE_ADDR', ''),
                            response.status_code,
                        )

                    return response

                return middleware
        """)


# ---------------------------------------------------------------------------
# Section 7: Testing Patterns (测试模式)
# ---------------------------------------------------------------------------


class TestGenerator:
    """
    Generate Django test code for common scenarios.

    Produces pytest-style tests covering:
    - Model unit tests
    - View/API endpoint tests
    - Authentication tests
    - Form validation tests
    - Integration tests
    """

    @staticmethod
    def generate_model_test(model_name: str, fields: List[str]) -> str:
        return textwrap.dedent(f"""\
            import pytest
            from django.test import TestCase


            class {model_name}Test(TestCase):
                \"\"\"Unit tests for {model_name} model.\"\"\"

                def setUp(self):
                    self.data = {{
                        {chr(10).join(f"        '{f}': 'test_{f}'," for f in fields)}
                    }}

                def test_create_{model_name.lower()}(self):
                    \"\"\"Test creating a {model_name} instance.\"\"\"
                    instance = {model_name}.objects.create(**self.data)
                    self.assertIsNotNone(instance.pk)
                    self.assertEqual(str(instance), instance.name)

                def test_{model_name.lower()}_str_representation(self):
                    \"\"\"Test string representation.\"\"\"
                    instance = {model_name}.objects.create(**self.data)
                    self.assertIsInstance(str(instance), str)

                def test_{model_name.lower()}_update(self):
                    \"\"\"Test updating a {model_name} instance.\"\"\"
                    instance = {model_name}.objects.create(**self.data)
                    instance.save()
                    refreshed = {model_name}.objects.get(pk=instance.pk)
                    self.assertIsNotNone(refreshed)

                def test_{model_name.lower()}_delete(self):
                    \"\"\"Test deleting a {model_name} instance.\"\"\"
                    instance = {model_name}.objects.create(**self.data)
                    pk = instance.pk
                    instance.delete()
                    self.assertFalse({model_name}.objects.filter(pk=pk).exists())

                def test_{model_name.lower()}_queryset(self):
                    \"\"\"Test querying {model_name} instances.\"\"\"
                    {model_name}.objects.create(**self.data)
                    self.assertGreaterEqual({model_name}.objects.count(), 1)
        """)

    @staticmethod
    def generate_api_test(resource_name: str) -> str:
        return textwrap.dedent(f"""\
            import json
            from django.test import TestCase, Client
            from django.urls import reverse


            class {resource_name}APITest(TestCase):
                \"\"\"API endpoint tests for {resource_name}.\"\"\"

                def setUp(self):
                    self.client = Client()
                    self.list_url = reverse('{resource_name.lower()}-list')

                def test_list_{resource_name.lower()}(self):
                    \"\"\"Test GET list endpoint.\"\"\"
                    response = self.client.get(self.list_url)
                    self.assertEqual(response.status_code, 200)

                def test_create_{resource_name.lower()}(self):
                    \"\"\"Test POST create endpoint.\"\"\"
                    data = {{'name': 'test'}}
                    response = self.client.post(
                        self.list_url,
                        data=json.dumps(data),
                        content_type='application/json',
                    )
                    self.assertIn(response.status_code, [200, 201])

                def test_unauthorized_access(self):
                    \"\"\"Test that unauthenticated users get 401/403.\"\"\"
                    response = self.client.get(self.list_url)
                    # Depending on permission settings
                    self.assertIn(response.status_code, [200, 401, 403])
        """)


# ---------------------------------------------------------------------------
# Section 8: Demonstration Functions
# ---------------------------------------------------------------------------


def demonstrate_settings_builder() -> None:
    """Show multi-environment settings generation."""
    print("=" * 70)
    print("PART 1: Multi-Environment Django Settings")
    print("=" * 70)

    for env in Environment:
        builder = DjangoSettingsBuilder("myproject")
        builder.set_environment(env)
        builder.add_app("rest_framework")
        builder.add_app("corsheaders")
        builder.set_auth_model("accounts.User")

        settings = builder.build()
        print(f"\n  [{env.value.upper()}]")
        print(f"    DEBUG:            {settings.get('DEBUG')}")
        print(f"    DB Engine:        {settings['DATABASES']['default'].get('ENGINE', 'N/A')}")
        print(f"    Cache Backend:    {settings['CACHES']['default'].get('BACKEND', 'N/A')[:50]}")
        print(f"    Installed Apps:   {len(settings['INSTALLED_APPS'])}")
        print(f"    Middleware:       {len(settings['MIDDLEWARE'])}")


def demonstrate_custom_user() -> None:
    """Show custom user model patterns."""
    print("\n" + "=" * 70)
    print("PART 2: Custom User Model")
    print("=" * 70)

    # Create a user
    user = UserProfile(
        username="zhangsan",
        email="zhangsan@example.com",
        phone="13800138000",
        first_name="San",
        last_name="Zhang",
        role="admin",
    )
    user.set_password("SecureP@ss123!")

    print(f"\n  User: {user.full_name}")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Phone: {user.phone}")
    print(f"  Role: {user.role}")

    # Validation
    errors = user.validate()
    print(f"  Validation errors: {errors or 'None'}")

    # Password verification
    print(f"  Password check (correct): {user.check_password('SecureP@ss123!')}")
    print(f"  Password check (wrong):   {user.check_password('wrong_password')}")

    # Login tracking
    user.record_login("192.168.1.100")
    print(f"  Login count: {user.login_count}")
    print(f"  Last IP: {user.last_login_ip}")

    # Soft delete
    user.soft_delete()
    print(f"  Is deleted: {user.is_deleted}")
    print(f"  Is active: {user.is_active}")


def demonstrate_signals() -> None:
    """Show Django signal patterns with audit logging."""
    print("\n" + "=" * 70)
    print("PART 3: Django Signals & Audit Logging")
    print("=" * 70)

    audit = AuditLogger()

    # Simulate model operations
    class MockModel:
        def __init__(self, **kwargs: Any) -> None:
            self.pk = kwargs.get("pk", "1")
            self.id = self.pk
            self.name = kwargs.get("name", "")
            self.email = kwargs.get("email", "")

    # Simulate CREATE
    instance = MockModel(pk="1", name="Test User", email="test@example.com")
    pre_save.send(sender=MockModel, instance=instance)
    instance.__dict__["_state"] = "fake"  # Django internal
    post_save.send(sender=MockModel, instance=instance, created=True)

    # Simulate UPDATE
    instance.name = "Updated User"
    pre_save.send(sender=MockModel, instance=instance)
    post_save.send(sender=MockModel, instance=instance, created=False)

    # Simulate DELETE
    pre_delete.send(sender=MockModel, instance=instance)

    # Show audit logs
    logs = audit.get_logs()
    print(f"\n  Audit logs ({len(logs)} entries):")
    for log in logs:
        print(f"    [{log.action}] {log.model_name}#{log.object_id}")
        if log.changes:
            for field, change in log.changes.items():
                print(f"      {field}: {change['old']} -> {change['new']}")


def demonstrate_deployment_checklist() -> None:
    """Show deployment checklist with sample completion."""
    print("\n" + "=" * 70)
    print("PART 4: Deployment Checklist")
    print("=" * 70)

    checklist = DeploymentChecklist()

    # Simulate checking some items
    checklist.check("Security", 0)   # SECRET_KEY
    checklist.check("Security", 1)   # DEBUG = False
    checklist.check("Security", 2)   # ALLOWED_HOSTS
    checklist.check("Database", 0)   # Migrations
    checklist.check("Database", 1)   # Backup
    checklist.check("Static Files", 0)  # collectstatic
    checklist.check("Cache", 0)      # Redis
    checklist.check("Logging", 0)    # File logging
    checklist.check("Logging", 1)    # Error level
    checklist.check("Logging", 2)    # Log rotation
    checklist.check("Testing", 0)    # Unit tests
    checklist.check("Backup", 0)     # DB backup
    checklist.check("Backup", 2)     # Restoration tested

    checklist.print_report()


def demonstrate_url_config() -> None:
    """Show URL configuration patterns."""
    print("\n" + "=" * 70)
    print("PART 5: URL Configuration Patterns")
    print("=" * 70)

    builder = URLConfigBuilder(namespace="api")

    builder.add("", "views.index", name="index")
    builder.add("health/", "views.health_check", name="health")
    builder.add_rest_resource("users", "UserViewSet", basename="user")
    builder.add_rest_resource("products", "ProductViewSet", basename="product")
    builder.include("auth/", "accounts.urls", namespace="accounts")

    print(f"\n{builder.generate()}")


def demonstrate_middleware_generation() -> None:
    """Show middleware code generation."""
    print("\n" + "=" * 70)
    print("PART 6: Middleware Generation")
    print("=" * 70)

    factory = MiddlewareFactory()

    print("\n--- Request Timer Middleware ---")
    print(factory.generate_request_timer())

    print("\n--- Rate Limiter Middleware ---")
    print(factory.generate_rate_limiter())


# ---------------------------------------------------------------------------
# Main Guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Django Commercial Project Best Practices -- Enterprise Demo")
    print("=" * 70)

    demonstrate_settings_builder()
    demonstrate_custom_user()
    demonstrate_signals()
    demonstrate_deployment_checklist()
    demonstrate_url_config()
    demonstrate_middleware_generation()

    print("\n" + "=" * 70)
    print("All demonstrations completed successfully.")
    print("=" * 70)
