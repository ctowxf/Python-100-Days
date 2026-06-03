"""
53_frontend_separation.py - 前后端分离开发入门 (Frontend-Backend Separation)
=============================================================================

本模块演示Django在前后端分离架构中的应用,包括:
- RESTful API设计与实现
- JSON响应与序列化
- CORS跨域支持
- Token认证(JWT)
- API版本管理
- Swagger/OpenAPI文档
- 前后端通信模式

企业级应用场景:
- SPA(单页应用)后端API服务
- 移动App后端API
- 微服务API网关
- 第三方开放平台API

依赖安装:
    pip install django djangorestframework djangorestframework-simplejwt django-cors-headers
"""

from __future__ import annotations

import os
import sys
import json
import uuid
import hashlib
import datetime
from decimal import Decimal
from typing import Any, Optional, List, Dict, Tuple, Union, Type
from functools import wraps

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
        SECRET_KEY='demo-secret-key-for-jwt-token-signing',
        ROOT_URLCONF=__name__,
        REST_FRAMEWORK={
            'DEFAULT_RENDERER_CLASSES': [
                'rest_framework.renderers.JSONRenderer',
            ],
            'DEFAULT_PARSER_CLASSES': [
                'rest_framework.parsers.JSONParser',
            ],
            'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
            'PAGE_SIZE': 20,
            'DEFAULT_AUTHENTICATION_CLASSES': [],
            'DEFAULT_PERMISSION_CLASSES': [],
        },
    )
    django.setup()

from django.db import models, connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, Avg


# ============================================================================
# 第一部分: 数据模型
# ============================================================================

class Article(models.Model):
    """
    文章模型 - 用于演示RESTful API

    C++对比: 模型定义
    - Django: class Article(models.Model) 一行搞定映射
    - C++ ODB: 需要 #pragma db object + 手动映射
    - C++手动SQL: 需要编写完整的CRUD SQL语句
    """
    title: models.CharField = models.CharField(max_length=200, verbose_name='标题')
    content: models.TextField = models.TextField(verbose_name='正文')
    author: models.CharField = models.CharField(max_length=100, verbose_name='作者')
    category: models.CharField = models.CharField(
        max_length=50,
        verbose_name='分类',
        choices=[
            ('tech', '技术'),
            ('life', '生活'),
            ('news', '资讯'),
            ('tutorial', '教程'),
        ],
    )
    tags: models.CharField = models.CharField(
        max_length=500, blank=True, default='',
        verbose_name='标签(逗号分隔)',
    )
    view_count: models.PositiveIntegerField = models.IntegerField(default=0, verbose_name='浏览量')
    like_count: models.PositiveIntegerField = models.IntegerField(default=0, verbose_name='点赞数')
    is_published: models.BooleanField = models.BooleanField(default=True, verbose_name='是否发布')
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'api_article'
        verbose_name = '文章'
        verbose_name_plural = '文章列表'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title

    @property
    def tag_list(self) -> List[str]:
        """获取标签列表"""
        return [t.strip() for t in self.tags.split(',') if t.strip()]


# ============================================================================
# 第二部分: 序列化器(手动实现,不依赖DRF)
# ============================================================================

class Serializer:
    """
    简易序列化器 - 手动实现对象到字典的转换

    Django REST Framework的ModelSerializer是企业级首选,
    此处手动实现以理解底层原理

    C++对比:
    - C++中序列化通常使用protobuf/flatbuffers/msgpack
    - 或手动编写toJson()/fromJson()方法
    - Python的动态类型让序列化器实现极其简洁
    """

    def __init__(self, instance: Any = None, data: Dict = None, many: bool = False):
        self.instance = instance
        self._data = data
        self.many = many
        self._errors: Dict[str, List[str]] = {}

    @property
    def errors(self) -> Dict[str, List[str]]:
        return self._errors

    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0

    def to_dict(self, instance: Any) -> Dict[str, Any]:
        """子类重写此方法定义序列化字段"""
        raise NotImplementedError

    @property
    def data(self) -> Union[List[Dict], Dict]:
        if self.many and self.instance is not None:
            return [self.to_dict(obj) for obj in self.instance]
        elif self.instance is not None:
            return self.to_dict(self.instance)
        return {}

    def validate(self, data: Dict[str, Any]) -> None:
        """子类重写此方法实现验证逻辑"""
        pass

    def create(self, validated_data: Dict[str, Any]) -> Any:
        """子类重写此方法实现创建逻辑"""
        raise NotImplementedError

    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        """子类重写此方法实现更新逻辑"""
        raise NotImplementedError


