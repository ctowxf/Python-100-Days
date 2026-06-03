"""
正则表达式的应用 - 综合示例
============================

本文件涵盖:
  - re 模块核心函数: compile, match, search, findall, finditer, sub, split
  - 正则表达式模式: 字符类, 量词, 锚点, 分组, 命名分组, 前瞻/后顾
  - C++ 对比: Python re vs C++ std::regex
  - 企业级示例: 邮箱验证, 电话提取, 日志解析, 数据清洗, URL路由

作者: Python 100 Days 学习笔记
日期: 2026-06-02
"""

from __future__ import annotations

import re
from typing import Optional


# ============================================================================
# 第一部分: re 模块基础 — compile / match / search / fullmatch
# ============================================================================

def demo_compile_and_match() -> None:
    """
    compile() 将正则表达式编译为 Pattern 对象, 适合重复使用。
    match()  从字符串开头匹配; fullmatch() 要求完全匹配。

    C++ 对比 — Python re vs C++ std::regex:
        Python:  pattern = re.compile(r"\\d+")
        C++:     std::regex pattern("\\d+");
        Python 使用 raw string (r"") 避免转义地狱,
        C++ 中反斜杠本身就需要转义, 因此写法更繁琐。
    """
    print("=" * 60)
    print("1. compile / match / fullmatch")
    print("=" * 60)

    # 编译正则表达式对象 — 复用时性能更优
    username_pattern: re.Pattern[str] = re.compile(
        r"^[a-zA-Z0-9_]{6,20}$"
    )

    test_usernames: list[str] = ["alice_01", "ab", "valid_user_99", "has space"]
    for name in test_usernames:
        # match 从字符串起始位置尝试匹配
        result: Optional[re.Match[str]] = username_pattern.match(name)
        status: str = "VALID" if result else "INVALID"
        print(f"  用户名 '{name}': {status}")

    # fullmatch 要求整个字符串完全匹配模式
    qq_pattern: re.Pattern[str] = re.compile(r"[1-9]\d{4,11}")
    test_qqs: list[str] = ["12345", "88888888", "01234"]
    for qq in test_qqs:
        result = qq_pattern.fullmatch(qq)
        status = "VALID" if result else "INVALID"
        print(f"  QQ号 '{qq}': {status}")


# ============================================================================
# 第二部分: search / findall / finditer
# ============================================================================

def demo_search_and_findall() -> None:
    """
    search()   在字符串中搜索第一个匹配
    findall()  返回所有匹配的字符串列表
    finditer() 返回匹配对象的迭代器 (可获取位置信息)

    C++ 对比 — Python findall vs C++ std::regex_iterator:
        Python:  phones = re.findall(r"1[3-9]\\d{9}", text)
        C++:     auto begin = std::sregex_iterator(text.begin(), text.end(), pattern);
                 // 需要手动遍历迭代器, 代码量显著更多
    """
    print("\n" + "=" * 60)
    print("2. search / findall / finditer")
    print("=" * 60)

    text: str = (
        "联系方式: 张三 13812345678, 李四 15600998765, "
        "王五 14798765432, 办公室 010-88886666"
    )

    # 使用前瞻 (?<=\\D) 和后顾 (?=\\D) 确保手机号前后不是数字
    phone_pattern: re.Pattern[str] = re.compile(
        r"(?<=\D)(1[3-9]\d{9})(?=\D)"
    )

    # findall 返回匹配的字符串列表
    phones: list[str] = phone_pattern.findall(text)
    print(f"  findall 手机号: {phones}")

    # finditer 返回 Match 对象, 可获取匹配位置
    print("  finditer 详情:")
    for match in phone_pattern.finditer(text):
        print(f"    号码={match.group()}, 位置=[{match.start()}:{match.end()}]")

    # search 只返回第一个匹配
    first: Optional[re.Match[str]] = phone_pattern.search(text)
    if first:
        print(f"  search 第一个匹配: {first.group()} at pos {first.start()}")


# ============================================================================
# 第三部分: 分组 (Groups) 与命名分组 (Named Groups)
# ============================================================================

