"""
Web前端入门 - Python HTTP服务器与Web框架基础
=============================================

本模块演示Python内置http.server模块的使用，包括：
- 基础HTTP服务器
- 模板渲染（string.Template）
- 简易Web框架概念
- 静态文件服务
- RESTful API端点

C++对比：Python http.server vs C++ libmicrohttpd
- Python: 内置标准库，零依赖，适合开发和测试
- C++ libmicrohttpd: 高性能，适合生产环境，需要编译链接

作者: Python-100-Days
日期: 2026-06-02
"""

import json
import mimetypes
import os
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from pathlib import Path
from string import Template
from typing import Any, Callable, Optional


# ============================================================================
# 第一部分：模板渲染系统
# ============================================================================

class TemplateEngine:
    """
    简易模板引擎，基于string.Template实现。

    支持变量替换和基本的条件渲染逻辑。

    用法:
        engine = TemplateEngine()
        result = engine.render("Hello, $name!", name="World")
    """

    def __init__(self, template_dir: Optional[str] = None) -> None:
        """
        初始化模板引擎。

        Args:
            template_dir: 模板文件目录路径
        """
        self.template_dir: Path = Path(template_dir) if template_dir else Path.cwd()
        self._cache: dict[str, Template] = {}

    def render(self, template_str: str, **kwargs: Any) -> str:
        """
        渲染模板字符串。

        Args:
            template_str: 包含$变量的模板字符串
            **kwargs: 模板变量键值对

        Returns:
            渲染后的字符串
        """
        template = Template(template_str)
        return template.safe_substitute(**kwargs)

    def render_file(self, filename: str, **kwargs: Any) -> str:
        """
        从文件加载并渲染模板。

        Args:
            filename: 模板文件名
            **kwargs: 模板变量

        Returns:
            渲染后的HTML内容

        Raises:
            FileNotFoundError: 模板文件不存在
        """
        filepath = self.template_dir / filename

        if filename not in self._cache:
            if not filepath.exists():
                raise FileNotFoundError(f"模板文件不存在: {filepath}")
            self._cache[filename] = Template(filepath.read_text(encoding='utf-8'))

        return self._cache[filename].safe_substitute(**kwargs)


# ============================================================================
# 第二部分：HTML页面生成器
# ============================================================================