class ArticleSerializer(Serializer):
    """
    文章序列化器

    功能:
    - 对象 -> 字典(序列化)
    - 字典 -> 对象(反序列化+验证)
    """

    # 可读字段(序列化时输出)
    READ_FIELDS = {'id', 'title', 'content', 'author', 'category', 'tags',
                   'tag_list', 'view_count', 'like_count', 'is_published',
                   'created_at', 'updated_at'}

    # 可写字段(反序列化时接受)
    WRITE_FIELDS = {'title', 'content', 'author', 'category', 'tags', 'is_published'}

    # 必填字段
    REQUIRED_FIELDS = {'title', 'content', 'author'}

    def to_dict(self, instance: Article) -> Dict[str, Any]:
        """序列化: Article对象 -> 字典"""
        return {
            'id': instance.id,
            'title': instance.title,
            'content': instance.content,
            'author': instance.author,
            'category': instance.category,
            'category_display': instance.get_category_display(),
            'tags': instance.tag_list,
            'view_count': instance.view_count,
            'like_count': instance.like_count,
            'is_published': instance.is_published,
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
        }

    def validate(self, data: Dict[str, Any]) -> None:
        """验证输入数据"""
        self._errors = {}

        # 必填字段检查
        for field in self.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                self._errors.setdefault(field, []).append(f'{field}是必填字段')

        # 标题长度验证
        if 'title' in data and len(data['title']) > 200:
            self._errors.setdefault('title', []).append('标题不能超过200个字符')

        # 内容长度验证
        if 'content' in data and len(data['content']) < 10:
            self._errors.setdefault('content', []).append('内容不能少于10个字符')

        # 分类验证
        valid_categories = {'tech', 'life', 'news', 'tutorial'}
        if 'category' in data and data['category'] not in valid_categories:
            self._errors.setdefault('category', []).append(
                f'无效的分类: {data["category"]}, 可选值: {valid_categories}'
            )

    def create(self, validated_data: Dict[str, Any]) -> Article:
        """创建文章"""
        return Article.objects.create(**validated_data)

    def update(self, instance: Article, validated_data: Dict[str, Any]) -> Article:
        """更新文章"""
        for key, value in validated_data.items():
            if key in self.WRITE_FIELDS:
                setattr(instance, key, value)
        instance.save()
        return instance

    def extract_validated_data(self) -> Dict[str, Any]:
        """从输入数据中提取可写字段"""
        if self._data is None:
            return {}
        return {k: v for k, v in self._data.items() if k in self.WRITE_FIELDS}


# ============================================================================
# 第三部分: 通用API响应工具
# ============================================================================