def demo_groups_and_named_groups() -> None:
    """
    ()   捕获分组, 通过 group(1), group(2) 访问
    (?P<name>...)  命名分组, 通过 group("name") 访问
    (?:...)  非捕获分组, 仅用于逻辑分组不占用编号

    C++ 对比 — Python named groups vs C++ named captures:
        Python:  (?P<year>\\d{4})-(?P<month>\\d{2})
        C++11:   (?<year>\\d{4})-(?<month>\\d{2})   // C++ 命名分组语法
        Python 通过 match.group("name") 访问;
        C++ 通过 match["name"] 访问 (需 C++17+ 完整支持)。
    """
    print("\n" + "=" * 60)
    print("3. 分组与命名分组")
    print("=" * 60)

    # 普通分组 — 提取日期各部分
    date_text: str = "今天是 2026-06-02, 昨天是 2026-06-01"
    date_pattern: re.Pattern[str] = re.compile(
        r"(\d{4})-(\d{2})-(\d{2})"
    )

    for m in date_pattern.finditer(date_text):
        full: str = m.group(0)   # 整个匹配
        year: str = m.group(1)   # 第1个分组
        month: str = m.group(2)  # 第2个分组
        day: str = m.group(3)    # 第3个分组
        print(f"  完整匹配: {full} -> 年={year}, 月={month}, 日={day}")

    # 命名分组 — 更具可读性
    named_pattern: re.Pattern[str] = re.compile(
        r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
    )
    m = named_pattern.search(date_text)
    if m:
        print(f"  命名分组: year={m.group('year')}, "
              f"month={m.group('month')}, day={m.group('day')}")
        # groupdict() 返回所有命名分组的字典
        print(f"  groupdict: {m.groupdict()}")

    # 非捕获分组 — (?:...) 不占用编号
    version_pattern: re.Pattern[str] = re.compile(
        r"(?:http|https)://(\S+)"
    )
    url: str = "访问 https://example.com/path 获取详情"
    m = version_pattern.search(url)
    if m:
        # group(1) 直接是域名部分, 跳过了 (?:http|https)
        print(f"  非捕获分组提取域名: {m.group(1)}")


# ============================================================================
# 第四部分: 前瞻 (Lookahead) 与后顾 (Lookbehind)
# ============================================================================

def demo_lookahead_and_lookbehind() -> None:
    """
    (?=exp)   正向前瞻: 后面是 exp 的位置
    (?!exp)   负向前瞻: 后面不是 exp 的位置
    (?<=exp)  正向后顾: 前面是 exp 的位置
    (?<!exp)  负向后顾: 前面不是 exp 的位置

    前瞻/后顾是零宽断言, 不消耗字符, 仅匹配位置。
    """
    print("\n" + "=" * 60)
    print("4. 前瞻与后顾 (Lookahead & Lookbehind)")
    print("=" * 60)

    # 正向前瞻: 匹配 "ing" 前面的单词部分
    text1: str = "I'm dancing and singing in the morning"
    lookahead_pattern: re.Pattern[str] = re.compile(r"\b\w+(?=ing)\b")
    results: list[str] = lookahead_pattern.findall(text1)
    print(f"  正向前瞻 (?=ing): {results}")

    # 正向后顾: 匹配 "danc" 后面的 "ing"
    lookbehind_pattern: re.Pattern[str] = re.compile(r"(?<=danc)\w+\b")
    results = lookbehind_pattern.findall(text1)
    print(f"  正向后顾 (?<=danc): {results}")

    # 负向前瞻: 匹配后面不是数字的字母序列
    text2: str = "item123 item item456 other"
    neg_lookahead: re.Pattern[str] = re.compile(r"\b[a-zA-Z]+(?!\d)\b")
    results = neg_lookahead.findall(text2)
    print(f"  负向前瞻 (字母后不跟数字): {results}")

    # 负向后顾: 匹配前面不是 $ 的数字
    text3: str = "价格$99 数量99 金额$150 库存200"
    neg_lookbehind: re.Pattern[str] = re.compile(r"(?<!\$)\b(\d+)\b")
    results = neg_lookbehind.findall(text3)
    print(f"  负向后顾 (前面不是$的数字): {results}")

    # 组合使用: 提取不带引号的值 (引号内容前后都是特定字符)
    text4: str = 'name="Alice" age=30 city="NYC" score=95'
    combo: re.Pattern[str] = re.compile(r'(?<=")[\w]+(?=")')
    results = combo.findall(text4)
    print(f"  引号内的值: {results}")


