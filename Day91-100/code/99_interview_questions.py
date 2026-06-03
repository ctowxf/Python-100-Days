"""
Day 99 - Interview Questions: Data Structures, Algorithms, System Design, and Python Internals
================================================================================================

Comprehensive demonstrations of common technical interview topics with
runnable Python code examples. Each section covers a topic area with
explanations, implementations, and comparisons to C++ where applicable.

Topics covered:
    1. Data structures (hash table, LRU cache, trie, BST, heap)
    2. Algorithms (sorting, binary search, dynamic programming, graph BFS/DFS)
    3. Python internals (GIL, memory model, decorators, metaclasses, descriptors)
    4. Concurrency (threading, multiprocessing, asyncio, GIL implications)
    5. Design patterns (singleton, factory, observer, strategy, decorator)
    6. System design patterns (rate limiter, circuit breaker, consistent hashing)

C++ Comparison (applied throughout each section):
    - Data structure implementations compare Python dict/list vs C++ STL
    - Algorithm complexity analysis applies to both languages
    - Python GIL vs C++ std::thread true parallelism
    - Python duck typing vs C++ templates / virtual dispatch

Requirements:
    None (stdlib only)

Run:
    python 99_interview_questions.py
"""

from __future__ import annotations

import abc
import bisect
import collections
import copy
import enum
import functools
import hashlib
import heapq
import itertools
import json
import logging
import math
import os
import sys
import textwrap
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    ClassVar,
    Deque,
    Dict,
    Final,
    FrozenSet,
    Generic,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Protocol,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

logger: Final = logging.getLogger(__name__)

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


# ===================================================================
# Section 1 -- 数据结构 (Data Structures)
# ===================================================================


# --- 1a. 手写哈希表 (Hash Table from Scratch) ---

class SimpleHashTable:
    """用纯Python实现的哈希表（开放寻址法 - 线性探测）。

    面试要点:
        - 哈希冲突解决: 链地址法(chaining) vs 开放寻址(open addressing)
        - 负载因子(load factor) = 元素数 / 桶数，超过阈值需要rehash
        - 时间复杂度: 平均O(1)，最坏O(n)
        - Python的dict底层使用开放寻址（紧凑哈希表）

    C++ 对比:
        - std::unordered_map 使用链地址法
        - std::map 使用红黑树，O(log n)
        - Python dict 自Python 3.6起保持插入顺序
        - C++ unordered_map 不保证顺序
    """

    _EMPTY = object()   # 空槽位标记
    _DELETED = object()  # 已删除槽位标记
    _LOAD_FACTOR_THRESHOLD = 0.7

    def __init__(self, initial_capacity: int = 16) -> None:
        self._capacity = initial_capacity
        self._size = 0
        self._keys: List[Any] = [self._EMPTY] * self._capacity
        self._values: List[Any] = [self._EMPTY] * self._capacity

    def _hash(self, key: Any) -> int:
        """计算哈希值并映射到桶索引。"""
        return hash(key) % self._capacity

    def _find_slot(self, key: Any) -> int:
        """查找键对应的槽位索引（线性探测）。"""
        index = self._hash(key)
        first_deleted = -1
        for _ in range(self._capacity):
            if self._keys[index] is self._EMPTY:
                return first_deleted if first_deleted >= 0 else index
            if self._keys[index] is self._DELETED:
                if first_deleted < 0:
                    first_deleted = index
            elif self._keys[index] == key:
                return index
            index = (index + 1) % self._capacity
        return first_deleted if first_deleted >= 0 else -1

    def _rehash(self) -> None:
        """扩容并重新哈希所有元素。"""
        old_keys, old_values = self._keys, self._values
        self._capacity *= 2
        self._size = 0
        self._keys = [self._EMPTY] * self._capacity
        self._values = [self._EMPTY] * self._capacity
        for k, v in zip(old_keys, old_values):
            if k is not self._EMPTY and k is not self._DELETED:
                self.put(k, v)

    def put(self, key: Any, value: Any) -> None:
        """插入或更新键值对。"""
        if (self._size + 1) / self._capacity > self._LOAD_FACTOR_THRESHOLD:
            self._rehash()
        index = self._find_slot(key)
        if self._keys[index] is self._EMPTY or self._keys[index] is self._DELETED:
            self._size += 1
        self._keys[index] = key
        self._values[index] = value

    def get(self, key: Any, default: Any = None) -> Any:
        """获取键对应的值。"""
        index = self._find_slot(key)
        if self._keys[index] == key:
            return self._values[index]
        return default

    def delete(self, key: Any) -> bool:
        """删除键值对。"""
        index = self._find_slot(key)
        if self._keys[index] == key:
            self._keys[index] = self._DELETED
            self._values[index] = self._DELETED
            self._size -= 1
            return True
        return False

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: Any) -> bool:
        index = self._find_slot(key)
        return self._keys[index] == key

    def items(self) -> List[Tuple[Any, Any]]:
        """返回所有键值对。"""
        return [
            (k, v) for k, v in zip(self._keys, self._values)
            if k is not self._EMPTY and k is not self._DELETED
        ]


# --- 1b. LRU缓存 (Least Recently Used Cache) ---

