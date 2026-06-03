"""
52_middleware.py - Django中间件的应用 (Middleware in Django)
===========================================================

本模块演示Django中间件的全面应用,包括:
- 中间件的工作原理(请求/响应生命周期)
- 函数式中间件(装饰器风格)
- 类式中间件(MiddlewareMixin)
- 请求预处理与响应后处理钩子
- 异常处理中间件

C++对比: Django中间件 vs C++拦截器模式(Interceptor Pattern)
----------------------------------------------------------------
Django中间件与C++中的拦截器/过滤器链模式高度相似:

1. C++拦截器模式:
   class IInterceptor {
   public:
       virtual ~IInterceptor() = default;
       virtual bool preHandle(Request& req, Response& res) = 0;
       virtual void postHandle(Request& req, Response& res) = 0;
       virtual void afterCompletion(Request& req, Response& res) = 0;
   };
   class InterceptorChain {
       std::vector<std::unique_ptr<IInterceptor>> interceptors;
       void doFilter(Request& req, Response& res) {
           for (auto& interceptor : interceptors) {
               if (!interceptor->preHandle(req, res)) return;
           }
           // dispatch to handler...
           for (auto it = interceptors.rbegin(); it != interceptors.rend(); ++it) {
               (*it)->postHandle(req, res);
           }
       }
   };

2. Django中间件:
   class MyMiddleware:
       def __init__(self, get_response): ...
       def __call__(self, request): ...
       def process_view(self, request, view_func, view_args, view_kwargs): ...
       def process_exception(self, request, exception): ...
       def process_template_response(self, request, response): ...

   关键差异:
   - Django中间件使用Python的"可调用对象"模式(__call__),更简洁
   - C++拦截器需要显式接口定义,类型安全但代码量更大
   - Django中间件按MIDDLEWARE列表顺序执行(请求从上到下,响应从下到上)
   - C++拦截器链通常通过责任链模式实现,支持动态添加/移除

3. Java Servlet Filter / Spring Interceptor:
   - 与Django中间件概念几乎相同
   - C++没有标准的中间件/过滤器框架,需要自行实现

企业级应用场景:
- 速率限制(Rate Limiting): 防止API滥用
- 请求日志记录(Request Logging): 审计追踪
- IP黑名单(IP Blocking): 安全防护
- CORS跨域资源共享: 前后端分离必备
- 请求签名验证(API Signature): 接口安全
- 性能监控(Performance Monitoring): APM
- 维护模式(Maintenance Mode): 运维开关

依赖安装:
    pip install django
"""

from __future__ import annotations

import os
import sys
import time
import json
import hashlib
import logging
import ipaddress
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from functools import wraps
from collections import defaultdict
from threading import Lock

# ============================================================================
# Django环境配置
# ============================================================================

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
        SECRET_KEY='demo-secret-key-for-middleware-testing',
        ALLOWED_HOSTS=['*'],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],
    )
    django.setup()

from django.http import (
    HttpRequest, HttpResponse, JsonResponse,
    HttpResponseForbidden, HttpResponseNotAllowed,
    HttpResponseRedirect, HttpResponseServerError,
)
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve


# ============================================================================
# 日志配置
# ============================================================================

logger = logging.getLogger('middleware')
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    ))
    logger.addHandler(handler)


# ============================================================================
# 第一部分: 速率限制中间件 (Rate Limiter)
# ============================================================================