# ============================================================================
# 第五部分: sub 替换与 split 拆分
# ============================================================================

def demo_sub_and_split() -> None:
    """
    sub(pattern, repl, string)  替换匹配内容
    split(pattern, string)      按模式拆分字符串

    repl 可以是字符串或函数 (函数接收 Match 对象, 返回替换字符串)。
    """
    print("\n" + "=" * 60)
    print("5. sub 替换与 split 拆分")
    print("=" * 60)

    # sub 基础替换 — 脱敏手机号
    raw_text: str = "请联系 13812345678 或 15600998765"
    masked: str = re.sub(
        r"(1[3-9]\d)\d{4}(\d{4})",
        r"\1****\2",
        raw_text,
    )
    print(f"  手机号脱敏: {masked}")

    # sub 使用函数作为替换 — 动态替换
    def uppercase_replacer(match: re.Match[str]) -> str:
        return match.group().upper()

    text: str = "hello world from python"
    result: str = re.sub(r"\b\w+", uppercase_replacer, text)
    print(f"  函数替换(首字母大写): {result}")

    # sub 限制替换次数
    messy: str = "aabbccaabbcc"
    cleaned: str = re.sub(r"aa", "XX", messy, count=1)
    print(f"  限制替换次数(count=1): {cleaned}")

    # split 按多种分隔符拆分
    poem: str = "窗前明月光，疑是地上霜。举头望明月，低头思故乡。"
    parts: list[str] = re.split(r"[，。]", poem)
    # 过滤空字符串
    parts = [p for p in parts if p]
    print(f"  拆分诗句: {parts}")

    # split 保留分隔符 (使用捕获组)
    csv_line: str = "name,age;city|country"
    tokens: list[str] = re.split(r"([,;|])", csv_line)
    print(f"  拆分并保留分隔符: {tokens}")


# ============================================================================
# 第六部分: 企业级示例 — 邮箱验证器
# ============================================================================

def validate_email(email: str) -> bool:
    """
    验证邮箱地址格式是否合法。

    规则:
      - 用户名: 字母、数字、点、下划线、连字符
      - @ 符号
      - 域名: 字母、数字、点、连字符
      - 顶级域名: 2~10 个字母

    Python re vs C++ std::regex:
        Python 一行即可: re.match(pattern, email)
        C++ 需要: std::smatch m; std::regex_match(email, m, pattern);
        且 C++ 的 ECMAScript 语法与 Python 的 PCRE 略有差异。
    """
    pattern: re.Pattern[str] = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}$"
    )
    return pattern.match(email) is not None


def demo_email_validator() -> None:
    """演示邮箱验证功能。"""
    print("\n" + "=" * 60)
    print("6. 企业示例 — 邮箱验证器")
    print("=" * 60)

    emails: list[str] = [
        "user@example.com",
        "first.last@company.co.uk",
        "admin@sub.domain.org",
        "invalid@",
        "@no-user.com",
        "no-at-sign.com",
        "user@.invalid.com",
        "test+tag@gmail.com",
    ]
    for email in emails:
        status: str = "VALID" if validate_email(email) else "INVALID"
        print(f"  {email:30s} -> {status}")


# ============================================================================
# 第七部分: 企业级示例 — 电话号码提取器
# ============================================================================

def extract_phones(text: str) -> list[dict[str, str]]:
    """
    从文本中提取中国大陆手机号和座机号。

    手机号: 1[3-9] 开头的 11 位数字
    座机号: 区号(3~4位)-号码(7~8位)

    使用命名分组方便后续处理。
    """
    results: list[dict[str, str]] = []

    # 手机号模式 (带前后零宽断言防止部分匹配)
    mobile_pattern: re.Pattern[str] = re.compile(
        r"(?<!\d)(?P<mobile>1[3-9]\d{9})(?!\d)"
    )
    for m in mobile_pattern.finditer(text):
        results.append({"type": "手机", "number": m.group("mobile")})

    # 座机号模式
    landline_pattern: re.Pattern[str] = re.compile(
        r"(?<!\d)(?P<area>0\d{2,3})-(?P<number>\d{7,8})(?!\d)"
    )
    for m in landline_pattern.finditer(text):
        full: str = f"{m.group('area')}-{m.group('number')}"
        results.append({"type": "座机", "number": full})

    return results