class APIResponse:
    """
    统一API响应格式

    企业级API应该使用统一的响应格式:
    {
        "code": 200,
        "message": "success",
        "data": { ... },
        "meta": { "page": 1, "total": 100 }
    }

    C++对比:
    C++中通常定义一个ApiResponse模板类:
        template<typename T>
        struct ApiResponse {
            int code;
            std::string message;
            std::optional<T> data;
            json toJson() const { ... }
        };
    """

    @staticmethod
    def success(data: Any = None, message: str = 'success', meta: Dict = None) -> JsonResponse:
        """成功响应"""
        body: Dict[str, Any] = {
            'code': 200,
            'message': message,
            'data': data,
        }
        if meta:
            body['meta'] = meta
        return JsonResponse(body, json_dumps_params={'ensure_ascii': False})

    @staticmethod
    def created(data: Any = None, message: str = '创建成功') -> JsonResponse:
        """创建成功响应"""
        return JsonResponse(
            {'code': 201, 'message': message, 'data': data},
            status=201,
            json_dumps_params={'ensure_ascii': False},
        )

    @staticmethod
    def error(message: str = '请求错误', code: int = 400, errors: Dict = None) -> JsonResponse:
        """错误响应"""
        body: Dict[str, Any] = {
            'code': code,
            'message': message,
        }
        if errors:
            body['errors'] = errors
        return JsonResponse(body, status=code, json_dumps_params={'ensure_ascii': False})

    @staticmethod
    def not_found(message: str = '资源不存在') -> JsonResponse:
        """404响应"""
        return APIResponse.error(message, code=404)

    @staticmethod
    def unauthorized(message: str = '未授权') -> JsonResponse:
        """401响应"""
        return APIResponse.error(message, code=401)

    @staticmethod
    def forbidden(message: str = '禁止访问') -> JsonResponse:
        """403响应"""
        return APIResponse.error(message, code=403)

    @staticmethod
    def paginated(data: List, page: int, page_size: int, total: int) -> JsonResponse:
        """分页响应"""
        total_pages = (total + page_size - 1) // page_size
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': data,
            'meta': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
            },
        }, json_dumps_params={'ensure_ascii': False})


# ============================================================================
# 第四部分: Token认证(JWT简化实现)
# ============================================================================

class JWTService:
    """
    JWT(Json Web Token)服务 - 简化实现

    JWT由三部分组成: Header.Payload.Signature
    - Header: {"alg": "HS256", "typ": "JWT"} (Base64编码)
    - Payload: {"user_id": 1, "exp": timestamp} (Base64编码)
    - Signature: HMAC-SHA256(header.payload, secret)

    C++对比:
    - C++中JWT实现需要Base64编解码+HMAC-SHA256
    - 常用库: jwt-cpp, cpp-jwt
    - Python的jwt/PyJWT库更简洁

    企业级改进:
    - 使用PyJWT库(生产环境不建议手写)
    - 支持Token刷新(Refresh Token)
    - 支持Token黑名单(用户登出后Token失效)
    - 密钥管理使用环境变量或密钥管理服务
    """

    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1小时
    REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7天

    @classmethod
    def create_access_token(cls, user_id: int, username: str) -> str:
        """创建访问Token"""
        import base64
        import hmac

        header = {'alg': cls.ALGORITHM, 'typ': 'JWT'}
        payload = {
            'user_id': user_id,
            'username': username,
            'type': 'access',
            'exp': int((datetime.datetime.now() + datetime.timedelta(
                minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
            )).timestamp()),
            'iat': int(datetime.datetime.now().timestamp()),
            'jti': str(uuid.uuid4()),
        }

        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip('=')

        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')

        message = f'{header_b64}.{payload_b64}'
        signature = hmac.new(
            cls.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256,
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')

        return f'{header_b64}.{payload_b64}.{signature_b64}'

    @classmethod
    def decode_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """解码并验证Token"""
        import base64
        import hmac

        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None

            header_b64, payload_b64, signature_b64 = parts

            # 验证签名
            message = f'{header_b64}.{payload_b64}'
            expected_sig = hmac.new(
                cls.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256,
            ).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')

            if not hmac.compare_digest(signature_b64, expected_sig_b64):
                return None

            # 解码Payload
            padding = 4 - len(payload_b64) % 4
            payload_b64_padded = payload_b64 + '=' * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64_padded))

            # 检查过期
            if payload.get('exp', 0) < datetime.datetime.now().timestamp():
                return None

            return payload
        except Exception:
            return None

    @classmethod
    def create_refresh_token(cls, user_id: int) -> str:
        """创建刷新Token"""
        return cls.create_access_token(user_id, 'refresh')


