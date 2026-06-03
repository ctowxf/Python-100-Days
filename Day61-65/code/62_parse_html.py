"""
Day 62 - 用Python解析HTML页面-2
覆盖内容: BeautifulSoup4, CSS选择器, XPath
企业级实战: 新闻爬虫, 价格监控
"""

from __future__ import annotations

import re
import json
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from lxml import etree

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# 通用请求头
HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# 请求超时 (秒)
REQUEST_TIMEOUT: int = 10


# ===================================================================
# Part 1: BeautifulSoup4 与 CSS 选择器基础
# ===================================================================

# 用于演示的示例 HTML 片段
SAMPLE_HTML: str = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>示例商城 - 商品列表</title>
</head>
<body>
    <header id="site-header">
        <h1 class="logo">示例商城</h1>
        <nav>
            <ul class="nav-list">
                <li><a href="/">首页</a></li>
                <li><a href="/products">商品</a></li>
                <li><a href="/about">关于</a></li>
            </ul>
        </nav>
    </header>

    <main id="content">
        <section class="product-grid">
            <div class="product-card" data-id="1001">
                <img src="img/laptop.jpg" alt="笔记本电脑">
                <h2 class="product-name">高性能笔记本电脑</h2>
                <p class="product-desc">16GB内存 / 512GB SSD / 独立显卡</p>
                <span class="price" data-currency="CNY">6999.00</span>
                <span class="stock in-stock">有货</span>
                <a href="/product/1001" class="btn-detail">查看详情</a>
            </div>
            <div class="product-card" data-id="1002">
                <img src="img/phone.jpg" alt="智能手机">
                <h2 class="product-name">旗舰智能手机</h2>
                <p class="product-desc">8GB内存 / 256GB存储 / 5G</p>
                <span class="price" data-currency="CNY">4999.00</span>
                <span class="stock out-of-stock">缺货</span>
                <a href="/product/1002" class="btn-detail">查看详情</a>
            </div>
            <div class="product-card" data-id="1003">
                <img src="img/tablet.jpg" alt="平板电脑">
                <h2 class="product-name">轻薄平板电脑</h2>
                <p class="product-desc">8GB内存 / 128GB存储 / 触控笔</p>
                <span class="price" data-currency="CNY">3299.00</span>
                <span class="stock in-stock">有货</span>
                <a href="/product/1003" class="btn-detail">查看详情</a>
            </div>
            <div class="product-card" data-id="1004">
                <img src="img/headphone.jpg" alt="无线耳机">
                <h2 class="product-name">降噪无线耳机</h2>
                <p class="product-desc">主动降噪 / 30小时续航 / 蓝牙5.3</p>
                <span class="price" data-currency="CNY">899.00</span>
                <span class="stock in-stock">有货</span>
                <a href="/product/1004" class="btn-detail">查看详情</a>
            </div>
        </section>
    </main>

    <footer id="site-footer">
        <p>&copy; 2026 示例商城 版权所有</p>
    </footer>