class LRUCache:
    """基于OrderedDict的LRU缓存。

    面试要点:
        - LRU淘汰策略: 最久未使用的数据先被淘汰
        - get和put操作都必须是O(1)
        - 使用哈希表(O(1)查找) + 双向链表(O(1)插入/删除)

    C++ 对比:
        - C++ std::list 实现双向链表
        - C++ std::unordered_map 实现哈希表
        - 组合两者即可实现O(1)的LRU
        - Python OrderedDict 内部已实现此组合
    """

    def __init__(self, capacity: int = 128) -> None:
        self._cache: collections.OrderedDict[str, Any] = collections.OrderedDict()
        self._capacity = capacity

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，同时标记为最近使用。"""
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: str, value: Any) -> None:
        """插入或更新缓存值。"""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        return len(self._cache)


# --- 1c. 前缀树 (Trie) ---

class TrieNode:
    """前缀树节点。"""

    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: Dict[str, TrieNode] = {}
        self.is_end: bool = False


class Trie:
    """前缀树（字典树）实现。

    面试要点:
        - 用于自动补全、拼写检查、IP路由表
        - 每个节点代表一个字符
        - 从根到叶的路径代表一个单词
        - 时间复杂度: 插入/查找/前缀匹配都是O(m)，m为单词长度

    C++ 对比:
        - C++通常用 std::unordered_map<char, TrieNode*> 或数组
        - 数组方式(26个子节点)空间换时间
        - Python的dict更灵活但开销略大
    """

    def __init__(self) -> None:
        self._root = TrieNode()

    def insert(self, word: str) -> None:
        """插入一个单词。"""
        node = self._root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True

    def search(self, word: str) -> bool:
        """精确查找一个单词。"""
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        """检查是否存在以prefix开头的单词。"""
        return self._find_node(prefix) is not None

    def autocomplete(self, prefix: str, max_results: int = 5) -> List[str]:
        """根据前缀自动补全，返回最多max_results个匹配单词。"""
        node = self._find_node(prefix)
        if node is None:
            return []
        results: List[str] = []
        self._dfs_collect(node, list(prefix), results, max_results)
        return results

    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """查找前缀对应的节点。"""
        node = self._root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def _dfs_collect(self, node: TrieNode, path: List[str],
                     results: List[str], limit: int) -> None:
        """DFS收集所有以当前路径为前缀的单词。"""
        if len(results) >= limit:
            return
        if node.is_end:
            results.append("".join(path))
        for char, child in sorted(node.children.items()):
            path.append(char)
            self._dfs_collect(child, path, results, limit)
            path.pop()


# --- 1d. 二叉搜索树 (BST) ---

@dataclass
class BSTNode:
    """二叉搜索树节点。"""

    value: int
    left: Optional[BSTNode] = None
    right: Optional[BSTNode] = None


class BinarySearchTree:
    """二叉搜索树。

    面试要点:
        - 中序遍历得到有序序列
        - 查找/插入/删除: 平均O(log n)，最坏O(n)（退化为链表）
        - 自平衡BST: AVL树、红黑树保证O(log n)

    C++ 对比:
        - std::map / std::set 底层是红黑树
        - C++需要手动管理内存（new/delete或智能指针）
        - Python有GC自动回收
    """

    def __init__(self) -> None:
        self._root: Optional[BSTNode] = None

    def insert(self, value: int) -> None:
        """插入一个值。"""
        self._root = self._insert(self._root, value)

    def _insert(self, node: Optional[BSTNode], value: int) -> BSTNode:
        if node is None:
            return BSTNode(value)
        if value < node.value:
            node.left = self._insert(node.left, value)
        elif value > node.value:
            node.right = self._insert(node.right, value)
        return node

    def search(self, value: int) -> bool:
        """查找一个值。"""
        return self._search(self._root, value)

    def _search(self, node: Optional[BSTNode], value: int) -> bool:
        if node is None:
            return False
        if value == node.value:
            return True
        if value < node.value:
            return self._search(node.left, value)
        return self._search(node.right, value)

    def inorder(self) -> List[int]:
        """中序遍历（有序输出）。"""
        result: List[int] = []
        self._inorder(self._root, result)
        return result

    def _inorder(self, node: Optional[BSTNode], result: List[int]) -> None:
        if node:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)

    def min_value(self) -> Optional[int]:
        """返回最小值。"""
        node = self._root
        if node is None:
            return None
        while node.left:
            node = node.left
        return node.value

    def max_value(self) -> Optional[int]:
        """返回最大值。"""
        node = self._root
        if node is None:
            return None
        while node.right:
            node = node.right
        return node.value


# --- 1e. 堆 (Heap) ---

class MinHeap:
    """最小堆实现（面试手写版本，不使用heapq）。

    面试要点:
        - 完全二叉树，用数组存储
        - 父节点 <= 子节点
        - 插入: O(log n)，取最小: O(1)，删除最小: O(log n)
        - Python heapq模块是最小堆（元组第一元素比较实现最大堆）

    C++ 对比:
        - std::priority_queue 默认最大堆
        - std::make_heap / push_heap / pop_heap
        - Python heapq 原地操作列表
    """

    def __init__(self) -> None:
        self._data: List[int] = []

    def push(self, value: int) -> None:
        """插入元素并上浮。"""
        self._data.append(value)
        self._sift_up(len(self._data) - 1)

    def pop(self) -> int:
        """删除并返回最小元素。"""
        if not self._data:
            raise IndexError("pop from empty heap")
        # 交换根和最后一个元素
        self._data[0], self._data[-1] = self._data[-1], self._data[0]
        min_val = self._data.pop()
        if self._data:
            self._sift_down(0)
        return min_val

    def peek(self) -> int:
        """返回最小元素（不删除）。"""
        if not self._data:
            raise IndexError("peek on empty heap")
        return self._data[0]

    def _sift_up(self, index: int) -> None:
        """上浮操作。"""
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index] < self._data[parent]:
                self._data[index], self._data[parent] = self._data[parent], self._data[index]
                index = parent
            else:
                break

    def _sift_down(self, index: int) -> None:
        """下沉操作。"""
        n = len(self._data)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2
            if left < n and self._data[left] < self._data[smallest]:
                smallest = left
            if right < n and self._data[right] < self._data[smallest]:
                smallest = right
            if smallest != index:
                self._data[index], self._data[smallest] = self._data[smallest], self._data[index]
                index = smallest
            else:
                break

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)


# ===================================================================
# Section 2 -- 算法 (Algorithms)
# ===================================================================


# --- 2a. 排序算法 (Sorting Algorithms) ---

def bubble_sort(arr: List[int]) -> List[int]:
    """冒泡排序 -- 时间O(n^2)，空间O(1)，稳定。

    面试要点: 理解"稳定排序"的含义（相等元素保持原有顺序）。
    C++ 对比: std::stable_sort 使用归并+插入混合，O(n log n)。
    """
    result = arr[:]
    n = len(result)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True
        if not swapped:
            break  # 已有序，提前终止
    return result


def quick_sort(arr: List[int]) -> List[int]:
    """快速排序 -- 平均O(n log n)，最坏O(n^2)，不稳定。

    面试要点:
        - 分治思想: 选择pivot，分区，递归
        - 最坏情况发生在已排序数组（选第一个元素为pivot）
        - 优化: 三数取中法选pivot，小数组切换到插入排序

    C++ 对比:
        - std::sort 使用内省排序(introsort): 快排+堆排+插入排序
        - C++快排不保证稳定性
    """
    if len(arr) <= 1:
        return arr[:]
    result = arr[:]
    _quick_sort(result, 0, len(result) - 1)
    return result


def _quick_sort(arr: List[int], low: int, high: int) -> None:
    """快速排序原地分区实现。"""
    if low < high:
        pivot_index = _partition(arr, low, high)
        _quick_sort(arr, low, pivot_index - 1)
        _quick_sort(arr, pivot_index + 1, high)


def _partition(arr: List[int], low: int, high: int) -> int:
    """Lomuto分区方案。"""
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def merge_sort(arr: List[int]) -> List[int]:
    """归并排序 -- 时间O(n log n)，空间O(n)，稳定。

    面试要点:
        - 分治: 分割->递归排序->合并
        - 稳定排序，适合链表排序
        - 空间复杂度较高(需要额外数组)

    C++ 对比:
        - std::stable_sort 基于归并排序
        - 链表排序首选归并(不需要随机访问)
    """
    if len(arr) <= 1:
        return arr[:]
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)


def _merge(left: List[int], right: List[int]) -> List[int]:
    """合并两个有序数组。"""
    result: List[int] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# --- 2b. 二分查找 (Binary Search) ---

def binary_search(arr: List[int], target: int) -> int:
    """标准二分查找，返回索引或-1。

    面试要点:
        - 前提: 数组必须有序
        - 时间O(log n)，空间O(1)
        - 注意边界: left <= right vs left < right
        - 变体: 查找第一个/最后一个等于target的位置

    C++ 对比:
        - std::binary_search 返回bool
        - std::lower_bound / upper_bound 返回迭代器
        - Python bisect模块功能等价
    """
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2  # 防溢出写法
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


def binary_search_leftmost(arr: List[int], target: int) -> int:
    """查找target第一次出现的位置（左边界二分）。

    返回插入点（bisect_left语义）。
    """
    left, right = 0, len(arr)
    while left < right:
        mid = left + (right - left) // 2
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    return left


def binary_search_rightmost(arr: List[int], target: int) -> int:
    """查找target最后一次出现位置的下一个位置（右边界二分）。

    返回插入点（bisect_right语义）。
    """
    left, right = 0, len(arr)
    while left < right:
        mid = left + (right - left) // 2
        if arr[mid] <= target:
            left = mid + 1
        else:
            right = mid
    return left


# --- 2c. 动态规划 (Dynamic Programming) ---

def longest_common_subsequence(text1: str, text2: str) -> int:
    """最长公共子序列(LCS)长度。

    面试要点:
        - 经典DP问题，二维状态转移
        - dp[i][j] = text1[:i]和text2[:j]的LCS长度
        - 时间O(mn)，空间可优化到O(min(m,n))

    C++ 对比:
        - 算法逻辑完全相同
        - C++使用vector<vector<int>>或滚动数组
        - Python列表嵌套即可
    """
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def knapsack_01(weights: List[int], values: List[int], capacity: int) -> int:
    """0-1背包问题，返回最大价值。

    面试要点:
        - 每个物品只能选一次
        - dp[j] = 容量为j时的最大价值
        - 空间优化: 一维数组，逆序遍历

    C++ 对比:
        - 算法完全相同
        - C++可用std::vector<int> dp(capacity + 1, 0)
    """
    n = len(weights)
    dp = [0] * (capacity + 1)
    for i in range(n):
        # 逆序遍历保证每个物品只用一次
        for j in range(capacity, weights[i] - 1, -1):
            dp[j] = max(dp[j], dp[j - weights[i]] + values[i])
    return dp[capacity]


def coin_change(coins: List[int], amount: int) -> int:
    """零钱兑换，返回最少硬币数，不能凑成返回-1。

    面试要点:
        - 完全背包变体（每种硬币无限使用）
        - dp[i] = 凑成金额i的最少硬币数
        - dp[0] = 0，dp[i] = min(dp[i - c] + 1) for c in coins
    """
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
    return dp[amount] if dp[amount] != float("inf") else -1


# --- 2d. 图算法 (Graph Algorithms) ---

def bfs(graph: Dict[int, List[int]], start: int) -> List[int]:
    """广度优先搜索，返回访问顺序。

    面试要点:
        - 使用队列(FIFO)
        - 保证最短路径（无权图）
        - 时间O(V+E)

    C++ 对比:
        - std::queue<int> 作为队列
        - std::vector<bool> visited 代替set
        - 性能更优(连续内存)
    """
    visited: Set[int] = {start}
    queue: Deque[int] = deque([start])
    order: List[int] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return order


def dfs(graph: Dict[int, List[int]], start: int) -> List[int]:
    """深度优先搜索(迭代版)，返回访问顺序。

    面试要点:
        - 使用栈(LIFO)
        - 适合拓扑排序、环检测、连通分量
        - 时间O(V+E)

    C++ 对比:
        - std::stack<int> 或递归
        - 注意递归深度限制(栈溢出)
        - Python默认递归限制1000
    """
    visited: Set[int] = {start}
    stack: List[int] = [start]
    order: List[int] = []
    while stack:
        node = stack.pop()
        order.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)
    return order


def topological_sort(graph: Dict[int, List[int]]) -> List[int]:
    """拓扑排序(Kahn's BFS算法)。

    面试要点:
        - 适用于有向无环图(DAG)
        - 应用: 任务调度、课程安排、编译依赖
        - 检测环: 如果结果长度 != 节点数，说明有环

    C++ 对比:
        - 算法逻辑相同
        - C++使用 std::queue + vector<int> in_degree
    """
    # 计算入度
    in_degree: Dict[int, int] = collections.defaultdict(int)
    all_nodes: Set[int] = set()
    for node, neighbors in graph.items():
        all_nodes.add(node)
        for neighbor in neighbors:
            in_degree[neighbor] += 1
            all_nodes.add(neighbor)

    # 入度为0的节点入队
    queue: Deque[int] = deque(node for node in all_nodes if in_degree[node] == 0)
    result: List[int] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(all_nodes):
        raise ValueError("图中存在环，无法进行拓扑排序")
    return result


# ===================================================================
# Section 3 -- Python 内部机制 (Python Internals)
# ===================================================================


# --- 3a. 装饰器深入 (Decorators In-Depth) ---

def retry(max_attempts: int = 3, delay: float = 1.0,
          exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    """带重试机制的装饰器。

    面试要点:
        - 装饰器本质: 高阶函数，接受函数返回函数
        - @functools.wraps 保留原函数的元信息
        - 闭包: 内部函数捕获外部函数的变量
        - 带参数的装饰器需要三层嵌套

    C++ 对比:
        - C++没有原生装饰器语法
        - 可通过模板+CRTP或宏实现类似效果
        - Python装饰器更灵活(运行时动态修改)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


def memoize(func: Callable) -> Callable:
    """缓存装饰器(functools.lru_cache的简化版)。

    面试要点:
        - 记忆化(Memoization)是DP的递归实现优化
        - 避免重复计算相同的子问题
        - 适用于纯函数(相同输入总是相同输出)
    """
    cache: Dict[Tuple, Any] = {}

    @functools.wraps(func)
    def wrapper(*args: Any) -> Any:
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    wrapper.cache = cache  # type: ignore[attr-defined]
    wrapper.cache_clear = lambda: cache.clear()  # type: ignore[attr-defined]
    return wrapper


# --- 3b. 描述符协议 (Descriptor Protocol) ---

class Validated:
    """描述符：在属性赋值时进行验证。

    面试要点:
        - 描述符协议: __get__, __set__, __delete__
        - data descriptor(有__set__)优先于实例字典
        - non-data descriptor(只有__get__)被实例字典覆盖
        - property、classmethod、staticmethod都是描述符

    C++ 对比:
        - C++没有直接等价机制
        - 可通过operator重载或proxy pattern模拟
        - Python描述符是元编程的核心机制
    """

    def __init__(self, validator: Callable[[Any], bool], error_msg: str) -> None:
        self._validator = validator
        self._error_msg = error_msg

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return obj.__dict__.get(self._attr_name)

    def __set__(self, obj: Any, value: Any) -> None:
        if not self._validator(value):
            raise ValueError(f"{self._error_msg}: {value!r}")
        obj.__dict__[self._attr_name] = value


# --- 3c. 元类 (Metaclass) ---

class SingletonMeta(type):
    """单例元类。

    面试要点:
        - 元类是"创建类的类"，type是最基本的元类
        - __new__控制类的创建，__call__控制实例的创建
        - 单例模式: 确保一个类只有一个实例
        - 应用: 数据库连接池、配置管理器、日志器

    C++ 对比:
        - C++单例通过私有构造函数+静态方法实现
        - C++ Meyer's Singleton利用static局部变量的线程安全初始化
        - Python元类更灵活但更复杂
    """

    _instances: Dict[type, Any] = {}
    _lock = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class AppConfig(metaclass=SingletonMeta):
    """应用配置单例。"""

    def __init__(self) -> None:
        self._settings: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)