def demo_phone_extractor() -> None:
    """演示电话号码提取功能。"""
    print("\n" + "=" * 60)
    print("7. 企业示例 — 电话号码提取器")
    print("=" * 60)

    sample: str = (
        "紧急联系方式:\n"
        "  张三 手机: 13812345678 座机: 010-88886666\n"
        "  李四 手机: 15600998765 座机: 021-55557777\n"
        "  传真号码: 0755-12345678\n"
        "  注意: 110和119是报警电话, 不是手机号"
    )

    phones: list[dict[str, str]] = extract_phones(sample)
    for p in phones:
        print(f"  [{p['type']}] {p['number']}")


# ============================================================================
# 第八部分: 企业级示例 — 日志解析器
# ============================================================================

import datetime


class LogEntry:
    """结构化日志条目。"""

    def __init__(
        self,
        timestamp: str,
        level: str,
        module: str,
        message: str,
    ) -> None:
        self.timestamp = timestamp
        self.level = level
        self.module = module
        self.message = message

    def __repr__(self) -> str:
        return (f"LogEntry(time={self.timestamp}, level={self.level}, "
                f"module={self.module}, msg='{self.message[:30]}...')")


def parse_log(log_text: str) -> list[LogEntry]:
    """
    解析标准格式日志。

    格式: [2026-06-02 10:30:45] [ERROR] [auth] 用户登录失败
    使用命名分组提取各字段。
    """
    pattern: re.Pattern[str] = re.compile(
        r"\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s*"
        r"\[(?P<level>DEBUG|INFO|WARN|ERROR|FATAL)\]\s*"
        r"\[(?P<module>\w+)\]\s*"
        r"(?P<message>.+)"
    )
    entries: list[LogEntry] = []
    for m in pattern.finditer(log_text):
        entries.append(LogEntry(
            timestamp=m.group("timestamp"),
            level=m.group("level"),
            module=m.group("module"),
            message=m.group("message").strip(),
        ))
    return entries


def filter_logs_by_level(
    entries: list[LogEntry],
    min_level: str = "WARN",
) -> list[LogEntry]:
    """按最低日志级别过滤。"""
    level_order: dict[str, int] = {
        "DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3, "FATAL": 4,
    }
    min_val: int = level_order.get(min_level, 2)
    return [e for e in entries if level_order.get(e.level, 0) >= min_val]


def demo_log_parser() -> None:
    """演示日志解析功能。"""
    print("\n" + "=" * 60)
    print("8. 企业示例 — 日志解析器")
    print("=" * 60)

    log_text: str = """\
[2026-06-02 08:00:01] [INFO] [main] 系统启动完成
[2026-06-02 08:05:12] [DEBUG] [db] 数据库连接池初始化 (size=10)
[2026-06-02 09:30:45] [WARN] [auth] 用户 admin 连续登录失败 3 次
[2026-06-02 10:15:33] [ERROR] [payment] 支付网关超时: connection refused
[2026-06-02 10:16:01] [ERROR] [payment] 重试支付失败, 订单号: ORD-20260602-001
[2026-06-02 11:00:00] [INFO] [cron] 定时任务执行完毕
[2026-06-02 12:30:00] [FATAL] [main] 内存溢出, 系统即将关闭"""

    entries: list[LogEntry] = parse_log(log_text)
    print(f"  共解析 {len(entries)} 条日志")

    # 过滤 WARN 及以上级别
    warnings: list[LogEntry] = filter_logs_by_level(entries, "WARN")
    print(f"  WARN 及以上级别 ({len(warnings)} 条):")
    for entry in warnings:
        print(f"    {entry}")


# ============================================================================
# 第九部分: 企业级示例 — 数据清洗器
# ============================================================================

