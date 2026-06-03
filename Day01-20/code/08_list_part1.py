"""
Python 列表 (list) 入门 —— 第 08 天练习与扩展

覆盖内容:
    1. 列表创建（字面量、list() 构造器、列表推导式）
    2. 索引（正向 / 反向）
    3. 切片 [start:end:stride]
    4. 常用方法: append, insert, remove, pop, sort, reverse
    5. 列表运算: +, *, in / not in, 关系比较
    6. 遍历列表
    7. C++ 对比说明
    8. 企业级示例: 任务队列、日志缓冲区、最近浏览记录

Author: Python-100-Days
Version: 1.0
"""

import random
from collections import deque


# ============================================================
# 1. 列表创建
# ============================================================

def demo_create_list():
    """演示列表的多种创建方式"""

    # ---------- 1a. 字面量语法 ----------
    nums = [35, 12, 99, 68, 55, 35, 87]
    langs = ['Python', 'Java', 'Go', 'Kotlin']
    mixed = [100, 12.3, 'Python', True]  # 可以混放，但不推荐

    print("=== 字面量创建 ===")
    print(f"nums  : {nums}")
    print(f"langs : {langs}")
    print(f"mixed : {mixed}")

    # ---------- 1b. list() 构造器 ----------
    nums_from_range = list(range(1, 10))
    chars_from_str = list('hello')

    print("\n=== list() 构造器 ===")
    print(f"list(range(1,10))  -> {nums_from_range}")
    print(f"list('hello')      -> {chars_from_str}")

    # ---------- 1c. 列表推导式 ----------
    # Python list comprehension has no C++ equivalent
    # C++ 没有直接对应的语法，需要 std::transform + lambda 或手写循环
    squares = [x ** 2 for x in range(1, 11)]
    evens = [x for x in range(20) if x % 2 == 0]

    print("\n=== 列表推导式 (list comprehension) ===")
    print(f"[x**2 for x in range(1,11)]            -> {squares}")
    print(f"[x for x in range(20) if x % 2 == 0]   -> {evens}")

    # ---------- 1d. 重复运算创建 ----------
    counters = [0] * 6
    print(f"\n[0] * 6 -> {counters}")


# ============================================================
# 2. 索引（正向 / 反向）
# ============================================================

def demo_indexing():
    """演示正向索引和反向索引"""

    fruits = ['apple', 'banana', 'cherry', 'durian', 'elderberry']
    print("=== 索引演示 ===")
    print(f"fruits = {fruits}")
    print(f"正向索引: fruits[0]={fruits[0]}, fruits[2]={fruits[2]}, fruits[4]={fruits[4]}")
    print(f"反向索引: fruits[-1]={fruits[-1]}, fruits[-3]={fruits[-3]}, fruits[-5]={fruits[-5]}")

    # 通过索引修改元素
    fruits[1] = 'blueberry'
    print(f"\n修改 fruits[1] = 'blueberry' -> {fruits}")

    # 索引越界演示（注释掉以免中断程序）
    # fruits[5]  # IndexError: list index out of range
    # fruits[-6] # IndexError: list index out of range


# ============================================================
# 3. 切片 [start:end:stride]
# ============================================================

def demo_slicing():
    """
    演示切片操作

    Python 切片 vs C++ std::span:
        - Python: list[start:end:stride] 内建语法，返回新列表（浅拷贝）
        - C++20:  std::span<int> s(vec.data()+1, 3) 是视图，不拷贝数据
        - Python 切片越界不报错，自动截断；C++ span 越界是 UB
    """

    items = ['apple', 'strawberry', 'durian', 'peach', 'watermelon']
    print("=== 切片演示 ===")
    print(f"items = {items}")
    print(f"items[1:3]     -> {items[1:3]}")       # ['strawberry', 'durian']
    print(f"items[:3]      -> {items[:3]}")         # 省略 start=0
    print(f"items[::2]     -> {items[::2]}")        # 步长为2
    print(f"items[-4:-2]   -> {items[-4:-2]}")      # 反向索引切片
    print(f"items[-2::-1]  -> {items[-2::-1]}")     # 反向步长，倒序遍历
    print(f"items[::-1]    -> {items[::-1]}")        # 整个列表反转

    # 通过切片批量修改
    items[1:3] = ['x', 'o']
    print(f"\nitems[1:3] = ['x','o'] -> {items}")


# ============================================================
# 4. 常用方法: append, insert, remove, pop, sort, reverse
# ============================================================

