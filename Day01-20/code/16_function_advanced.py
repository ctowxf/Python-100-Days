"""
Python 函数使用进阶 -- 高阶函数、Lambda、闭包、装饰器、递归
============================================================

本文件覆盖 Day01-20 中第 16 课与第 17 课的核心知识点：
  - 高阶函数 (Higher-Order Functions)
  - Lambda 匿名函数与偏函数 (partial)
  - 作用域：global / nonlocal
  - 闭包 (Closures)
  - 装饰器 (Decorators)：基础、带参、叠加
  - 递归 (Recursion)
  - Python 与 C++ 的对比注释
  - 企业级装饰器实战：retry / timing / caching / auth

运行方式：
  python 16_function_advanced.py

Version: 1.0
"""

import functools
import operator
import time
import hashlib
import random
from functools import wraps


# ==============================================================================
# 第一部分 -- 高阶函数
# ==============================================================================

def calc(init_value, op_func, *args, **kwargs):
    """高阶函数示例：将二元运算作为参数传入，实现通用的聚合计算。

    Args:
        init_value: 运算的初始值（累加用 0，累乘用 1）。
        op_func: 二元运算函数，如 operator.add / operator.mul。
        *args:  任意个位置参数。
        **kwargs: 任意个关键字参数。

    Returns:
        聚合运算的结果。
    """
    items = list(args) + list(kwargs.values())
    result = init_value
    for item in items:
        if type(item) in (int, float):
            result = op_func(result, item)
    return result


def demo_higher_order_functions():
    """演示高阶函数的基本用法。"""
    print("=" * 60)
    print("高阶函数 (Higher-Order Functions)")
    print("=" * 60)

    # 1) 用 operator.add 做求和
    print(calc(0, operator.add, 1, 2, 3, 4, 5))  # 15

    # 2) 用 operator.mul 做累乘
    print(calc(1, operator.mul, 1, 2, 3, 4, 5))  # 120

    # 3) filter + map -- 过滤偶数后求平方
    old_nums = [35, 12, 8, 99, 60, 52]
    new_nums = list(map(lambda x: x ** 2, filter(lambda x: x % 2 == 0, old_nums)))
    print("filter + map 结果:", new_nums)  # [144, 64, 3600, 2704]

    # 4) 列表生成式实现相同功能（更 Pythonic）
    new_nums2 = [num ** 2 for num in old_nums if num % 2 == 0]
    print("列表生成式结果:  ", new_nums2)

    # 5) sorted 的 key 参数 -- 按字符串长度排序
    old_strings = ['in', 'apple', 'zoo', 'waxberry', 'pear']
    print("默认排序:  ", sorted(old_strings))
    print("按长度排序:", sorted(old_strings, key=len))


# ==============================================================================
# 第二部分 -- Lambda 匿名函数与偏函数
# ==============================================================================

def demo_lambda_and_partial():
    """演示 Lambda 函数和偏函数 (functools.partial)。"""
    print("\n" + "=" * 60)
    print("Lambda 匿名函数 & 偏函数 (partial)")
    print("=" * 60)

    # ---- Lambda: 一行代码实现阶乘 ----
    fac = lambda n: functools.reduce(operator.mul, range(2, n + 1), 1)
    print("fac(6) =", fac(6))  # 720

    # ---- Lambda: 一行代码判断素数 ----
    is_prime = lambda x: x > 1 and all(
        map(lambda f: x % f, range(2, int(x ** 0.5) + 1))
    )
    print("is_prime(37) =", is_prime(37))  # True
    print("is_prime(1)  =", is_prime(1))   # False

    # ---- 偏函数: 固定 int 的 base 参数 ----
    int2 = functools.partial(int, base=2)
    int8 = functools.partial(int, base=8)
    int16 = functools.partial(int, base=16)
    print("int('1001')   =", int('1001'))     # 1001
    print("int2('1001')  =", int2('1001'))     # 9
    print("int8('1001')  =", int8('1001'))     # 513
    print("int16('1001') =", int16('1001'))    # 4097

    # ---- Python lambda vs C++ lambda ----
    # C++:  auto add = [](int a, int b) { return a + b; };
    # Python: add = lambda a, b: a + b
    # 主要区别:
    #   1. Python lambda 只能包含单个表达式，C++ lambda 可包含多条语句。
    #   2. C++ lambda 用 [] 显式捕获外部变量；Python lambda 隐式捕获（闭包）。
    #   3. C++ lambda 可以指定返回类型；Python lambda 返回表达式的值。
    add = lambda a, b: a + b
    print("lambda add(3, 4) =", add(3, 4))  # 7


