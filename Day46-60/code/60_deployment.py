"""
60_deployment.py - Django项目上线 (Project Deployment)
======================================================

本模块全面演示Django项目的部署上线技术,包括:
- 部署清单(Checklist)
- Gunicorn/uWSGI应用服务器配置
- Nginx反向代理与静态文件服务
- Docker容器化部署
- Docker Compose多服务编排
- CI/CD持续集成/持续部署
- systemd服务管理
- 监控与日志

C++对比: Python部署 vs C++构建流水线
------------------------------------
1. Python部署:
   - 源代码直接运行(解释执行)
   - pip install安装依赖(requirements.txt)
   - 无需编译步骤(开发到部署路径短)
   - 虚拟环境隔离(venv/conda)
   - WSGI/ASGI服务器运行(Gunicorn/uWSGI)
   - Docker镜像通常较大(含Python运行时+依赖)

2. C++构建流水线:
   - 源代码需要编译(CMake/Make/Bazel)
   - 编译产物是二进制可执行文件
   - 交叉编译支持(不同CPU架构/操作系统)
   - 依赖管理复杂(vcpkg/conan/系统包管理器)
   - 部署产物体积小(静态链接)
   - 但需要保证目标环境的libc兼容性

3. 关键差异:
   ┌───────────────────┬──────────────────────────────────────┐
   │   Python部署      │   C++构建部署                        │
   ├───────────────────┼──────────────────────────────────────┤
   │ pip + venv        │ CMake + vcpkg/conan                  │
   │ 源码部署          │ 编译产物部署                         │
   │ Gunicorn/uWSGI    │ Nginx直接代理二进制                   │
   │ Docker: ~200-800MB│ Docker: ~10-100MB(多阶段构建)        │
   │ 热重载(reload)    │ 需要重启进程                         │
   │ 解释执行(较慢)     │ 编译执行(极快)                       │
   │ 部署速度快         │ 构建+部署慢(需要编译)                │
   └───────────────────┴──────────────────────────────────────┘

企业级部署架构:
    Internet -> Nginx(反向代理+负载均衡+SSL)
                  ├── 静态文件 -> /static/ (Nginx直接服务)
                  └── 动态请求 -> Gunicorn (多个Worker进程)
                                    ├── Django App 1
                                    ├── Django App 2
                                    └── Django App N
                                      │
                                    PostgreSQL/MySQL + Redis

依赖安装:
    pip install django gunicorn whitenoise
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import textwrap
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# 第一部分: 部署清单
# ============================================================================

DEPLOYMENT_CHECKLIST = {
    "1_代码准备": [
        "确保所有代码已提交到版本控制系统(Git)",
        "创建发布标签(release tag): git tag v1.0.0",
        "运行所有单元测试并确保通过",
        "运行代码质量检查(flake8, black, isort)",
        "检查依赖版本并锁定(pip freeze > requirements.txt)",
    ],
    "2_配置管理": [
        "DEBUG = False",
        "SECRET_KEY从环境变量读取(不硬编码在代码中)",
        "ALLOWED_HOSTS配置为实际域名",
        "DATABASES配置为生产数据库(MySQL/PostgreSQL)",
        "静态文件配置: STATIC_ROOT, STATIC_URL",
        "媒体文件配置: MEDIA_ROOT, MEDIA_URL",
        "日志配置: 文件日志+级别设置",
        "CORS配置: 限制允许的源",
        "CSRF_TRUSTED_ORIGINS配置",
        "安全相关配置: SECURE_*, HSTS, XSS过滤等",
    ],
    "3_数据库": [
        "创建生产数据库和数据库用户",
        "执行数据库迁移(python manage.py migrate)",
        "收集静态文件(python manage.py collectstatic)",
        "创建超级用户(python manage.py createsuperuser)",
        "配置数据库备份策略",
        "配置数据库连接池(如django-db-connection-pool)",
    ],
    "4_安全加固": [
        "启用HTTPS(SSL证书配置)",
        "配置安全响应头(X-Frame-Options, CSP等)",
        "配置防火墙(只开放80/443端口)",
        "禁用DEBUG模式",
        "配置速率限制",
        "配置IP白名单/黑名单",
        "定期更新依赖(安全补丁)",
    ],
    "5_性能优化": [
        "配置缓存(Redis/Memcached)",
        "配置数据库查询优化(select_related/prefetch_related)",
        "配置Gunicorn Worker数量(通常2*CPU+1)",
        "配置Nginx连接数和缓冲区",
        "启用Gzip压缩",
        "配置静态文件缓存(Cache-Control)",
        "使用CDN加速静态资源",
    ],
    "6_监控运维": [
        "配置应用监控(Sentry/Prometheus)",
        "配置日志收集(ELK/Loki)",
        "配置健康检查端点(/health/)",
        "配置告警规则(错误率/响应时间/磁盘空间)",
        "配置自动备份",
        "准备回滚方案",
    ],
}


# ============================================================================
# 第二部分: 项目配置数据模型
# ============================================================================

@dataclass
class ProjectConfig:
    """部署配置中心数据类 - 所有生成器共享的配置"""

    project_name: str = "mysite"
    domain: str = "example.com"
    python_version: str = "3.11"
    framework: str = "django"  # "django" | "flask"
    workers: int = 4
    worker_class: str = "gthread"  # gthread | uvicorn.workers.UvicornWorker
    threads: int = 2
    bind_host: str = "0.0.0.0"
    bind_port: int = 8000
    static_url: str = "/static/"
    media_url: str = "/media/"
    db_engine: str = "postgres"  # postgres | mysql
    db_name: str = "app_db"
    db_user: str = "app_user"
    db_password: str = "changeme"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "super-secret-change-me-in-production"
    allowed_hosts: list = field(default_factory=lambda: ["*"])
    ssl: bool = True
    output_dir: str = "./deploy_output"

    @property
    def db_service(self) -> str:
        return "postgres" if self.db_engine == "postgres" else "mysql"

    @property
    def db_image(self) -> str:
        return "postgres:16-alpine" if self.db_engine == "postgres" else "mysql:8.0"

    @property
    def db_port(self) -> int:
        return 5432 if self.db_engine == "postgres" else 3306

    @property
    def db_env_vars(self) -> Dict[str, str]:
        if self.db_engine == "postgres":
            return {
                "POSTGRES_DB": self.db_name,
                "POSTGRES_USER": self.db_user,
                "POSTGRES_PASSWORD": self.db_password,
            }
        return {
            "MYSQL_DATABASE": self.db_name,
            "MYSQL_USER": self.db_user,
            "MYSQL_PASSWORD": self.db_password,
            "MYSQL_ROOT_PASSWORD": self.db_password,
        }


# ============================================================================
# 第三部分: Gunicorn配置生成器
# ============================================================================

class GunicornConfigGenerator:
    """
    Gunicorn配置生成器

    Gunicorn是Python WSGI HTTP服务器,生产环境首选
    特点: 简单、高效、稳定、易于配置

    C++对比:
    - Python: Gunicorn管理多个Worker进程运行Django
    - C++: 通常直接由systemd管理二进制进程,或通过Nginx反向代理
    - C++没有直接对标的WSGI服务器概念
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        self.cfg = cfg

    def generate(self) -> str:
        """生成gunicorn.conf.py配置文件"""
        return textwrap.dedent(f"""\
            \"\"\"
            Gunicorn configuration for {self.cfg.project_name}
            Generated by 60_deployment.py

            Usage: gunicorn -c gunicorn.conf.py {self.cfg.project_name}.wsgi:application
            \"\"\"

            import multiprocessing
            import os

            # ------ Server Socket ------
            bind = "{self.cfg.bind_host}:{self.cfg.bind_port}"
            backlog = 2048

            # ------ Worker Processes ------
            # 推荐: 2 * CPU核心数 + 1
            workers = {self.cfg.workers}
            worker_class = "{self.cfg.worker_class}"
            threads = {self.cfg.threads}
            worker_connections = 1000
            timeout = 120
            graceful_timeout = 30
            keepalive = 5

            # ------ Process Management ------
            # 最大请求数(处理这么多请求后Worker自动重启,防止内存泄漏)
            max_requests = 1000
            max_requests_jitter = 50

            # 预加载应用(减少内存使用,但热重载时所有Worker同时重启)
            preload_app = True

            # ------ Logging ------
            accesslog = "-"
            errorlog = "-"
            loglevel = "info"
            access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

            # ------ Process Naming ------
            proc_name = "{self.cfg.project_name}"

            # ------ Server Mechanics ------
            daemon = False
            raw_env = [
                "DJANGO_SETTINGS_MODULE={self.cfg.project_name}.settings_production",
            ]
            reload = False  # True in development only

            # ------ Hooks ------
            def on_starting(server) -> None:
                \"\"\"Called just before the master process is initialized.\"\"\"
                pass

            def post_fork(server, worker) -> None:
                \"\"\"Called just after a worker has been forked.\"\"\"
                server.log.info("Worker spawned (pid: %s)", worker.pid)

            def pre_exec(server) -> None:
                \"\"\"Called just before a new master process is forked.\"\"\"
                server.log.info("Forked child, re-executing.")

            def worker_exit(server, worker) -> None:
                \"\"\"Called when a worker has been exited.\"\"\"
                server.log.info("Worker exited (pid: %s)", worker.pid)
        """)


