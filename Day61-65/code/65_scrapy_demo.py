"""
Scrapy 爬虫框架简介 - 核心组件演示
====================================
本模块演示 Scrapy 框架的核心架构，包括 Spider（蜘蛛程序）和 Pipeline（数据管道），
并通过一个企业级电商爬虫示例展示实际应用场景。

Scrapy 架构核心组件:
    1. Engine（引擎）     - 控制整个系统的数据处理流程
    2. Scheduler（调度器）- 管理请求队列
    3. Downloader（下载器）- 抓取网页内容
    4. Spiders（蜘蛛）    - 定义抓取和解析规则
    5. Pipeline（管道）   - 清洗、验证、存储数据
    6. Middlewares（中间件）- 扩展框架功能

数据处理流程:
    Spider 产出 Request -> Engine 交给 Scheduler 排队
    -> Engine 取出 Request -> Downloader 下载
    -> Response 交给 Spider 解析 -> 产出 Item
    -> Item 交给 Pipeline 处理（清洗/去重/存储）
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Generator, Optional
from urllib.parse import urljoin

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

LOG_FORMAT: str = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("scrapy_demo")


# ===========================================================================
# Part 1: Item 数据模型 - 定义爬取数据的结构
# ===========================================================================

@dataclass
class ProductItem:
    """电商商品数据模型，对应 Scrapy 中的 Item。

    Attributes:
        product_id:  商品唯一标识
        title:       商品标题
        price:       商品价格（单位：元）
        rating:      用户评分（0.0 ~ 5.0）
        review_count: 评论数量
        category:    商品分类
        url:         商品详情页 URL
        image_url:   商品主图 URL
        timestamp:   爬取时间戳
    """

    product_id: str = ""
    title: str = ""
    price: float = 0.0
    rating: float = 0.0
    review_count: int = 0
    category: str = ""
    url: str = ""
    image_url: str = ""
    timestamp: float = field(default_factory=time.time)

    def is_valid(self) -> bool:
        """验证商品数据是否完整有效。"""
        return bool(self.product_id and self.title and self.price > 0)


# ===========================================================================
# Part 2: Pipeline 数据管道 - 数据清洗、去重与持久化
# ===========================================================================

class BasePipeline(ABC):
    """数据管道基类，定义管道的标准接口。

    每个 Pipeline 组件都是一个 Python 类，获取数据条目并执行处理，
    同时决定是否继续传递给下一个管道。
    """

    @abstractmethod
    def open_spider(self, spider_name: str) -> None:
        """爬虫启动时调用，用于初始化资源。"""

    @abstractmethod
    def process_item(self, item: ProductItem, spider_name: str) -> Optional[ProductItem]:
        """处理单个数据条目。返回 None 表示丢弃该条目。"""

    @abstractmethod
    def close_spider(self, spider_name: str) -> None:
        """爬虫结束时调用，用于释放资源。"""


class CleaningPipeline(BasePipeline):
    """数据清洗管道 - 清理 HTML 标签、规范化字段值。

    职责:
        - 去除标题中的 HTML 实体和多余空白
        - 确保价格为正浮点数
        - 限制评分在 [0, 5] 范围内
    """

    def open_spider(self, spider_name: str) -> None:
        logger.info("[CleaningPipeline] 爬虫 '%s' 启动，开始数据清洗。", spider_name)

    def process_item(self, item: ProductItem, spider_name: str) -> Optional[ProductItem]:
        # 清理标题：去除 HTML 标签和多余空白
        item.title = re.sub(r"<[^>]+>", "", item.title).strip()
        item.title = re.sub(r"\s+", " ", item.title)

        # 规范化价格
        if item.price < 0:
            logger.warning("[CleaningPipeline] 商品 %s 价格异常 (%.2f)，已修正为 0。", item.product_id, item.price)
            item.price = 0.0

        # 规范化评分
        item.rating = max(0.0, min(5.0, item.rating))

        logger.debug("[CleaningPipeline] 已清洗商品: %s", item.title[:30])
        return item

    def close_spider(self, spider_name: str) -> None:
        logger.info("[CleaningPipeline] 爬虫 '%s' 结束。", spider_name)


class DeduplicationPipeline(BasePipeline):
    """去重管道 - 基于 product_id 去除重复商品。

    职责:
        - 检查商品是否已爬取过
        - 丢弃重复数据，避免冗余存储
    """

    def __init__(self) -> None:
        self._seen_ids: set[str] = set()
        self._duplicate_count: int = 0

    def open_spider(self, spider_name: str) -> None:
        self._seen_ids.clear()
        self._duplicate_count = 0
        logger.info("[DeduplicationPipeline] 爬虫 '%s' 启动，初始化去重集合。", spider_name)

    def process_item(self, item: ProductItem, spider_name: str) -> Optional[ProductItem]:
        if item.product_id in self._seen_ids:
            self._duplicate_count += 1
            logger.debug("[DeduplicationPipeline] 发现重复商品: %s，已丢弃。", item.product_id)
            return None
        self._seen_ids.add(item.product_id)
        return item

    def close_spider(self, spider_name: str) -> None:
        logger.info(
            "[DeduplicationPipeline] 爬虫 '%s' 结束。共发现 %d 个重复商品。",
            spider_name, self._duplicate_count,
        )


class ValidationPipeline(BasePipeline):
    """验证管道 - 检查必要字段是否完整。

    职责:
        - 确保商品数据包含必要字段（product_id, title, price）
        - 丢弃不完整的数据条目
    """

    def __init__(self) -> None:
        self._invalid_count: int = 0

    def open_spider(self, spider_name: str) -> None:
        self._invalid_count = 0
        logger.info("[ValidationPipeline] 爬虫 '%s' 启动。", spider_name)

    def process_item(self, item: ProductItem, spider_name: str) -> Optional[ProductItem]:
        if not item.is_valid():
            self._invalid_count += 1
            logger.warning(
                "[ValidationPipeline] 商品数据不完整 (id=%s, title=%s)，已丢弃。",
                item.product_id, item.title[:20] if item.title else "N/A",
            )
            return None
        return item

    def close_spider(self, spider_name: str) -> None:
        logger.info(
            "[ValidationPipeline] 爬虫 '%s' 结束。共丢弃 %d 条无效数据。",
            spider_name, self._invalid_count,
        )


class SQLitePipeline(BasePipeline):
    """SQLite 持久化管道 - 将商品数据写入 SQLite 数据库。

    职责:
        - 创建数据库表（如不存在）
        - 批量插入或更新商品记录
        - 爬虫结束时提交事务并关闭连接
    """

    def __init__(self, db_path: str = "products.db") -> None:
        self._db_path: str = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._cursor: Optional[sqlite3.Cursor] = None
        self._item_count: int = 0

    def open_spider(self, spider_name: str) -> None:
        self._conn = sqlite3.connect(self._db_path)
        self._cursor = self._conn.cursor()
        self._item_count = 0
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id   TEXT PRIMARY KEY,
                title        TEXT NOT NULL,
                price        REAL NOT NULL,
                rating       REAL DEFAULT 0.0,
                review_count INTEGER DEFAULT 0,
                category     TEXT DEFAULT '',
                url          TEXT DEFAULT '',
                image_url    TEXT DEFAULT '',
                timestamp    REAL
            )
        """)
        self._conn.commit()
        logger.info("[SQLitePipeline] 爬虫 '%s' 启动，数据库: %s", spider_name, self._db_path)

    def process_item(self, item: ProductItem, spider_name: str) -> Optional[ProductItem]:
        assert self._cursor is not None
        self._cursor.execute("""
            INSERT OR REPLACE INTO products
            (product_id, title, price, rating, review_count, category, url, image_url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.product_id, item.title, item.price, item.rating,
            item.review_count, item.category, item.url, item.image_url, item.timestamp,
        ))
        self._item_count += 1
        return item

    def close_spider(self, spider_name: str) -> None:
        if self._conn:
            self._conn.commit()
            self._conn.close()
        logger.info("[SQLitePipeline] 爬虫 '%s' 结束。共写入 %d 条记录到 %s。", spider_name, self._item_count, self._db_path)


class JSONExportPipeline(BasePipeline):
    """JSON 导出管道 - 将爬取结果导出为 JSON 文件。"""

    def __init__(self, output_file: str = "products.json") -> None:
        self._output_file: str = output_file
        self._items: list[dict[str, Any]] = []

    def open_spider(self, spider_name: str) -> None:
        self._items.clear()
        logger.info("[JSONExportPipeline] 爬虫 '%s' 启动。", spider_name)

    def process_item(self, item: ProductItem, spider_name: str) -> Optional[ProductItem]:
        self._items.append(asdict(item))
        return item

    def close_spider(self, spider_name: str) -> None:
        with open(self._output_file, "w", encoding="utf-8") as f:
            json.dump(self._items, f, ensure_ascii=False, indent=2)
        logger.info("[JSONExportPipeline] 爬虫 '%s' 结束。已导出 %d 条记录到 %s。", spider_name, len(self._items), self._output_file)


# ===========================================================================
# Part 3: Spider 蜘蛛程序 - 定义抓取和解析规则
# ===========================================================================

class BaseSpider(ABC):
    """蜘蛛程序基类，模拟 Scrapy Spider 的核心接口。

    Scrapy 中的 Spider 是用户自定义的类，用于：
        - 定义起始 URL
        - 解析响应内容
        - 提取结构化数据
        - 跟踪链接进行深度爬取
    """

    name: str = "base"
    allowed_domains: list[str] = []
    start_urls: list[str] = []

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"spider.{self.name}")

    @abstractmethod
    def parse(self, response_text: str, url: str) -> Generator[ProductItem | dict[str, str], None, None]:
        """解析页面响应，产出 Item 或新的请求。

        Args:
            response_text: 页面 HTML 内容
            url: 当前页面 URL

        Yields:
            ProductItem 实例或包含待爬 URL 的字典
        """

    def start_requests(self) -> Generator[dict[str, str], None, None]:
        """生成初始请求。默认使用 start_urls。"""
        for url in self.start_urls:
            yield {"url": url, "callback": "parse"}

    def __repr__(self) -> str:
        return f"<Spider '{self.name}' domains={self.allowed_domains}>"


class EcommerceSpider(BaseSpider):
    """企业级电商爬虫 - 爬取商品列表页和详情页。

    演示了 Scrapy Spider 的关键特性:
        1. start_requests - 生成初始请求
        2. parse         - 解析列表页，提取商品概要并跟踪详情链接
        3. parse_detail  - 解析详情页，提取完整商品信息
        4. yield Item    - 将数据交给 Pipeline 处理
        5. yield Request - 跟踪新链接进行深度爬取

    适用场景:
        - 电商平台商品数据采集
        - 价格监控与竞品分析
        - 商品评论聚合
    """

    name: str = "ecommerce"
    allowed_domains: list[str] = ["example-shop.com"]
    start_urls: list[str] = [
        "https://example-shop.com/category/phones?page=1",
        "https://example-shop.com/category/laptops?page=1",
    ]

    def __init__(self, max_pages: int = 3) -> None:
        super().__init__()
        self.max_pages: int = max_pages
        self._page_counters: dict[str, int] = {}

    def start_requests(self) -> Generator[dict[str, str], None, None]:
        """生成初始请求，支持分页爬取。"""
        for url in self.start_urls:
            self.logger.info("[Spider] 发起初始请求: %s", url)
            yield {"url": url, "callback": "parse"}

    def _simulate_response(self, url: str) -> str:
        """模拟服务器响应（实际项目中由 Scrapy 引擎的 Downloader 完成）。"""
        category = "phones" if "phones" in url else "laptops"
        page_match = re.search(r"page=(\d+)", url)
        page = int(page_match.group(1)) if page_match else 1
        items_html = []
        for i in range(1, 4):  # 模拟每页 3 个商品
            pid = f"{category}_{page}_{i}"
            price = 2999.0 + i * 500 + page * 100
            rating = round(3.5 + i * 0.3, 1)
            items_html.append(
                f'<div class="product-card" data-id="{pid}">'
                f'  <h2 class="product-title">品牌{i} {category.title()} 第{page}页</h2>'
                f'  <span class="price">¥{price:.2f}</span>'
                f'  <span class="rating">{rating}</span>'
                f'  <span class="reviews">{100 * i + page * 10}条评价</span>'
                f'  <a href="/product/{pid}" class="detail-link">查看详情</a>'
                f'  <img src="https://img.example.com/{pid}.jpg" />'
                f'</div>'
            )
        pagination = ""
        if page < self.max_pages:
            next_page = re.sub(r"page=\d+", f"page={page + 1}", url)
            pagination = f'<div class="pagination"><a href="{next_page}">下一页</a></div>'
        return f"<html><body>{''.join(items_html)}{pagination}</body></html>"

    def parse(self, response_text: str, url: str) -> Generator[ProductItem | dict[str, str], None, None]:
        """解析商品列表页。

        提取商品概要信息，并跟踪商品详情链接和分页链接。
        """
        self.logger.info("[Spider] 正在解析列表页: %s", url)

        # 提取商品卡片（模拟 CSS 选择器: '.product-card'）
        card_pattern = re.compile(
            r'<div class="product-card" data-id="([^"]+)">'
            r'.*?<h2 class="product-title">([^<]+)</h2>'
            r'.*?<span class="price">¥([\d.]+)</span>'
            r'.*?<span class="rating">([\d.]+)</span>'
            r'.*?<span class="reviews">(\d+)条评价</span>'
            r'.*?<a href="([^"]+)" class="detail-link">查看详情</a>'
            r'.*?<img src="([^"]+)"',
            re.DOTALL,
        )

        for match in card_pattern.finditer(response_text):
            pid, title, price, rating, reviews, detail_path, img_url = match.groups()

            # 产出详情页请求（模拟 yield Request）
            detail_url = urljoin(url, detail_path)
            self.logger.debug("[Spider] 发现商品 %s，跟踪详情页: %s", pid, detail_url)
            yield {"url": detail_url, "callback": "parse_detail", "meta": {"product_id": pid, "category": url}}

            # 同时产出列表页的概要 Item
            yield ProductItem(
                product_id=pid,
                title=title.strip(),
                price=float(price),
                rating=float(rating),
                review_count=int(reviews),
                category="phones" if "phones" in url else "laptops",
                url=detail_url,
                image_url=img_url,
            )

        # 跟踪分页链接（模拟 CSS 选择器: '.pagination a::attr(href)'）
        page_pattern = re.compile(r'<a href="([^"]+)">下一页</a>')
        for match in page_pattern.finditer(response_text):
            next_url = urljoin(url, match.group(1))
            current_page = self._page_counters.get(url, 1)
            if current_page < self.max_pages:
                self._page_counters[next_url] = current_page + 1
                self.logger.info("[Spider] 跟踪分页链接: %s (第%d页)", next_url, current_page + 1)
                yield {"url": next_url, "callback": "parse"}

    def parse_detail(self, response_text: str, url: str) -> Generator[ProductItem, None, None]:
        """解析商品详情页，提取完整商品信息。"""
        self.logger.info("[Spider] 正在解析详情页: %s", url)

        # 模拟从详情页提取更丰富的数据
        detail_pattern = re.compile(
            r'<div class="product-detail"[^>]*>'
            r'.*?<h1>([^<]+)</h1>'
            r'.*?<span class="detail-price">¥([\d.]+)</span>'
            r'.*?<div class="description">([^<]+)</div>',
            re.DOTALL,
        )

        match = detail_pattern.search(response_text)
        if match:
            title, price, _description = match.groups()
            yield ProductItem(
                product_id=url.split("/")[-1],
                title=title.strip(),
                price=float(price),
            )


# ===========================================================================
# Part 4: Pipeline 管道调度器 - 按优先级串联多个管道
# ===========================================================================

class PipelineManager:
    """管道调度器 - 按优先级依次调用各 Pipeline 组件。

    模拟 Scrapy 引擎的 Pipeline 调度机制:
        1. 爬虫启动时调用所有管道的 open_spider
        2. 每个 Item 按优先级依次经过各管道的 process_item
        3. 如果某管道返回 None，后续管道不再处理该 Item
        4. 爬虫结束时调用所有管道的 close_spider

    Args:
        pipelines: (优先级, Pipeline实例) 的列表，优先级数字越小越先执行
    """

    def __init__(self, pipelines: list[tuple[int, BasePipeline]]) -> None:
        # 按优先级排序（数字小的先执行）
        self._pipelines: list[BasePipeline] = [p for _, p in sorted(pipelines, key=lambda x: x[0])]
        self._processed_count: int = 0
        self._dropped_count: int = 0

    def open_spider(self, spider_name: str) -> None:
        """爬虫启动，依次调用各管道的 open_spider。"""
        logger.info("[PipelineManager] 启动管道链 (共 %d 个管道)。", len(self._pipelines))
        for pipeline in self._pipelines:
            pipeline.open_spider(spider_name)

    def process_item(self, item: ProductItem, spider_name: str) -> Optional[ProductItem]:
        """将 Item 依次通过各管道处理。"""
        current_item: Optional[ProductItem] = item
        for pipeline in self._pipelines:
            if current_item is None:
                break
            current_item = pipeline.process_item(current_item, spider_name)
        if current_item is None:
            self._dropped_count += 1
        else:
            self._processed_count += 1
        return current_item

    def close_spider(self, spider_name: str) -> None:
        """爬虫结束，依次调用各管道的 close_spider。"""
        for pipeline in self._pipelines:
            pipeline.close_spider(spider_name)
        logger.info(
            "[PipelineManager] 管道链执行完毕。处理: %d 条，丢弃: %d 条。",
            self._processed_count, self._dropped_count,
        )


# ===========================================================================
# Part 5: 模拟 Scrapy 引擎 - 串联 Spider 和 Pipeline
# ===========================================================================

class SimpleEngine:
    """简易 Scrapy 引擎 - 模拟核心数据处理流程。

    Scrapy 引擎的数据流:
        1. 引擎询问 Spider 需要处理哪个网站，获取起始 URL
        2. 引擎将 URL 交给调度器排队
        3. 引擎从调度器取出 URL，通过下载器下载页面
        4. 下载器返回响应，引擎交给 Spider 解析
        5. Spider 解析后产出 Item 和新 Request
        6. Item 交给 Pipeline 处理，新 Request 交给调度器
        7. 重复步骤 2-6，直到没有待处理的 URL
    """

    def __init__(self, spider: BaseSpider, pipeline_manager: PipelineManager) -> None:
        self._spider: BaseSpider = spider
        self._pipeline_manager: PipelineManager = pipeline_manager
        self._request_queue: list[dict[str, str]] = []
        self._visited_urls: set[str] = set()

    def _fetch(self, url: str) -> str:
        """模拟下载器 - 获取页面内容。实际项目中由 Scrapy Downloader 完成。"""
        logger.debug("[Engine] 下载器正在获取: %s", url)
        # 在真实 Scrapy 中，Downloader 通过 HTTP 请求获取页面
        # 这里使用 Spider 的模拟方法代替
        return self._spider._simulate_response(url)

    def run(self) -> None:
        """运行爬虫 - 模拟 Scrapy 引擎的完整数据处理流程。"""
        logger.info("=" * 60)
        logger.info("[Engine] Scrapy 引擎启动")
        logger.info("[Engine] 蜘蛛程序: %s", self._spider)
        logger.info("=" * 60)

        # Step 1: 从 Spider 获取初始请求
        for request in self._spider.start_requests():
            self._request_queue.append(request)

        # 启动 Pipeline
        self._pipeline_manager.open_spider(self._spider.name)

        # Step 2-8: 循环处理队列中的请求
        while self._request_queue:
            request = self._request_queue.pop(0)
            url: str = request["url"]
            callback_name: str = request.get("callback", "parse")

            # 避免重复访问
            if url in self._visited_urls:
                continue
            self._visited_urls.add(url)

            # Step 4-5: 下载页面
            response_text = self._fetch(url)

            # Step 6-7: 调用 Spider 的解析方法
            callback = getattr(self._spider, callback_name)
            results = callback(response_text, url)

            # Step 8: 处理解析结果
            for result in results:
                if isinstance(result, ProductItem):
                    # Item 交给 Pipeline 处理
                    self._pipeline_manager.process_item(result, self._spider.name)
                elif isinstance(result, dict) and "url" in result:
                    # 新的 Request 加入队列
                    if result["url"] not in self._visited_urls:
                        self._request_queue.append(result)

        # 爬虫结束，关闭 Pipeline
        self._pipeline_manager.close_spider(self._spider.name)

        logger.info("=" * 60)
        logger.info("[Engine] Scrapy 引擎停止。共爬取 %d 个页面。", len(self._visited_urls))
        logger.info("=" * 60)


# ===========================================================================
# Part 6: 主程序入口 - 配置并运行爬虫
# ===========================================================================

def create_pipeline_config() -> list[tuple[int, BasePipeline]]:
    """创建并配置数据管道。

    管道执行顺序（按优先级数字从小到大）:
        100 - CleaningPipeline:      数据清洗
        200 - ValidationPipeline:    数据验证
        300 - DeduplicationPipeline: 数据去重
        400 - SQLitePipeline:        持久化到数据库
        500 - JSONExportPipeline:    导出为 JSON 文件

    Returns:
        (优先级, Pipeline实例) 的列表
    """
    return [
        (100, CleaningPipeline()),
        (200, ValidationPipeline()),
        (300, DeduplicationPipeline()),
        (400, SQLitePipeline(db_path="ecommerce_products.db")),
        (500, JSONExportPipeline(output_file="ecommerce_products.json")),
    ]


def main() -> None:
    """主函数 - 配置并运行电商爬虫示例。"""
    logger.info(">>> Scrapy 框架演示 - 企业级电商爬虫 <<<")
    logger.info("")

    # 1. 创建蜘蛛程序
    spider = EcommerceSpider(max_pages=3)
    logger.info("蜘蛛程序: %s", spider)
    logger.info("目标域名: %s", spider.allowed_domains)
    logger.info("起始 URL: %s", spider.start_urls)
    logger.info("")

    # 2. 配置数据管道
    pipelines = create_pipeline_config()
    logger.info("已配置 %d 个数据管道:", len(pipelines))
    for priority, pipeline in pipelines:
        logger.info("  [%d] %s", priority, type(pipeline).__name__)
    logger.info("")

    # 3. 创建管道管理器
    pipeline_manager = PipelineManager(pipelines)

    # 4. 创建引擎并运行
    engine = SimpleEngine(spider, pipeline_manager)
    engine.run()

    logger.info("")
    logger.info(">>> 演示完成 <<<")


if __name__ == "__main__":
    main()