class RateLimiterMiddleware:
    """
    API速率限制中间件 - 基于滑动窗口算法

    功能:
    - 按IP地址限制请求频率
    - 支持不同路径的不同限制策略
    - 超限时返回429 Too Many Requests
    - 响应头包含速率限制信息(X-RateLimit-*)

    C++对比:
    - C++中实现速率限制通常使用令牌桶(Token Bucket)或漏桶(Leaky Bucket)算法
    - 需要线程安全的map存储(IP -> 请求记录),使用std::mutex或std::shared_mutex
    - Django的单线程请求模型简化了并发问题,但仍需考虑多进程场景

    企业级改进方向:
    - 使用Redis存储速率限制数据(支持分布式部署)
    - 支持基于API Key/用户ID的限制(而非仅IP)
    - 实现滑动窗口日志算法(更精确)
    """

    # 默认限制: 每分钟60次请求
    DEFAULT_RATE_LIMIT = 60
    DEFAULT_RATE_WINDOW = 60  # 秒

    # 路径特定限制配置
    PATH_LIMITS: Dict[str, Tuple[int, int]] = {
        '/api/login/': (5, 60),      # 登录接口: 每分钟5次
        '/api/register/': (3, 60),    # 注册接口: 每分钟3次
        '/api/upload/': (10, 60),     # 上传接口: 每分钟10次
    }

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        # 内存存储: {ip_address: [(timestamp, path), ...]}
        self._request_log: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        self._lock = Lock()
        logger.info('RateLimiterMiddleware 已初始化')

    def __call__(self, request: HttpRequest) -> HttpResponse:
        client_ip = self._get_client_ip(request)
        path = request.path
        now = time.time()

        # 获取当前路径的限制配置
        rate_limit, rate_window = self.PATH_LIMITS.get(
            path, (self.DEFAULT_RATE_LIMIT, self.DEFAULT_RATE_WINDOW)
        )

        # 清理过期记录并检查速率
        with self._lock:
            self._cleanup_old_records(client_ip, now, rate_window)
            request_count = len(self._request_log[client_ip])

            if request_count >= rate_limit:
                logger.warning(f'速率限制触发: IP={client_ip}, path={path}, count={request_count}')
                response = JsonResponse(
                    {
                        'error': 'Too Many Requests',
                        'message': f'请求过于频繁,请在{rate_window}秒后重试',
                        'retry_after': rate_window,
                    },
                    status=429,
                )
                response['Retry-After'] = str(rate_window)
                response['X-RateLimit-Limit'] = str(rate_limit)
                response['X-RateLimit-Remaining'] = '0'
                response['X-RateLimit-Reset'] = str(int(now + rate_window))
                return response

            # 记录本次请求
            self._request_log[client_ip].append((now, path))

        # 正常处理请求
        response = self.get_response(request)

        # 添加速率限制响应头
        remaining = rate_limit - request_count - 1
        response['X-RateLimit-Limit'] = str(rate_limit)
        response['X-RateLimit-Remaining'] = str(max(0, remaining))
        response['X-RateLimit-Reset'] = str(int(now + rate_window))

        return response

    def _get_client_ip(self, request: HttpRequest) -> str:
        """获取客户端真实IP(考虑反向代理)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    def _cleanup_old_records(self, ip: str, now: float, window: int) -> None:
        """清理过期的请求记录"""
        cutoff = now - window
        self._request_log[ip] = [
            (ts, path) for ts, path in self._request_log[ip]
            if ts > cutoff
        ]
        if not self._request_log[ip]:
            del self._request_log[ip]


# ============================================================================
# 第二部分: 请求日志中间件 (Request Logger)
# ============================================================================

class RequestLoggerMiddleware:
    """
    请求日志记录中间件

    功能:
    - 记录每个请求的方法、路径、状态码、耗时
    - 记录请求体(可配置)
    - 记录响应体大小
    - 支持日志脱敏(过滤敏感字段)

    C++对比:
    - C++中通常使用AOP(面向切面编程)或装饰器模式实现请求日志
    - 常见方案: Boost.Log, spdlog, glog
    - Python的logging模块配合中间件模式比C++更简洁
    """

    # 敏感字段(请求体中需要脱敏的字段)
    SENSITIVE_FIELDS: Set[str] = {'password', 'token', 'secret', 'authorization', 'credit_card'}

    # 不记录日志的路径(健康检查等)
    SKIP_PATHS: Set[str] = {'/health/', '/ping/', '/favicon.ico'}

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        logger.info('RequestLoggerMiddleware 已初始化')

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 跳过不需要记录的路径
        if request.path in self.SKIP_PATHS:
            return self.get_response(request)

        # 记录请求开始
        start_time = time.time()
        request_data = self._extract_request_data(request)

        logger.info(
            f'>>> {request.method} {request.path} | '
            f'IP={self._get_client_ip(request)} | '
            f'UserAgent={request.META.get("HTTP_USER_AGENT", "N/A")[:80]}'
        )

        if request_data:
            logger.debug(f'    请求参数: {json.dumps(request_data, ensure_ascii=False)[:500]}')

        # 处理请求
        try:
            response = self.get_response(request)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f'<<< {request.method} {request.path} | '
                f'EXCEPTION: {type(e).__name__}: {e} | '
                f'耗时: {elapsed:.3f}s'
            )
            raise

        # 记录响应
        elapsed = time.time() - start_time
        status_code = response.status_code

        log_level = logger.warning if status_code >= 400 else logger.info
        log_level(
            f'<<< {request.method} {request.path} | '
            f'Status={status_code} | '
            f'Size={len(response.content)}bytes | '
            f'耗时: {elapsed:.3f}s'
        )

        # 添加性能响应头
        response['X-Request-Duration'] = f'{elapsed:.3f}s'

        return response

    def _extract_request_data(self, request: HttpRequest) -> Dict[str, Any]:
        """提取请求参数(脱敏处理)"""
        data: Dict[str, Any] = {}

        # GET参数
        if request.GET:
            data['query'] = dict(request.GET)

        # POST参数(JSON或表单)
        if request.method in ('POST', 'PUT', 'PATCH'):
            try:
                if request.content_type == 'application/json':
                    body = json.loads(request.body)
                    data['body'] = self._sanitize_data(body)
                elif request.POST:
                    data['body'] = self._sanitize_data(dict(request.POST))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data['body'] = '<binary data>'

        return data

    def _sanitize_data(self, data: Any) -> Any:
        """数据脱敏: 将敏感字段值替换为***"""
        if isinstance(data, dict):
            return {
                key: '***' if key.lower() in self.SENSITIVE_FIELDS else self._sanitize_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        return data

    def _get_client_ip(self, request: HttpRequest) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """异常处理钩子: 记录未捕获的异常"""
        logger.exception(
            f'请求处理异常: {request.method} {request.path} | '
            f'{type(exception).__name__}: {exception}'
        )
        return None  # 返回None表示继续传播异常


# ============================================================================
# 第三部分: IP黑名单中间件 (IP Blocker)
# ============================================================================

class IPBlockerMiddleware:
    """
    IP黑名单中间件

    功能:
    - 支持IP地址和CIDR网段黑名单
    - 支持IP白名单(白名单中的IP不受黑名单限制)
    - 支持动态更新黑名单(通过管理接口)
    - 被拦截的IP返回403 Forbidden

    C++对比:
    - C++中IP过滤通常在网络层(如iptables/nftables)或应用层实现
    - 使用ipaddress库进行CIDR匹配,类似C++的inet_ntop/inet_pton
    - Python的ipaddress模块比C++的socket API更易用
    """

    # IP黑名单(支持单个IP和CIDR网段)
    BLOCKED_IPS: Set[str] = {
        '192.168.1.100',
        '10.0.0.0/8',
        '172.16.0.0/12',
    }

    # IP白名单(不受黑名单限制)
    WHITELISTED_IPS: Set[str] = {
        '127.0.0.1',
        '::1',
    }

    # 封禁路径(只拦截特定路径,空集合表示拦截所有路径)
    BLOCKED_PATHS: Set[str] = set()  # 空=拦截所有

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        # 预编译CIDR网络对象
        self._blocked_networks: List[ipaddress.IPv4Network] = []
        for ip_str in self.BLOCKED_IPS:
            try:
                self._blocked_networks.append(ipaddress.ip_network(ip_str, strict=False))
            except ValueError:
                logger.warning(f'无效的IP/网段: {ip_str}')

        self._whitelisted_ips: Set[ipaddress.IPv4Address] = set()
        for ip_str in self.WHITELISTED_IPS:
            try:
                self._whitelisted_ips.add(ipaddress.ip_address(ip_str))
            except ValueError:
                pass

        logger.info(
            f'IPBlockerMiddleware 已初始化 | '
            f'黑名单: {len(self._blocked_networks)}条 | '
            f'白名单: {len(self._whitelisted_ips)}条'
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        client_ip_str = self._get_client_ip(request)

        try:
            client_ip = ipaddress.ip_address(client_ip_str)
        except ValueError:
            logger.warning(f'无效的客户端IP: {client_ip_str}')
            return self.get_response(request)

        # 白名单检查
        if client_ip in self._whitelisted_ips:
            return self.get_response(request)

        # 路径过滤
        if self.BLOCKED_PATHS and request.path not in self.BLOCKED_PATHS:
            return self.get_response(request)

        # 黑名单检查
        for network in self._blocked_networks:
            if client_ip in network:
                logger.warning(f'IP被拦截: {client_ip_str} | 路径: {request.path}')
                return JsonResponse(
                    {
                        'error': 'Forbidden',
                        'message': '您的IP地址已被限制访问',
                    },
                    status=403,
                )

        return self.get_response(request)

    def _get_client_ip(self, request: HttpRequest) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    @classmethod
    def add_to_blacklist(cls, ip_or_cidr: str) -> None:
        """动态添加IP到黑名单"""
        cls.BLOCKED_IPS.add(ip_or_cidr)
        logger.info(f'IP已加入黑名单: {ip_or_cidr}')

    @classmethod
    def remove_from_blacklist(cls, ip_or_cidr: str) -> None:
        """从黑名单移除IP"""
        cls.BLOCKED_IPS.discard(ip_or_cidr)
        logger.info(f'IP已从黑名单移除: {ip_or_cidr}')


# ============================================================================
# 第四部分: CORS跨域中间件
# ============================================================================

class CORSMiddleware:
    """
    CORS(跨域资源共享)中间件

    功能:
    - 处理OPTIONS预检请求(Preflight)
    - 设置Access-Control-Allow-*响应头
    - 支持配置允许的源、方法、头
    - 支持凭据(Credentials)传递

    C++对比:
    - CORS是HTTP协议层面的概念,与编程语言无关
    - C++ Web框架(Crow, Drogon, oat++)通常内置CORS支持
    - Django的django-cors-headers库是生产环境首选
    - 此处演示从零实现,理解CORS工作原理

    CORS工作流程:
    1. 浏览器发送OPTIONS预检请求(非简单请求)
    2. 服务端返回允许的源、方法、头
    3. 浏览器检查预检响应,决定是否发送实际请求
    4. 实际请求时,服务端再次返回CORS头
    """

    # 允许的源(生产环境应限制为具体域名)
    ALLOWED_ORIGINS: Set[str] = {
        'http://localhost:3000',
        'http://localhost:8080',
        'http://127.0.0.1:3000',
        'https://example.com',
    }

    # 允许的HTTP方法
    ALLOWED_METHODS: Set[str] = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'}

    # 允许的请求头
    ALLOWED_HEADERS: Set[str] = {
        'Content-Type', 'Authorization', 'X-Requested-With',
        'Accept', 'Origin', 'X-CSRFToken',
    }

    # 允许暴露的响应头
    EXPOSE_HEADERS: Set[str] = {
        'X-Request-Duration', 'X-RateLimit-Limit',
        'X-RateLimit-Remaining', 'X-RateLimit-Reset',
    }

    # 预检请求缓存时间(秒)
    MAX_AGE = 86400  # 24小时

    # 是否允许携带凭据
    ALLOW_CREDENTIALS = True

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        logger.info('CORSMiddleware 已初始化')

    def __call__(self, request: HttpRequest) -> HttpResponse:
        origin = request.META.get('HTTP_ORIGIN', '')

        # 预检请求(OPTIONS)
        if request.method == 'OPTIONS':
            response = HttpResponse(status=204)
            self._set_cors_headers(response, origin)
            response['Access-Control-Allow-Methods'] = ', '.join(self.ALLOWED_METHODS)
            response['Access-Control-Allow-Headers'] = ', '.join(self.ALLOWED_HEADERS)
            response['Access-Control-Max-Age'] = str(self.MAX_AGE)
            return response

        # 正常请求
        response = self.get_response(request)
        self._set_cors_headers(response, origin)
        return response

    def _set_cors_headers(self, response: HttpResponse, origin: str) -> None:
        """设置CORS响应头"""
        if self._is_origin_allowed(origin):
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
        elif not origin:
            # 无Origin头(同源请求或非浏览器客户端)
            pass
        else:
            # 不允许的源: 不设置CORS头,浏览器会拒绝
            logger.warning(f'CORS: 不允许的源: {origin}')

        if self.ALLOW_CREDENTIALS:
            response['Access-Control-Allow-Credentials'] = 'true'

        if self.EXPOSE_HEADERS:
            response['Access-Control-Expose-Headers'] = ', '.join(self.EXPOSE_HEADERS)

    def _is_origin_allowed(self, origin: str) -> bool:
        """检查源是否被允许"""
        if not origin:
            return False
        # 开发环境: 允许所有源
        if '*' in self.ALLOWED_ORIGINS:
            return True
        return origin in self.ALLOWED_ORIGINS


# ============================================================================
# 第五部分: 维护模式中间件
# ============================================================================

class MaintenanceModeMiddleware:
    """
    维护模式中间件

    功能:
    - 通过配置开关启用/禁用维护模式
    - 维护模式下返回503 Service Unavailable
    - 允许特定IP(管理员)正常访问
    - 支持自定义维护页面

    企业级用途:
    - 数据库迁移期间
    - 系统升级期间
    - 紧急安全修复期间
    """

    # 维护模式开关(可通过环境变量或配置中心动态修改)
    MAINTENANCE_MODE = False

    # 维护模式下允许访问的IP
    MAINTENANCE_ALLOWED_IPS: Set[str] = {'127.0.0.1', '::1'}

    # 维护模式下允许访问的路径
    MAINTENANCE_ALLOWED_PATHS: Set[str] = {'/admin/', '/health/'}

    # 预计恢复时间
    ESTIMATED_RECOVERY_TIME: Optional[str] = None

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        logger.info('MaintenanceModeMiddleware 已初始化')

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self.MAINTENANCE_MODE:
            return self.get_response(request)

        client_ip = self._get_client_ip(request)

        # 允许的IP
        if client_ip in self.MAINTENANCE_ALLOWED_IPS:
            return self.get_response(request)

        # 允许的路径
        if request.path in self.MAINTENANCE_ALLOWED_PATHS:
            return self.get_response(request)

        # 返回维护页面
        recovery_info = ''
        if self.ESTIMATED_RECOVERY_TIME:
            recovery_info = f'预计恢复时间: {self.ESTIMATED_RECOVERY_TIME}'

        return JsonResponse(
            {
                'error': 'Service Unavailable',
                'message': '系统正在维护中,请稍后再试',
                'estimated_recovery': recovery_info,
            },
            status=503,
        )

    def _get_client_ip(self, request: HttpRequest) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


# ============================================================================
# 第六部分: API签名验证中间件
# ============================================================================

class APISignatureMiddleware:
    """
    API签名验证中间件

    功能:
    - 验证API请求的签名(防止篡改)
    - 支持HMAC-SHA256签名算法
    - 防重放攻击(时间戳+随机数)

    签名算法:
    1. 将请求参数按字母排序拼接
    2. 添加时间戳和随机数(nonce)
    3. 使用密钥进行HMAC-SHA256签名
    4. 将签名放入请求头X-API-Signature

    企业级用途:
    - 开放API接口安全
    - 第三方系统对接
    - 支付回调验证
    """

    # 签名验证密钥(生产环境应从配置中心获取)
    API_SECRET = 'your-api-secret-key-here'

    # 签名有效期(秒) - 防重放攻击
    SIGNATURE_TTL = 300  # 5分钟

    # 需要签名验证的路径前缀
    SIGNATURE_REQUIRED_PATHS: Set[str] = {'/api/external/'}

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        # 已使用的nonce缓存(防重放)
        self._used_nonces: Dict[str, float] = {}
        logger.info('APISignatureMiddleware 已初始化')

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 检查是否需要签名验证
        if not any(request.path.startswith(p) for p in self.SIGNATURE_REQUIRED_PATHS):
            return self.get_response(request)

        # 提取签名信息
        signature = request.META.get('HTTP_X_API_SIGNATURE', '')
        timestamp = request.META.get('HTTP_X_API_TIMESTAMP', '')
        nonce = request.META.get('HTTP_X_API_NONCE', '')

        if not all([signature, timestamp, nonce]):
            return JsonResponse(
                {'error': 'Missing signature parameters', 'code': 'AUTH_001'},
                status=401,
            )

        # 检查时间戳有效期
        try:
            req_time = float(timestamp)
            if abs(time.time() - req_time) > self.SIGNATURE_TTL:
                return JsonResponse(
                    {'error': 'Signature expired', 'code': 'AUTH_002'},
                    status=401,
                )
        except ValueError:
            return JsonResponse(
                {'error': 'Invalid timestamp', 'code': 'AUTH_003'},
                status=400,
            )

        # 检查nonce(防重放)
        if nonce in self._used_nonces:
            return JsonResponse(
                {'error': 'Duplicate request (nonce already used)', 'code': 'AUTH_004'},
                status=401,
            )

        # 验证签名
        expected_signature = self._compute_signature(request, timestamp, nonce)
        if not self._constant_time_compare(signature, expected_signature):
            return JsonResponse(
                {'error': 'Invalid signature', 'code': 'AUTH_005'},
                status=401,
            )

        # 记录nonce(简化实现,生产环境应使用Redis)
        self._used_nonces[nonce] = time.time()
        # 清理过期nonce
        cutoff = time.time() - self.SIGNATURE_TTL
        self._used_nonces = {
            n: t for n, t in self._used_nonces.items() if t > cutoff
        }

        return self.get_response(request)

    def _compute_signature(self, request: HttpRequest, timestamp: str, nonce: str) -> str:
        """计算期望的签名"""
        import hmac

        # 构建签名字符串
        parts = [f'timestamp={timestamp}', f'nonce={nonce}']

        # 添加查询参数
        for key in sorted(request.GET.keys()):
            parts.append(f'{key}={request.GET[key]}')

        # 添加POST参数
        if request.method in ('POST', 'PUT', 'PATCH'):
            try:
                body = json.loads(request.body)
                if isinstance(body, dict):
                    for key in sorted(body.keys()):
                        parts.append(f'{key}={body[key]}')
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        message = '&'.join(parts)

        # HMAC-SHA256签名
        signature = hmac.new(
            self.API_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        return signature

    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """恒定时间比较(防止时序攻击)"""
        import hmac
        return hmac.compare_digest(a, b)


# ============================================================================
# 第七部分: 函数式中间件(装饰器风格)
# ============================================================================

def login_required_middleware(get_response: Callable[[HttpRequest], HttpResponse]) -> Callable:
    """
    登录验证函数式中间件(装饰器风格)

    这种写法更接近Python装饰器的风格,适合简单的中间件逻辑

    需要登录才能访问的路径通过LOGIN_REQUIRED_URLS配置
    未登录用户:
    - Ajax请求返回JSON提示
    - 普通请求重定向到登录页

    C++对比:
    类似于C++中的函数包装器或AOP切面:
    auto loginGuard = [](auto handler) {
        return [handler](Request& req, Response& res) {
            if (!req.session().has("userid")) {
                return res.redirect("/login/");
            }
            return handler(req, res);
        };
    };
    """
    LOGIN_REQUIRED_URLS = {
        '/api/user/profile/',
        '/api/orders/',
        '/api/cart/',
        '/reports/',
    }

    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.path in LOGIN_REQUIRED_URLS:
            # 模拟session检查
            if not request.session.get('userid'):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'code': 10003, 'hint': '请先登录'},
                        status=401,
                    )
                else:
                    backurl = request.get_full_path()
                    return HttpResponseRedirect(f'/login/?backurl={backurl}')
        return get_response(request, *args, **kwargs)

    return wrapper


# ============================================================================
# 第八部分: 类式中间件(MiddlewareMixin)
# ============================================================================

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    安全响应头中间件(MiddlewareMixin风格)

    添加安全相关的HTTP响应头:
    - X-Content-Type-Options: 防止MIME类型嗅探
    - X-Frame-Options: 防止点击劫持
    - X-XSS-Protection: XSS过滤
    - Strict-Transport-Security: 强制HTTPS
    - Content-Security-Policy: 内容安全策略
    - Referrer-Policy: 引用来源策略

    C++对比:
    C++ Web框架中,安全头通常在Web服务器(Nginx/Apache)层面配置:
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    Django中间件提供了应用层面的灵活控制
    """

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """请求预处理: 记录请求开始时间"""
        request._start_time = time.time()
        return None  # 返回None继续处理链

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """响应后处理: 添加安全头"""
        # 防止MIME类型嗅探
        response['X-Content-Type-Options'] = 'nosniff'

        # 防止点击劫持
        response['X-Frame-Options'] = 'SAMEORIGIN'

        # XSS过滤
        response['X-XSS-Protection'] = '1; mode=block'

        # 内容安全策略
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.bootcss.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:;"
        )

        # 引用来源策略
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # 添加服务器标识
        response['X-Powered-By'] = 'Django'

        # 请求耗时
        if hasattr(request, '_start_time'):
            elapsed = time.time() - request._start_time
            response['X-Request-Duration'] = f'{elapsed:.4f}s'

        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[JsonResponse]:
        """异常处理: 统一错误响应格式"""
        logger.exception(f'未处理异常: {request.method} {request.path}')

        return JsonResponse(
            {
                'error': 'Internal Server Error',
                'message': str(exception) if settings.DEBUG else '服务器内部错误',
                'path': request.path,
                'method': request.method,
            },
            status=500,
        )