# --- 3d. __slots__ 优化 ---

class PointWithSlots:
    """使用__slots__优化内存的类。

    面试要点:
        - __slots__禁止__dict__创建，节省内存
        - 每个实例节省约100-200字节
        - 限制: 不能动态添加未声明的属性
        - 不支持多继承中多个有__slots__的父类

    C++ 对比:
        - C++类天然有固定布局(类似__slots__)
        - Python __dict__ 等价于C++的运行时反射开销
        - __slots__让Python接近C++的内存效率
    """

    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def distance_to(self, other: PointWithSlots) -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class PointWithoutSlots:
    """不使用__slots__的普通类(用于对比)。"""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


# --- 3e. GIL 说明 ---

def demonstrate_gil_implications() -> str:
    """演示GIL(全局解释器锁)的影响。

    面试要点:
        - GIL是CPython的全局锁，同一时刻只有一个线程执行Python字节码
        - GIL在I/O操作时释放，所以I/O密集型任务多线程仍有优势
        - CPU密集型任务应使用multiprocessing绕过GIL
        - Python 3.13引入了实验性的free-threaded模式(无GIL)

    C++ 对比:
        - C++ std::thread 实现真正的并行
        - GIL是Python特有的限制
        - C++需要手动使用mutex/lock_guard保护共享数据
        - Python的GIL简化了引用计数的线程安全
    """
    lines = [
        "GIL (Global Interpreter Lock) 关键知识点:",
        "  1. GIL确保同一时刻只有一个线程执行Python字节码",
        "  2. I/O密集型: 多线程仍有优势(GIL在I/O等待时释放)",
        "  3. CPU密集型: 使用multiprocessing绕过GIL",
        "  4. Python 3.13+: 实验性free-threaded模式(PEP 703)",
        "  5. numpy等C扩展可以在计算时释放GIL",
        "",
        "  推荐策略:",
        "    I/O密集  -> asyncio (最高效率) 或 threading",
        "    CPU密集  -> multiprocessing 或 concurrent.futures.ProcessPoolExecutor",
        "    混合型   -> asyncio + 进程池执行器",
    ]
    return "\n".join(lines)


