"""
函数应用实战 - 企业级示例合集

包含以下示例：
1. 随机验证码生成
2. 素数判断
3. 最大公约数和最小公倍数
4. 数据统计分析
5. 双色球随机选号

Author: Python-100-Days
Version: 2.0
"""

import random
import string
import math
from typing import List, Tuple, Optional


# =============================================================================
# 示例1：随机验证码
# =============================================================================

ALL_CHARS: str = string.digits + string.ascii_letters


def generate_code(*, code_len: int = 4) -> str:
    """
    生成指定长度的随机验证码

    Args:
        code_len: 验证码的长度，默认为4个字符

    Returns:
        由大小写英文字母和数字构成的随机验证码字符串

    Examples:
        >>> generate_code()
        '59tZ'
        >>> generate_code(code_len=6)
        'FxJucw'
    """
    return ''.join(random.choices(ALL_CHARS, k=code_len))


def verify_code(input_code: str, expected_code: str, ignore_case: bool = False) -> bool:
    """
    验证输入的验证码是否正确

    Args:
        input_code: 用户输入的验证码
        expected_code: 期望的验证码
        ignore_case: 是否忽略大小写，默认为False

    Returns:
        验证是否通过
    """
    if ignore_case:
        return input_code.lower() == expected_code.lower()
    return input_code == expected_code


# =============================================================================
# 示例2：判断素数
# =============================================================================

def is_prime(num: int) -> bool:
    """
    判断一个正整数是不是质数

    Args:
        num: 大于1的正整数

    Returns:
        如果num是质数返回True，否则返回False

    Examples:
        >>> is_prime(2)
        True
        >>> is_prime(4)
        False
        >>> is_prime(17)
        True
    """
    if num < 2:
        return False
    for i in range(2, int(num ** 0.5) + 1):
        if num % i == 0:
            return False
    return True


def get_primes_in_range(start: int, end: int) -> List[int]:
    """
    获取指定范围内的所有素数

    Args:
        start: 范围起始值
        end: 范围结束值（不包含）

    Returns:
        素数列表
    """
    return [num for num in range(start, end) if is_prime(num)]


def count_primes(limit: int) -> int:
    """
    计算小于指定数的素数个数

    Args:
        limit: 上限值

    Returns:
        素数个数
    """
    return sum(1 for num in range(2, limit) if is_prime(num))


# =============================================================================
# 示例3：最大公约数和最小公倍数
# =============================================================================

def gcd(x: int, y: int) -> int:
    """
    求两个正整数的最大公约数（Greatest Common Divisor）

    Args:
        x: 第一个正整数
        y: 第二个正整数

    Returns:
        最大公约数

    Examples:
        >>> gcd(12, 8)
        4
        >>> gcd(15, 25)
        5
    """
    while y % x != 0:
        x, y = y % x, x
    return x


def lcm(x: int, y: int) -> int:
    """
    求两个正整数的最小公倍数（Least Common Multiple）

    Args:
        x: 第一个正整数
        y: 第二个正整数

    Returns:
        最小公倍数

    Examples:
        >>> lcm(3, 4)
        12
        >>> lcm(6, 8)
        24
    """
    return x * y // gcd(x, y)


def gcd_multiple(*numbers: int) -> int:
    """
    求多个正整数的最大公约数

    Args:
        *numbers: 可变数量的正整数

    Returns:
        最大公约数
    """
    from functools import reduce
    return reduce(gcd, numbers)


def lcm_multiple(*numbers: int) -> int:
    """
    求多个正整数的最小公倍数

    Args:
        *numbers: 可变数量的正整数

    Returns:
        最小公倍数
    """
    from functools import reduce
    return reduce(lcm, numbers)


# =============================================================================
# 示例4：数据统计
# =============================================================================

def ptp(data: List[float]) -> float:
    """
    计算极差（全距）

    Args:
        data: 数据列表

    Returns:
        极差值
    """
    return max(data) - min(data)


def mean(data: List[float]) -> float:
    """
    计算算术平均值

    Args:
        data: 数据列表

    Returns:
        平均值
    """
    return sum(data) / len(data)