# ============================================================================
# 第九部分: 中间件配置与注册
# ============================================================================

# 生产环境推荐的MIDDLEWARE配置
PRODUCTION_MIDDLEWARE = [
    # Django内置中间件(按依赖顺序)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # 自定义中间件(按功能分层)
    # 第1层: 基础设施(安全、日志、CORS)
    'code.middleware_52.SecurityHeadersMiddleware',
    'code.middleware_52.RequestLoggerMiddleware',
    'code.middleware_52.CORSMiddleware',
    'code.middleware_52.MaintenanceModeMiddleware',

    # 第2层: 访问控制(IP过滤、速率限制、认证)
    'code.middleware_52.IPBlockerMiddleware',
    'code.middleware_52.RateLimiterMiddleware',
    'code.middleware_52.APISignatureMiddleware',
]


# ============================================================================
# 第十部分: Django视图与URL配置(演示用)
# ============================================================================

from django.urls import path


def index_view(request: HttpRequest) -> HttpResponse:
    """首页"""
    return JsonResponse({
        'message': 'Django中间件演示',
        'endpoints': [
            'GET  /api/public/     - 公开接口(无限制)',
            'GET  /api/data/       - 数据接口(有速率限制)',
            'POST /api/external/   - 外部API(需要签名验证)',
            'GET  /health/         - 健康检查(跳过日志)',
        ],
    })


