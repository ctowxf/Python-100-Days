"""
Python循环结构完整指南 - 从基础到企业级应用

本文件涵盖：
1. for-in循环与range()函数
2. while循环
3. break与continue控制流
4. for-else与while-else（Python特有）
5. C++与Python循环对比
6. Pythonic循环：enumerate()与zip()
7. 企业级应用示例

Author: Python-100-Days
Version: 1.0
"""


# ============================================================================
# 第一部分：for-in循环基础
# ============================================================================

def basic_for_in():
    """for-in循环基础用法演示"""
    print("=" * 60)
    print("【1. for-in循环基础】")
    print("=" * 60)

    # 1.1 基本for-in循环
    print("\n1.1 基本for-in循环:")
    for i in range(5):
        print(f"  第{i}次循环")

    # 1.2 range()函数的各种用法
    print("\n1.2 range()函数用法:")

    # range(stop): 0到stop-1
    print(f"  range(5) = {list(range(5))}")

    # range(start, stop): start到stop-1
    print(f"  range(2, 7) = {list(range(2, 7))}")

    # range(start, stop, step): 带步长
    print(f"  range(0, 10, 2) = {list(range(0, 10, 2))}")

    # 负步长：递减序列
    print(f"  range(10, 0, -2) = {list(range(10, 0, -2))}")

    # 1.3 遍历字符串
    print("\n1.3 遍历字符串:")
    for char in "Python":
        print(f"  {char}", end=" ")
    print()

    # 1.4 遍历列表
    print("\n1.4 遍历列表:")
    fruits = ["苹果", "香蕉", "橙子", "葡萄"]
    for fruit in fruits:
        print(f"  {fruit}")


# ============================================================================
# 第二部分：while循环
# ============================================================================

def basic_while():
    """while循环基础用法演示"""
    print("\n" + "=" * 60)
    print("【2. while循环】")
    print("=" * 60)

    # 2.1 基本while循环
    print("\n2.1 基本while循环 - 求1到100的和:")
    total = 0
    i = 1
    while i <= 100:
        total += i
        i += 1
    print(f"  1+2+...+100 = {total}")

    # 2.2 while True + break（不确定循环次数）
    print("\n2.2 while True + break:")
    count = 0
    while True:
        count += 1
        if count > 5:
            break
    print(f"  循环执行了{count}次后break")

    # 2.3 欧几里得算法（辗转相除法）求最大公约数
    print("\n2.3 欧几里得算法求最大公约数:")
    x, y = 48, 36
    a, b = x, y
    while b:
        a, b = b, a % b
    print(f"  gcd({x}, {y}) = {a}")


# ============================================================================
# 第三部分：break与continue
# ============================================================================

def break_continue():
    """break与continue控制流演示"""
    print("\n" + "=" * 60)
    print("【3. break与continue】")
    print("=" * 60)

    # 3.1 break：立即终止循环
    print("\n3.1 break示例 - 查找第一个偶数:")
    numbers = [1, 3, 5, 8, 9, 10]
    for num in numbers:
        if num % 2 == 0:
            print(f"  找到第一个偶数: {num}")
            break

    # 3.2 continue：跳过本次迭代
    print("\n3.2 continue示例 - 只打印奇数:")
    for i in range(1, 11):
        if i % 2 == 0:
            continue
        print(f"  {i}", end=" ")
    print()

    # 3.3 嵌套循环中的break（只跳出内层循环）
    print("\n3.3 嵌套循环中的break:")
    for i in range(3):
        for j in range(5):
            if j == 3:
                break  # 只跳出内层for j循环
            print(f"  ({i},{j})", end=" ")
        print()


# ============================================================================
# 第四部分：for-else与while-else（Python特有语法）
# ============================================================================