def clean_raw_data(raw: str) -> dict[str, Optional[str]]:
    """
    从非结构化文本中提取并清洗结构化数据。

    应用场景: 从 OCR 结果、用户输入等混乱文本中提取关键字段。
    """
    result: dict[str, Optional[str]] = {
        "name": None,
        "id_card": None,
        "amount": None,
        "date": None,
    }

    # 姓名: 2~4 个中文字符, 前面可能有 "姓名" 等标签
    name_m: Optional[re.Match[str]] = re.search(
        r"(?:姓名[：:]\s*)(?P<name>[一-龥]{2,4})", raw
    )
    if name_m:
        result["name"] = name_m.group("name")

    # 身份证号: 18 位 (最后一位可能是 X)
    id_m: Optional[re.Match[str]] = re.search(
        r"(?<!\d)(?P<id>[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])"
        r"(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx])(?!\d)",
        raw,
    )
    if id_m:
        result["id_card"] = id_m.group("id").upper()

    # 金额: 带有 ￥ 或 ¥ 前缀 (必须有币符, 避免误匹配其他数字)
    amount_m: Optional[re.Match[str]] = re.search(
        r"[￥¥]\s*(?P<amount>[\d,]+\.?\d*)\s*元?", raw
    )
    if amount_m:
        # 去除千分位逗号
        result["amount"] = amount_m.group("amount").replace(",", "")

    # 日期: 支持多种格式
    date_m: Optional[re.Match[str]] = re.search(
        r"(?P<date>\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)", raw
    )
    if date_m:
        result["date"] = date_m.group("date")

    return result


def normalize_whitespace(text: str) -> str:
    """将连续空白字符规范化为单个空格, 并去除首尾空白。"""
    return re.sub(r"\s+", " ", text).strip()


def remove_html_tags(html: str) -> str:
    """去除 HTML 标签, 保留纯文本。"""
    return re.sub(r"<[^>]+>", "", html)


def demo_data_cleaner() -> None:
    """演示数据清洗功能。"""
    print("\n" + "=" * 60)
    print("9. 企业示例 — 数据清洗器")
    print("=" * 60)

    # 从 OCR 结果中提取结构化数据
    ocr_text: str = (
        "姓名：张三丰  身份证号:110101199003071234  "
        "金额: ￥1,234.56元  日期:2026年06月02日"
    )
    data: dict[str, Optional[str]] = clean_raw_data(ocr_text)
    print("  OCR 数据提取:")
    for key, value in data.items():
        print(f"    {key}: {value}")

    # HTML 清洗
    html: str = "<p>Hello <b>World</b></p><br/><div>Test</div>"
    plain: str = remove_html_tags(html)
    print(f"\n  HTML 清洗: '{html}' -> '{plain}'")

    # 空白规范化
    messy: str = "  hello    world   \t  python  \n  regex  "
    clean: str = normalize_whitespace(messy)
    print(f"  空白规范化: '{clean}'")


# ============================================================================
# 第十部分: 企业级示例 — URL 路由器
# ============================================================================

class URLRouter:
    """
    轻量级 URL 路由器, 使用正则表达式匹配路径。

    支持:
      - 静态路径: /home, /about
      - 动态参数: /users/<id>, /posts/<year>/<slug>
      - 类型约束: /items/<int:id>

    C++ 对比 — Python named groups vs C++ named captures:
        Python 路由模式: r"/users/(?P<id>\\d+)"
        C++ 路由模式:    "/users/(?<id>\\\\d+)"
        Python 的 groupdict() 等价于 C++ 的 match["id"] 访问方式,
        但 Python 的 API 更加简洁统一。
    """

    # 类型转换映射
    TYPE_PATTERNS: dict[str, str] = {
        "int": r"\d+",
        "str": r"[^/]+",
        "slug": r"[-a-zA-Z0-9_]+",
        "path": r".+",
    }

    def __init__(self) -> None:
        self._routes: list[tuple[re.Pattern[str], str, list[str]]] = []

    def add_route(self, pattern: str, handler: str) -> None:
        """注册路由规则。将 <type:name> 转换为正则命名分组。"""
        # 将 <int:id> 替换为 (?P<id>\d+)
        param_names: list[str] = []

        def _replace_param(match: re.Match[str]) -> str:
            type_name: str = match.group(1) or "str"
            param_name: str = match.group(2)
            param_names.append(param_name)
            regex_part: str = self.TYPE_PATTERNS.get(type_name, r"[^/]+")
            return f"(?P<{param_name}>{regex_part})"

        regex_str: str = re.sub(
            r"<(?:(\w+):)?(\w+)>",
            _replace_param,
            pattern,
        )
        compiled: re.Pattern[str] = re.compile(f"^{regex_str}$")
        self._routes.append((compiled, handler, param_names))

    def resolve(self, path: str) -> Optional[tuple[str, dict[str, str]]]:
        """解析 URL 路径, 返回 (handler, params) 或 None。"""
        for pattern, handler, _ in self._routes:
            m: Optional[re.Match[str]] = pattern.match(path)
            if m:
                return handler, m.groupdict()
        return None