# ==============================================================================
# 第三部分 -- 作用域: global / nonlocal
# ==============================================================================

# 全局变量示例
counter = 0


def demo_scope():
    """演示 global 与 nonlocal 关键字的作用域规则。"""
    print("\n" + "=" * 60)
    print("作用域: global / nonlocal")
    print("=" * 60)

    # ---- global: 在函数内部修改全局变量 ----
    global counter
    print("修改前 counter =", counter)
    counter += 10
    print("修改后 counter =", counter)

    # ---- nonlocal: 在嵌套函数中修改外层函数的变量 ----
    def outer():
        msg = "outer"

        def inner():
            nonlocal msg
            msg = "inner modified"
            print("  inner() 中 msg =", msg)

        inner()
        print("  outer() 中 msg =", msg)

    outer()

    # ---- 对比三种作用域 ----
    x = "global"

    def level1():
        x = "level1-local"

        def level2():
            nonlocal x          # 引用 level1 的 x
            x = "level2-nonlocal"
            print("  level2 x =", x)

        level2()
        print("  level1 x =", x)

    level1()
    print("  global x =", x)

    # ---- Python vs C++ 作用域对比 ----
    # Python: LEGB 规则 -- Local -> Enclosing -> Global -> Built-in
    # C++:    块作用域，内层同名变量遮蔽外层，无 Enclosing 概念；
    #         C++17 的 structured bindings 和 captured variables 提供类似能力。
    # Python nonlocal 对应 C++ lambda 的 [&] (按引用捕获)。


# ==============================================================================
# 第四部分 -- 闭包 (Closures)
# ==============================================================================

def demo_closures():
    """演示闭包的原理与经典用法。"""
    print("\n" + "=" * 60)
    print("闭包 (Closures)")
    print("=" * 60)

    # ---- 闭包基础: 计数器 ----
    def make_counter(start=0):
        """返回一个计数器函数，每次调用返回递增的值。"""
        count = [start]  # 使用列表以便在内部函数中修改

        def counter_func():
            count[0] += 1
            return count[0]

        return counter_func

    c = make_counter(10)
    print("闭包计数器:", c(), c(), c())  # 11 12 13

    # ---- 闭包实现乘法器工厂 ----
    def make_multiplier(factor):
        """返回一个将输入乘以 factor 的函数。"""
        def multiplier(x):
            return x * factor
        return multiplier

    double = make_multiplier(2)
    triple = make_multiplier(3)
    print("double(5) =", double(5))  # 10
    print("triple(5) =", triple(5))  # 15

    # ---- 闭包实现缓存 ----
    def make_cache():
        """用闭包实现简单的函数结果缓存。"""
        cache = {}

        def cached_square(n):
            if n not in cache:
                print(f"  计算 {n} 的平方...")
                cache[n] = n ** 2
            else:
                print(f"  {n} 的平方已在缓存中")
            return cache[n]

        return cached_square

    sq = make_cache()
    print("cached_square(4) =", sq(4))   # 计算
    print("cached_square(4) =", sq(4))   # 命中缓存
    print("cached_square(5) =", sq(5))   # 计算

    # ---- Python 闭包 vs C++ lambda with capture ----
    # Python 闭包:
    #   def make_adder(n):
    #       def adder(x): return x + n   # n 被隐式捕获
    #       return adder
    #
    # C++ 等价:
    #   auto make_adder(int n) {
    #       return [n](int x) { return x + n; };  // [n] 按值捕获
    #   }
    #
    # 关键区别:
    #   1. Python 隐式捕获外层变量；C++ 必须在 [] 中显式列出。
    #   2. C++ 可选 [n] 按值捕获 或 [&n] 按引用捕获；
    #      Python 闭包中的可变对象(如列表)天然按引用共享。
    #   3. Python 闭包变量在函数销毁前一直存活；
    #      C++ lambda 按值捕获的变量生命周期取决于 lambda 对象本身。
    #   4. Python 函数是一等公民，天然支持闭包；
    #      C++ 需要 C++11 及以上版本的 lambda 语法。