class HTMLGenerator:
    """
    HTML页面生成器，用于动态生成Web页面。

    演示如何在Python中构建HTML响应，对应前端HTML基础知识。
    """

    # 基础页面模板
    BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               line-height: 1.6; color: #333; background: #f5f5f5; }
        .container { max-width: 960px; margin: 0 auto; padding: 20px; }
        header { background: #2c3e50; color: white; padding: 20px 0; text-align: center; }
        nav { background: #34495e; padding: 10px 0; }
        nav a { color: white; text-decoration: none; padding: 10px 20px; }
        nav a:hover { background: #2c3e50; }
        .card { background: white; border-radius: 8px; padding: 20px; margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
        .btn { display: inline-block; padding: 10px 20px; border: none; border-radius: 4px;
               cursor: pointer; text-decoration: none; color: white; }
        .btn-primary { background: #3498db; }
        .btn-success { background: #2ecc71; }
        .btn-danger { background: #e74c3c; }
        footer { text-align: center; padding: 20px; color: #666; margin-top: 40px; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>$title</h1>
            <p>$subtitle</p>
        </div>
    </header>
    <nav>
        <div class="container">
            <a href="/">首页</a>
            <a href="/products">产品列表</a>
            <a href="/api/data">API数据</a>
            <a href="/about">关于</a>
        </div>
    </nav>
    <main class="container">
        $content
    </main>
    <footer>
        <div class="container">
            <p>Python http.server 演示 | $year</p>
        </div>
    </footer>
</body>
</html>"""

    @staticmethod
    def generate_product_table(products: list[dict[str, Any]]) -> str:
        """
        生成产品库存表格HTML。

        对应文档中的Vue.js库存管理示例，这里用Python服务端渲染实现。

        Args:
            products: 产品数据列表

        Returns:
            HTML表格字符串
        """
        rows = ""
        for product in products:
            status = '<span style="color: red;">已售罄</span>' if product['quantity'] == 0 else f"{product['quantity']}台"
            rows += f"""
            <tr>
                <td>{product['id']}</td>
                <td>{product['name']}</td>
                <td>{status}</td>
                <td><a href="/api/products/{product['id']}" class="btn btn-primary">详情</a></td>
            </tr>"""

        total = sum(p['quantity'] for p in products)

        return f"""
        <div class="card">
            <h2>库存信息</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>产品名称</th>
                        <th>库存数量</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <p style="margin-top: 20px;"><strong>库存总量：{total}台</strong></p>
        </div>"""

    @classmethod
    def render_page(cls, title: str, subtitle: str, content: str) -> str:
        """
        渲染完整页面。

        Args:
            title: 页面标题
            subtitle: 副标题
            content: 主要内容HTML

        Returns:
            完整HTML页面
        """
        return Template(cls.BASE_TEMPLATE).safe_substitute(
            title=title,
            subtitle=subtitle,
            content=content,
            year=datetime.now().year
        )


# ============================================================================
# 第三部分：路由系统
# ============================================================================

@dataclass
class Route:
    """
    路由数据类，存储URL路径与处理函数的映射关系。

    Attributes:
        path: URL路径模式
        handler: 处理函数
        methods: 允许的HTTP方法
    """
    path: str
    handler: Callable[..., tuple[str, int]]
    methods: list[str] = field(default_factory=lambda: ['GET'])


class Router:
    """
    简易路由器，实现URL到处理函数的映射。

    这是Web框架（如Flask、Django）路由系统的基础概念。

    用法:
        router = Router()

        @router.route('/')
        def index():
            return '<h1>首页</h1>', 200
    """

    def __init__(self) -> None:
        self._routes: list[Route] = []
        self._before_request: list[Callable[[], None]] = []
        self._after_request: list[Callable[[str], str]] = []

    def route(self, path: str, methods: Optional[list[str]] = None) -> Callable:
        """
        路由装饰器。

        Args:
            path: URL路径
            methods: HTTP方法列表

        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            self._routes.append(Route(
                path=path,
                handler=func,
                methods=methods or ['GET']
            ))
            return func
        return decorator

    def before_request(self, func: Callable) -> Callable:
        """注册请求前钩子。"""
        self._before_request.append(func)
        return func

    def after_request(self, func: Callable[[str], str]) -> Callable:
        """注册请求后钩子。"""
        self._after_request.append(func)
        return func

    def match(self, path: str, method: str) -> Optional[tuple[Callable, dict[str, str]]]:
        """
        匹配请求路径。

        支持简单的路径参数，如 /products/<id>

        Args:
            path: 请求路径
            method: HTTP方法

        Returns:
            (handler, params) 元组，未匹配返回None
        """
        for route in self._routes:
            if method not in route.methods:
                continue

            # 简单路径匹配
            if route.path == path:
                return route.handler, {}

            # 支持 <param> 形式的路径参数
            if '<' in route.path:
                route_parts = route.path.split('/')
                path_parts = path.split('/')

                if len(route_parts) == len(path_parts):
                    params: dict[str, str] = {}
                    match = True

                    for rp, pp in zip(route_parts, path_parts):
                        if rp.startswith('<') and rp.endswith('>'):
                            params[rp[1:-1]] = pp
                        elif rp != pp:
                            match = False
                            break

                    if match:
                        return route.handler, params

        return None


# ============================================================================
# 第四部分：请求处理器
# ============================================================================

class WebRequestHandler(BaseHTTPRequestHandler):
    """
    自定义HTTP请求处理器。

    继承BaseHTTPRequestHandler，实现：
    - 路由分发
    - 静态文件服务
    - JSON API响应
    - 错误处理

    C++对比：
    - Python: 一个类处理所有请求，简洁但单线程
    - C++ libmicrohttpd: 回调函数模式，支持并发
    """

    router: Router = Router()
    template_engine: TemplateEngine = TemplateEngine()
    static_dir: str = 'static'

    def do_GET(self) -> None:
        """处理GET请求。"""
        self._handle_request('GET')

    def do_POST(self) -> None:
        """处理POST请求。"""
        self._handle_request('POST')

    def _handle_request(self, method: str) -> None:
        """
        统一请求处理入口。

        Args:
            method: HTTP方法
        """
        # 解析URL
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 执行请求前钩子
        for hook in self.router._before_request:
            hook()

        # 尝试路由匹配
        result = self.router.match(path, method)

        if result:
            handler, params = result
            try:
                # 合并路径参数和查询参数
                response_content, status_code = handler(**params, **query)

                # 执行请求后钩子
                for hook in self.router._after_request:
                    response_content = hook(response_content)

                self._send_response(response_content, status_code)
            except Exception as e:
                self._send_error(500, str(e))
        elif self._serve_static(path):
            # 尝试作为静态文件服务
            pass
        else:
            self._send_error(404, f"页面未找到: {path}")

    def _serve_static(self, path: str) -> bool:
        """
        静态文件服务。

        支持CSS、JavaScript、图片等静态资源。

        Args:
            path: 请求路径

        Returns:
            是否成功提供静态文件
        """
        # 移除路径开头的斜杠
        rel_path = path.lstrip('/')
        file_path = Path(self.static_dir) / rel_path

        if file_path.exists() and file_path.is_file():
            # 猜测MIME类型
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = 'application/octet-stream'

            content = file_path.read_bytes()

            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return True

        return False

    def _send_response(self, content: str, status_code: int = 200) -> None:
        """
        发送HTTP响应。

        Args:
            content: 响应内容
            status_code: HTTP状态码
        """
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _send_json(self, data: Any, status_code: int = 200) -> None:
        """
        发送JSON响应。

        Args:
            data: 要序列化的数据
            status_code: HTTP状态码
        """
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _send_error(self, status_code: int, message: str) -> None:
        """
        发送错误响应。

        Args:
            status_code: HTTP状态码
            message: 错误信息
        """
        error_html = HTMLGenerator.render_page(
            title=f"错误 {status_code}",
            subtitle=message,
            content=f"""
            <div class="card" style="text-align: center;">
                <h2>{status_code}</h2>
                <p>{message}</p>
                <a href="/" class="btn btn-primary" style="margin-top: 20px;">返回首页</a>
            </div>"""
        )
        self._send_response(error_html, status_code)

    def log_message(self, format: str, *args: Any) -> None:
        """自定义日志格式。"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sys.stderr.write(f"[{timestamp}] {format % args}\n")


# ============================================================================
# 第五部分：应用配置
# ============================================================================

@dataclass
class AppConfig:
    """
    应用配置数据类。

    Attributes:
        host: 服务器主机地址
        port: 服务器端口
        debug: 调试模式
        static_dir: 静态文件目录
        template_dir: 模板文件目录
    """
    host: str = 'localhost'
    port: int = 8000
    debug: bool = True
    static_dir: str = 'static'
    template_dir: str = 'templates'

    @property
    def server_address(self) -> tuple[str, int]:
        """获取服务器地址元组。"""
        return (self.host, self.port)


# ============================================================================
# 第六部分：示例数据
# ============================================================================

PRODUCTS: list[dict[str, Any]] = [
    {"id": 1, "name": "iPhone 15 Pro", "quantity": 20, "price": 8999},
    {"id": 2, "name": "华为 Mate 60", "quantity": 0, "price": 6999},
    {"id": 3, "name": "小米 14", "quantity": 50, "price": 3999},
    {"id": 4, "name": "三星 Galaxy S24", "quantity": 15, "price": 7499},
    {"id": 5, "name": "OPPO Find X7", "quantity": 30, "price": 5999},
]


# ============================================================================
# 第七部分：路由处理器
# ============================================================================

router = WebRequestHandler.router


@router.route('/')
def index_handler(**kwargs: Any) -> tuple[str, int]:
    """
    首页处理器。

    展示欢迎信息和系统概览。
    """
    content = """
    <div class="card">
        <h2>欢迎来到Python Web服务器演示</h2>
        <p>本项目演示了如何使用Python内置的http.server模块构建Web应用。</p>
        <h3 style="margin-top: 20px;">功能特性</h3>
        <ul style="margin-left: 20px; margin-top: 10px;">
            <li>HTTP请求处理</li>
            <li>路由系统</li>
            <li>模板渲染</li>
            <li>静态文件服务</li>
            <li>RESTful API</li>
        </ul>
        <h3 style="margin-top: 20px;">快速链接</h3>
        <div style="margin-top: 10px;">
            <a href="/products" class="btn btn-primary">查看产品</a>
            <a href="/api/products" class="btn btn-success">API文档</a>
        </div>
    </div>

    <div class="card">
        <h2>技术对比</h2>
        <table>
            <thead>
                <tr>
                    <th>特性</th>
                    <th>Python http.server</th>
                    <th>C++ libmicrohttpd</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>依赖</td>
                    <td>标准库，零依赖</td>
                    <td>需要编译安装</td>
                </tr>
                <tr>
                    <td>性能</td>
                    <td>中等，适合开发测试</td>
                    <td>高，适合生产环境</td>
                </tr>
                <tr>
                    <td>并发</td>
                    <td>单线程（可扩展）</td>
                    <td>原生多线程</td>
                </tr>
                <tr>
                    <td>学习曲线</td>
                    <td>简单</td>
                    <td>较陡</td>
                </tr>
                <tr>
                    <td>开发效率</td>
                    <td>高</td>
                    <td>中等</td>
                </tr>
            </tbody>
        </table>
    </div>"""

    return HTMLGenerator.render_page(
        title="Python Web服务器",
        subtitle="基于http.server的Web应用演示",
        content=content
    ), 200


@router.route('/products')
def products_handler(**kwargs: Any) -> tuple[str, int]:
    """
    产品列表处理器。

    展示产品库存信息，对应文档中的Vue.js库存管理示例。
    """
    table_html = HTMLGenerator.generate_product_table(PRODUCTS)

    return HTMLGenerator.render_page(
        title="产品管理",
        subtitle="产品库存信息",
        content=table_html
    ), 200


@router.route('/about')
def about_handler(**kwargs: Any) -> tuple[str, int]:
    """关于页面处理器。"""
    content = """
    <div class="card">
        <h2>关于本项目</h2>
        <p>本项目是Python-100-Days学习计划的一部分，用于演示Web前端基础知识。</p>

        <h3 style="margin-top: 20px;">学习目标</h3>
        <ul style="margin-left: 20px; margin-top: 10px;">
            <li>理解HTTP协议基础</li>
            <li>掌握Python Web服务器开发</li>
            <li>了解前端渲染与后端渲染的区别</li>
            <li>学习RESTful API设计</li>
        </ul>

        <h3 style="margin-top: 20px;">前端框架参考</h3>
        <ul style="margin-left: 20px; margin-top: 10px;">
            <li>Vue.js - 渐进式JavaScript框架</li>
            <li>Element - 基于Vue的UI组件库</li>
            <li>ECharts - 数据可视化库</li>
            <li>Bulma - Flexbox CSS框架</li>
            <li>Bootstrap - 响应式布局框架</li>
        </ul>
    </div>"""

    return HTMLGenerator.render_page(
        title="关于",
        subtitle="项目说明",
        content=content
    ), 200


# ============================================================================
# 第八部分：API端点
# ============================================================================

@router.route('/api/products', methods=['GET'])
def api_products_handler(**kwargs: Any) -> tuple[str, int]:
    """
    产品API端点。

    返回JSON格式的产品数据，供前端JavaScript使用。
    对应文档中Vue.js通过fetch获取数据的示例。
    """
    # 注意：这里返回JSON字符串，实际应用中应使用专门的JSON响应方法
    return json.dumps({
        "status": "success",
        "data": PRODUCTS,
        "total": len(PRODUCTS),
        "timestamp": datetime.now().isoformat()
    }, ensure_ascii=False), 200


@router.route('/api/products/<id>', methods=['GET'])
def api_product_detail_handler(id: str = '', **kwargs: Any) -> tuple[str, int]:
    """
    单个产品详情API。

    Args:
        id: 产品ID
    """
    product = next((p for p in PRODUCTS if str(p['id']) == id), None)

    if product:
        return json.dumps({
            "status": "success",
            "data": product
        }, ensure_ascii=False), 200
    else:
        return json.dumps({
            "status": "error",
            "message": f"产品ID {id} 不存在"
        }, ensure_ascii=False), 404


@router.route('/api/data', methods=['GET'])
def api_data_handler(**kwargs: Any) -> tuple[str, int]:
    """
    数据统计API。

    返回库存统计数据，可用于ECharts等可视化库。
    """
    total_quantity = sum(p['quantity'] for p in PRODUCTS)
    out_of_stock = sum(1 for p in PRODUCTS if p['quantity'] == 0)

    return json.dumps({
        "status": "success",
        "statistics": {
            "total_products": len(PRODUCTS),
            "total_quantity": total_quantity,
            "out_of_stock": out_of_stock,
            "in_stock": len(PRODUCTS) - out_of_stock
        },
        "chart_data": [
            {"name": p['name'], "value": p['quantity']}
            for p in PRODUCTS
        ]
    }, ensure_ascii=False), 200


# ============================================================================
# 第九部分：中间件和钩子
# ============================================================================

@router.before_request
def log_request() -> None:
    """请求前日志记录。"""
    pass  # 日志已在log_message中处理


@router.after_request
def add_server_header(response: str) -> str:
    """响应后处理，可添加额外信息。"""
    return response


# ============================================================================
# 第十部分：服务器工厂
# ============================================================================

class WebServerFactory:
    """
    Web服务器工厂类。

    提供创建不同类型服务器的便捷方法。

    企业级应用场景：
    - 开发服务器：用于本地开发和调试
    - 静态文件服务器：用于前端资源托管
    - API服务器：提供RESTful接口
    """

    @staticmethod
    def create_development_server(
        config: Optional[AppConfig] = None
    ) -> HTTPServer:
        """
        创建开发服务器。

        开发服务器特点：
        - 启用详细日志
        - 支持热重载（需额外实现）
        - 错误页面显示详细信息

        Args:
            config: 应用配置

        Returns:
            HTTPServer实例
        """
        if config is None:
            config = AppConfig(debug=True)

        server = HTTPServer(config.server_address, WebRequestHandler)
        return server

    @staticmethod
    def create_static_file_server(
        directory: str,
        port: int = 8080
    ) -> HTTPServer:
        """
        创建静态文件服务器。

        用于托管前端资源（HTML、CSS、JavaScript、图片等）。

        Args:
            directory: 静态文件目录
            port: 监听端口

        Returns:
            HTTPServer实例
        """
        class StaticHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, directory=directory, **kwargs)

        server = HTTPServer(('localhost', port), StaticHandler)
        return server

    @staticmethod
    def create_api_server(
        config: Optional[AppConfig] = None
    ) -> HTTPServer:
        """
        创建API服务器。

        专门用于提供RESTful API接口。

        Args:
            config: 应用配置

        Returns:
            HTTPServer实例
        """
        if config is None:
            config = AppConfig(port=5000)

        server = HTTPServer(config.server_address, WebRequestHandler)
        return server


# ============================================================================
# 第十一部分：多线程服务器扩展
# ============================================================================

class ThreadedHTTPServer(HTTPServer):
    """
    多线程HTTP服务器。

    Python标准库的HTTPServer默认是单线程的，
    这里通过混入ThreadingMixIn实现并发处理。

    C++对比：
    - Python: 需要手动添加线程支持
    - C++ libmicrohttpd: 内置线程池支持
    """

    import socketserver
    allow_reuse_address = True

    def process_request(
        self, request: Any, client_address: tuple[str, int]
    ) -> None:
        """多线程处理请求。"""
        import threading
        thread = threading.Thread(
            target=self.process_request_thread,
            args=(request, client_address)
        )
        thread.daemon = True
        thread.start()

    def process_request_thread(
        self, request: Any, client_address: tuple[str, int]
    ) -> None:
        """线程中处理请求。"""
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


# ============================================================================
# 第十二部分：演示函数
# ============================================================================

def demo_template_rendering() -> None:
    """
    演示模板渲染功能。
    """
    print("=" * 60)
    print("模板渲染演示")
    print("=" * 60)

    engine = TemplateEngine()

    # 基础变量替换
    result = engine.render(
        "<h1>$title</h1><p>欢迎, $name!</p>",
        title="首页",
        name="Python开发者"
    )
    print(f"\n基础渲染结果:\n{result}")

    # 列表渲染
    items = ['HTML', 'CSS', 'JavaScript']
    list_html = ''.join(f'<li>{item}</li>' for item in items)
    result = engine.render(
        "<ul>$items</ul>",
        items=list_html
    )
    print(f"\n列表渲染结果:\n{result}")


def demo_html_generation() -> None:
    """
    演示HTML生成功能。
    """
    print("\n" + "=" * 60)
    print("HTML生成演示")
    print("=" * 60)

    page = HTMLGenerator.render_page(
        title="测试页面",
        subtitle="HTML生成器演示",
        content="<div class='card'><p>这是动态生成的内容</p></div>"
    )
    print(f"\n生成的HTML长度: {len(page)} 字符")
    print(f"包含标题标签: {'<title>测试页面</title>' in page}")


def demo_routing() -> None:
    """
    演示路由系统。
    """
    print("\n" + "=" * 60)
    print("路由系统演示")
    print("=" * 60)

    test_router = Router()

    @test_router.route('/')
    def home() -> tuple[str, int]:
        return "首页", 200

    @test_router.route('/users/<id>')
    def user_detail(id: str = '') -> tuple[str, int]:
        return f"用户 {id}", 200

    # 测试路由匹配
    test_cases = ['/', '/users/42', '/notfound']

    for path in test_cases:
        result = test_router.match(path, 'GET')
        if result:
            handler, params = result
            response, status = handler(**params)
            print(f"  {path} -> {response} (状态码: {status})")
        else:
            print(f"  {path} -> 404 未找到")


def demo_server_info() -> None:
    """
    显示服务器信息。
    """
    print("\n" + "=" * 60)
    print("服务器信息")
    print("=" * 60)

    config = AppConfig()
    print(f"\n主机: {config.host}")
    print(f"端口: {config.port}")
    print(f"调试模式: {config.debug}")
    print(f"访问地址: http://{config.host}:{config.port}")


def run_server(
    host: str = 'localhost',
    port: int = 8000,
    threaded: bool = False
) -> None:
    """
    运行Web服务器。

    Args:
        host: 监听地址
        port: 监听端口
        threaded: 是否使用多线程
    """
    config = AppConfig(host=host, port=port)

    if threaded:
        server = ThreadedHTTPServer(config.server_address, WebRequestHandler)
        print(f"多线程服务器启动于 http://{host}:{port}")
    else:
        server = HTTPServer(config.server_address, WebRequestHandler)
        print(f"单线程服务器启动于 http://{host}:{port}")

    print("按 Ctrl+C 停止服务器")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == '__main__':
    print("Python Web前端基础 - http.server演示")
    print("=" * 60)

    # 运行演示
    demo_template_rendering()
    demo_html_generation()
    demo_routing()
    demo_server_info()

    print("\n" + "=" * 60)
    print("启动说明")
    print("=" * 60)
    print("""
使用方法：
  1. 直接运行: python 32_web_frontend.py
  2. 启动服务器: 在代码中调用 run_server()

可用路由：
  /           - 首页
  /products   - 产品列表
  /about      - 关于页面
  /api/products     - 产品API (JSON)
  /api/products/<id> - 产品详情API
  /api/data   - 数据统计API

C++对比要点：
  - Python http.server: 内置标准库，开发快速，适合原型开发
  - C++ libmicrohttpd: 高性能，适合高并发生产环境

企业级建议：
  - 开发环境: 使用Python http.server
  - 生产环境: 考虑Gunicorn + Flask/Django
  - 高性能场景: 考虑C++/Go/Rust实现
""")

    # 取消注释以下行以启动服务器
    # run_server(host='localhost', port=8000)