# ============================================================================
# 第五部分: 装饰器(认证、权限)
# ============================================================================

def api_view(methods: List[str] = None):
    """
    API视图装饰器 - 统一处理请求方法检查和异常

    类似于DRF的@api_view装饰器
    """
    if methods is None:
        methods = ['GET']

    def decorator(view_func):
        @wraps(view_func)
        @csrf_exempt
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if request.method not in methods:
                return APIResponse.error(
                    f'不支持的请求方法: {request.method}',
                    code=405,
                )
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return APIResponse.error(f'服务器内部错误: {str(e)}', code=500)

        return wrapper
    return decorator


def token_required(view_func):
    """
    Token认证装饰器

    从请求头Authorization中提取Bearer Token并验证
    """
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return APIResponse.unauthorized('缺少认证Token')

        token = auth_header[7:]  # 去掉"Bearer "前缀
        payload = JWTService.decode_token(token)

        if payload is None:
            return APIResponse.unauthorized('Token无效或已过期')

        # 将用户信息附加到request对象
        request.user_id = payload.get('user_id')
        request.username = payload.get('username')

        return view_func(request, *args, **kwargs)

    return wrapper


# ============================================================================
# 第六部分: RESTful API视图(函数式)
# ============================================================================

@csrf_exempt
@require_http_methods(['GET'])
def api_index(request: HttpRequest) -> JsonResponse:
    """
    API首页 - 返回API文档

    URL: GET /api/v1/
    """
    return APIResponse.success(data={
        'name': 'Django前后端分离API',
        'version': 'v1',
        'endpoints': {
            'articles': {
                'list':    'GET  /api/v1/articles/',
                'create':  'POST /api/v1/articles/',
                'detail':  'GET  /api/v1/articles/<id>/',
                'update':  'PUT  /api/v1/articles/<id>/',
                'delete':  'DELETE /api/v1/articles/<id>/',
            },
            'auth': {
                'login':   'POST /api/v1/auth/login/',
                'refresh': 'POST /api/v1/auth/refresh/',
            },
            'stats': {
                'dashboard': 'GET /api/v1/stats/dashboard/',
            },
        },
    })


@api_view(['GET', 'POST'])
def article_list(request: HttpRequest) -> JsonResponse:
    """
    文章列表API

    GET  /api/v1/articles/          - 获取文章列表(支持分页、筛选、搜索)
    POST /api/v1/articles/          - 创建新文章

    查询参数:
    - page: 页码(默认1)
    - page_size: 每页数量(默认20)
    - category: 分类筛选
    - search: 搜索关键词(标题和内容)
    - ordering: 排序字段(-created_at, view_count, -like_count)
    - is_published: 发布状态筛选
    """
    if request.method == 'GET':
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        category = request.GET.get('category')
        search = request.GET.get('search')
        ordering = request.GET.get('ordering', '-created_at')
        is_published = request.GET.get('is_published')

        # 构建查询
        queryset = Article.objects.all()

        # 分类筛选
        if category:
            queryset = queryset.filter(category=category)

        # 发布状态筛选
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')

        # 搜索
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        # 排序
        valid_orderings = {'created_at', '-created_at', 'view_count', '-view_count',
                           'like_count', '-like_count', 'title', '-title'}
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)

        # 分页
        total = queryset.count()
        offset = (page - 1) * page_size
        articles = queryset[offset:offset + page_size]

        # 序列化
        serializer = ArticleSerializer(articles, many=True)

        return APIResponse.paginated(
            data=serializer.data,
            page=page,
            page_size=page_size,
            total=total,
        )

    elif request.method == 'POST':
        # 解析请求体
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return APIResponse.error('无效的JSON数据')

        # 验证和创建
        serializer = ArticleSerializer(data=body)
        serializer.validate(body)

        if not serializer.is_valid:
            return APIResponse.error('数据验证失败', errors=serializer.errors)

        validated_data = serializer.extract_validated_data()
        article = serializer.create(validated_data)

        return APIResponse.created(
            data=serializer.to_dict(article),
            message='文章创建成功',
        )