def demo_url_router() -> None:
    """演示 URL 路由器功能。"""
    print("\n" + "=" * 60)
    print("10. 企业示例 — URL 路由器")
    print("=" * 60)

    router: URLRouter = URLRouter()
    router.add_route("/", "home_handler")
    router.add_route("/about", "about_handler")
    router.add_route("/users/<int:id>", "user_detail_handler")
    router.add_route("/users/<int:uid>/posts/<slug:pid>", "user_post_handler")
    router.add_route("/files/<path:filepath>", "file_handler")

    test_paths: list[str] = [
        "/",
        "/about",
        "/users/42",
        "/users/7/posts/hello-world",
        "/files/docs/readme.txt",
        "/unknown/path",
    ]
    for path in test_paths:
        result = router.resolve(path)
        if result:
            handler, params = result
            print(f"  {path:35s} -> {handler}({params})")
        else:
            print(f"  {path:35s} -> 404 Not Found")


# ============================================================================
# 第十一部分: 综合对比表 — Python re vs C++ std::regex
# ============================================================================

def print_comparison_table() -> None:
    """
    打印 Python re 与 C++ std::regex 的对比说明。
    """
    print("\n" + "=" * 60)
    print("附录: Python re vs C++ std::regex 对比")
    print("=" * 60)

    comparisons: list[tuple[str, str, str]] = [
        (
            "模块/头文件",
            "import re",
            "#include <regex>",
        ),
        (
            "编译正则",
            're.compile(r"\\d+")',
            'std::regex pattern("\\\\d+");',
        ),
        (
            "简单匹配",
            're.match(pattern, text)',
            'std::regex_match(text, pattern)',
        ),
        (
            "搜索",
            're.search(pattern, text)',
            'std::regex_search(text, match, pattern)',
        ),
        (
            "查找全部",
            're.findall(pattern, text)',
            'std::sregex_iterator(begin, end, pattern)',
        ),
        (
            "替换",
            're.sub(pattern, repl, text)',
            'std::regex_replace(text, pattern, repl)',
        ),
        (
            "命名分组",
            '(?P<name>\\w+)',
            '(?<name>\\w+)   // C++11',
        ),
        (
            "访问命名组",
            'match.group("name")',
            'match["name"]   // C++17',
        ),
        (
            "前瞻/后顾",
            "完整支持 (?=) (?!) (?<=) (?<!)",
            "完整支持 (ECMAScript 语法)",
        ),
        (
            "原生字符串",
            'r"\\d+" (无需双重转义)',
            '"\\\\\\d+" (需双重转义反斜杠)',
        ),
    ]

    for feature, py, cpp in comparisons:
        print(f"\n  [{feature}]")
        print(f"    Python: {py}")
        print(f"    C++   : {cpp}")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    demo_compile_and_match()
    demo_search_and_findall()
    demo_groups_and_named_groups()
    demo_lookahead_and_lookbehind()
    demo_sub_and_split()
    demo_email_validator()
    demo_phone_extractor()
    demo_log_parser()
    demo_data_cleaner()
    demo_url_router()
    print_comparison_table()

    print("\n" + "=" * 60)
    print("所有示例执行完毕。")
    print("=" * 60)