def public_api(request: HttpRequest) -> JsonResponse:
    """公开API - 受CORS和安全头中间件保护"""
    return JsonResponse({
        'status': 'ok',
        'message': '这是一个公开API,受CORS和安全头中间件保护',
        'timestamp': datetime.now().isoformat(),
    })


def data_api(request: HttpRequest) -> JsonResponse:
    """数据API - 受速率限制中间件保护"""
    return JsonResponse({
        'data': [
            {'id': 1, 'name': '商品A', 'price': 99.99},
            {'id': 2, 'name': '商品B', 'price': 199.99},
            {'id': 3, 'name': '商品C', 'price': 299.99},
        ],
        'total': 3,
    })


def external_api(request: HttpRequest) -> JsonResponse:
    """外部API - 需要签名验证"""
    return JsonResponse({
        'status': 'verified',
        'message': '签名验证通过,请求合法',
    })


def health_check(request: HttpRequest) -> JsonResponse:
    """健康检查 - 跳过日志记录"""
    return JsonResponse({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


urlpatterns = [
    path('', index_view, name='index'),
    path('api/public/', public_api, name='public_api'),
    path('api/data/', data_api, name='data_api'),
    path('api/external/', external_api, name='external_api'),
    path('health/', health_check, name='health_check'),
]


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    """主函数: 演示中间件的工作原理"""
    print('=' * 70)
    print('  Django中间件的应用 - 企业级中间件实战演示')
    print('  (Django Middleware - Enterprise Middleware Demo)')
    print('=' * 70)

    # 1. 中间件原理说明
    print('\n[1] Django中间件工作原理:')
    print('  请求流程: Client -> MIDDLEWARE[0] -> MIDDLEWARE[1] -> ... -> View')
    print('  响应流程: View -> ... -> MIDDLEWARE[1] -> MIDDLEWARE[0] -> Client')
    print('  异常流程: View -> Exception -> MIDDLEWARE[i].process_exception -> ...')

    # 2. 展示所有中间件
    print('\n[2] 本模块包含的中间件:')
    middleware_list = [
        ('RateLimiterMiddleware', '滑动窗口速率限制,按IP限制API调用频率'),
        ('RequestLoggerMiddleware', '请求/响应日志记录,支持敏感数据脱敏'),
        ('IPBlockerMiddleware', 'IP黑名单,支持CIDR网段和白名单'),
        ('CORSMiddleware', 'CORS跨域资源共享,支持预检请求'),
        ('MaintenanceModeMiddleware', '维护模式,支持IP白名单和自定义维护页'),
        ('APISignatureMiddleware', 'API签名验证,HMAC-SHA256+防重放'),
        ('SecurityHeadersMiddleware', '安全响应头(XSS/CSP/HSTS等)'),
        ('login_required_middleware', '函数式登录验证中间件(装饰器风格)'),
    ]

    for idx, (name, desc) in enumerate(middleware_list, start=1):
        print(f'  {idx}. {name}')
        print(f'     {desc}')

    # 3. 中间件配置顺序说明
    print('\n[3] 中间件配置顺序(重要!):')
    print('  MIDDLEWARE = [')
    print('      # Django内置(必须按顺序)')
    print('      "django.middleware.security.SecurityMiddleware",    # 安全')
    print('      "django.contrib.sessions.middleware.SessionMiddleware",  # Session')
    print('      "django.middleware.common.CommonMiddleware",         # 通用')
    print('      "django.middleware.csrf.CsrfViewMiddleware",        # CSRF')
    print('      "django.contrib.auth.middleware.AuthenticationMiddleware",  # 认证')
    print('      ...')
    print('      # 自定义(按功能分层)')
    print('      "...SecurityHeadersMiddleware",    # 第1层: 安全头')
    print('      "...RequestLoggerMiddleware",      # 第1层: 日志')
    print('      "...CORSMiddleware",               # 第1层: CORS')
    print('      "...IPBlockerMiddleware",          # 第2层: IP过滤')
    print('      "...RateLimiterMiddleware",        # 第2层: 速率限制')
    print('  ]')

    # 4. C++对比
    print('\n[4] Django中间件 vs C++拦截器模式:')
    comparison = """
    ┌──────────────────────┬──────────────────────────────────────┐
    │   Django Middleware  │   C++ Interceptor / Filter Chain     │
    ├──────────────────────┼──────────────────────────────────────┤
    │ __call__ + 钩子方法   │ 纯虚函数接口(preHandle/postHandle)  │
    │ Python可调用对象      │ C++多态(虚函数/模板)                │
    │ 列表配置(声明式)      │ 代码注册(命令式)                    │
    │ 框架自动管理生命周期   │ 需手动管理对象生命周期               │
    │ 运行时动态添加/移除   │ 编译时确定(或使用插件架构)           │
    │ 单线程请求模型        │ 需考虑线程安全(std::mutex)          │
    │ 异常直接传播          │ 需要try-catch或错误码               │
    │ GIL限制并发          │ 真正的多线程并发                    │
    └──────────────────────┴──────────────────────────────────────┘
    """
    print(comparison)

    # 5. 企业级最佳实践
    print('\n[5] 企业级中间件最佳实践:')
    practices = [
        '1. 中间件应该单一职责,一个中间件只做一件事',
        '2. 中间件执行顺序很重要: Session依赖的中间件必须放在SessionMiddleware之后',
        '3. 生产环境使用Redis存储速率限制和nonce数据(支持多进程/分布式)',
        '4. 敏感数据(password/token)在日志中必须脱敏',
        '5. CORS的ALLOWED_ORIGINS在生产环境必须限制为具体域名',
        '6. API签名验证使用恒定时间比较(防止时序攻击)',
        '7. 维护模式开关应支持通过环境变量或配置中心动态修改',
        '8. 健康检查端点应跳过认证和日志中间件(减少开销)',
        '9. 中间件中的异常应该被正确捕获并记录,而不是直接抛出',
        '10. 使用中间件实现横切关注点(cross-cutting concerns),避免视图函数中的重复代码',
    ]
    for p in practices:
        print(f'  {p}')

    # 6. 生产环境MIDDLEWARE配置
    print('\n[6] 生产环境MIDDLEWARE配置示例:')
    print('  请参考 PRODUCTION_MIDDLEWARE 变量')

    print('\n' + '=' * 70)
    print('  所有演示执行完毕!')
    print('=' * 70)


if __name__ == '__main__':
    main()