# ==============================================================================
# 第五部分 -- 递归 (Recursion)
# ==============================================================================

def demo_recursion():
    """演示递归的经典例子和优化技巧。"""
    print("\n" + "=" * 60)
    print("递归 (Recursion)")
    print("=" * 60)

    # ---- 递归求阶乘 ----
    def fac(n):
        if n in (0, 1):
            return 1
        return n * fac(n - 1)

    print("fac(5) =", fac(5))   # 120
    print("fac(10) =", fac(10)) # 3628800

    # ---- 递归求斐波那契（原始版本，性能差） ----
    def fib_naive(n):
        if n in (1, 2):
            return 1
        return fib_naive(n - 1) + fib_naive(n - 2)

    # ---- 用 lru_cache 装饰器优化递归 ----
    @functools.lru_cache(maxsize=256)
    def fib_cached(n):
        if n in (1, 2):
            return 1
        return fib_cached(n - 1) + fib_cached(n - 2)

    print("fib_cached(10) =", fib_cached(10))  # 55
    print("fib_cached(50) =", fib_cached(50))  # 12586269025

    # ---- 递归：循环递推版本（最高效） ----
    def fib_iter(n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    print("fib_iter(50)  =", fib_iter(50))

    # ---- 递归求幂（快速幂算法） ----
    def power(base, exp):
        """递归实现快速幂: O(log n)"""
        if exp == 0:
            return 1
        if exp % 2 == 0:
            half = power(base, exp // 2)
            return half * half
        else:
            return base * power(base, exp - 1)

    print("power(2, 10) =", power(2, 10))  # 1024

    # ---- 递归遍历嵌套字典（企业常见） ----
    def flatten_dict(d, parent_key='', sep='.'):
        """将嵌套字典展平为单层字典。"""
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten_dict(v, new_key, sep))
            else:
                items[new_key] = v
        return items

    nested = {
        "db": {"host": "localhost", "port": 5432, "credentials": {"user": "admin", "pass": "secret"}},
        "cache": {"redis": {"host": "127.0.0.1", "port": 6379}}
    }
    print("展平嵌套字典:", flatten_dict(nested))


# ==============================================================================
# 第六部分 -- 装饰器 (Decorators)
# ==============================================================================

# ---------- 6.1 基础装饰器 ----------

def record_time(func):
    """计时装饰器：记录函数执行时间。

    Python 装饰器 vs C++ 装饰器模式:
    ---------------------------------
    Python 装饰器是一种语法糖，本质是高阶函数：
        @decorator
        def func(): ...
        等价于: func = decorator(func)
    C++ 没有原生装饰器语法，通常通过以下方式实现：
        1. 装饰器模式 (Decorator Pattern) -- 组合+继承，接口不变。
        2. C++ 模板元编程。
        3. C++11 lambda 包装。
    Python 装饰器在**定义时**修改函数行为；
    C++ 装饰器模式在**运行时**通过对象组合修改行为。
    Python 更灵活（动态修改任意函数），C++ 更显式（类型安全）。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] 执行时间: {elapsed:.6f} 秒")
        return result
    return wrapper


# ---------- 6.2 企业级装饰器：重试机制 ----------

def retry(max_attempts=3, delay=1.0, exceptions=(Exception,)):
    """重试装饰器：在函数抛出指定异常时自动重试。

    企业级应用场景：
    - 网络请求失败后重试
    - 数据库连接断开后重连
    - 第三方 API 临时不可用

    Args:
        max_attempts: 最大尝试次数（含首次调用）。
        delay: 每次重试之间的等待秒数。
        exceptions: 需要捕获并重试的异常类型元组。
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait = delay * attempt  # 退避策略
                        print(f"  [{func.__name__}] 第 {attempt} 次失败: {e}, "
                              f"{wait}s 后重试...")
                        time.sleep(wait)
                    else:
                        print(f"  [{func.__name__}] 第 {attempt} 次失败，已达到最大重试次数")
            raise last_exception
        return wrapper
    return decorator


# ---------- 6.3 企业级装饰器：缓存 ----------

def memoize(func):
    """手动实现的记忆化装饰器，替代 functools.lru_cache 的简单版本。

    企业级应用场景：
    - 避免重复计算昂贵的纯函数结果
    - 缓存数据库查询结果
    - 缓存配置文件解析结果
    """
    cache = {}

    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    wrapper.cache = cache  # 暴露缓存供外部检查/清除
    wrapper.cache_clear = lambda: cache.clear()
    return wrapper


# ---------- 6.4 企业级装饰器：权限验证 ----------

def require_auth(required_role=None):
    """认证装饰器：模拟检查用户是否具有指定角色。

    企业级应用场景：
    - Web API 的接口权限校验
    - 微服务间的调用鉴权
    - 管理后台的功能级别权限控制

    Args:
        required_role: 需要的角色名，None 表示仅需登录。
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 模拟从上下文获取当前用户
            current_user = kwargs.pop('_current_user', None)
            if current_user is None:
                raise PermissionError("未登录：缺少 _current_user 参数")
            if required_role and current_user.get('role') != required_role:
                raise PermissionError(
                    f"权限不足：用户 '{current_user['name']}' "
                    f"没有 '{required_role}' 角色"
                )
            print(f"  [auth] 用户 '{current_user['name']}' 权限验证通过")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ---------- 6.5 带参数的装饰器 ----------

def log(level="INFO"):
    """带参数的日志装饰器，允许调用者指定日志级别。

    带参装饰器实际上是一个"返回装饰器的函数"：
    @log("DEBUG")  -->  log("DEBUG") 返回 decorator --> decorator(func)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"  [{level}] 调用 {func.__name__}({args}, {kwargs})")
            result = func(*args, **kwargs)
            print(f"  [{level}] {func.__name__} 返回 {result}")
            return result
        return wrapper
    return decorator