# ============================================================================
# 第四部分: Nginx配置生成器
# ============================================================================

class NginxConfigGenerator:
    """
    Nginx配置生成器

    Nginx职责:
    - 反向代理: 将动态请求转发给Gunicorn
    - 静态文件服务: 直接服务/media/和/static/
    - SSL终止: 处理HTTPS加密/解密
    - 负载均衡: 多台后端服务器的流量分发
    - 请求缓冲: 保护后端免受慢客户端影响
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        self.cfg = cfg

    def generate(self) -> str:
        """生成nginx.conf配置文件"""
        upstream_name = f"{self.cfg.project_name}_upstream"
        ssl_block = self._ssl_block() if self.cfg.ssl else ""
        listen_directive = "443 ssl" if self.cfg.ssl else "80"
        http_to_https = self._http_redirect_block() if self.cfg.ssl else ""

        return textwrap.dedent(f"""\
            # ----------------------------------------------------------
            # Nginx configuration for {self.cfg.project_name}
            # Generated by 60_deployment.py
            # ----------------------------------------------------------

            upstream {upstream_name} {{
                server app:{self.cfg.bind_port};
                keepalive 32;
            }}

            {http_to_https}

            server {{
                listen       {listen_directive};
                listen       [::]:{listen_directive};
                server_name  {self.cfg.domain};
                charset      utf-8;

                # Security headers
                add_header X-Frame-Options "DENY" always;
                add_header X-Content-Type-Options "nosniff" always;
                add_header X-XSS-Protection "1; mode=block" always;
                add_header Referrer-Policy "strict-origin-when-cross-origin" always;
                add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;" always;

                # Max upload size
                client_max_body_size 20M;

                # Logging
                access_log /var/log/nginx/{self.cfg.project_name}_access.log;
                error_log  /var/log/nginx/{self.cfg.project_name}_error.log;

                {ssl_block}

                # Static files served directly by Nginx
                location {self.cfg.static_url} {{
                    alias /srv/staticfiles/;
                    expires 30d;
                    access_log off;
                    add_header Cache-Control "public, immutable";
                }}

                # Media files
                location {self.cfg.media_url} {{
                    alias /srv/media/;
                    expires 7d;
                    add_header Cache-Control "public";
                }}

                # Health check (no logging)
                location /health/ {{
                    proxy_pass http://{upstream_name};
                    access_log off;
                }}

                # All other requests proxied to Gunicorn
                location / {{
                    proxy_pass       http://{upstream_name};
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                    proxy_set_header X-Forwarded-Proto $scheme;
                    proxy_set_header X-Forwarded-Host $server_name;
                    proxy_redirect   off;

                    # Timeout
                    proxy_connect_timeout 30;
                    proxy_send_timeout 30;
                    proxy_read_timeout 30;

                    # Buffering
                    proxy_buffering on;
                    proxy_buffer_size 4k;
                    proxy_buffers 8 4k;

                    # WebSocket support
                    proxy_http_version 1.1;
                    proxy_set_header Upgrade $http_upgrade;
                    proxy_set_header Connection "upgrade";
                }}

                # Deny access to hidden files
                location ~ /\\. {{
                    deny all;
                    access_log off;
                    log_not_found off;
                }}
            }}
        """)

    def _ssl_block(self) -> str:
        return textwrap.dedent("""\
            # SSL / TLS
            ssl_certificate     /etc/nginx/certs/fullchain.pem;
            ssl_certificate_key /etc/nginx/certs/privkey.pem;
            ssl_protocols       TLSv1.2 TLSv1.3;
            ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
            ssl_prefer_server_ciphers on;
            ssl_session_cache   shared:SSL:10m;
            ssl_session_timeout 10m;
            ssl_stapling        on;
            ssl_stapling_verify on;

            # HSTS
            add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        """)

    def _http_redirect_block(self) -> str:
        return textwrap.dedent(f"""\
            # Redirect HTTP -> HTTPS
            server {{
                listen 80;
                listen [::]:80;
                server_name {self.cfg.domain};
                return 301 https://$host$request_uri;
            }}
        """)


# ============================================================================
# 第五部分: Django生产配置生成器
# ============================================================================

class DjangoSettingsGenerator:
    """
    Django生产配置生成器

    关键配置:
    - DEBUG = False
    - SECRET_KEY从环境变量读取
    - ALLOWED_HOSTS限制
    - 安全响应头(HSTS, XSS, CSRF等)
    - 日志配置
    - 缓存配置(Redis)
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        self.cfg = cfg

    def generate(self) -> str:
        allowed = ", ".join(f'"{h}"' for h in self.cfg.allowed_hosts)
        return textwrap.dedent(f"""\
            \"\"\"
            Production settings for {self.cfg.project_name}.
            Generated by 60_deployment.py

            Usage:
                DJANGO_SETTINGS_MODULE={self.cfg.project_name}.settings_production \\
                gunicorn -c gunicorn.conf.py {self.cfg.project_name}.wsgi:application
            \"\"\"
            import os
            from .settings import *  # noqa: F401,F403

            DEBUG = False

            SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "{self.cfg.secret_key}")

            ALLOWED_HOSTS = [{allowed}]

            # --- Database ---
            DATABASES = {{
                "default": {{
                    "ENGINE": "django.db.backends.{'postgresql' if self.cfg.db_engine == 'postgres' else 'mysql'}",
                    "NAME": os.environ.get("DB_NAME", "{self.cfg.db_name}"),
                    "USER": os.environ.get("DB_USER", "{self.cfg.db_user}"),
                    "PASSWORD": os.environ.get("DB_PASSWORD", "{self.cfg.db_password}"),
                    "HOST": os.environ.get("DB_HOST", "{self.cfg.db_service}"),
                    "PORT": os.environ.get("DB_PORT", "{self.cfg.db_port}"),
                    "CONN_MAX_AGE": 600,
                }}
            }}

            # --- Static files ---
            STATIC_ROOT = "/srv/staticfiles"
            STATIC_URL = "{self.cfg.static_url}"
            MEDIA_ROOT = "/srv/media"
            MEDIA_URL = "{self.cfg.media_url}"

            # --- Cache (Redis) ---
            CACHES = {{
                "default": {{
                    "BACKEND": "django.core.cache.backends.redis.RedisCache",
                    "LOCATION": os.environ.get("REDIS_URL", "{self.cfg.redis_url}"),
                }}
            }}

            # --- Security hardening ---
            SECURE_HSTS_SECONDS = 31536000
            SECURE_HSTS_INCLUDE_SUBDOMAINS = True
            SECURE_HSTS_PRELOAD = True
            SECURE_SSL_REDIRECT = True
            SECURE_CONTENT_TYPE_NOSNIFF = True
            SECURE_BROWSER_XSS_FILTER = True
            SESSION_COOKIE_SECURE = True
            CSRF_COOKIE_SECURE = True
            X_FRAME_OPTIONS = "DENY"

            # --- Logging ---
            LOGGING = {{
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {{
                    "verbose": {{
                        "format": "{{levelname}} {{asctime}} {{module}} {{process:d}} {{thread:d}} {{message}}",
                        "style": "{{",
                    }},
                }},
                "handlers": {{
                    "console": {{
                        "class": "logging.StreamHandler",
                        "formatter": "verbose",
                    }},
                }},
                "root": {{
                    "handlers": ["console"],
                    "level": "WARNING",
                }},
            }}
        """)