def for_else_while_else():
    """
    for-else与while-else演示

    Python特有语法：
    - else子句在循环正常结束时执行（没有被break中断）
    - 如果循环被break中断，else子句不会执行
    - C++中没有这种语法
    """
    print("\n" + "=" * 60)
    print("【4. for-else与while-else（Python特有）】")
    print("=" * 60)

    # 4.1 for-else：正常结束
    print("\n4.1 for-else（正常结束，else会执行）:")
    for i in range(5):
        print(f"  i={i}", end=" ")
    else:
        print("\n  -> 循环正常结束，else子句执行")

    # 4.2 for-else：被break中断
    print("\n4.2 for-else（被break中断，else不会执行）:")
    for i in range(5):
        if i == 3:
            print(f"\n  -> break! i={i}")
            break
        print(f"  i={i}", end=" ")
    else:
        print("  -> 这行不会被执行")

    # 4.3 企业级应用：for-else用于搜索
    print("\n4.3 for-else用于搜索（优雅的模式）:")
    target = 42
    data = [10, 25, 33, 42, 55, 67]
    for item in data:
        if item == target:
            print(f"  找到目标值: {item}")
            break
    else:
        print(f"  未找到目标值: {target}")

    # 4.4 while-else示例
    print("\n4.4 while-else示例:")
    n = 5
    while n > 0:
        print(f"  n={n}", end=" ")
        n -= 1
    else:
        print("\n  -> while循环正常结束")


# ============================================================================
# 第五部分：C++与Python循环对比
# ============================================================================

