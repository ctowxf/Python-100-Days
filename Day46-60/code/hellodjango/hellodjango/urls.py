"""
URL configuration for hellodjango project.
项目 URL 路由配置

在 Django 中，URL 配置负责将 HTTP 请求映射到对应的视图函数
类似 C++ 中的路由表或请求分发器

C++ 对比:
    // C++ 中可能使用 map 或 switch-case 进行路由
    std::map<std::string, Handler> routes = {
        {"/admin/", adminHandler},
        {"/polls/", pollsHandler},
    };

    // Django 使用 urlpatterns 列表，更加声明式
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('polls/', include('polls.urls')),
    ]
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from django.views.generic import RedirectView
from typing import List

# URL 模式列表
# 类型注解：List[Union[URLPattern, URLResolver]]
# URLPattern: 具体的 URL 模式
# URLResolver: URL 解析器（用于 include）
urlpatterns: List[URLPattern | URLResolver] = [
    # 根路径重定向到投票应用
    path('', RedirectView.as_view(url='/polls/', permanent=True)),

    # Django 管理后台
    # 类似 C++ 中的管理界面路由
    path('admin/', admin.site.urls),

    # 投票应用路由
    # include() 函数将 polls 应用的 URL 配置包含进来
    # 类似 C++ 中的模块化路由
    path('polls/', include('polls.urls')),

    # Django REST Framework 认证路由
    path('api-auth/', include('rest_framework.urls')),
]

# 开发环境下提供媒体文件服务
# 生产环境应使用 Nginx 等 Web 服务器处理
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 自定义错误页面（可选）
# 类似 C++ 中的异常处理器
# handler404 = 'polls.views.custom_404'
# handler500 = 'polls.views.custom_500'