# ============================================================================
# 第六部分: Dockerfile生成器
# ============================================================================

class DockerfileGenerator:
    """
    Dockerfile生成器 - 多阶段构建

    多阶段构建(Multi-stage Build)优势:
    - 构建阶段包含编译工具(gcc等),运行阶段不需要
    - 最终镜像体积减小50%以上
    - 安全性提升(不包含编译工具和源码)

    C++对比:
    - C++多阶段构建效果更显著(编译器+构建工具可达几百MB)
    - C++最终镜像可能只有几MB(静态链接的二进制)
    - Python镜像通常100-500MB(Python运行时+依赖)
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        self.cfg = cfg

    def generate(self) -> str:
        wsgi_app = (
            f"{self.cfg.project_name}.wsgi:application"
            if self.cfg.framework == "django"
            else f"{self.cfg.project_name}:app"
        )
        collectstatic = (
            "RUN python manage.py collectstatic --noinput"
            if self.cfg.framework == "django"
            else ""
        )
        return textwrap.dedent(f"""\
            # ==============================================================
            # Multi-stage Dockerfile for {self.cfg.project_name}
            # Generated by 60_deployment.py
            # ==============================================================

            # ------------------------- Stage 1: Builder ------------------
            FROM python:{self.cfg.python_version}-slim AS builder

            ENV PYTHONDONTWRITEBYTECODE=1 \\
                PYTHONUNBUFFERED=1 \\
                PIP_NO_CACHE_DIR=1

            WORKDIR /build

            # Install build-time OS dependencies
            RUN apt-get update && \\
                apt-get install -y --no-install-recommends \\
                    build-essential \\
                    libpq-dev \\
                    gcc \\
                && rm -rf /var/lib/apt/lists/*

            # Install Python dependencies into a virtual env
            RUN python -m venv /opt/venv
            ENV PATH="/opt/venv/bin:$PATH"

            COPY requirements.txt .
            RUN pip install --no-cache-dir --upgrade pip && \\
                pip install --no-cache-dir -r requirements.txt && \\
                pip install --no-cache-dir gunicorn whitenoise

            # ------------------------- Stage 2: Runtime ------------------
            FROM python:{self.cfg.python_version}-slim AS runtime

            ENV PYTHONDONTWRITEBYTECODE=1 \\
                PYTHONUNBUFFERED=1 \\
                PATH="/opt/venv/bin:$PATH"

            WORKDIR /app

            # Install only the runtime OS libraries (no compilers)
            RUN apt-get update && \\
                apt-get install -y --no-install-recommends \\
                    libpq5 \\
                    curl \\
                && rm -rf /var/lib/apt/lists/* \\
                && useradd --create-home --shell /bin/bash appuser

            # Copy the virtual env from the builder
            COPY --from=builder /opt/venv /opt/venv

            # Copy application code
            COPY --chown=appuser:appuser . .

            # Collect static files (Django)
            {collectstatic}

            # Create directories for logs / media
            RUN mkdir -p /srv/media /srv/staticfiles /var/log/{self.cfg.project_name} && \\
                chown -R appuser:appuser /app /srv/media /srv/staticfiles

            USER appuser

            EXPOSE {self.cfg.bind_port}

            HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
                CMD curl -f http://localhost:{self.cfg.bind_port}/health/ || exit 1

            CMD ["gunicorn", \\
                 "--config", "gunicorn.conf.py", \\
                 "{wsgi_app}"]
        """)


# ============================================================================
# 第七部分: Docker Compose生成器
# ============================================================================

class DockerComposeGenerator:
    """
    Docker Compose多服务编排生成器

    编排的服务:
    - app: Gunicorn应用服务器
    - nginx: Nginx反向代理
    - db: PostgreSQL/MySQL数据库
    - redis: Redis缓存
    - celery: Celery异步任务Worker(可选)
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        self.cfg = cfg

    def generate(self) -> str:
        db_env = "\n".join(
            f"      {k}: {v}" for k, v in self.cfg.db_env_vars.items()
        )
        db_volume = (
            "postgres_data:/var/lib/postgresql/data"
            if self.cfg.db_engine == "postgres"
            else "mysql_data:/var/lib/mysql"
        )
        db_healthcheck = (
            'test: ["CMD-SHELL", "pg_isready -U $POSTGRES_USER"]'
            if self.cfg.db_engine == "postgres"
            else 'test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]'
        )
        return textwrap.dedent(f"""\
            # ==============================================================
            # docker-compose.yml for {self.cfg.project_name}
            # Generated by 60_deployment.py
            #
            # Usage:
            #   docker compose up -d --build
            #   docker compose logs -f app
            #   docker compose down
            # ==============================================================

            version: "3.9"

            services:
              # ---- Application (Gunicorn) ----
              app:
                build:
                  context: .
                  dockerfile: Dockerfile
                container_name: {self.cfg.project_name}_app
                restart: unless-stopped
                env_file: .env
                environment:
                  DJANGO_SETTINGS_MODULE: {self.cfg.project_name}.settings_production
                  DB_HOST: {self.cfg.db_service}
                  DB_PORT: "{self.cfg.db_port}"
                  DB_NAME: {self.cfg.db_name}
                  DB_USER: {self.cfg.db_user}
                  DB_PASSWORD: {self.cfg.db_password}
                  REDIS_URL: {self.cfg.redis_url}
                volumes:
                  - static_volume:/srv/staticfiles
                  - media_volume:/srv/media
                  - log_volume:/var/log/{self.cfg.project_name}
                expose:
                  - "{self.cfg.bind_port}"
                depends_on:
                  {self.cfg.db_service}:
                    condition: service_healthy
                  redis:
                    condition: service_healthy
                networks:
                  - backend
                deploy:
                  resources:
                    limits:
                      cpus: '2.0'
                      memory: 1G

              # ---- Nginx reverse proxy ----
              nginx:
                image: nginx:1.25-alpine
                container_name: {self.cfg.project_name}_nginx
                restart: unless-stopped
                ports:
                  - "80:80"
                  - "443:443"
                volumes:
                  - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
                  - static_volume:/srv/staticfiles:ro
                  - media_volume:/srv/media:ro
                  - ./certs:/etc/nginx/certs:ro
                depends_on:
                  - app
                networks:
                  - backend

              # ---- Database ----
              {self.cfg.db_service}:
                image: {self.cfg.db_image}
                container_name: {self.cfg.project_name}_{self.cfg.db_service}
                restart: unless-stopped
                environment:
            {db_env}
                volumes:
                  - {db_volume}
                ports:
                  - "{self.cfg.db_port}:{self.cfg.db_port}"
                healthcheck:
                  {db_healthcheck}
                  interval: 10s
                  timeout: 5s
                  retries: 5
                networks:
                  - backend

              # ---- Redis ----
              redis:
                image: redis:7-alpine
                container_name: {self.cfg.project_name}_redis
                restart: unless-stopped
                command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
                volumes:
                  - redis_data:/data
                ports:
                  - "6379:6379"
                healthcheck:
                  test: ["CMD", "redis-cli", "ping"]
                  interval: 10s
                  timeout: 5s
                  retries: 5
                networks:
                  - backend

              # ---- Celery Worker (optional) ----
              celery:
                build:
                  context: .
                  dockerfile: Dockerfile
                container_name: {self.cfg.project_name}_celery
                command: >
                  celery -A {self.cfg.project_name} worker
                  --loglevel=info
                  --concurrency=4
                restart: unless-stopped
                env_file: .env
                environment:
                  DJANGO_SETTINGS_MODULE: {self.cfg.project_name}.settings_production
                  DB_HOST: {self.cfg.db_service}
                  DB_NAME: {self.cfg.db_name}
                  DB_USER: {self.cfg.db_user}
                  DB_PASSWORD: {self.cfg.db_password}
                  REDIS_URL: {self.cfg.redis_url}
                depends_on:
                  {self.cfg.db_service}:
                    condition: service_healthy
                  redis:
                    condition: service_healthy
                networks:
                  - backend

            volumes:
              postgres_data:
              redis_data:
              static_volume:
              media_volume:
              log_volume:

            networks:
              backend:
                driver: bridge
        """)


# ============================================================================
# 第八部分: CI/CD流水线生成器
# ============================================================================

class CICDGenerator:
    """
    CI/CD流水线生成器

    支持生成:
    - GitHub Actions配置
    - GitLab CI配置

    流水线阶段:
    1. Test: 运行测试+代码检查
    2. Build: 构建Docker镜像+推送
    3. Deploy: 部署到生产服务器
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        self.cfg = cfg

    def github_actions(self) -> str:
        """生成GitHub Actions CI/CD配置"""
        db_env_lines = "\n".join(
            f"          {k}: {v}" for k, v in self.cfg.db_env_vars.items()
        )
        db_health = (
            "--health-cmd=pg_isready" if self.cfg.db_engine == "postgres"
            else "--health-cmd=\"mysqladmin ping -h localhost\""
        )
        return textwrap.dedent(f"""\
            # ==============================================================
            # .github/workflows/deploy.yml
            # CI/CD Pipeline for {self.cfg.project_name}
            # Generated by 60_deployment.py
            # ==============================================================

            name: CI/CD Pipeline

            on:
              push:
                branches: [main, master]
              pull_request:
                branches: [main, master]

            env:
              REGISTRY: ghcr.io
              IMAGE_NAME: ${{{{ github.repository }}}}

            jobs:
              # ---------- Test ----------
              test:
                runs-on: ubuntu-latest
                services:
                  {self.cfg.db_service}:
                    image: {self.cfg.db_image}
                    env:
            {db_env_lines}
                    ports:
                      - {self.cfg.db_port}:{self.cfg.db_port}
                    options: >-
                      {db_health}
                      --health-interval=10s
                      --health-timeout=5s
                      --health-retries=5
                steps:
                  - uses: actions/checkout@v4

                  - name: Set up Python {self.cfg.python_version}
                    uses: actions/setup-python@v5
                    with:
                      python-version: "{self.cfg.python_version}"
                      cache: pip

                  - name: Install dependencies
                    run: |
                      python -m pip install --upgrade pip
                      pip install -r requirements.txt
                      pip install flake8 pytest pytest-cov

                  - name: Lint with flake8
                    run: |
                      flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                      flake8 . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics

                  - name: Run tests
                    env:
                      DJANGO_SETTINGS_MODULE: {self.cfg.project_name}.settings_test
                      DB_HOST: localhost
                      DB_PORT: "{self.cfg.db_port}"
                    run: |
                      python manage.py check --deploy
                      pytest --cov=. --cov-report=xml --tb=short -q

              # ---------- Build & Push Image ----------
              build:
                needs: test
                runs-on: ubuntu-latest
                if: github.event_name == 'push'
                permissions:
                  contents: read
                  packages: write
                steps:
                  - uses: actions/checkout@v4

                  - name: Log in to Container Registry
                    uses: docker/login-action@v3
                    with:
                      registry: ${{{{ env.REGISTRY }}}}
                      username: ${{{{ github.actor }}}}
                      password: ${{{{ secrets.GITHUB_TOKEN }}}}

                  - name: Extract metadata
                    id: meta
                    uses: docker/metadata-action@v5
                    with:
                      images: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}
                      tags: |
                        type=sha
                        type=ref,event=branch

                  - name: Build and push Docker image
                    uses: docker/build-push-action@v5
                    with:
                      context: .
                      push: true
                      tags: ${{{{ steps.meta.outputs.tags }}}}
                      labels: ${{{{ steps.meta.outputs.labels }}}}

              # ---------- Deploy ----------
              deploy:
                needs: build
                runs-on: ubuntu-latest
                if: github.ref == 'refs/heads/main'
                environment: production
                steps:
                  - name: Deploy to server via SSH
                    uses: appleboy/ssh-action@v1
                    with:
                      host: ${{{{ secrets.SERVER_HOST }}}}
                      username: ${{{{ secrets.SERVER_USER }}}}
                      key: ${{{{ secrets.SSH_PRIVATE_KEY }}}}
                      script: |
                        cd /opt/{self.cfg.project_name}
                        docker compose pull
                        docker compose up -d --remove-orphans
                        docker compose exec -T app python manage.py migrate --noinput
                        docker compose exec -T app python manage.py collectstatic --noinput
                        docker system prune -af
                        echo "Deployment complete at $(date)"
        """)

    def gitlab_ci(self) -> str:
        """生成GitLab CI配置"""
        db_env_lines = "\n".join(
            f"    {k}: {v}" for k, v in self.cfg.db_env_vars.items()
        )
        return textwrap.dedent(f"""\
            # ==============================================================
            # .gitlab-ci.yml
            # CI/CD Pipeline for {self.cfg.project_name}
            # ==============================================================

            stages:
              - test
              - build
              - deploy

            variables:
              IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

            test:
              stage: test
              image: python:{self.cfg.python_version}-slim
              services:
                - name: {self.cfg.db_image}
                  alias: {self.cfg.db_service}
              variables:
            {db_env_lines}
                DB_HOST: {self.cfg.db_service}
                DB_PORT: "{self.cfg.db_port}"
              script:
                - pip install --upgrade pip
                - pip install -r requirements.txt
                - pip install flake8 pytest
                - flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                - pytest --tb=short -q
              only:
                - main
                - merge_requests

            build:
              stage: build
              image: docker:24-dind
              services:
                - docker:24-dind
              before_script:
                - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
              script:
                - docker build -t $IMAGE_TAG .
                - docker tag $IMAGE_TAG $CI_REGISTRY_IMAGE:latest
                - docker push $IMAGE_TAG
                - docker push $CI_REGISTRY_IMAGE:latest
              only:
                - main

            deploy:
              stage: deploy
              image: alpine:latest
              before_script:
                - apk add --no-cache openssh-client
                - eval $(ssh-agent -s)
                - echo "$SSH_PRIVATE_KEY" | tr -d '\\r' | ssh-add -
              script:
                - ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "
                    cd /opt/{self.cfg.project_name} &&
                    docker compose pull &&
                    docker compose up -d --remove-orphans &&
                    echo 'Deployed successfully'"
              only:
                - main
              when: manual
        """)


# ============================================================================
# 第九部分: 辅助文件生成器
# ============================================================================

def generate_requirements(cfg: ProjectConfig) -> str:
    """生成requirements.txt"""
    lines = [
        "# Core framework",
        f"{'Django>=4.2,<5' if cfg.framework == 'django' else 'Flask>=3.0'}",
        "",
        "# WSGI server",
        "gunicorn>=21.2",
        "",
        "# Database driver",
        "psycopg2-binary>=2.9" if cfg.db_engine == "postgres" else "mysqlclient>=2.2",
        "",
        "# Cache / Message broker",
        "redis>=5.0",
        "",
        "# Task queue (optional)",
        "celery[redis]>=5.3",
        "",
        "# Static files (Django)",
        "whitenoise>=6.5",
        "",
        "# Security",
        "django-cors-headers>=4.3",
        "",
        "# Utilities",
        "python-dotenv>=1.0",
        "",
        "# Testing & Linting (dev)",
        "# pytest>=8.0",
        "# pytest-django>=4.8",
        "# pytest-cov>=4.0",
        "# flake8>=7.0",
    ]
    return "\n".join(lines) + "\n"


def generate_env_template(cfg: ProjectConfig) -> str:
    """生成.env模板文件"""
    return textwrap.dedent(f"""\
        # --------------------------------------------------
        # Environment variables for {cfg.project_name}
        # Copy to .env and fill in real values
        # NEVER commit .env to version control!
        # --------------------------------------------------

        DJANGO_SECRET_KEY={cfg.secret_key}
        DJANGO_SETTINGS_MODULE={cfg.project_name}.settings_production

        DB_NAME={cfg.db_name}
        DB_USER={cfg.db_user}
        DB_PASSWORD={cfg.db_password}
        DB_HOST={cfg.db_service}
        DB_PORT={cfg.db_port}

        REDIS_URL={cfg.redis_url}

        # Celery
        CELERY_BROKER_URL={cfg.redis_url}
        CELERY_RESULT_BACKEND={cfg.redis_url}

        # Server (for CI/CD deploy)
        SERVER_HOST=your-server-ip
        SERVER_USER=root
    """)


def generate_systemd_service(cfg: ProjectConfig) -> str:
    """生成systemd服务文件"""
    return textwrap.dedent(f"""\
        [Unit]
        Description={cfg.project_name} Django Application
        After=network.target postgresql.service redis.service
        Wants=postgresql.service redis.service

        [Service]
        Type=notify
        User=django
        Group=django
        RuntimeDirectory=gunicorn
        WorkingDirectory=/opt/{cfg.project_name}
        Environment="PATH=/opt/{cfg.project_name}/venv/bin"
        EnvironmentFile=/opt/{cfg.project_name}/.env

        ExecStart=/opt/{cfg.project_name}/venv/bin/gunicorn \\
            --config /opt/{cfg.project_name}/gunicorn.conf.py \\
            {cfg.project_name}.wsgi:application

        ExecReload=/bin/kill -s HUP $MAINPID
        ExecStop=/bin/kill -s TERM $MAINPID

        Restart=on-failure
        RestartSec=5s
        TimeoutStartSec=30
        TimeoutStopSec=30

        # Resource limits
        LimitNOFILE=65535

        # Security hardening
        PrivateTmp=true
        ProtectSystem=strict
        ProtectHome=true
        NoNewPrivileges=true

        # Logging
        StandardOutput=journal
        StandardError=journal
        SyslogIdentifier={cfg.project_name}

        [Install]
        WantedBy=multi-user.target
    """)


# ============================================================================
# 第十部分: 文件写入器
# ============================================================================

class DeploymentWriter:
    """
    部署文件写入器 - 编排所有生成器并写入磁盘

    企业级实践: 配置即代码(Infrastructure as Code)
    所有部署配置通过代码生成,版本控制,可审计
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        self.cfg = cfg
        self.output_dir = Path(cfg.output_dir)

    def write_all(self) -> List[Path]:
        """生成所有部署文件并写入磁盘"""
        written: List[Path] = []

        generators: List[Tuple[str, str]] = [
            ("Dockerfile",                          DockerfileGenerator(self.cfg).generate()),
            ("docker-compose.yml",                  DockerComposeGenerator(self.cfg).generate()),
            ("nginx.conf",                          NginxConfigGenerator(self.cfg).generate()),
            ("gunicorn.conf.py",                    GunicornConfigGenerator(self.cfg).generate()),
            ("settings_production.py",              DjangoSettingsGenerator(self.cfg).generate()),
            (".github/workflows/deploy.yml",        CICDGenerator(self.cfg).github_actions()),
            (".gitlab-ci.yml",                      CICDGenerator(self.cfg).gitlab_ci()),
            ("requirements.txt",                    generate_requirements(self.cfg)),
            (".env.example",                        generate_env_template(self.cfg)),
            ("myproject.service",                   generate_systemd_service(self.cfg)),
        ]

        for relative_path, content in generators:
            full_path = self.output_dir / relative_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            written.append(full_path)

        return written


# ============================================================================
# 第十一部分: CLI入口
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Enterprise deployment toolkit - generate production config files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python 60_deployment.py generate-all --project mysite --domain example.com
              python 60_deployment.py generate-all --project mysite --framework flask --no-ssl
              python 60_deployment.py generate-all --output ./prod_deploy --db-engine mysql
        """),
    )
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate-all", help="Generate all deployment artefacts")
    gen.add_argument("--project", default="mysite", help="Project/package name (default: mysite)")
    gen.add_argument("--domain", default="example.com", help="Domain name (default: example.com)")
    gen.add_argument("--framework", choices=["django", "flask"], default="django", help="Web framework")
    gen.add_argument("--python-version", default="3.11", help="Python version for Docker image")
    gen.add_argument("--workers", type=int, default=4, help="Gunicorn worker count")
    gen.add_argument("--threads", type=int, default=2, help="Threads per Gunicorn worker")
    gen.add_argument("--db-engine", choices=["postgres", "mysql"], default="postgres", help="Database engine")
    gen.add_argument("--db-name", default="app_db", help="Database name")
    gen.add_argument("--db-user", default="app_user", help="Database user")
    gen.add_argument("--db-password", default="changeme", help="Database password")
    gen.add_argument("--no-ssl", action="store_true", help="Disable SSL in Nginx config")
    gen.add_argument("--output", default="./deploy_output", help="Output directory")

    sub.add_parser("checklist", help="Print deployment checklist")

    return parser


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    """CLI入口函数"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        # 无子命令时展示演示
        demo_mode()
        return

    if args.command == "checklist":
        print_checklist()
        return

    if args.command == "generate-all":
        cfg = ProjectConfig(
            project_name=args.project,
            domain=args.domain,
            framework=args.framework,
            python_version=args.python_version,
            workers=args.workers,
            threads=args.threads,
            db_engine=args.db_engine,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            ssl=not args.no_ssl,
            output_dir=args.output,
        )

        writer = DeploymentWriter(cfg)
        paths = writer.write_all()

        print(f"\n{'='*60}")
        print(f"  Deployment files generated for: {cfg.project_name}")
        print(f"  Framework: {cfg.framework}  |  DB: {cfg.db_engine}  |  SSL: {cfg.ssl}")
        print(f"  Output directory: {cfg.output_dir}")
        print(f"{'='*60}\n")
        for p in paths:
            print(f"  [OK] {p}")
        print(f"\nTotal: {len(paths)} files written.\n")
        print("Next steps:")
        print(f"  1. cd {cfg.output_dir}")
        print("  2. Edit .env.example -> .env with real credentials")
        print("  3. Place SSL certs in ./certs/ (if SSL enabled)")
        print("  4. Place requirements.txt in your project root")
        print("  5. docker compose up -d --build")


def print_checklist() -> None:
    """打印部署清单"""
    print('\n' + '=' * 70)
    print('  Django项目部署清单 (Deployment Checklist)')
    print('=' * 70)
    for section, items in DEPLOYMENT_CHECKLIST.items():
        print(f'\n  {section}:')
        for item in items:
            print(f'    [ ] {item}')


def demo_mode() -> None:
    """演示模式: 展示所有配置和最佳实践"""
    print('=' * 70)
    print('  Django项目上线 - 企业级部署实战指南')
    print('  (Project Deployment - Enterprise Deployment Guide)')
    print('=' * 70)

    # 1. 部署清单
    print_checklist()

    # 2. 展示配置文件
    cfg = ProjectConfig()
    print('\n[2] 配置文件预览:')
    generators = [
        ('Gunicorn配置', GunicornConfigGenerator(cfg)),
        ('Nginx配置', NginxConfigGenerator(cfg)),
        ('Django生产配置', DjangoSettingsGenerator(cfg)),
        ('Dockerfile', DockerfileGenerator(cfg)),
        ('Docker Compose', DockerComposeGenerator(cfg)),
        ('GitHub Actions CI/CD', CICDGenerator(cfg)),
    ]
    for name, gen in generators:
        content = gen.generate()
        print(f'\n  {name}: {len(content.splitlines())} 行')

    # 3. Docker命令速查
    print('\n[3] Docker命令速查:')
    docker_commands = [
        ('构建镜像', 'docker build -t myproject:latest .'),
        ('运行容器', 'docker run -d -p 8000:8000 myproject:latest'),
        ('编排服务', 'docker compose up -d --build'),
        ('查看服务', 'docker compose ps'),
        ('查看日志', 'docker compose logs -f app'),
        ('进入容器', 'docker compose exec app /bin/bash'),
        ('数据库迁移', 'docker compose exec app python manage.py migrate'),
        ('收集静态', 'docker compose exec app python manage.py collectstatic'),
        ('停止服务', 'docker compose down'),
        ('清理资源', 'docker system prune -a'),
    ]
    for desc, cmd in docker_commands:
        print(f'  {desc:15s}: {cmd}')

    # 4. systemd命令
    print('\n[4] systemd服务管理:')
    commands = [
        ('重载配置', 'sudo systemctl daemon-reload'),
        ('开机自启', 'sudo systemctl enable myproject'),
        ('启动服务', 'sudo systemctl start myproject'),
        ('停止服务', 'sudo systemctl stop myproject'),
        ('优雅重载', 'sudo systemctl reload myproject'),
        ('查看状态', 'sudo systemctl status myproject'),
        ('查看日志', 'sudo journalctl -u myproject -f'),
    ]
    for desc, cmd in commands:
        print(f'  {desc:15s}: {cmd}')

    # 5. 部署流程图
    print('\n[5] 典型部署流程:')
    flow = """
    代码提交(Git Push)
         |
         v
    CI/CD Pipeline(GitHub Actions)
         |
         +-- 运行测试(pytest)
         +-- 代码检查(flake8/black)
         +-- 构建Docker镜像
         +-- 推送到镜像仓库(GHCR/Docker Hub)
              |
              v
    生产服务器(SSH Deploy)
         |
         +-- docker compose pull
         +-- docker compose up -d
         +-- python manage.py migrate
         +-- python manage.py collectstatic
         +-- 服务健康检查(/health/)

    +--------------------------------------------+
    |           生产环境架构                       |
    |                                             |
    |  Internet                                  |
    |     |                                      |
    |     v                                      |
    |  Nginx (SSL + 反向代理 + 静态文件服务)      |
    |     |                                      |
    |     +-- /static/ -> Nginx直接服务           |
    |     +-- /media/  -> Nginx直接服务           |
    |     +-- /        -> Gunicorn               |
    |           |                                |
    |           +-- Django Worker 1 (gthread)    |
    |           +-- Django Worker 2              |
    |           +-- Django Worker N              |
    |                 |                          |
    |           +-----+-----+                   |
    |           v           v                   |
    |       PostgreSQL    Redis                  |
    +--------------------------------------------+
    """
    print(flow)

    # 6. C++对比
    print('[6] Python部署 vs C++构建部署:')
    comparison = """
    +---------------------+------------------------------------------+
    |   Python/Django     |   C++项目部署                            |
    +---------------------+------------------------------------------+
    | pip install         | cmake + make + install                   |
    | requirements.txt    | CMakeLists.txt + conanfile.txt           |
    | 源码直接部署        | 编译产物部署(二进制可执行文件)            |
    | Gunicorn/uWSGI      | systemd直接管理进程                      |
    | Docker ~200-800MB   | Docker ~10-100MB(多阶段构建+静态链接)    |
    | 秒级部署(无编译)    | 分钟级部署(需要编译)                      |
    | 热重载(reload)      | 需要重启进程                             |
    | 虚拟环境(venv)      | 系统依赖(ldd检查libc兼容)                |
    | 动态加载            | 静态链接(性能优先)                       |
    +---------------------+------------------------------------------+
    """
    print(comparison)

    # 7. CLI使用说明
    print('[7] CLI使用说明:')
    print('  python 60_deployment.py generate-all --project mysite --domain example.com')
    print('  python 60_deployment.py generate-all --project mysite --framework flask --no-ssl')
    print('  python 60_deployment.py generate-all --output ./prod_deploy --db-engine mysql')
    print('  python 60_deployment.py checklist')

    print('\n' + '=' * 70)
    print('  所有部署配置展示完毕!')
    print('=' * 70)


if __name__ == '__main__':
    main()