# ---------- 6.6 叠加装饰器 ----------

def uppercase(func):
    """将函数返回值转为大写字符串。"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return str(result).upper()
    return wrapper


def add_exclamation(func):
    """在函数返回值后追加感叹号。"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return str(result) + "!!!"
    return wrapper


# ---------- 6.7 装饰器演示函数 ----------

@record_time
def simulate_download(filename):
    """模拟文件下载。"""
    duration = random.uniform(0.01, 0.05)
    time.sleep(duration)
    return f"{filename} 下载完成"


@retry(max_attempts=3, delay=0.1, exceptions=(ConnectionError,))
def unreliable_api_call(data):
    """模拟不稳定的第三方 API 调用（约 60% 概率失败）。"""
    if random.random() < 0.6:
        raise ConnectionError(f"服务端返回 503，请求数据: {data}")
    return {"status": "ok", "data": data}


@memoize
def expensive_calculation(n):
    """模拟昂贵的计算。"""
    print(f"  [memoize] 正在计算 {n} 的结果...")
    time.sleep(0.1)
    return n ** 3


@log("DEBUG")
def add_numbers(a, b):
    return a + b


@uppercase
@add_exclamation
def greet(name):
    return f"hello {name}"


@require_auth(required_role="admin")
def delete_user(user_id):
    """模拟删除用户的管理操作。"""
    return f"用户 {user_id} 已被删除"