# ===================================================================
# Section 4 -- 并发编程 (Concurrency)
# ===================================================================


def threading_demo() -> Dict[str, Any]:
    """演示线程安全的计数器。

    面试要点:
        - 竞态条件(race condition)和数据竞争(data race)
        - threading.Lock 保护临界区
        - GIL不能替代锁(字节码之间仍有竞态)
    """
    class ThreadSafeCounter:
        """线程安全的计数器。"""

        def __init__(self) -> None:
            self._value = 0
            self._lock = threading.Lock()

        def increment(self) -> None:
            with self._lock:
                self._value += 1

        @property
        def value(self) -> int:
            return self._value

    counter = ThreadSafeCounter()
    threads = []
    for _ in range(10):
        t = threading.Thread(target=lambda: [counter.increment() for _ in range(1000)])
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    return {
        "expected": 10000,
        "actual": counter.value,
        "correct": counter.value == 10000,
    }


def async_pattern_demo() -> str:
    """演示asyncio模式(不需要真正运行async)。

    面试要点:
        - asyncio是单线程并发，基于事件循环
        - async/await语法糖简化协程编写
        - 适合I/O密集型(网络请求、文件操作)
        - 不适合CPU密集型(会阻塞事件循环)

    C++ 对比:
        - C++20引入co_await/co_yield协程
        - Boost.Asio 提供异步I/O
        - Python asyncio更易用但性能不如C++协程
    """
    code = textwrap.dedent("""\
        import asyncio

        async def fetch_data(url: str) -> dict:
            \"\"\"模拟异步HTTP请求。\"\"\"
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return {"url": url, "status": 200}

        async def process_batch(urls: list[str]) -> list[dict]:
            \"\"\"并发处理一批请求。\"\"\"
            tasks = [fetch_data(url) for url in urls]
            return await asyncio.gather(*tasks)

        # 运行
        results = asyncio.run(process_batch(["http://a.com", "http://b.com"]))
    """)
    return code