</body>
</html>
"""


@dataclass
class Product:
    """商品数据模型。"""
    product_id: str
    name: str
    description: str
    price: float
    currency: str
    in_stock: bool
    image_url: str
    detail_url: str


def demo_bs4_css_selector() -> list[Product]:
    """
    演示 BeautifulSoup4 配合 CSS 选择器解析 HTML。

    CSS 选择器速查:
        标签选择器:     tag
        类选择器:       .class
        ID选择器:       #id
        属性选择器:     [attr], [attr=value], [attr^=prefix]
        后代选择器:     ancestor descendant
        子元素选择器:   parent > child
        伪类选择器:     :nth-child(n), :first-child, :last-child
        组合选择器:     selector1, selector2
    """
    logger.info("=== BeautifulSoup4 + CSS 选择器演示 ===")

    soup: BeautifulSoup = BeautifulSoup(SAMPLE_HTML, "lxml")

    # 1. 基本选择器 -------------------------------------------------------
    title_text: str = soup.select_one("title").text.strip()
    logger.info("页面标题 (标签选择器 'title'): %s", title_text)

    logo_text: str = soup.select_one("h1.logo").text.strip()
    logger.info("Logo (类选择器 'h1.logo'): %s", logo_text)

    header_tag: Tag = soup.select_one("#site-header")
    logger.info("Header 标签名 (ID选择器 '#site-header'): %s", header_tag.name)

    # 2. 组合与层级选择器 -------------------------------------------------
    nav_links: list[Tag] = soup.select("nav ul.nav-list li a")
    logger.info("导航链接 (组合选择器):")
    for link in nav_links:
        logger.info("  - %s -> %s", link.text.strip(), link.get("href"))

    # 子元素选择器: 只选直接子元素
    product_cards: list[Tag] = soup.select("section.product-grid > div.product-card")
    logger.info("商品卡片数量 (子元素选择器): %d", len(product_cards))

    # 3. 属性选择器 -------------------------------------------------------
    in_stock_spans: list[Tag] = soup.select("span.stock.in-stock")
    logger.info("有货商品数 (多类选择器 '.stock.in-stock'): %d", len(in_stock_spans))

    cny_prices: list[Tag] = soup.select("span.price[data-currency='CNY']")
    logger.info("人民币价格元素 (属性选择器): %d 个", len(cny_prices))

    # 4. 伪类选择器 -------------------------------------------------------
    first_card: Tag = soup.select_one("div.product-card:nth-child(1)")
    first_name: str = first_card.select_one(".product-name").text.strip()
    logger.info("第一个商品 (伪类 ':nth-child(1)'): %s", first_name)

    last_card: Tag = soup.select_one("div.product-card:last-child")
    last_name: str = last_card.select_one(".product-name").text.strip()
    logger.info("最后一个商品 (伪类 ':last-child'): %s", last_name)

    # 5. 提取结构化商品数据 -----------------------------------------------
    products: list[Product] = []
    for card in product_cards:
        product = Product(
            product_id=str(card.get("data-id", "")),
            name=card.select_one(".product-name").text.strip(),
            description=card.select_one(".product-desc").text.strip(),
            price=float(card.select_one(".price").text.strip()),
            currency=str(card.select_one(".price").get("data-currency", "CNY")),
            in_stock="in-stock" in card.select_one(".stock").get("class", []),
            image_url=str(card.select_one("img").get("src", "")),
            detail_url=str(card.select_one("a.btn-detail").get("href", "")),
        )
        products.append(product)
        logger.info("  解析商品: %s - %.2f %s [%s]",
                     product.name, product.price, product.currency,
                     "有货" if product.in_stock else "缺货")

    return products


# ===================================================================
# Part 2: XPath 基础解析
# ===================================================================

SAMPLE_XML: str = """\
<?xml version="1.0" encoding="UTF-8"?>
<bookstore>
    <book category="fiction">
      <title lang="eng">Harry Potter</title>
      <author>J.K. Rowling</author>
      <price>29.99</price>
    </book>
    <book category="tech">
      <title lang="zh">Learning XML</title>
      <author>Erik T. Ray</author>
      <price>39.95</price>
    </book>
    <book category="tech">
      <title lang="eng">Python Cookbook</title>
      <author>David Beazley</author>
      <price>45.50</price>
    </book>