def demo_decorators():
    """演示装饰器的各类用法。"""
    print("\n" + "=" * 60)
    print("装饰器 (Decorators)")
    print("=" * 60)

    # 1) 计时装饰器
    simulate_download("report.pdf")

    # 2) 重试装饰器
    print("\n重试装饰器演示:")
    try:
        result = unreliable_api_call("query=python")
        print(f"  API 返回: {result}")
    except ConnectionError as e:
        print(f"  最终失败: {e}")

    # 3) 缓存装饰器
    print("\n缓存装饰器演示:")
    print("  结果:", expensive_calculation(10))
    print("  结果:", expensive_calculation(10))  # 命中缓存，不会重新计算
    print("  缓存内容:", expensive_calculation.cache)

    # 4) 日志装饰器
    print("\n日志装饰器演示:")
    add_numbers(3, 5)

    # 5) 叠加装饰器（执行顺序: 从下到上 --> add_exclamation 先, uppercase 后）
    print("\n叠加装饰器演示:")
    print("  greet('world') =", greet('world'))  # HELLO WORLD!!!

    # 6) 认证装饰器 -- 通过
    print("\n认证装饰器演示 (通过):")
    admin = {"name": "Alice", "role": "admin"}
    print("  ", delete_user(42, _current_user=admin))

    # 7) 认证装饰器 -- 拒绝
    print("\n认证装饰器演示 (拒绝):")
    viewer = {"name": "Bob", "role": "viewer"}
    try:
        delete_user(42, _current_user=viewer)
    except PermissionError as e:
        print(f"  PermissionError: {e}")

    # 8) 使用 __wrapped__ 绕过装饰器
    print("\n使用 __wrapped__ 绕过装饰器:")
    simulate_download.__wrapped__("raw_file.dat")


# ==============================================================================
# 第七部分 -- Python vs C++ 综合对比表
# ==============================================================================

def print_cpp_comparison():
    """打印 Python 与 C++ 在函数高级特性上的对比。"""
    print("\n" + "=" * 60)
    print("Python vs C++ 函数高级特性对比")
    print("=" * 60)

    comparisons = [
        ("特性", "Python", "C++"),
        ("-" * 20, "-" * 20, "-" * 20),
        (
            "闭包",
            "隐式捕获外层变量\n"
            "  def make(n):\n"
            "    return lambda x: x + n",
            "[n] 按值 / [&n] 按引用显式捕获\n"
            "  auto make(int n){\n"
            "    return [n](int x){return x+n;};}"
        ),
        (
            "装饰器",
            "@decorator 语法糖\n"
            "  定义时替换函数\n"
            "  动态/灵活/元编程",
            "装饰器模式 (OOP)\n"
            "  运行时组合/继承\n"
            "  显式/类型安全"
        ),
        (
            "Lambda",
            "lambda x: x + 1\n"
            "  仅限单个表达式\n"
            "  无类型声明",
            "[](int x){ return x+1; }\n"
            "  可多条语句\n"
            "  需声明捕获和返回类型"
        ),
        (
            "一等函数",
            "函数天然是一等公民\n"
            "  可赋值/传参/返回",
            "C++11 lambda + std::function\n"
            "  可赋值/传参/返回"
        ),
        (
            "递归优化",
            "lru_cache 装饰器\n"
            "  sys.setrecursionlimit",
            "编译器尾递归优化\n"
            "  constexpr 编译期计算"
        ),
    ]

    for row in comparisons:
        print(f"  {row[0]:<20} | {row[1]:<22} | {row[2]}")


# ==============================================================================
# 主程序入口
# ==============================================================================

if __name__ == "__main__":
    demo_higher_order_functions()
    demo_lambda_and_partial()
    demo_scope()
    demo_closures()
    demo_recursion()
    demo_decorators()
    print_cpp_comparison()

    print("\n" + "=" * 60)
    print("所有演示执行完毕！")
    print("=" * 60)