def cpp_vs_python_comparison():
    """
    C++与Python循环语法对比

    C++传统for循环: for(int i=0; i<n; i++) {...}
    Python等价写法: for i in range(n): ...

    Python的for-else在C++中没有直接等价语法
    """
    print("\n" + "=" * 60)
    print("【5. C++与Python循环对比】")
    print("=" * 60)

    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │                    C++ vs Python 循环对比                    │
    ├─────────────────────────────────────────────────────────────┤
    │  C++:  for(int i=0; i<10; i++) { printf("%d ", i); }       │
    │  Python: for i in range(10): print(i, end=' ')             │
    ├─────────────────────────────────────────────────────────────┤
    │  C++:  for(int i=0; i<10; i+=2) { ... }                    │
    │  Python: for i in range(0, 10, 2): ...                     │
    ├─────────────────────────────────────────────────────────────┤
    │  C++:  for(int i=10; i>0; i--) { ... }                     │
    │  Python: for i in range(10, 0, -1): ...                    │
    ├─────────────────────────────────────────────────────────────┤
    │  C++:  for(auto& item : vector) { ... }  (C++11)           │
    │  Python: for item in iterable: ...                         │
    ├─────────────────────────────────────────────────────────────┤
    │  Python特有: for-else / while-else                         │
    │  C++无直接等价语法，需要用额外的标志变量实现类似逻辑         │
    └─────────────────────────────────────────────────────────────┘
    """)

    # C++等价写法演示
    print("5.1 C++风格 vs Python风格:")

    # C++: for(int i=0; i<5; i++)
    print("  C++:    for(int i=0; i<5; i++)")
    print("  Python: ", end="")
    for i in range(5):
        print(i, end=" ")
    print()

    # C++: for(int i=0; i<10; i+=2)
    print("\n  C++:    for(int i=0; i<10; i+=2)")
    print("  Python: ", end="")
    for i in range(0, 10, 2):
        print(i, end=" ")
    print()

    # C++: for(int i=10; i>0; i--)
    print("\n  C++:    for(int i=10; i>0; i--)")
    print("  Python: ", end="")
    for i in range(10, 0, -1):
        print(i, end=" ")
    print()

    # for-else对比（C++需要额外标志变量）
    print("\n5.2 for-else的C++等价实现:")
    print("""
    // C++实现（需要额外的标志变量）:
    bool found = false;
    for(int i=0; i<n; i++) {
        if(arr[i] == target) {
            found = true;
            break;
        }
    }
    if(!found) {
        printf("未找到\\n");
    }

    // Python实现（使用for-else，更优雅）:
    for item in arr:
        if item == target:
            break
    else:
        print("未找到")
    """)


# ============================================================================
# 第六部分：Pythonic循环 - enumerate()与zip()
# ============================================================================

def pythonic_loops():
    """
    Pythonic循环方式

    enumerate(): 同时获取索引和值，替代C++的索引循环
    zip(): 并行遍历多个序列
    """
    print("\n" + "=" * 60)
    print("【6. Pythonic循环: enumerate()与zip()】")
    print("=" * 60)

    # 6.1 enumerate() - 同时获取索引和值
    print("\n6.1 enumerate()替代C++索引循环:")
    fruits = ["苹果", "香蕉", "橙子", "葡萄"]

    # C++风格（不推荐）
    print("  C++风格（不推荐）:")
    for i in range(len(fruits)):
        print(f"    [{i}] {fruits[i]}")

    # Pythonic风格（推荐）
    print("  Pythonic风格（推荐）:")
    for index, fruit in enumerate(fruits):
        print(f"    [{index}] {fruit}")

    # enumerate()指定起始索引
    print("  enumerate()指定起始索引:")
    for index, fruit in enumerate(fruits, start=1):
        print(f"    第{index}个: {fruit}")

    # 6.2 zip() - 并行遍历多个序列
    print("\n6.2 zip()并行遍历多个序列:")
    names = ["Alice", "Bob", "Charlie"]
    ages = [25, 30, 35]
    cities = ["北京", "上海", "广州"]

    print("  同时遍历姓名、年龄和城市:")
    for name, age, city in zip(names, ages, cities):
        print(f"    {name}, {age}岁, 来自{city}")

    # 6.3 enumerate() + zip()组合
    print("\n6.3 enumerate() + zip()组合:")
    for idx, (name, age) in enumerate(zip(names, ages), 1):
        print(f"    {idx}. {name}: {age}岁")

    # 6.4 字典遍历的Pythonic方式
    print("\n6.4 字典遍历:")
    student = {"name": "小明", "age": 20, "grade": "大二"}
    for key, value in student.items():
        print(f"    {key}: {value}")


# ============================================================================
# 第七部分：企业级应用示例
# ============================================================================

def enterprise_retry_mechanism():
    """
    企业级示例1：重试机制

    模拟网络请求失败后的自动重试，带指数退避策略
    """
    print("\n" + "=" * 60)
    print("【7.1 企业级示例：重试机制（Retry Mechanism）】")
    print("=" * 60)

    import random
    import time

    def unreliable_api_call():
        """模拟不稳定的API调用，70%概率失败"""
        if random.random() < 0.7:
            raise ConnectionError("网络连接超时")
        return {"status": "success", "data": "响应数据"}

    def retry_with_backoff(func, max_retries=5, base_delay=0.1):
        """
        带指数退避的重试机制

        Args:
            func: 要重试的函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）

        Returns:
            函数执行结果

        Raises:
            最后一次重试的异常
        """
        for attempt in range(1, max_retries + 1):
            try:
                result = func()
                print(f"  ✓ 第{attempt}次尝试成功")
                return result
            except Exception as e:
                if attempt == max_retries:
                    print(f"  ✗ 第{attempt}次尝试失败，已达最大重试次数")
                    raise
                # 指数退避：delay = base_delay * 2^(attempt-1)
                delay = base_delay * (2 ** (attempt - 1))
                print(f"  ✗ 第{attempt}次尝试失败: {e}，{delay:.2f}秒后重试...")
                time.sleep(delay)

    # 演示重试机制
    print("\n演示重试机制（最多重试5次）:")
    try:
        result = retry_with_backoff(unreliable_api_call, max_retries=5, base_delay=0.05)
        print(f"  最终结果: {result}")
    except ConnectionError as e:
        print(f"  最终失败: {e}")


def enterprise_pagination_loop():
    """
    企业级示例2：分页查询循环

    模拟从API分页获取数据，直到没有更多数据
    """
    print("\n" + "=" * 60)
    print("【7.2 企业级示例：分页查询循环（Pagination）】")
    print("=" * 60)

    def fetch_page(page_num, page_size=3):
        """模拟分页API调用"""
        # 模拟数据源（共10条数据）
        all_data = [
            {"id": i, "name": f"用户_{i}", "email": f"user{i}@example.com"}
            for i in range(1, 11)
        ]
        start = (page_num - 1) * page_size
        end = start + page_size
        page_data = all_data[start:end]
        has_more = end < len(all_data)
        return page_data, has_more

    print("\n分页获取数据（每页3条）:")
    all_results = []
    page_num = 1

    while True:
        page_data, has_more = fetch_page(page_num)
        all_results.extend(page_data)
        print(f"  第{page_num}页: 获取{len(page_data)}条数据")

        if not has_more:
            print(f"  已到达最后一页，共获取{len(all_results)}条数据")
            break

        page_num += 1

    # 显示结果
    print("\n  数据预览:")
    for item in all_results[:5]:
        print(f"    {item}")
    if len(all_results) > 5:
        print(f"    ... 共{len(all_results)}条")


def enterprise_batch_processing():
    """
    企业级示例3：数据批量处理

    模拟大数据量的分批处理场景
    """
    print("\n" + "=" * 60)
    print("【7.3 企业级示例：数据批量处理（Batch Processing）】")
    print("=" * 60)

    def process_batch(batch):
        """模拟处理一批数据"""
        results = []
        for item in batch:
            # 模拟数据处理（如：数据清洗、转换等）
            processed = {
                "id": item["id"],
                "value": item["value"] * 2,
                "status": "processed"
            }
            results.append(processed)
        return results

    # 生成模拟数据（100条）
    data = [{"id": i, "value": i * 10} for i in range(1, 101)]

    batch_size = 20
    total_batches = (len(data) + batch_size - 1) // batch_size

    print(f"\n数据总量: {len(data)}条")
    print(f"批次大小: {batch_size}条")
    print(f"总批次数: {total_batches}")

    print("\n开始批量处理:")
    all_processed = []

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(data))
        current_batch = data[start_idx:end_idx]

        # 处理当前批次
        batch_results = process_batch(current_batch)
        all_processed.extend(batch_results)

        progress = (batch_num + 1) / total_batches * 100
        print(f"  批次{batch_num + 1}/{total_batches}: "
              f"处理{len(current_batch)}条 | 进度: {progress:.0f}%")

    print(f"\n  ✓ 处理完成，共处理{len(all_processed)}条数据")


def enterprise_polling_pattern():
    """
    企业级示例4：轮询模式（Polling Pattern）

    模拟定期检查任务状态，直到任务完成或超时
    """
    print("\n" + "=" * 60)
    print("【7.4 企业级示例：轮询模式（Polling Pattern）】")
    print("=" * 60)

    import random
    import time

    def check_task_status(task_id):
        """模拟检查异步任务状态"""
        # 模拟任务进度
        if not hasattr(check_task_status, 'progress'):
            check_task_status.progress = 0

        check_task_status.progress += random.randint(15, 35)
        if check_task_status.progress >= 100:
            check_task_status.progress = 100
            return {"status": "completed", "progress": 100}
        return {"status": "running", "progress": check_task_status.progress}

    def poll_task(task_id, interval=0.1, timeout=2.0):
        """
        轮询任务状态直到完成或超时

        Args:
            task_id: 任务ID
            interval: 轮询间隔（秒）
            timeout: 超时时间（秒）

        Returns:
            最终任务状态
        """
        start_time = time.time()
        attempt = 0

        while True:
            attempt += 1
            elapsed = time.time() - start_time

            # 检查超时
            if elapsed > timeout:
                print(f"  ⏱ 超时！已等待{elapsed:.1f}秒")
                return {"status": "timeout", "progress": check_task_status.progress}

            # 检查任务状态
            status = check_task_status(task_id)
            print(f"  轮询#{attempt}: 状态={status['status']}, "
                  f"进度={status['progress']}%, 耗时={elapsed:.2f}s")

            if status["status"] == "completed":
                print(f"  ✓ 任务完成！总耗时: {elapsed:.2f}秒")
                return status

            # 等待下次轮询
            time.sleep(interval)

    # 演示轮询模式
    print("\n开始轮询任务状态:")
    result = poll_task("task_001", interval=0.1, timeout=2.0)
    print(f"  最终结果: {result}")


def enterprise_search_with_fallback():
    """
    企业级示例5：带降级的搜索模式

    使用for-else实现优雅的多数据源搜索
    """
    print("\n" + "=" * 60)
    print("【7.5 企业级示例：带降级的搜索模式】")
    print("=" * 60)

    # 模拟多个数据源
    cache = {"user_1001": {"name": "Alice", "source": "cache"}}
    database = {"user_1002": {"name": "Bob", "source": "database"}}
    remote_api = {"user_1003": {"name": "Charlie", "source": "remote"}}

    def search_user(user_id):
        """
        从多个数据源搜索用户，使用for-else实现优雅降级

        搜索顺序: 缓存 -> 数据库 -> 远程API -> 默认值
        """
        sources = [
            ("缓存", cache),
            ("数据库", database),
            ("远程API", remote_api)
        ]

        for source_name, source in sources:
            if user_id in source:
                result = source[user_id]
                print(f"  ✓ 从{source_name}找到: {result}")
                return result
        else:
            # 所有数据源都未找到，执行降级逻辑
            default = {"name": "未知用户", "source": "default"}
            print(f"  ✗ 所有数据源未找到，返回默认值: {default}")
            return default

    # 测试不同用户
    print("\n搜索用户:")
    for uid in ["user_1001", "user_1002", "user_1003", "user_9999"]:
        print(f"\n  搜索 {uid}:")
        search_user(uid)


# ============================================================================
# 第八部分：嵌套循环与模式打印
# ============================================================================

def nested_loops_patterns():
    """嵌套循环与模式打印"""
    print("\n" + "=" * 60)
    print("【8. 嵌套循环与模式打印】")
    print("=" * 60)

    # 8.1 九九乘法表
    print("\n8.1 九九乘法表:")
    for i in range(1, 10):
        for j in range(1, i + 1):
            print(f"{j}×{i}={i*j}", end="\t")
        print()

    # 8.2 等腰三角形
    print("\n8.2 等腰三角形（5行）:")
    n = 5
    for i in range(1, n + 1):
        spaces = " " * (n - i)
        stars = "*" * (2 * i - 1)
        print(f"  {spaces}{stars}")


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        Python循环结构完整指南 - 从基础到企业级应用        ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # 基础部分
    basic_for_in()
    basic_while()
    break_continue()
    for_else_while_else()

    # C++对比
    cpp_vs_python_comparison()

    # Pythonic循环
    pythonic_loops()

    # 嵌套循环
    nested_loops_patterns()

    # 企业级示例
    enterprise_retry_mechanism()
    enterprise_pagination_loop()
    enterprise_batch_processing()
    enterprise_polling_pattern()
    enterprise_search_with_fallback()

    print("\n" + "=" * 60)
    print("【总结】")
    print("=" * 60)
    print("""
    Python循环核心要点:
    ┌─────────────────────────────────────────────────────────────┐
    │ 1. for-in: 已知循环次数时使用                               │
    │ 2. while:  未知循环次数时使用                               │
    │ 3. break:  立即终止当前循环                                 │
    │ 4. continue: 跳过本次迭代，进入下一次                       │
    │ 5. for-else: 循环正常结束时执行（未被break中断）            │
    │ 6. while-else: 同上                                         │
    │ 7. enumerate(): 获取索引和值（替代C++索引循环）             │
    │ 8. zip(): 并行遍历多个序列                                 │
    │ 9. range(): 生成整数序列（替代C++的for(int i=0;i<n;i++)）  │
    └─────────────────────────────────────────────────────────────┘
    """)
