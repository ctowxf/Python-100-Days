"""
Django settings for hellodjango project.
Django 项目配置文件

在 C++ 中，配置通常通过配置文件或预处理指令实现
Django 使用 Python 模块作为配置，更加灵活

C++ 对比:
    // C++ 中可能使用 JSON/YAML 配置文件
    // 或者使用预处理指令
    #define DEBUG true
    #define DATABASE_URL "sqlite:///db.sqlite3"

    // Django 使用 Python 字典结构，类型安全且易于扩展
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# 项目根目录路径，类似 C++ 中的项目根目录宏
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# 安全密钥，生产环境必须从环境变量读取
# 类似 C++ 中的密钥管理，但 Python/Django 提供了更好的安全性
SECRET_KEY: str = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-change-this-in-production-!@#$%^&*()'
)

# SECURITY WARNING: don't run with debug turned on in production!
# 调试模式，生产环境必须关闭
# 类似 C++ 中的 #ifdef DEBUG 条件编译
DEBUG: bool = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

# 允许访问的主机列表
# 类似 C++ 中的网络访问控制
ALLOWED_HOSTS: List[str] = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1'
).split(',')

# Application definition
# 应用定义，类似 C++ 中的模块/组件注册
INSTALLED_APPS: List[str] = [
    # Django 内置应用
    'django.contrib.admin',           # 管理后台
    'django.contrib.auth',            # 认证系统
    'django.contrib.contenttypes',    # 内容类型框架
    'django.contrib.sessions',        # 会话框架
    'django.contrib.messages',        # 消息框架
    'django.contrib.staticfiles',     # 静态文件服务

    # 第三方应用
    # 类似 C++ 中的第三方库引入
    'rest_framework',                 # Django REST framework
    'corsheaders',                    # CORS 跨域支持
    'django_filters',                 # 过滤器支持

    # 本地应用
    # 类似 C++ 中的自定义模块
    'polls.apps.PollsConfig',         # 投票应用
]

# 中间件配置
# 类似 C++ 中的中间件模式或装饰器模式
MIDDLEWARE: List[str] = [
    'django.middleware.security.SecurityMiddleware',      # 安全中间件
    'django.contrib.sessions.middleware.SessionMiddleware',  # 会话中间件
    'corsheaders.middleware.CorsMiddleware',             # CORS 中间件
    'django.middleware.common.CommonMiddleware',         # 通用中间件
    'django.middleware.csrf.CsrfViewMiddleware',        # CSRF 保护
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # 认证中间件
    'django.contrib.messages.middleware.MessageMiddleware',  # 消息中间件
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # 点击劫持保护
]

# URL 配置根模块
ROOT_URLCONF: str = 'hellodjango.urls'

# 模板配置
# 类似 C++ 中的模板引擎配置
TEMPLATES: List[Dict[str, Any]] = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # 项目级模板目录
        ],
        'APP_DIRS': True,  # 应用级模板目录
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI 应用入口
WSGI_APPLICATION: str = 'hellodjango.wsgi.application'

# Database
# 数据库配置，类似 C++ 中的数据库连接配置
# Django 默认使用 SQLite，生产环境建议使用 PostgreSQL
DATABASES: Dict[str, Dict[str, Any]] = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # SQLite 数据库引擎
        'NAME': BASE_DIR / 'db.sqlite3',         # 数据库文件路径
        # PostgreSQL 配置示例（生产环境推荐）:
        # 'ENGINE': 'django.db.backends.postgresql',
        # 'NAME': os.environ.get('DB_NAME', 'hellodjango'),
        # 'USER': os.environ.get('DB_USER', 'postgres'),
        # 'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        # 'HOST': os.environ.get('DB_HOST', 'localhost'),
        # 'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Cache configuration
# 缓存配置，类似 C++ 中的缓存系统
# 使用 Redis 作为缓存后端，性能优异
CACHES: Dict[str, Dict[str, Any]] = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'hellodjango',  # 缓存键前缀
        'TIMEOUT': 300,  # 默认缓存超时时间（秒）
    }
}

# Password validation
# 密码验证规则，类似 C++ 中的输入验证
AUTH_PASSWORD_VALIDATORS: List[Dict[str, str]] = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # 最小密码长度
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# 国际化配置，类似 C++ 中的国际化支持
LANGUAGE_CODE: str = 'zh-hans'  # 中文简体

TIME_ZONE: str = 'Asia/Shanghai'  # 时区设置

USE_I18N: bool = True  # 启用国际化

USE_TZ: bool = True  # 启用时区支持

# Static files (CSS, JavaScript, Images)
# 静态文件配置，类似 C++ 中的资源文件管理
STATIC_URL: str = '/static/'  # 静态文件URL前缀

STATIC_ROOT: Path = BASE_DIR / 'staticfiles'  # 静态文件收集目录

STATICFILES_DIRS: List[Path] = [
    BASE_DIR / 'static',  # 静态文件源目录
]

# Media files (User uploaded files)
# 媒体文件配置，类似 C++ 中的用户上传文件管理
MEDIA_URL: str = '/media/'  # 媒体文件URL前缀

MEDIA_ROOT: Path = BASE_DIR / 'media'  # 媒体文件存储目录

# Default primary key field type
# 默认主键字段类型，类似 C++ 中的数据类型定义
DEFAULT_AUTO_FIELD: str = 'django.db.models.BigAutoField'

# Django REST Framework configuration
# DRF 配置，类似 C++ 中的 REST API 框架配置
REST_FRAMEWORK: Dict[str, Any] = {
    # 分页配置
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # 每页显示数量

    # 认证配置
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],

    # 权限配置
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],

    # 过滤配置
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # 限流配置
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttle.AnonRateThrottle',
        'rest_framework.throttle.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # 匿名用户限流
        'user': '1000/hour',  # 认证用户限流
    },

    # 序列化器配置
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
}

# Celery configuration
# Celery 异步任务队列配置，类似 C++ 中的线程池或任务队列
CELERY_BROKER_URL: str = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND: str = os.environ.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT: List[str] = ['json']  # 接受的内容类型
CELERY_TASK_SERIALIZER: str = 'json'  # 任务序列化格式
CELERY_RESULT_SERIALIZER: str = 'json'  # 结果序列化格式
CELERY_TIMEZONE: str = 'Asia/Shanghai'  # Celery 时区
CELERY_TASK_TRACK_STARTED: bool = True  # 跟踪任务开始状态
CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 任务时间限制（秒）
CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1  # 工作进程预取倍数

# CORS 配置
# 跨域资源共享配置，类似 C++ 中的网络跨域处理
CORS_ALLOWED_ORIGINS: List[str] = [
    'http://localhost:3000',  # 前端开发服务器
    'http://127.0.0.1:3000',
]

CORS_ALLOW_CREDENTIALS: bool = True  # 允许携带凭证

# 日志配置
# 类似 C++ 中的日志系统配置
LOGGING: Dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'propagate': True,
        },
        'polls': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