# ===================================================================
# Section 5 -- 设计模式 (Design Patterns)
# ===================================================================


# --- 5a. 工厂模式 (Factory Pattern) ---

class Notification(abc.ABC):
    """通知接口。"""

    @abc.abstractmethod
    def send(self, message: str, recipient: str) -> bool:
        ...


class EmailNotification(Notification):
    """邮件通知。"""

    def send(self, message: str, recipient: str) -> bool:
        logger.info("发送邮件到 %s: %s", recipient, message)
        return True


class SMSNotification(Notification):
    """短信通知。"""

    def send(self, message: str, recipient: str) -> bool:
        logger.info("发送短信到 %s: %s", recipient, message)
        return True


class PushNotification(Notification):
    """推送通知。"""

    def send(self, message: str, recipient: str) -> bool:
        logger.info("推送到 %s: %s", recipient, message)
        return True


class NotificationFactory:
    """通知工厂 -- 根据类型创建对应的通知对象。

    面试要点:
        - 工厂模式封装对象创建逻辑
        - 客户端不需要知道具体的类
        - 符合开闭原则(新增通知类型不修改现有代码)

    C++ 对比:
        - C++使用虚函数 + 工厂方法
        - Python使用鸭子类型可以更灵活
        - C++模板工厂(CRTP)在编译时确定类型
    """

    _registry: Dict[str, Type[Notification]] = {
        "email": EmailNotification,
        "sms": SMSNotification,
        "push": PushNotification,
    }

    @classmethod
    def register(cls, name: str, notification_class: Type[Notification]) -> None:
        cls._registry[name] = notification_class

    @classmethod
    def create(cls, notification_type: str) -> Notification:
        if notification_type not in cls._registry:
            raise ValueError(f"Unknown notification type: {notification_type}")
        return cls._registry[notification_type]()


# --- 5b. 观察者模式 (Observer Pattern) ---

class EventEmitter:
    """事件发射器 -- 观察者模式的实现。

    面试要点:
        - 定义一对多的依赖关系
        - 当主题状态改变时，所有观察者自动收到通知
        - 应用: GUI事件处理、消息中间件、响应式编程

    C++ 对比:
        - C++使用 std::function + std::vector 存储回调
        - Boost.Signals2 提供线程安全的信号槽机制
        - Qt框架的信号槽(singal-slot)就是观察者模式
    """

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[..., Any]]] = collections.defaultdict(list)

    def on(self, event: str, callback: Optional[Callable[..., Any]] = None) -> Any:
        """注册事件监听器(也可作为装饰器使用)。

        用法:
            emitter.on("event", handler)      # 直接注册
            @emitter.on("event")              # 作为装饰器
            def handler(data): ...
        """
        if callback is not None:
            # 直接注册模式: emitter.on("event", func)
            self._listeners[event].append(callback)
            return callback
        # 装饰器模式: @emitter.on("event")
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._listeners[event].append(func)
            return func
        return decorator

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """触发事件。"""
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)

    def off(self, event: str, callback: Callable[..., Any]) -> None:
        """移除事件监听器。"""
        if event in self._listeners:
            self._listeners[event].remove(callback)


# --- 5c. 策略模式 (Strategy Pattern) ---

class SortStrategy(abc.ABC):
    """排序策略接口。"""

    @abc.abstractmethod
    def sort(self, data: List[int]) -> List[int]:
        ...


class BubbleSortStrategy(SortStrategy):
    def sort(self, data: List[int]) -> List[int]:
        return bubble_sort(data)


class QuickSortStrategy(SortStrategy):
    def sort(self, data: List[int]) -> List[int]:
        return quick_sort(data)


class MergeSortStrategy(SortStrategy):
    def sort(self, data: List[int]) -> List[int]:
        return merge_sort(data)


class DataProcessor:
    """使用策略模式的数据处理器。

    面试要点:
        - 策略模式: 定义算法族，分别封装，可互换
        - 消除if-else分支
        - 运行时动态切换算法

    C++ 对比:
        - C++使用虚函数或 std::function
        - C++模板策略在编译时绑定(零开销)
        - Python策略在运行时绑定(更灵活)
    """

    def __init__(self, strategy: SortStrategy) -> None:
        self._strategy = strategy

    def set_strategy(self, strategy: SortStrategy) -> None:
        self._strategy = strategy

    def process(self, data: List[int]) -> List[int]:
        return self._strategy.sort(data)


# ===================================================================
# Section 6 -- 系统设计模式 (System Design Patterns)
# ===================================================================


# --- 6a. 限流器 (Rate Limiter) ---