@api_view(['GET', 'PUT', 'DELETE'])
def article_detail(request: HttpRequest, article_id: int) -> JsonResponse:
    """
    文章详情API

    GET    /api/v1/articles/<id>/  - 获取文章详情
    PUT    /api/v1/articles/<id>/  - 更新文章(全量)
    DELETE /api/v1/articles/<id>/  - 删除文章
    """
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        return APIResponse.not_found(f'文章不存在: id={article_id}')

    if request.method == 'GET':
        # 增加浏览量(F对象原子操作)
        Article.objects.filter(pk=article_id).update(view_count=models.F('view_count') + 1)
        article.refresh_from_db()

        serializer = ArticleSerializer(article)
        return APIResponse.success(data=serializer.data)

    elif request.method == 'PUT':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return APIResponse.error('无效的JSON数据')

        serializer = ArticleSerializer(data=body)
        serializer.validate(body)

        if not serializer.is_valid:
            return APIResponse.error('数据验证失败', errors=serializer.errors)

        validated_data = serializer.extract_validated_data()
        article = serializer.update(article, validated_data)

        return APIResponse.success(
            data=serializer.to_dict(article),
            message='文章更新成功',
        )

    elif request.method == 'DELETE':
        article_title = article.title
        article.delete()
        return APIResponse.success(message=f'文章已删除: {article_title}')


# ============================================================================
# 第七部分: Class-Based View(类视图)
# ============================================================================

class ArticleViewSet(View):
    """
    文章视图集(Class-Based View)

    Django的类视图是实现RESTful API的另一种方式:
    - 比函数式视图更好地组织代码
    - 支持方法分发(get/post/put/delete)
    - 可以通过Mixin实现代码复用

    C++对比:
    Django CBV类似于C++中的策略模式(Strategy Pattern):
    class ArticleHandler : public HttpHandler {
        void get(Request& req, Response& res) override { ... }
        void post(Request& req, Response& res) override { ... }
    };
    """

    @csrf_exempt
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """请求分发"""
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            return APIResponse.error(f'服务器错误: {str(e)}', code=500)

    def get(self, request: HttpRequest) -> JsonResponse:
        """获取文章列表或详情"""
        article_id = request.GET.get('id')
        if article_id:
            try:
                article = Article.objects.get(pk=int(article_id))
                serializer = ArticleSerializer(article)
                return APIResponse.success(data=serializer.data)
            except Article.DoesNotExist:
                return APIResponse.not_found()
        else:
            articles = Article.objects.filter(is_published=True)[:10]
            serializer = ArticleSerializer(articles, many=True)
            return APIResponse.success(data=serializer.data)

    def post(self, request: HttpRequest) -> JsonResponse:
        """创建文章"""
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return APIResponse.error('无效的JSON数据')

        serializer = ArticleSerializer(data=body)
        serializer.validate(body)
        if not serializer.is_valid:
            return APIResponse.error('验证失败', errors=serializer.errors)

        article = serializer.create(serializer.extract_validated_data())
        return APIResponse.created(data=serializer.to_dict(article))


# ============================================================================
# 第八部分: 统计API(仪表盘数据)
# ============================================================================