def demo_methods():
    """演示列表最常用的六种方法"""

    print("=== 列表方法演示 ===")

    # ---------- append: 在末尾追加 ----------
    stack = []
    stack.append('task_A')
    stack.append('task_B')
    stack.append('task_C')
    print(f"append 后: {stack}")

    # ---------- insert: 在指定位置插入 ----------
    stack.insert(1, 'task_X')   # 在索引1处插入
    print(f"insert(1, 'task_X'): {stack}")

    # ---------- remove: 删除第一个匹配项 ----------
    stack.remove('task_X')
    print(f"remove('task_X'): {stack}")

    # ---------- pop: 弹出末尾元素（默认）或指定索引 ----------
    last = stack.pop()
    print(f"pop() -> '{last}', 剩余: {stack}")

    first = stack.pop(0)
    print(f"pop(0) -> '{first}', 剩余: {stack}")

    # ---------- sort: 原地排序 ----------
    nums = [64, 34, 25, 12, 22, 11, 90]
    print(f"\n排序前: {nums}")
    nums.sort()                     # 升序
    print(f"sort() 升序: {nums}")
    nums.sort(reverse=True)         # 降序
    print(f"sort(reverse=True) 降序: {nums}")

    # ---------- reverse: 原地反转 ----------
    nums.reverse()
    print(f"reverse() 后: {nums}")


# ============================================================
# 5. 列表运算: +, *, in / not in, 关系比较
# ============================================================

def demo_operations():
    """演示列表的运算符"""

    print("=== 列表运算演示 ===")

    a = [1, 2, 3]
    b = [4, 5, 6]

    # 拼接
    print(f"{a} + {b} = {a + b}")

    # 重复
    print(f"{a} * 3 = {a * 3}")

    # 成员测试
    print(f"2 in {a}        -> {2 in a}")
    print(f"9 not in {a}    -> {9 not in a}")

    # 关系比较（逐元素字典序）
    print(f"\n[1,2,3] == [1,2,3]  -> {[1,2,3] == [1,2,3]}")
    print(f"[1,2,3] < [3,2,1]   -> {[1,2,3] < [3,2,1]}")


# ============================================================
# 6. 遍历列表
# ============================================================

def demo_iteration():
    """演示两种遍历方式"""

    languages = ['Python', 'Java', 'C++', 'Kotlin']
    print("=== 遍历方式一: 索引遍历 ===")
    for i in range(len(languages)):
        print(f"  [{i}] {languages[i]}")

    print("\n=== 遍历方式二: 直接遍历 ===")
    for lang in languages:
        print(f"  {lang}")

    print("\n=== 遍历方式三: enumerate (推荐) ===")
    for idx, lang in enumerate(languages):
        print(f"  [{idx}] {lang}")


# ============================================================
# 7. 经典案例: 掷骰子统计
# ============================================================