</bookstore>
"""


def demo_xpath_basics() -> None:
    """演示 XPath 基本语法解析 XML/HTML。"""
    logger.info("=== XPath 基础解析演示 ===")

    tree: etree._Element = etree.HTML(SAMPLE_XML.replace("<?xml version=\"1.0\" encoding=\"UTF-8\"?>", ""))

    # 1. 绝对路径 vs 相对路径
    root_children: list[etree._Element] = tree.xpath("/html/body/bookstore/*")
    logger.info("根节点下子元素数量: %d", len(root_children))

    # 2. 选取所有 book 的 title (相对路径 //)
    all_titles: list[etree._Element] = tree.xpath("//book/title")
    logger.info("所有书籍标题 (//book/title):")
    for t in all_titles:
        logger.info("  - %s (lang=%s)", t.text, t.get("lang"))

    # 3. 属性选择
    tech_books: list[etree._Element] = tree.xpath("//book[@category='tech']/title")
    logger.info("技术类书籍 (//book[@category='tech']/title):")
    for t in tech_books:
        logger.info("  - %s", t.text)

    # 4. 谓词过滤 - 价格大于 35 的书
    expensive: list[etree._Element] = tree.xpath("//book[price > 35.00]/title")
    logger.info("价格 > 35 的书籍 (//book[price>35]/title):")
    for t in expensive:
        logger.info("  - %s", t.text)

    # 5. 索引选择 - 第一本书
    first_book: list[etree._Element] = tree.xpath("//book[1]/title")
    logger.info("第一本书 (//book[1]/title): %s", first_book[0].text)

    # 6. 通配符
    all_elements_count: int = len(tree.xpath("//*"))
    logger.info("文档总元素数 (//*): %d", all_elements_count)

    # 7. 多路径选择 (|)
    titles_and_prices: list[etree._Element] = tree.xpath("//title | //price")
    logger.info("所有 title 和 price (//title | //price):")
    for elem in titles_and_prices:
        logger.info("  <%s>%s</%s>", elem.tag, elem.text, elem.tag)


# ===================================================================
# Part 3: XPath 解析 HTML 页面 (豆瓣 Top250 示例)
# ===================================================================

@dataclass
class Movie:
    """电影数据模型。"""
    rank: int
    title: str
    rating: float
    quote: str = ""
    info: str = ""


def scrape_douban_top250_xpath(pages: int = 1) -> list[Movie]:
    """
    使用 XPath 解析豆瓣电影 Top250。

    Args:
        pages: 爬取页数 (1-10), 每页25部电影。

    Returns:
        Movie 对象列表。
    """
    logger.info("=== XPath 爬取豆瓣电影 Top250 (前 %d 页) ===", pages)

    movies: list[Movie] = []
    base_url: str = "https://movie.douban.com/top250"

    for page in range(1, pages + 1):
        start: int = (page - 1) * 25
        url: str = f"{base_url}?start={start}"
        logger.info("正在请求第 %d 页: %s", page, url)

        try:
            resp: requests.Response = requests.get(
                url, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("请求失败: %s", exc)
            continue

        tree: etree._Element = etree.HTML(resp.text)

        # XPath 提取电影标题
        title_nodes: list[etree._Element] = tree.xpath(
            '//div[@class="info"]/div[@class="hd"]/a/span[@class="title"][1]'
        )
        # XPath 提取电影评分
        rating_nodes: list[etree._Element] = tree.xpath(
            '//div[@class="info"]/div[@class="bd"]/div/span[@class="rating_num"]'
        )
        # XPath 提取一句话评价
        quote_nodes: list[etree._Element] = tree.xpath(
            '//div[@class="info"]/div[@class="bd"]/p[@class="quote"]/span'
        )
        # XPath 提取电影信息 (导演/年份等)
        info_nodes: list[etree._Element] = tree.xpath(
            '//div[@class="info"]/div[@class="bd"]/p[1]'
        )

        for i, (t_node, r_node) in enumerate(zip(title_nodes, rating_nodes)):
            title_text: str = t_node.text.strip() if t_node.text else ""
            rating_text: str = r_node.text.strip() if r_node.text else "0.0"
            quote_text: str = ""
            if i < len(quote_nodes) and quote_nodes[i].text:
                quote_text = quote_nodes[i].text.strip()
            info_text: str = ""
            if i < len(info_nodes) and info_nodes[i].text:
                info_text = info_nodes[i].text.strip()

            movie = Movie(
                rank=start + i + 1,
                title=title_text,
                rating=float(rating_text),
                quote=quote_text,
                info=info_text,
            )
            movies.append(movie)

        logger.info("第 %d 页解析完成, 获取 %d 部电影", page, len(title_nodes))
        time.sleep(1)  # 礼貌延迟

    return movies


# ===================================================================
# Part 4: BeautifulSoup4 CSS 选择器解析 (豆瓣 Top250 示例)
# ===================================================================

def scrape_douban_top250_bs4(pages: int = 1) -> list[Movie]:
    """
    使用 BeautifulSoup4 + CSS 选择器解析豆瓣电影 Top250。

    Args:
        pages: 爬取页数 (1-10)。

    Returns:
        Movie 对象列表。
    """
    logger.info("=== BeautifulSoup4 爬取豆瓣电影 Top250 (前 %d 页) ===", pages)

    movies: list[Movie] = []
    base_url: str = "https://movie.douban.com/top250"

    for page in range(1, pages + 1):
        start: int = (page - 1) * 25
        url: str = f"{base_url}?start={start}"
        logger.info("正在请求第 %d 页: %s", page, url)

        try:
            resp: requests.Response = requests.get(
                url, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("请求失败: %s", exc)
            continue

        soup: BeautifulSoup = BeautifulSoup(resp.text, "lxml")

        # CSS 选择器提取
        title_spans: list[Tag] = soup.select(
            "div.info > div.hd > a > span.title:nth-of-type(1)"
        )
        rating_spans: list[Tag] = soup.select(
            "div.info > div.bd > span.rating_num"
        )
        quote_spans: list[Tag] = soup.select(
            "div.info > div.bd > p.quote > span"
        )

        for i, (t_span, r_span) in enumerate(zip(title_spans, rating_spans)):
            title_text: str = t_span.text.strip()
            rating_text: str = r_span.text.strip()
            quote_text: str = ""
            if i < len(quote_spans):
                quote_text = quote_spans[i].text.strip()

            movie = Movie(
                rank=start + i + 1,
                title=title_text,
                rating=float(rating_text) if rating_text else 0.0,
                quote=quote_text,
            )
            movies.append(movie)

        logger.info("第 %d 页解析完成, 获取 %d 部电影", page, len(title_spans))
        time.sleep(1)

    return movies


# ===================================================================
# Part 5: 企业级实战 - 新闻爬虫
# ===================================================================

@dataclass
class NewsArticle:
    """新闻文章数据模型。"""
    title: str
    url: str
    source: str = ""
    publish_time: str = ""
    summary: str = ""
    category: str = ""


class NewsScraper:
    """
    通用新闻爬虫基类。
    子类只需实现 _parse_articles 方法即可适配不同新闻站点。
    """

    def __init__(self, base_url: str, source_name: str) -> None:
        self.base_url: str = base_url
        self.source_name: str = source_name
        self.session: requests.Session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_page(self, url: str) -> Optional[str]:
        """获取页面 HTML 内容。"""
        try:
            resp: requests.Response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            return resp.text
        except requests.RequestException as exc:
            logger.error("获取页面失败 [%s]: %s", url, exc)
            return None

    def _parse_articles(self, html: str) -> list[NewsArticle]:
        """子类重写: 从 HTML 中解析新闻列表。"""
        raise NotImplementedError

    def scrape(self, pages: int = 1) -> list[NewsArticle]:
        """
        抓取新闻。

        Args:
            pages: 抓取页数。

        Returns:
            NewsArticle 列表。
        """
        all_articles: list[NewsArticle] = []
        for page in range(1, pages + 1):
            url: str = self._build_url(page)
            logger.info("[%s] 正在抓取第 %d 页: %s", self.source_name, page, url)
            html: Optional[str] = self.fetch_page(url)
            if html is None:
                continue
            articles: list[NewsArticle] = self._parse_articles(html)
            all_articles.extend(articles)
            logger.info("[%s] 第 %d 页获取 %d 篇文章",
                        self.source_name, page, len(articles))
            time.sleep(1)
        return all_articles

    def _build_url(self, page: int) -> str:
        """子类重写: 构造分页 URL。"""
        return self.base_url

    @staticmethod
    def to_json(articles: list[NewsArticle], indent: int = 2) -> str:
        """将新闻列表转为 JSON 字符串。"""
        return json.dumps(
            [asdict(a) for a in articles],
            ensure_ascii=False,
            indent=indent,
        )


class HackerNewsScraper(NewsScraper):
    """
    Hacker News 爬虫 (CSS 选择器实现)。
    站点: https://news.ycombinator.com/
    """

    def __init__(self) -> None:
        super().__init__(
            base_url="https://news.ycombinator.com/",
            source_name="Hacker News",
        )

    def _build_url(self, page: int) -> str:
        if page == 1:
            return self.base_url
        return f"{self.base_url}news?p={page}"

    def _parse_articles(self, html: str) -> list[NewsArticle]:
        soup: BeautifulSoup = BeautifulSoup(html, "lxml")
        articles: list[NewsArticle] = []

        # CSS 选择器: 每条新闻标题行
        title_rows: list[Tag] = soup.select("tr.athing")
        for row in title_rows:
            title_link: Optional[Tag] = row.select_one("span.titleline > a")
            if title_link is None:
                continue

            title: str = title_link.text.strip()
            href: str = str(title_link.get("href", ""))

            # 处理相对链接
            if href and not href.startswith(("http://", "https://")):
                href = urljoin(self.base_url, href)

            # 提取来源域名
            source_tag: Optional[Tag] = row.select_one("span.sitebit a .sitestr")
            source: str = source_tag.text.strip() if source_tag else ""

            article = NewsArticle(
                title=title,
                url=href,
                source=source or self.source_name,
                category="tech",
            )
            articles.append(article)

        return articles


class GenericNewsScraper(NewsScraper):
    """
    通用新闻爬虫模板 (XPath 实现)。
    用户可通过构造函数传入自定义的 XPath 规则。
    """

    def __init__(
        self,
        base_url: str,
        source_name: str,
        xpath_item: str,
        xpath_title: str,
        xpath_link: str = "@href",
        xpath_summary: str = "",
        xpath_time: str = "",
    ) -> None:
        super().__init__(base_url, source_name)
        self.xpath_item: str = xpath_item
        self.xpath_title: str = xpath_title
        self.xpath_link: str = xpath_link
        self.xpath_summary: str = xpath_summary
        self.xpath_time: str = xpath_time

    def _parse_articles(self, html: str) -> list[NewsArticle]:
        tree: etree._Element = etree.HTML(html)
        articles: list[NewsArticle] = []

        items: list[etree._Element] = tree.xpath(self.xpath_item)
        for item in items:
            # 标题
            title_nodes: list[etree._Element] = item.xpath(self.xpath_title)
            title: str = ""
            href: str = ""
            if title_nodes:
                node = title_nodes[0]
                title = (node.text or "").strip()
                # 尝试获取链接
                link_candidates: list[etree._Element] = item.xpath(
                    f"{self.xpath_title}/{self.xpath_link}"
                ) if self.xpath_link.startswith("@") else []
                if link_candidates:
                    href = str(link_candidates[0])
                elif node.tag == "a":
                    href = str(node.get("href", ""))

            # 摘要
            summary: str = ""
            if self.xpath_summary:
                summary_nodes: list[etree._Element] = item.xpath(self.xpath_summary)
                if summary_nodes:
                    summary = (summary_nodes[0].text or "").strip()

            # 时间
            pub_time: str = ""
            if self.xpath_time:
                time_nodes: list[etree._Element] = item.xpath(self.xpath_time)
                if time_nodes:
                    pub_time = (time_nodes[0].text or "").strip()

            if title:
                article = NewsArticle(
                    title=title,
                    url=urljoin(self.base_url, href),
                    source=self.source_name,
                    publish_time=pub_time,
                    summary=summary,
                )
                articles.append(article)

        return articles


# ===================================================================
# Part 6: 企业级实战 - 价格监控
# ===================================================================

@dataclass
class PriceRecord:
    """价格记录。"""
    product_name: str
    current_price: float
    original_price: float
    currency: str
    url: str
    timestamp: str = ""
    in_stock: bool = True

    @property
    def discount_pct(self) -> float:
        """计算折扣百分比。"""
        if self.original_price <= 0:
            return 0.0
        return round((1 - self.current_price / self.original_price) * 100, 1)


@dataclass
class PriceAlert:
    """价格警报。"""
    product_name: str
    current_price: float
    target_price: float
    url: str
    message: str


class PriceMonitor:
    """
    价格监控器。
    支持对多个商品设置目标价格, 当价格低于阈值时触发警报。
    """

    def __init__(self) -> None:
        self._watchlist: dict[str, float] = {}  # product_name -> target_price
        self._history: list[PriceRecord] = []
        self._alerts: list[PriceAlert] = []

    def add_watch(self, product_name: str, target_price: float) -> None:
        """添加监控商品及目标价格。"""
        self._watchlist[product_name] = target_price
        logger.info("已添加监控: %s (目标价: %.2f)", product_name, target_price)

    def remove_watch(self, product_name: str) -> None:
        """移除监控商品。"""
        self._watchlist.pop(product_name, None)
        logger.info("已移除监控: %s", product_name)

    def check_price(self, record: PriceRecord) -> Optional[PriceAlert]:
        """
        检查价格记录, 判断是否触发警报。

        Args:
            record: 价格记录。

        Returns:
            触发警报时返回 PriceAlert, 否则返回 None。
        """
        from datetime import datetime
        record.timestamp = datetime.now().isoformat()
        self._history.append(record)

        target: Optional[float] = self._watchlist.get(record.product_name)
        if target is None:
            return None

        if record.current_price <= target:
            alert = PriceAlert(
                product_name=record.product_name,
                current_price=record.current_price,
                target_price=target,
                url=record.url,
                message=(
                    f"[价格警报] {record.product_name} "
                    f"当前价格 {record.current_price:.2f} "
                    f"<= 目标价格 {target:.2f} "
                    f"(折扣: {record.discount_pct}%)"
                ),
            )
            self._alerts.append(alert)
            logger.warning(alert.message)
            return alert

        logger.info(
            "%s 当前 %.2f > 目标 %.2f, 继续监控",
            record.product_name, record.current_price, target,
        )
        return None

    def get_alerts(self) -> list[PriceAlert]:
        """获取所有触发的警报。"""
        return list(self._alerts)

    def get_history(self, product_name: Optional[str] = None) -> list[PriceRecord]:
        """获取价格历史。"""
        if product_name:
            return [r for r in self._history if r.product_name == product_name]
        return list(self._history)


def parse_price_from_html_bs4(html: str, base_url: str = "") -> list[PriceRecord]:
    """
    使用 BeautifulSoup4 从商品页面 HTML 中提取价格信息。
    适用于结构类似的电商页面模板。

    Args:
        html: 页面 HTML 内容。
        base_url: 基础 URL, 用于拼接相对链接。

    Returns:
        PriceRecord 列表。
    """
    soup: BeautifulSoup = BeautifulSoup(html, "lxml")
    records: list[PriceRecord] = []

    cards: list[Tag] = soup.select("div.product-card")
    for card in cards:
        name_tag: Optional[Tag] = card.select_one(".product-name")
        price_tag: Optional[Tag] = card.select_one(".price")
        original_tag: Optional[Tag] = card.select_one(".original-price")
        stock_tag: Optional[Tag] = card.select_one(".stock")
        link_tag: Optional[Tag] = card.select_one("a.btn-detail, a[href]")

        if not name_tag or not price_tag:
            continue

        name: str = name_tag.text.strip()
        try:
            current_price: float = float(re.sub(r"[^\d.]", "", price_tag.text))
        except ValueError:
            continue

        original_price: float = current_price
        if original_tag:
            try:
                original_price = float(re.sub(r"[^\d.]", "", original_tag.text))
            except ValueError:
                pass

        currency: str = str(price_tag.get("data-currency", "CNY"))
        in_stock: bool = True
        if stock_tag:
            classes: list[str] = stock_tag.get("class", [])
            in_stock = "out-of-stock" not in classes

        detail_url: str = ""
        if link_tag:
            href: str = str(link_tag.get("href", ""))
            detail_url = urljoin(base_url, href) if base_url else href

        record = PriceRecord(
            product_name=name,
            current_price=current_price,
            original_price=original_price,
            currency=currency,
            url=detail_url,
            in_stock=in_stock,
        )
        records.append(record)

    return records


def parse_price_from_html_xpath(html: str, base_url: str = "") -> list[PriceRecord]:
    """
    使用 XPath 从商品页面 HTML 中提取价格信息。

    Args:
        html: 页面 HTML 内容。
        base_url: 基础 URL。

    Returns:
        PriceRecord 列表。
    """
    tree: etree._Element = etree.HTML(html)
    records: list[PriceRecord] = []

    # XPath: 选取所有商品卡片
    cards: list[etree._Element] = tree.xpath('//div[contains(@class,"product-card")]')
    for card in cards:
        name_nodes: list[etree._Element] = card.xpath('.//*[contains(@class,"product-name")]')
        price_nodes: list[etree._Element] = card.xpath('.//*[contains(@class,"price")]')
        original_nodes: list[etree._Element] = card.xpath('.//*[contains(@class,"original-price")]')

        if not name_nodes or not price_nodes:
            continue

        name: str = (name_nodes[0].text or "").strip()
        try:
            current_price: float = float(re.sub(r"[^\d.]", "", (price_nodes[0].text or "0")))
        except ValueError:
            continue

        original_price: float = current_price
        if original_nodes:
            try:
                original_price = float(re.sub(r"[^\d.]", "", (original_nodes[0].text or "0")))
            except ValueError:
                pass

        currency: str = str(price_nodes[0].get("data-currency", "CNY"))

        link_nodes: list[etree._Element] = card.xpath('.//a/@href')
        detail_url: str = ""
        if link_nodes:
            href: str = str(link_nodes[0])
            detail_url = urljoin(base_url, href) if base_url else href

        record = PriceRecord(
            product_name=name,
            current_price=current_price,
            original_price=original_price,
            currency=currency,
            url=detail_url,
        )
        records.append(record)

    return records


# ===================================================================
# Part 7: 综合演示
# ===================================================================

def demo_local_html_parsing() -> None:
    """演示对本地 HTML 模板的解析 (无需网络)。"""
    logger.info("=" * 60)
    logger.info("综合演示: 本地 HTML 解析 + 价格监控")
    logger.info("=" * 60)

    # 1. BeautifulSoup4 + CSS 选择器解析商品
    products: list[Product] = demo_bs4_css_selector()
    logger.info("共解析 %d 个商品 (BeautifulSoup4)", len(products))

    # 2. 使用 XPath 解析同一份 HTML
    logger.info("--- 使用 XPath 解析同一份 HTML ---")
    xpath_records: list[PriceRecord] = parse_price_from_html_xpath(SAMPLE_HTML)
    for rec in xpath_records:
        logger.info("  [XPath] %s - %.2f %s", rec.product_name, rec.current_price, rec.currency)

    # 3. 使用 BS4 解析价格
    logger.info("--- 使用 BS4 解析价格 ---")
    bs4_records: list[PriceRecord] = parse_price_from_html_bs4(SAMPLE_HTML)
    for rec in bs4_records:
        logger.info("  [BS4] %s - %.2f %s (折扣 %.1f%%)",
                     rec.product_name, rec.current_price, rec.currency, rec.discount_pct)

    # 4. 价格监控演示
    logger.info("--- 价格监控演示 ---")
    monitor: PriceMonitor = PriceMonitor()
    monitor.add_watch("高性能笔记本电脑", 6500.00)
    monitor.add_watch("旗舰智能手机", 4500.00)
    monitor.add_watch("降噪无线耳机", 800.00)

    # 模拟价格检查
    test_records: list[PriceRecord] = [
        PriceRecord("高性能笔记本电脑", 6499.00, 6999.00, "CNY", "/product/1001"),
        PriceRecord("旗舰智能手机", 4999.00, 4999.00, "CNY", "/product/1002"),
        PriceRecord("降噪无线耳机", 799.00, 899.00, "CNY", "/product/1004"),
    ]

    for record in test_records:
        alert: Optional[PriceAlert] = monitor.check_price(record)

    alerts: list[PriceAlert] = monitor.get_alerts()
    logger.info("触发 %d 个价格警报:", len(alerts))
    for a in alerts:
        logger.info("  %s", a.message)

    # 5. 导出 JSON
    logger.info("--- 数据导出 ---")
    products_json: str = json.dumps(
        [asdict(p) for p in products], ensure_ascii=False, indent=2
    )
    logger.info("商品 JSON 数据 (前 200 字符):\n%s...", products_json[:200])


def demo_xpath_xml() -> None:
    """演示 XPath 解析 XML 数据。"""
    logger.info("=" * 60)
    logger.info("XPath XML 解析演示")
    logger.info("=" * 60)

    # 使用纯 lxml 解析 XML
    root: etree._ElementTree = etree.fromstring(
        SAMPLE_XML.encode("utf-8")
    )

    # 获取所有书名
    titles: list[str] = root.xpath("//title/text()")
    logger.info("所有书名: %s", titles)

    # 获取价格大于 35 的书
    expensive: list[str] = root.xpath("//book[price>35]/title/text()")
    logger.info("价格 > 35: %s", expensive)

    # 获取 lang 属性
    langs: list[str] = root.xpath("//title/@lang")
    logger.info("语言属性: %s", langs)

    # 获取类别
    categories: list[str] = root.xpath("//book/@category")
    logger.info("书籍类别: %s", categories)


def demo_douban_scraper() -> None:
    """
    演示豆瓣 Top250 爬虫 (仅爬取第 1 页作为演示)。
    注意: 需要网络连接, 且目标网站可能有反爬机制。
    """
    logger.info("=" * 60)
    logger.info("豆瓣 Top250 爬虫演示 (第 1 页)")
    logger.info("=" * 60)

    # 方法 1: XPath
    logger.info("--- 方法 1: XPath ---")
    try:
        movies_xpath: list[Movie] = scrape_douban_top250_xpath(pages=1)
        for m in movies_xpath[:5]:
            logger.info("  #%d %s - %.1f | %s", m.rank, m.title, m.rating, m.quote)
        logger.info("  ... 共 %d 部电影", len(movies_xpath))
    except Exception as exc:
        logger.warning("XPath 方式爬取失败 (可能是网络问题): %s", exc)

    # 方法 2: BeautifulSoup4
    logger.info("--- 方法 2: BeautifulSoup4 ---")
    try:
        movies_bs4: list[Movie] = scrape_douban_top250_bs4(pages=1)
        for m in movies_bs4[:5]:
            logger.info("  #%d %s - %.1f | %s", m.rank, m.title, m.rating, m.quote)
        logger.info("  ... 共 %d 部电影", len(movies_bs4))
    except Exception as exc:
        logger.warning("BS4 方式爬取失败 (可能是网络问题): %s", exc)


def demo_hacker_news_scraper() -> None:
    """演示 Hacker News 爬虫 (仅爬取第 1 页)。"""
    logger.info("=" * 60)
    logger.info("Hacker News 爬虫演示")
    logger.info("=" * 60)

    scraper: HackerNewsScraper = HackerNewsScraper()
    try:
        articles: list[NewsArticle] = scraper.scrape(pages=1)
        for a in articles[:10]:
            logger.info("  [%s] %s", a.source, a.title)
            if a.url:
                logger.info("    -> %s", a.url)
        logger.info("  ... 共 %d 篇文章", len(articles))

        # 导出 JSON
        json_output: str = NewsScraper.to_json(articles[:5])
        logger.info("JSON 输出示例 (前 3 篇):\n%s", json_output[:500])
    except Exception as exc:
        logger.warning("Hacker News 爬取失败: %s", exc)


# ===================================================================
# 主程序入口
# ===================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  Day 62: 用Python解析HTML页面-2")
    print("  BeautifulSoup4 | CSS选择器 | XPath | 新闻爬虫 | 价格监控")
    print("=" * 70)
    print()

    # ---------------------------------------------------------------
    # 1. 本地 HTML 解析演示 (无需网络)
    # ---------------------------------------------------------------
    demo_local_html_parsing()
    print()

    # ---------------------------------------------------------------
    # 2. XPath XML 解析演示
    # ---------------------------------------------------------------
    demo_xpath_xml()
    print()

    # ---------------------------------------------------------------
    # 3. XPath 基础语法演示
    # ---------------------------------------------------------------
    demo_xpath_basics()
    print()

    # ---------------------------------------------------------------
    # 4. 豆瓣 Top250 爬虫 (需要网络, 取消注释运行)
    # ---------------------------------------------------------------
    # demo_douban_scraper()
    # print()

    # ---------------------------------------------------------------
    # 5. Hacker News 爬虫 (需要网络, 取消注释运行)
    # ---------------------------------------------------------------
    # demo_hacker_news_scraper()
    # print()

    print("=" * 70)
    print("  所有演示完成!")
    print("=" * 70)