@api_view(['GET'])
def stats_dashboard(request: HttpRequest) -> JsonResponse:
    """
    统计仪表盘API

    返回文章统计数据,供前端ECharts等图表库渲染
    """
    total_articles = Article.objects.count()
    published_articles = Article.objects.filter(is_published=True).count()

    # 按分类统计
    category_stats = (
        Article.objects
        .values('category')
        .annotate(count=Count('id'), total_views=Sum('view_count'))
        .order_by('-count')
    )
    category_map = dict(Article._meta.get_field('category').choices)

    # 最热门文章
    top_articles = Article.objects.order_by('-view_count')[:5]
    top_data = [
        {'title': a.title, 'views': a.view_count, 'likes': a.like_count}
        for a in top_articles
    ]

    return APIResponse.success(data={
        'overview': {
            'total_articles': total_articles,
            'published_articles': published_articles,
            'draft_articles': total_articles - published_articles,
        },
        'category_distribution': [
            {
                'category': item['category'],
                'category_name': category_map.get(item['category'], item['category']),
                'count': item['count'],
                'total_views': item['total_views'] or 0,
            }
            for item in category_stats
        ],
        'top_articles': top_data,
    })


# ============================================================================
# 第九部分: 认证API
# ============================================================================

@csrf_exempt
@require_http_methods(['POST'])
def auth_login(request: HttpRequest) -> JsonResponse:
    """
    登录API - 返回JWT Token

    POST /api/v1/auth/login/
    Body: {"username": "admin", "password": "123456"}
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return APIResponse.error('无效的JSON数据')

    username = body.get('username', '')
    password = body.get('password', '')

    if not username or not password:
        return APIResponse.error('用户名和密码不能为空')

    # 简化验证(生产环境应使用Django的认证系统)
    demo_users = {
        'admin': {'id': 1, 'password_hash': hashlib.sha256('admin123'.encode()).hexdigest()},
        'editor': {'id': 2, 'password_hash': hashlib.sha256('editor123'.encode()).hexdigest()},
    }

    user = demo_users.get(username)
    if not user:
        return APIResponse.unauthorized('用户名或密码错误')

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user['password_hash']:
        return APIResponse.unauthorized('用户名或密码错误')

    # 生成Token
    access_token = JWTService.create_access_token(user['id'], username)
    refresh_token = JWTService.create_refresh_token(user['id'])

    return APIResponse.success(data={
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': JWTService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        'user': {
            'id': user['id'],
            'username': username,
        },
    }, message='登录成功')


# ============================================================================
# 第十部分: URL配置
# ============================================================================

from django.urls import path

urlpatterns = [
    # API v1
    path('api/v1/', api_index, name='api_index'),
    path('api/v1/articles/', article_list, name='article_list'),
    path('api/v1/articles/<int:article_id>/', article_detail, name='article_detail'),
    path('api/v1/stats/dashboard/', stats_dashboard, name='stats_dashboard'),
    path('api/v1/auth/login/', auth_login, name='auth_login'),
]


# ============================================================================
# 第十一部分: 示例数据填充
# ============================================================================

def populate_sample_data() -> None:
    """填充示例文章数据"""
    articles_data = [
        ('Django REST Framework入门指南', '本文详细介绍如何使用DRF构建RESTful API...',
         '张三', 'tutorial', 'django,rest,api,python', True),
        ('Python类型提示最佳实践', '从Python 3.5开始引入的类型提示(Type Hints)...',
         '李四', 'tech', 'python,typing,mypy', True),
        ('前后端分离架构设计', '在现代Web开发中,前后端分离已成为主流架构模式...',
         '王五', 'tech', '架构,前后端,api', True),
        ('Vue.js 3.0新特性解析', 'Vue.js 3.0带来了Composition API等重大更新...',
         '赵六', 'tech', 'vue,javascript,前端', True),
        ('MySQL索引优化实战', '合理的索引设计是数据库性能优化的关键...',
         '张三', 'tech', 'mysql,索引,性能优化', True),
        ('Docker容器化部署实践', '使用Docker实现应用的容器化部署...',
         '李四', 'tutorial', 'docker,devops,部署', True),
        ('Python异步编程深入', 'asyncio是Python异步编程的核心...',
         '王五', 'tech', 'python,async,asyncio', True),
        ('RESTful API设计规范', '一个好的API应该遵循RESTful设计原则...',
         '赵六', 'tutorial', 'rest,api,设计规范', True),
        ('Git工作流最佳实践', '选择合适的Git工作流对团队协作至关重要...',
         '张三', 'tutorial', 'git,版本控制,协作', True),
        ('Web安全防护指南', '了解常见的Web攻击手段及防护方法...',
         '李四', 'tech', '安全,xss,csrf,sql注入', True),
    ]

    for title, content, author, category, tags, is_published in articles_data:
        Article.objects.get_or_create(
            title=title,
            defaults={
                'content': content,
                'author': author,
                'category': category,
                'tags': tags,
                'is_published': is_published,
                'view_count': hash(title) % 1000,
                'like_count': hash(title) % 200,
            },
        )

    print(f'  已创建 {len(articles_data)} 篇示例文章')


# ============================================================================
# 第十二部分: 前端Vue.js示例代码(参考)
# ============================================================================

VUE_EXAMPLE = '''
<!-- Vue.js 3 前端示例 (使用Composition API) -->
<template>
  <div id="app">
    <h1>文章列表</h1>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <input v-model="searchQuery" placeholder="搜索文章..." @keyup.enter="fetchArticles">
      <select v-model="selectedCategory" @change="fetchArticles">
        <option value="">全部分类</option>
        <option value="tech">技术</option>
        <option value="life">生活</option>
        <option value="news">资讯</option>
        <option value="tutorial">教程</option>
      </select>
      <button @click="fetchArticles">搜索</button>
    </div>

    <!-- 文章列表 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else>
      <div v-for="article in articles" :key="article.id" class="article-card">
        <h2>{{ article.title }}</h2>
        <p>{{ article.content.substring(0, 100) }}...</p>
        <div class="meta">
          <span>作者: {{ article.author }}</span>
          <span>分类: {{ article.category_display }}</span>
          <span>浏览: {{ article.view_count }}</span>
          <span>点赞: {{ article.like_count }}</span>
        </div>
        <div class="tags">
          <span v-for="tag in article.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <button :disabled="!meta.has_prev" @click="changePage(meta.page - 1)">上一页</button>
      <span>第 {{ meta.page }} / {{ meta.total_pages }} 页 (共 {{ meta.total }} 篇)</span>
      <button :disabled="!meta.has_next" @click="changePage(meta.page + 1)">下一页</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

const API_BASE = '/api/v1'

export default {
  setup() {
    const articles = ref([])
    const meta = ref({ page: 1, total: 0, total_pages: 1, has_next: false, has_prev: false })
    const loading = ref(false)
    const searchQuery = ref('')
    const selectedCategory = ref('')

    const fetchArticles = async (page = 1) => {
      loading.value = true
      const params = new URLSearchParams({ page, page_size: 10 })
      if (searchQuery.value) params.append('search', searchQuery.value)
      if (selectedCategory.value) params.append('category', selectedCategory.value)

      try {
        const resp = await fetch(`${API_BASE}/articles/?${params}`)
        const json = await resp.json()
        if (json.code === 200) {
          articles.value = json.data
          meta.value = json.meta
        }
      } catch (err) {
        console.error('API请求失败:', err)
      } finally {
        loading.value = false
      }
    }

    const changePage = (page) => fetchArticles(page)

    onMounted(() => fetchArticles())

    return { articles, meta, loading, searchQuery, selectedCategory, fetchArticles, changePage }
  }
}
</script>
'''


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    """主函数: 创建表、填充数据、演示API"""
    print('=' * 70)
    print('  前后端分离开发入门 - 企业级API实战演示')
    print('  (Frontend-Backend Separation - Enterprise API Demo)')
    print('=' * 70)

    # 1. 创建数据库表
    print('\n[Step 1] 创建数据库表...')
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Article)
        print(f'  [OK] 创建表: {Article._meta.db_table}')

    # 2. 填充示例数据
    print('\n[Step 2] 填充示例数据...')
    populate_sample_data()

    # 3. 序列化演示
    print('\n[Step 3] 序列化器演示...')
    articles = Article.objects.all()
    serializer = ArticleSerializer(articles[:3], many=True)
    print(f'  序列化 {len(serializer.data)} 篇文章:')
    for item in serializer.data:
        print(f'    [{item["id"]}] {item["title"]} | {item["author"]} | 浏览:{item["view_count"]}')

    # 4. JWT Token演示
    print('\n[Step 4] JWT Token演示...')
    token = JWTService.create_access_token(1, 'admin')
    print(f'  生成Token: {token[:50]}...')
    payload = JWTService.decode_token(token)
    print(f'  解码Token: user_id={payload["user_id"]}, username={payload["username"]}')

    # 5. API端点说明
    print('\n[Step 5] API端点说明:')
    endpoints = [
        ('GET', '/api/v1/', 'API文档首页'),
        ('GET', '/api/v1/articles/', '文章列表(支持分页/搜索/筛选)'),
        ('POST', '/api/v1/articles/', '创建文章'),
        ('GET', '/api/v1/articles/<id>/', '文章详情'),
        ('PUT', '/api/v1/articles/<id>/', '更新文章'),
        ('DELETE', '/api/v1/articles/<id>/', '删除文章'),
        ('GET', '/api/v1/stats/dashboard/', '统计仪表盘'),
        ('POST', '/api/v1/auth/login/', '用户登录(获取Token)'),
    ]
    for method, path, desc in endpoints:
        print(f'    {method:6s} {path:40s} - {desc}')

    # 6. 前后端分离架构说明
    print('\n[Step 6] 前后端分离架构:')
    architecture = """
    ┌──────────────────────────────────────────────────────────┐
    │                    前端(Frontend)                         │
    │  Vue.js / React / Angular / 小程序 / 移动App             │
    │  - 页面渲染、用户交互、路由管理                            │
    │  - 通过HTTP/AJAX调用后端API                              │
    └─────────────────────┬────────────────────────────────────┘
                          │ HTTP (JSON)
                          │ GET/POST/PUT/DELETE
    ┌─────────────────────▼────────────────────────────────────┐
    │                    后端(Backend)                          │
    │  Django / Flask / FastAPI                                │
    │  - RESTful API接口                                       │
    │  - 业务逻辑处理                                          │
    │  - 数据验证与序列化                                       │
    │  - 认证与授权                                            │
    └─────────────────────┬────────────────────────────────────┘
                          │ ORM
    ┌─────────────────────▼────────────────────────────────────┐
    │                    数据库(Database)                       │
    │  MySQL / PostgreSQL / Redis                              │
    └──────────────────────────────────────────────────────────┘

    优势:
    1. 前后端解耦,并行开发
    2. 一套API服务多端(Web/App/小程序)
    3. 前端可独立部署(CDN加速)
    4. 后端可水平扩展(负载均衡)
    """
    print(architecture)

    # 7. C++对比
    print('\n[7] Django API vs C++ API框架:')
    comparison = """
    ┌─────────────────────┬──────────────────────────────────┐
    │   Django REST API   │   C++ API (Crow/Drogon/oat++)   │
    ├─────────────────────┼──────────────────────────────────┤
    │ Python动态类型       │ C++静态类型                      │
    │ ORM自动序列化        │ 需手动序列化(protobuf/json)      │
    │ 开发速度快           │ 运行速度快                       │
    │ 内置认证/分页/过滤   │ 需自行实现或使用中间件            │
    │ 生态丰富(DRF等)      │ 库相对较少                       │
    │ 适合快速迭代         │ 适合高性能场景                   │
    │ GIL限制并发          │ 真正并发(epoll/多线程)           │
    └─────────────────────┴──────────────────────────────────┘
    """
    print(comparison)

    print('\n' + '=' * 70)
    print('  所有演示执行完毕!')
    print('=' * 70)


if __name__ == '__main__':
    main()