def dice_simulation(times=6000):
    """
    掷骰子模拟 —— 用列表替代多个变量

    重构前需要 6 个变量 + 6 个 if/elif 分支;
    重构后只需要 1 个长度为 6 的列表 + 1 行索引操作。
    """
    counters = [0] * 6
    for _ in range(times):
        face = random.randrange(1, 7)
        counters[face - 1] += 1

    print(f"\n=== 掷骰子 {times} 次统计 ===")
    for face in range(1, 7):
        bar = '#' * (counters[face - 1] // 20)
        print(f"  {face}点: {counters[face - 1]:>4} 次  {bar}")


# ============================================================
# 8. C++ 对比说明
# ============================================================

def cpp_comparison_notes():
    """
    打印 Python list 与 C++ std::vector 的对比说明
    """
    notes = """
=== C++ 对比说明 ===

1) Python list vs C++ std::vector
   ---------------------------------------------------------------
   Python list:
     - 动态类型: 同一列表可存放 int, str, float 等混合类型
     - 语法简洁: [1, 2, 3]、列表推导式
     - 底层是 PyObject* 指针数组，内存开销大于 vector

   C++ std::vector<int>:
     - 静态类型: 所有元素必须是同一类型
     - 连续内存布局，缓存友好，性能更高
     - 需要 #include <vector>，语法更繁琐

   Python:
       nums = [1, 2, 3]
       nums.append(4)

   C++:
       std::vector<int> nums = {1, 2, 3};
       nums.push_back(4);

2) Python list comprehension has no C++ equivalent
   ---------------------------------------------------------------
   Python 列表推导式是一种声明式构造列表的语法糖，
   C++ 中没有直接等价物，需要借助 std::transform、
   std::copy_if 或手写 for 循环。

   Python:
       squares = [x**2 for x in range(10) if x % 2 == 0]

   C++ (最接近的写法):
       std::vector<int> squares;
       for (int x = 0; x < 10; ++x) {
           if (x % 2 == 0) squares.push_back(x * x);
       }

3) Slicing [1:3] vs C++ std::span
   ---------------------------------------------------------------
   Python:
       sub = nums[1:3]          # 返回新列表（浅拷贝）
       sub = nums[::-1]         # 反转，返回新列表
       # 越界自动截断，不报错

   C++20:
       std::span<int> s(vec.data()+1, 2);  // 视图，不拷贝
       // 没有内建步长/反转语法，需手动实现
       // 越界是未定义行为(UB)
"""
    print(notes)


# ============================================================
# 9. 企业级示例
# ============================================================

# ---------- 9a. 任务队列 (Task Queue) ----------

class TaskQueue:
    """
    基于 list 的简单任务队列 (FIFO)

    企业场景: Web 服务器将用户请求放入队列，
    后台 Worker 依次取出并处理。
    使用 list 的 append + pop(0) 实现。
    """

    def __init__(self):
        self._tasks: list[str] = []

    def enqueue(self, task: str):
        """将任务加入队尾"""
        self._tasks.append(task)
        print(f"  [入队] {task}  | 队列: {self._tasks}")

    def dequeue(self) -> str | None:
        """从队头取出任务"""
        if not self._tasks:
            print("  [队列为空]")
            return None
        task = self._tasks.pop(0)
        print(f"  [出队] {task}  | 队列: {self._tasks}")
        return task

    @property
    def size(self) -> int:
        return len(self._tasks)

    def __repr__(self):
        return f"TaskQueue({self._tasks})"


def demo_task_queue():
    print("=== 企业示例: 任务队列 ===")
    tq = TaskQueue()
    tq.enqueue("处理用户注册 #1001")
    tq.enqueue("发送订单确认邮件 #2002")
    tq.enqueue("生成日报 #3003")
    tq.dequeue()
    tq.dequeue()
    print(f"  剩余任务数: {tq.size}")


# ---------- 9b. 日志缓冲区 (Log Buffer) ----------

class LogBuffer:
    """
    固定大小的日志缓冲区

    企业场景: 高并发系统中，日志先写入内存缓冲区，
    攒满一批后一次性 flush 到磁盘或日志服务。
    当缓冲区满时，自动丢弃最早的日志。
    """

    def __init__(self, capacity: int = 100):
        self._capacity = capacity
        self._buffer: list[str] = []

    def write(self, message: str):
        """写入一条日志，超出容量则丢弃最旧的"""
        if len(self._buffer) >= self._capacity:
            discarded = self._buffer.pop(0)
            print(f"  [缓冲区已满] 丢弃: {discarded[:40]}...")
        self._buffer.append(message)

    def flush(self) -> list[str]:
        """将缓冲区全部日志取出（模拟写入磁盘）"""
        logs = self._buffer[:]
        self._buffer.clear()
        return logs

    @property
    def count(self) -> int:
        return len(self._buffer)


def demo_log_buffer():
    print("\n=== 企业示例: 日志缓冲区 ===")
    lb = LogBuffer(capacity=5)
    for i in range(8):
        lb.write(f"[2026-06-02 10:00:{i:02d}] INFO  请求处理完成 pid={1000+i}")
    print(f"  缓冲区当前日志数: {lb.count}")
    logs = lb.flush()
    print(f"  flush 了 {len(logs)} 条日志:")
    for log in logs:
        print(f"    {log}")


# ---------- 9c. 最近浏览记录 (Recent Items) ----------

class RecentItems:
    """
    最近浏览/访问记录

    企业场景: 电商网站"最近浏览的商品"、视频网站"继续观看"。
    新记录插入到列表头部，超出容量则移除末尾。
    重复访问时先去重再插入（保持唯一性）。
    """

    def __init__(self, max_items: int = 10):
        self._max_items = max_items
        self._items: list[str] = []

    def visit(self, item: str):
        """记录一次浏览"""
        # 如果已存在，先移除旧记录
        if item in self._items:
            self._items.remove(item)
        # 插入到列表头部
        self._items.insert(0, item)
        # 超出容量则删除末尾
        if len(self._items) > self._max_items:
            self._items.pop()

    @property
    def items(self) -> list[str]:
        return self._items[:]

    def __repr__(self):
        return f"RecentItems({self._items})"


def demo_recent_items():
    print("\n=== 企业示例: 最近浏览记录 ===")
    ri = RecentItems(max_items=5)
    browsing_history = [
        "MacBook Pro 14寸",
        "iPhone 15 Pro",
        "AirPods Pro",
        "MacBook Pro 14寸",   # 重复访问
        "iPad Air",
        "Apple Watch Ultra",
        "MacBook Pro 14寸",   # 再次重复
    ]
    for item in browsing_history:
        ri.visit(item)
        print(f"  浏览 '{item}' -> {ri._items}")


# ============================================================
# 主入口
# ============================================================

if __name__ == '__main__':
    demo_create_list()
    print()

    demo_indexing()
    print()

    demo_slicing()
    print()

    demo_methods()
    print()

    demo_operations()
    print()

    demo_iteration()
    print()

    dice_simulation()
    print()

    cpp_comparison_notes()

    demo_task_queue()
    demo_log_buffer()
    demo_recent_items()