class TokenBucketRateLimiter:
    """令牌桶限流器。

    面试要点:
        - 令牌桶算法: 桶以固定速率填充令牌，请求消耗令牌
        - 允许突发流量(桶中有足够令牌时)
        - 平滑限流(固定速率)
        - 应用: API限流、防止DDoS

    常见限流算法:
        1. 固定窗口计数器 -- 简单但有边界突发问题
        2. 滑动窗口计数器 -- 更平滑
        3. 漏桶(Leaky Bucket) -- 严格恒定速率
        4. 令牌桶(Token Bucket) -- 允许突发，最常用

    C++ 对比:
        - C++需要std::mutex + std::chrono实现
        - 分布式限流需要Redis + Lua脚本
    """

    def __init__(self, rate: float, capacity: int) -> None:
        """初始化。

        Args:
            rate: 每秒产生的令牌数
            capacity: 桶的最大容量
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> bool:
        """尝试获取令牌，成功返回True。"""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
            self._last_refill = now

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False


# --- 6b. 熔断器 (Circuit Breaker) ---

class CircuitState(enum.Enum):
    """熔断器状态。"""
    CLOSED = "closed"       # 正常状态，允许请求通过
    OPEN = "open"           # 熔断状态，拒绝所有请求
    HALF_OPEN = "half_open" # 半开状态，允许少量请求探测


class CircuitBreaker:
    """熔断器模式。

    面试要点:
        - 防止级联故障(cascading failure)
        - 三种状态: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
        - 当错误率超过阈值，熔断器打开，快速失败
        - 经过冷却时间后，进入半开状态尝试恢复
        - 应用: 微服务调用、外部API依赖

    C++ 对比:
        - C++实现需要mutex + condition_variable
        - Netflix Hystrix(Java)是业界标准实现
        - Python的pybreaker库提供生产级实现
    """

    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout: float = 30.0,
                 success_threshold: int = 2) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._success_threshold = success_threshold
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """获取当前状态，检查是否可以从OPEN转为HALF_OPEN。"""
        with self._lock:
            if (self._state == CircuitState.OPEN and
                    time.monotonic() - self._last_failure_time >= self._recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            return self._state

    def record_success(self) -> None:
        """记录一次成功调用。"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def record_failure(self) -> None:
        """记录一次失败调用。"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif (self._state == CircuitState.CLOSED and
                  self._failure_count >= self._failure_threshold):
                self._state = CircuitState.OPEN

    def allow_request(self) -> bool:
        """判断是否允许请求通过。"""
        current_state = self.state
        if current_state == CircuitState.CLOSED:
            return True
        if current_state == CircuitState.HALF_OPEN:
            return True  # 允许少量探测请求
        return False  # OPEN状态，拒绝请求


# --- 6c. 一致性哈希 (Consistent Hashing) ---

class ConsistentHashRing:
    """一致性哈希环。

    面试要点:
        - 解决分布式缓存节点增减时大量key重映射的问题
        - 普通哈希: key % N，当N变化时几乎所有key都需重映射
        - 一致性哈希: 只需重映射 K/N 个key
        - 虚拟节点: 解决数据倾斜问题
        - 应用: Redis集群、分布式缓存、负载均衡

    C++ 对比:
        - C++使用 std::map (红黑树) 实现有序哈希环
        - Python使用 sortedcontainers.SortedDict 或 bisect
        - 查找最近节点: upper_bound (C++) / bisect_right (Python)
    """

    def __init__(self, replicas: int = 150) -> None:
        """初始化。

        Args:
            replicas: 每个物理节点的虚拟节点数
        """
        self._replicas = replicas
        self._ring: Dict[int, str] = {}
        self._sorted_keys: List[int] = []
        self._nodes: Set[str] = set()

    def _hash(self, key: str) -> int:
        """计算哈希值。"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        """添加一个物理节点。"""
        self._nodes.add(node)
        for i in range(self._replicas):
            virtual_key = f"{node}:v{i}"
            hash_val = self._hash(virtual_key)
            self._ring[hash_val] = node
            bisect.insort(self._sorted_keys, hash_val)

    def remove_node(self, node: str) -> None:
        """移除一个物理节点。"""
        self._nodes.discard(node)
        for i in range(self._replicas):
            virtual_key = f"{node}:v{i}"
            hash_val = self._hash(virtual_key)
            if hash_val in self._ring:
                del self._ring[hash_val]
                idx = bisect.bisect_left(self._sorted_keys, hash_val)
                if idx < len(self._sorted_keys) and self._sorted_keys[idx] == hash_val:
                    self._sorted_keys.pop(idx)

    def get_node(self, key: str) -> Optional[str]:
        """获取key应该路由到的节点。"""
        if not self._ring:
            return None
        hash_val = self._hash(key)
        idx = bisect.bisect_right(self._sorted_keys, hash_val)
        if idx == len(self._sorted_keys):
            idx = 0  # 绕回环的起点
        return self._ring[self._sorted_keys[idx]]

    def get_distribution(self, sample_keys: List[str]) -> Dict[str, int]:
        """统计key在各节点上的分布(用于验证均匀性)。"""
        distribution: Dict[str, int] = collections.Counter()
        for key in sample_keys:
            node = self.get_node(key)
            if node:
                distribution[node] += 1
        return dict(distribution)


# ===================================================================
# Section 7 -- 综合演示 (Comprehensive Demonstration)
# ===================================================================


def demo_data_structures() -> None:
    """演示数据结构。"""
    print("=" * 60)
    print("1. 数据结构 (Data Structures)")
    print("=" * 60)

    # --- 哈希表 ---
    print("\n  [手写哈希表]")
    ht = SimpleHashTable()
    for i in range(10):
        ht.put(f"key_{i}", i * 10)
    print(f"    插入10个元素, size={len(ht)}")
    print(f"    get('key_3') = {ht.get('key_3')}")
    print(f"    get('missing') = {ht.get('missing', 'N/A')}")
    ht.delete("key_3")
    print(f"    删除key_3后, 'key_3' in ht = {'key_3' in ht}")

    # --- LRU缓存 ---
    print("\n  [LRU缓存]")
    lru = LRUCache(capacity=3)
    for k, v in [("a", 1), ("b", 2), ("c", 3)]:
        lru.put(k, v)
    print(f"    put a=1, b=2, c=3, size={len(lru)}")
    print(f"    get('a') = {lru.get('a')}  (标记为最近使用)")
    lru.put("d", 4)  # 淘汰最久未使用的"b"
    print(f"    put d=4 (淘汰b), get('b') = {lru.get('b')}")

    # --- 前缀树 ---
    print("\n  [前缀树 Trie]")
    trie = Trie()
    words = ["apple", "app", "application", "apt", "banana", "band", "bat"]
    for word in words:
        trie.insert(word)
    print(f"    插入单词: {words}")
    print(f"    search('app') = {trie.search('app')}")
    print(f"    search('ap') = {trie.search('ap')}  (不是完整单词)")
    print(f"    starts_with('ap') = {trie.starts_with('ap')}")
    print(f"    autocomplete('app') = {trie.autocomplete('app')}")
    print(f"    autocomplete('ba') = {trie.autocomplete('ba')}")

    # --- BST ---
    print("\n  [二叉搜索树 BST]")
    bst = BinarySearchTree()
    for val in [5, 3, 7, 1, 4, 6, 8]:
        bst.insert(val)
    print(f"    插入: [5, 3, 7, 1, 4, 6, 8]")
    print(f"    中序遍历: {bst.inorder()}")
    print(f"    search(4) = {bst.search(4)}")
    print(f"    search(9) = {bst.search(9)}")
    print(f"    min = {bst.min_value()}, max = {bst.max_value()}")

    # --- 堆 ---
    print("\n  [最小堆 MinHeap]")
    heap = MinHeap()
    for val in [5, 3, 8, 1, 4, 7, 2]:
        heap.push(val)
    popped = [heap.pop() for _ in range(4)]
    print(f"    依次push: [5, 3, 8, 1, 4, 7, 2]")
    print(f"    pop 4次: {popped}  (应为升序)")


def demo_algorithms() -> None:
    """演示算法。"""
    print("\n" + "=" * 60)
    print("2. 算法 (Algorithms)")
    print("=" * 60)

    # --- 排序 ---
    print("\n  [排序算法]")
    data = [38, 27, 43, 3, 9, 82, 10]
    print(f"    原始数据: {data}")
    print(f"    冒泡排序: {bubble_sort(data)}")
    print(f"    快速排序: {quick_sort(data)}")
    print(f"    归并排序: {merge_sort(data)}")

    # --- 二分查找 ---
    print("\n  [二分查找]")
    sorted_arr = [1, 3, 5, 7, 9, 11, 13, 15]
    target = 7
    idx = binary_search(sorted_arr, target)
    print(f"    数组: {sorted_arr}")
    print(f"    查找 {target}: 索引={idx}")

    # 带重复元素的查找
    arr_with_dup = [1, 2, 2, 2, 3, 4, 5]
    left = binary_search_leftmost(arr_with_dup, 2)
    right = binary_search_rightmost(arr_with_dup, 2)
    print(f"    数组: {arr_with_dup}")
    print(f"    2的左边界: index={left}, 右边界: index={right}")
    print(f"    2出现了 {right - left} 次")

    # --- 动态规划 ---
    print("\n  [动态规划]")
    print(f"    LCS('abcde', 'ace') = {longest_common_subsequence('abcde', 'ace')}")
    print(f"    LCS('abc', 'abc') = {longest_common_subsequence('abc', 'abc')}")
    print(f"    背包问题: weights=[2,3,4], values=[3,4,5], capacity=5")
    print(f"    最大价值 = {knapsack_01([2, 3, 4], [3, 4, 5], 5)}")
    print(f"    零钱兑换: coins=[1,5,11], amount=15")
    print(f"    最少硬币 = {coin_change([1, 5, 11], 15)}")

    # --- 图算法 ---
    print("\n  [图算法]")
    graph = {
        0: [1, 2],
        1: [3],
        2: [3, 4],
        3: [5],
        4: [5],
        5: [],
    }
    print(f"    图: {graph}")
    print(f"    BFS(从0): {bfs(graph, 0)}")
    print(f"    DFS(从0): {dfs(graph, 0)}")
    print(f"    拓扑排序: {topological_sort(graph)}")


def demo_python_internals() -> None:
    """演示Python内部机制。"""
    print("\n" + "=" * 60)
    print("3. Python内部机制 (Python Internals)")
    print("=" * 60)

    # --- 装饰器 ---
    print("\n  [装饰器]")

    @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
    def flaky_function(should_fail: bool) -> str:
        if should_fail:
            raise ValueError("intentional error")
        return "success"

    print(f"    retry装饰器: flaky_function(False) = '{flaky_function(False)}'")

    @memoize
    def fibonacci(n: int) -> int:
        if n < 2:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    print(f"    memoize装饰器: fibonacci(30) = {fibonacci(30)}")
    print(f"    缓存大小: {len(fibonacci.cache)} 个条目")  # type: ignore[attr-defined]

    # --- __slots__ 内存对比 ---
    print("\n  [__slots__ 内存优化]")
    p_slots = PointWithSlots(1.0, 2.0)
    p_no_slots = PointWithoutSlots(1.0, 2.0)
    slots_size = sys.getsizeof(p_slots)
    no_slots_size = sys.getsizeof(p_no_slots)
    has_dict_slots = hasattr(p_slots, "__dict__")
    has_dict_no_slots = hasattr(p_no_slots, "__dict__")
    print(f"    有__slots__:   size={slots_size}B, has __dict__={has_dict_slots}")
    print(f"    无__slots__:   size={no_slots_size}B, has __dict__={has_dict_no_slots}")
    print(f"    节省: {no_slots_size - slots_size}B/实例")

    # --- 单例 ---
    print("\n  [单例模式 via 元类]")
    config1 = AppConfig()
    config2 = AppConfig()
    config1.set("app_name", "InterviewDemo")
    print(f"    config1 is config2: {config1 is config2}")
    print(f"    config2.get('app_name') = {config2.get('app_name')}")

    # --- GIL说明 ---
    print("\n  [GIL说明]")
    print(demonstrate_gil_implications())

    # --- 线程安全 ---
    print("\n  [线程安全计数器]")
    result = threading_demo()
    print(f"    预期值: {result['expected']}, 实际值: {result['actual']}")
    print(f"    结果正确: {result['correct']}")


def demo_design_patterns() -> None:
    """演示设计模式。"""
    print("\n" + "=" * 60)
    print("4. 设计模式 (Design Patterns)")
    print("=" * 60)

    # --- 工厂模式 ---
    print("\n  [工厂模式]")
    for ntype in ["email", "sms", "push"]:
        notification = NotificationFactory.create(ntype)
        notification.send("Hello!", "user@example.com")

    # --- 观察者模式 ---
    print("\n  [观察者模式]")
    emitter = EventEmitter()

    @emitter.on("order_created")
    def send_confirmation(order_id: int) -> None:
        print(f"    -> 发送订单确认: order_id={order_id}")

    @emitter.on("order_created")
    def update_inventory(order_id: int) -> None:
        print(f"    -> 更新库存: order_id={order_id}")

    @emitter.on("order_created")
    def notify_warehouse(order_id: int) -> None:
        print(f"    -> 通知仓库: order_id={order_id}")

    print("    触发 'order_created' 事件:")
    emitter.emit("order_created", 12345)

    # --- 策略模式 ---
    print("\n  [策略模式]")
    data = [38, 27, 43, 3, 9, 82, 10]
    strategies = [
        ("冒泡排序", BubbleSortStrategy()),
        ("快速排序", QuickSortStrategy()),
        ("归并排序", MergeSortStrategy()),
    ]
    processor = DataProcessor(strategies[0][1])
    for name, strategy in strategies:
        processor.set_strategy(strategy)
        result = processor.process(data)
        print(f"    {name}: {result}")


def demo_system_design() -> None:
    """演示系统设计模式。"""
    print("\n" + "=" * 60)
    print("5. 系统设计模式 (System Design Patterns)")
    print("=" * 60)

    # --- 令牌桶限流器 ---
    print("\n  [令牌桶限流器]")
    limiter = TokenBucketRateLimiter(rate=5.0, capacity=10)
    allowed = sum(1 for _ in range(15) if limiter.acquire())
    print(f"    速率=5/s, 容量=10, 15次请求: {allowed} 次通过")

    # --- 熔断器 ---
    print("\n  [熔断器]")
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.5)
    print(f"    初始状态: {breaker.state.value}")

    # 触发熔断
    for i in range(4):
        breaker.record_failure()
    print(f"    连续失败4次后: {breaker.state.value}")
    print(f"    允许请求通过: {breaker.allow_request()}")

    # 等待恢复
    time.sleep(0.6)
    print(f"    0.6秒后: {breaker.state.value}")
    print(f"    允许请求通过: {breaker.allow_request()}")

    # 恢复成功
    breaker.record_success()
    breaker.record_success()
    print(f"    连续成功2次后: {breaker.state.value}")

    # --- 一致性哈希 ---
    print("\n  [一致性哈希]")
    ring = ConsistentHashRing(replicas=100)
    nodes = ["redis-1", "redis-2", "redis-3"]
    for node in nodes:
        ring.add_node(node)

    # 测试分布均匀性
    sample_keys = [f"user:{i}" for i in range(1000)]
    distribution = ring.get_distribution(sample_keys)
    print(f"    3个节点, 1000个key的分布:")
    for node, count in sorted(distribution.items()):
        pct = count / 1000 * 100
        print(f"      {node}: {count} ({pct:.1f}%)")

    # 添加新节点后的影响
    ring.add_node("redis-4")
    new_distribution = ring.get_distribution(sample_keys)
    print(f"    添加redis-4后分布:")
    for node, count in sorted(new_distribution.items()):
        pct = count / 1000 * 100
        print(f"      {node}: {count} ({pct:.1f}%)")


# ===================================================================
# Section 8 -- 面试知识点速查
# ===================================================================

INTERVIEW_CHEATSHEET: Final[List[Dict[str, str]]] = [
    {"topic": "list vs tuple", "answer": "list可变(mutable)，tuple不可变(immutable); tuple可做dict的key"},
    {"topic": "dict底层", "answer": "哈希表，开放寻址，Python 3.6+保持插入顺序，空间换时间"},
    {"topic": "GIL", "answer": "CPython全局解释器锁，同一时刻一个线程执行字节码; I/O时释放; 用multiprocessing绕过"},
    {"topic": "装饰器", "answer": "高阶函数，接受函数返回函数; @functools.wraps保留元信息; 带参需三层嵌套"},
    {"topic": "生成器", "answer": "yield暂停/恢复; 惰性求值节省内存; 适合大数据流处理"},
    {"topic": "深拷贝vs浅拷贝", "answer": "浅拷贝: 新容器但元素引用相同; 深拷贝: 完全独立的递归副本"},
    {"topic": "is vs ==", "answer": "is比较身份(id), ==比较值(equality); None用is判断"},
    {"topic": "MRO", "answer": "方法解析顺序, C3线性化算法; super()按MRO链调用"},
    {"topic": "垃圾回收", "answer": "引用计数为主 + 分代GC处理循环引用; gc.disable()可关闭"},
    {"topic": "协程vs线程", "answer": "协程: 单线程并发, 切换开销小, 适合I/O; 线程: OS调度, 有GIL限制"},
    {"topic": "SQL优化", "answer": "EXPLAIN分析; 合理索引; 避免SELECT *; 批量操作; 连接池"},
    {"topic": "RESTful设计", "answer": "资源导向URL; HTTP动词语义化; 状态码规范; 版本控制; HATEOAS"},
    {"topic": "CAP定理", "answer": "一致性/可用性/分区容错性不可兼得; CP: ZooKeeper; AP: Cassandra/DynamoDB"},
    {"topic": "事务隔离级别", "answer": "读未提交/读已提交/可重复读/串行化; MySQL默认可重复读"},
    {"topic": "Redis数据类型", "answer": "String/Hash/List/Set/ZSet; 应用: 缓存/会话/排行榜/限流"},
    {"topic": "Docker", "answer": "镜像(Image)是只读模板; 容器(Container)是运行实例; Dockerfile定义构建步骤"},
]


def print_interview_cheatsheet() -> None:
    """打印面试知识点速查表。"""
    lines = [
        "=" * 60,
        "面试知识点速查",
        "=" * 60,
    ]
    for i, entry in enumerate(INTERVIEW_CHEATSHEET, 1):
        lines.append(f"  {i:2d}. {entry['topic']}")
        lines.append(f"      {entry['answer']}")
    print("\n".join(lines))


# ===================================================================
# Main Entry Point
# ===================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stderr,
    )

    print("Day 99 - 面试中的公共问题")
    print("涵盖: 数据结构, 算法, Python内部机制, 并发, 设计模式, 系统设计")
    print()

    demo_data_structures()
    demo_algorithms()
    demo_python_internals()
    demo_design_patterns()
    demo_system_design()
    print_interview_cheatsheet()

    print("\n" + "=" * 60)
    print("所有演示完成!")
    print("=" * 60)
    print(textwrap.dedent("""\
        面试准备建议:
          1. 数据结构: 手写哈希表、LRU缓存、Trie、BST、堆
          2. 算法: 排序、二分查找、DP、图BFS/DFS、拓扑排序
          3. Python: 装饰器、描述符、元类、GIL、__slots__
          4. 并发: threading.Lock、multiprocessing、asyncio
          5. 设计模式: 工厂、观察者、策略、单例、装饰器
          6. 系统设计: 限流器、熔断器、一致性哈希、缓存策略
          7. 数据库: ACID、索引优化、N+1问题、主从复制
          8. 网络: TCP三次握手、HTTPS/TLS、HTTP/2、WebSocket

        推荐刷题资源:
          - LeetCode (算法题)
          - SQLZoo (SQL练习)
          - System Design Primer (系统设计)
          - Python Interview Bible (Python面试)
    """))