def median(data: List[float]) -> float:
    """
    计算中位数

    Args:
        data: 数据列表

    Returns:
        中位数
    """
    temp: List[float] = sorted(data)
    size: int = len(data)
    if size % 2 != 0:
        return temp[size // 2]
    else:
        return mean(temp[size // 2 - 1:size // 2 + 1])


def mode(data: List[float]) -> List[float]:
    """
    计算众数

    Args:
        data: 数据列表

    Returns:
        众数列表
    """
    from collections import Counter
    counter = Counter(data)
    max_count = max(counter.values())
    return [num for num, count in counter.items() if count == max_count]


def var(data: List[float], ddof: int = 1) -> float:
    """
    计算方差

    Args:
        data: 数据列表
        ddof: 自由度，默认为1（样本方差），设置为0计算总体方差

    Returns:
        方差
    """
    x_bar: float = mean(data)
    temp: List[float] = [(num - x_bar) ** 2 for num in data]
    return sum(temp) / (len(temp) - ddof)


def std(data: List[float], ddof: int = 1) -> float:
    """
    计算标准差

    Args:
        data: 数据列表
        ddof: 自由度，默认为1（样本标准差），设置为0计算总体标准差

    Returns:
        标准差
    """
    return var(data, ddof) ** 0.5


def cv(data: List[float], ddof: int = 1) -> float:
    """
    计算变异系数

    Args:
        data: 数据列表
        ddof: 自由度

    Returns:
        变异系数
    """
    return std(data, ddof) / mean(data)


def percentile(data: List[float], p: float) -> float:
    """
    计算百分位数

    Args:
        data: 数据列表
        p: 百分位（0-100）

    Returns:
        百分位数
    """
    temp: List[float] = sorted(data)
    k = (len(temp) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return temp[int(k)]
    return temp[f] * (c - k) + temp[c] * (k - f)


def describe(data: List[float]) -> dict:
    """
    输出描述性统计信息

    Args:
        data: 数据列表

    Returns:
        包含统计信息的字典
    """
    stats = {
        'count': len(data),
        'mean': mean(data),
        'median': median(data),
        'mode': mode(data),
        'min': min(data),
        'max': max(data),
        'ptp': ptp(data),
        'var': var(data),
        'std': std(data),
        'cv': cv(data),
        'q1': percentile(data, 25),
        'q3': percentile(data, 75),
        'iqr': percentile(data, 75) - percentile(data, 25),
    }

    print("=" * 50)
    print("描述性统计信息")
    print("=" * 50)
    print(f"样本量:    {stats['count']}")
    print(f"均值:      {stats['mean']:.4f}")
    print(f"中位数:    {stats['median']:.4f}")
    print(f"众数:      {stats['mode']}")
    print(f"最小值:    {stats['min']:.4f}")
    print(f"最大值:    {stats['max']:.4f}")
    print(f"极差:      {stats['ptp']:.4f}")
    print(f"方差:      {stats['var']:.4f}")
    print(f"标准差:    {stats['std']:.4f}")
    print(f"变异系数:  {stats['cv']:.4f}")
    print(f"25%分位:   {stats['q1']:.4f}")
    print(f"75%分位:   {stats['q3']:.4f}")
    print(f"四分位距:  {stats['iqr']:.4f}")
    print("=" * 50)

    return stats


# =============================================================================
# 示例5：双色球随机选号
# =============================================================================

# 双色球规则：红球6个（1-33），蓝球1个（1-16）
RED_BALLS: List[int] = list(range(1, 34))
BLUE_BALLS: List[int] = list(range(1, 17))


def choose_lottery() -> Tuple[List[int], int]:
    """
    生成一组双色球随机号码

    Returns:
        元组，包含6个红球号码列表和1个蓝球号码
    """
    red_balls: List[int] = sorted(random.sample(RED_BALLS, 6))
    blue_ball: int = random.choice(BLUE_BALLS)
    return red_balls, blue_ball


def display_lottery(red_balls: List[int], blue_ball: int) -> None:
    """
    格式化输出一组双色球号码

    Args:
        red_balls: 红球号码列表
        blue_ball: 蓝球号码
    """
    red_str = ' '.join(f'\033[31m{ball:02d}\033[0m' for ball in red_balls)
    blue_str = f'\033[34m{blue_ball:02d}\033[0m'
    print(f"{red_str}  {blue_str}")


def generate_lottery_numbers(n: int) -> List[Tuple[List[int], int]]:
    """
    生成多组双色球随机号码

    Args:
        n: 需要生成的组数

    Returns:
        包含多组号码的列表
    """
    return [choose_lottery() for _ in range(n)]


def check_lottery(my_red: List[int], my_blue: int,
                  prize_red: List[int], prize_blue: int) -> Tuple[int, int]:
    """
    检查中奖情况

    Args:
        my_red: 我的红球号码
        my_blue: 我的蓝球号码
        prize_red: 开奖红球号码
        prize_blue: 开奖蓝球号码

    Returns:
        元组，包含红球命中数和蓝球是否命中
    """
    red_hit: int = len(set(my_red) & set(prize_red))
    blue_hit: int = 1 if my_blue == prize_blue else 0
    return red_hit, blue_hit


def get_prize_level(red_hit: int, blue_hit: int) -> Optional[str]:
    """
    根据命中情况获取奖金等级

    Args:
        red_hit: 红球命中数
        blue_hit: 蓝球命中数（0或1）

    Returns:
        奖金等级字符串，未中奖返回None

    中奖规则：
        一等奖：6红 + 1蓝
        二等奖：6红 + 0蓝
        三等奖：5红 + 1蓝
        四等奖：5红 + 0蓝 或 4红 + 1蓝
        五等奖：4红 + 0蓝 或 3红 + 1蓝
        六等奖：2红 + 1蓝 或 1红 + 1蓝 或 0红 + 1蓝
    """
    prize_rules: dict = {
        (6, 1): "一等奖",
        (6, 0): "二等奖",
        (5, 1): "三等奖",
        (5, 0): "四等奖",
        (4, 1): "四等奖",
        (4, 0): "五等奖",
        (3, 1): "五等奖",
        (2, 1): "六等奖",
        (1, 1): "六等奖",
        (0, 1): "六等奖",
    }
    return prize_rules.get((red_hit, blue_hit))


# =============================================================================
# 企业级实用示例
# =============================================================================

def fibonacci(n: int) -> List[int]:
    """
    生成斐波那契数列

    Args:
        n: 数列长度

    Returns:
        斐波那契数列列表
    """
    if n <= 0:
        return []
    if n == 1:
        return [0]
    seq: List[int] = [0, 1]
    for _ in range(2, n):
        seq.append(seq[-1] + seq[-2])
    return seq


def factorial(n: int) -> int:
    """
    计算阶乘

    Args:
        n: 非负整数

    Returns:
        n的阶乘
    """
    if n < 0:
        raise ValueError("阶乘不接受负数")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def is_palindrome(text: str) -> bool:
    """
    判断字符串是否是回文

    Args:
        text: 输入字符串

    Returns:
        是否是回文
    """
    cleaned: str = ''.join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1]


def flatten(nested_list: list) -> list:
    """
    将嵌套列表展平为一维列表

    Args:
        nested_list: 嵌套列表

    Returns:
        展平后的一维列表
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """
    将列表分割为指定大小的块

    Args:
        lst: 输入列表
        chunk_size: 每块的大小

    Returns:
        分割后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def debounce(func, wait_ms: int = 300):
    """
    防抖函数装饰器（模拟前端防抖行为）

    Args:
        func: 要装饰的函数
        wait_ms: 等待时间（毫秒）

    Returns:
        装饰后的函数
    """
    import threading
    timer = None

    def wrapper(*args, **kwargs):
        nonlocal timer
        if timer is not None:
            timer.cancel()
        timer = threading.Timer(wait_ms / 1000, func, args=args, kwargs=kwargs)
        timer.start()

    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    重试装饰器

    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）

    Returns:
        装饰器函数
    """
    import time
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def memoize(func):
    """
    记忆化装饰器，缓存函数结果

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(sorted(kwargs.items()))
        if not hasattr(wrapper, '_cache'):
            wrapper._cache = {}
        if key not in wrapper._cache:
            wrapper._cache[key] = func(*args, **kwargs)
        return wrapper._cache[key]

    return wrapper


# 应用记忆化装饰器
@memoize
def fibonacci_memo(n: int) -> int:
    """
    使用记忆化的斐波那契计算

    Args:
        n: 第n个斐波那契数

    Returns:
        第n个斐波那契数的值
    """
    if n < 0:
        raise ValueError("n必须为非负整数")
    if n <= 1:
        return n
    return fibonacci_memo(n - 1) + fibonacci_memo(n - 2)


# =============================================================================
# 数据验证工具函数
# =============================================================================

def validate_email(email: str) -> bool:
    """
    简单验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        格式是否有效
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    验证中国大陆手机号格式

    Args:
        phone: 手机号码

    Returns:
        格式是否有效
    """
    import re
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_id_card(id_card: str) -> bool:
    """
    验证中国大陆身份证号格式（简单校验）

    Args:
        id_card: 身份证号码

    Returns:
        格式是否有效
    """
    import re
    if len(id_card) == 18:
        pattern = r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
        return bool(re.match(pattern, id_card))
    elif len(id_card) == 15:
        pattern = r'^[1-9]\d{5}\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}$'
        return bool(re.match(pattern, id_card))
    return False


# =============================================================================
# 主程序入口
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Python 函数应用实战 - 示例演示")
    print("=" * 60)

    # ---------- 示例1：随机验证码 ----------
    print("\n【示例1】随机验证码生成")
    print("-" * 40)
    print("生成5组4位验证码:")
    for _ in range(5):
        print(f"  {generate_code()}")

    print("\n生成3组6位验证码:")
    for _ in range(3):
        print(f"  {generate_code(code_len=6)}")

    # ---------- 示例2：判断素数 ----------
    print("\n【示例2】素数判断")
    print("-" * 40)
    test_numbers = [2, 3, 4, 7, 11, 13, 15, 17, 20, 23, 29, 31]
    for num in test_numbers:
        result = "是" if is_prime(num) else "不是"
        print(f"  {num:2d} {result}素数")

    print(f"\n100以内的素数:")
    primes = get_primes_in_range(2, 100)
    print(f"  {primes}")
    print(f"  共{len(primes)}个")

    # ---------- 示例3：最大公约数和最小公倍数 ----------
    print("\n【示例3】最大公约数和最小公倍数")
    print("-" * 40)
    test_pairs = [(12, 8), (15, 25), (7, 13), (36, 48)]
    for x, y in test_pairs:
        print(f"  gcd({x}, {y}) = {gcd(x, y)}")
        print(f"  lcm({x}, {y}) = {lcm(x, y)}")

    print(f"\n  多个数的GCD: gcd(12, 18, 24) = {gcd_multiple(12, 18, 24)}")
    print(f"  多个数的LCM: lcm(3, 4, 6) = {lcm_multiple(3, 4, 6)}")

    # ---------- 示例4：数据统计 ----------
    print("\n【示例4】数据统计分析")
    print("-" * 40)
    sample_data = [85, 92, 78, 95, 88, 76, 90, 91, 83, 87, 94, 79, 86, 88, 92]
    print(f"样本数据: {sample_data}")
    print()
    describe(sample_data)

    # ---------- 示例5：双色球随机选号 ----------
    print("\n【示例5】双色球随机选号")
    print("-" * 40)
    print("生成5注双色球号码:")
    for i in range(5):
        red, blue = choose_lottery()
        print(f"  第{i+1}注: ", end='')
        display_lottery(red, blue)

    # ---------- 企业级示例 ----------
    print("\n" + "=" * 60)
    print("企业级实用示例")
    print("=" * 60)

    # 斐波那契数列
    print("\n【斐波那契数列】")
    print("-" * 40)
    fib_seq = fibonacci(15)
    print(f"  前15个斐波那契数: {fib_seq}")

    # 阶乘
    print("\n【阶乘计算】")
    print("-" * 40)
    for n in [0, 1, 5, 10, 15]:
        print(f"  {n}! = {factorial(n)}")

    # 回文判断
    print("\n【回文判断】")
    print("-" * 40)
    test_strings = ["racecar", "A man a plan a canal Panama", "hello", "level", "12321"]
    for s in test_strings:
        result = "是" if is_palindrome(s) else "不是"
        print(f"  '{s}' {result}回文")

    # 列表操作
    print("\n【列表操作工具】")
    print("-" * 40)
    nested = [1, [2, 3], [4, [5, 6]], 7, [8, [9, [10]]]]
    print(f"  原始嵌套列表: {nested}")
    print(f"  展平结果: {flatten(nested)}")

    data = list(range(1, 11))
    print(f"\n  原始列表: {data}")
    print(f"  分块(大小3): {chunk_list(data, 3)}")

    # 数据验证
    print("\n【数据验证】")
    print("-" * 40)
    print(f"  邮箱验证 'user@example.com': {validate_email('user@example.com')}")
    print(f"  邮箱验证 'invalid-email': {validate_email('invalid-email')}")
    print(f"  手机验证 '13800138000': {validate_phone('13800138000')}")
    print(f"  手机验证 '12345678901': {validate_phone('12345678901')}")

    # 记忆化斐波那契
    print("\n【记忆化装饰器演示】")
    print("-" * 40)
    print(f"  fibonacci_memo(10) = {fibonacci_memo(10)}")
    print(f"  fibonacci_memo(20) = {fibonacci_memo(20)}")
    print(f"  fibonacci_memo(30) = {fibonacci_memo(30)}")
    print(f"  fibonacci_memo(50) = {fibonacci_memo(50)}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
