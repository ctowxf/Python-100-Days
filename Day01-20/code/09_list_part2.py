"""
Day 09 - Advanced List Operations (Part 2)
==========================================
Topics: list comprehension, nested lists, list as stack/queue, slicing tricks.
C++ Comparison: list comprehension vs std::transform + std::copy_if,
                nested list vs 2D array.
Enterprise examples: matrix operations, data filtering, batch processing.

Author: Python-100-Days
Version: 1.0
"""


# =============================================================================
# 1. LIST COMPREHENSION
# =============================================================================
# In Python, list comprehension is a concise syntax for creating lists.
# It is faster than a for-loop with append because the interpreter uses
# a dedicated LIST_APPEND bytecode instruction instead of method calls.
#
# C++ COMPARISON: List Comprehension vs std::transform + std::copy_if
# ---------------------------------------------------------------------------
# C++ has no direct equivalent of list comprehension.  To achieve the same
# effect you typically combine algorithms from <algorithm>:
#
#   // Transform: square each element
#   std::vector<int> nums1 = {35, 12, 97, 64, 55};
#   std::vector<int> nums2;
#   std::transform(nums1.begin(), nums1.end(), std::back_inserter(nums2),
#                  [](int n) { return n * n; });
#
#   // Filter: keep only elements > 50
#   std::vector<int> nums3;
#   std::copy_if(nums1.begin(), nums1.end(), std::back_inserter(nums3),
#                [](int n) { return n > 50; });
#
#   // Combined transform + filter requires a manual loop or ranges (C++20).
#
# Python collapses all of this into a single readable expression:
#   nums2 = [n ** 2 for n in nums1]
#   nums3 = [n for n in nums1 if n > 50]
# ---------------------------------------------------------------------------


def demo_basic_list_comprehension():
    """Basic list comprehension patterns from the tutorial."""
    print("=" * 60)
    print("1. BASIC LIST COMPREHENSION")
    print("=" * 60)

    # Pattern 1: filter -- numbers divisible by 3 or 5
    items = [i for i in range(1, 100) if i % 3 == 0 or i % 5 == 0]
    print(f"Numbers 1-99 divisible by 3 or 5 ({len(items)} items):")
    print(items)
    print()

    # Pattern 2: transform -- square each element
    nums1 = [35, 12, 97, 64, 55]
    nums2 = [num ** 2 for num in nums1]
    print(f"Original : {nums1}")
    print(f"Squared  : {nums2}")
    print()

    # Pattern 3: transform + filter -- keep only values > 50
    nums3 = [num for num in nums1 if num > 50]
    print(f"Values > 50 from {nums1}: {nums3}")
    print()

    # Pattern 4: conditional expression inside comprehension
    labels = ["even" if x % 2 == 0 else "odd" for x in range(10)]
    print(f"Even/odd labels for 0-9: {labels}")


# =============================================================================
# 2. NESTED LISTS  (2-D structures)
# =============================================================================
# A nested list is a list whose elements are themselves lists.  It is the
# idiomatic way to represent matrices / tables in pure Python.
#
# C++ COMPARISON: Nested List vs 2D Array
# ---------------------------------------------------------------------------
# C++ offers several 2-D containers:
#   int matrix[3][3];                         // fixed-size, stack-allocated
#   std::vector<std::vector<int>> matrix;     // dynamic, row-major
#   // C++23 mdspan for non-owning multidimensional view
#
# Key differences from Python nested lists:
#   - C++ arrays are homogeneous (element type fixed at compile time).
#   - Python lists can mix types in the same row (though rarely desired).
#   - C++ vector<vector<int>> stores rows contiguously *within* each inner
#     vector, but the outer vector stores pointers to separate heap blocks.
#     Python's list-of-lists is analogous: each inner list is a separate
#     PyObject with its own memory block.
#   - For heavy numeric work, both ecosystems reach for NumPy / Eigen, which
#     guarantee a single contiguous memory block for the entire matrix.
# ---------------------------------------------------------------------------


def demo_nested_lists():
    """Creating and accessing nested lists (tables / matrices)."""
    print("=" * 60)
    print("2. NESTED LISTS")
    print("=" * 60)

    # 5 students, 3 exam scores each
    scores = [
        [95, 83, 92],
        [80, 75, 82],
        [92, 97, 90],
        [80, 78, 69],
        [65, 66, 89],
    ]

    # Access: scores[row][col]
    print(f"All scores       : {scores}")
    print(f"Student 0 scores : {scores[0]}")
    print(f"Student 0, Exam 1: {scores[0][1]}")
    print()

    # Build a nested list with a comprehension (random scores)
    import random
    random_scores = [
        [random.randint(60, 100) for _ in range(3)]   # 3 exams
        for _ in range(5)                              # 5 students
    ]
    print("Randomly generated scores (5 students x 3 exams):")
    for row in random_scores:
        print(f"  {row}")


# =============================================================================
# 3. ENTERPRISE EXAMPLE: MATRIX OPERATIONS
# =============================================================================

def matrix_add(a, b):
    """Element-wise addition of two matrices represented as nested lists."""
    return [
        [a[i][j] + b[i][j] for j in range(len(a[0]))]
        for i in range(len(a))
    ]


def matrix_transpose(m):
    """Transpose a matrix (rows become columns)."""
    return [
        [m[row][col] for row in range(len(m))]
        for col in range(len(m[0]))
    ]


def matrix_multiply(a, b):
    """Multiply two matrices using nested list comprehensions."""
    rows_a, cols_a = len(a), len(a[0])
    cols_b = len(b[0])
    return [
        [
            sum(a[i][k] * b[k][j] for k in range(cols_a))
            for j in range(cols_b)
        ]
        for i in range(rows_a)
    ]


def demo_matrix_operations():
    """Enterprise-style matrix operations using nested lists."""
    print("=" * 60)
    print("3. ENTERPRISE EXAMPLE: MATRIX OPERATIONS")
    print("=" * 60)

    A = [[1, 2, 3],
         [4, 5, 6]]

    B = [[7, 8, 9],
         [10, 11, 12]]

    print("Matrix A:")
    for row in A:
        print(f"  {row}")
    print("Matrix B:")
    for row in B:
        print(f"  {row}")

    C = matrix_add(A, B)
    print("A + B:")
    for row in C:
        print(f"  {row}")

    AT = matrix_transpose(A)
    print("Transpose of A:")
    for row in AT:
        print(f"  {row}")

    # Multiply: (2x3) * (3x2) => (2x2)
    D = [[1, 2],
         [3, 4],
         [5, 6]]
    E = matrix_multiply(A, D)
    print("A * D  (2x3 * 3x2 => 2x2):")
    for row in E:
        print(f"  {row}")


# =============================================================================
# 4. ENTERPRISE EXAMPLE: DATA FILTERING
# =============================================================================

def demo_data_filtering():
    """
    Filter a list of employee records using list comprehension.
    Simulates a common enterprise data-processing task.
    """
    print("=" * 60)
    print("4. ENTERPRISE EXAMPLE: DATA FILTERING")
    print("=" * 60)

    employees = [
        {"name": "Alice",   "dept": "Engineering", "salary": 120000},
        {"name": "Bob",     "dept": "Marketing",   "salary": 85000},
        {"name": "Charlie", "dept": "Engineering", "salary": 135000},
        {"name": "Diana",   "dept": "HR",          "salary": 78000},
        {"name": "Eve",     "dept": "Engineering", "salary": 110000},
        {"name": "Frank",   "dept": "Marketing",   "salary": 92000},
        {"name": "Grace",   "dept": "HR",          "salary": 88000},
    ]

    # Filter: engineers earning above 115k
    senior_engineers = [
        e for e in employees
        if e["dept"] == "Engineering" and e["salary"] > 115000
    ]
    print("Senior engineers (salary > 115k):")
    for e in senior_engineers:
        print(f"  {e['name']:10s}  ${e['salary']:,}")

    # Aggregate: average salary by department
    departments = {e["dept"] for e in employees}
    print("\nAverage salary by department:")
    for dept in sorted(departments):
        dept_salaries = [e["salary"] for e in employees if e["dept"] == dept]
        avg = sum(dept_salaries) / len(dept_salaries)
        print(f"  {dept:15s}  ${avg:>10,.2f}  ({len(dept_salaries)} employees)")

    # List of names sorted by salary descending
    ranked = [
        e["name"] for e in sorted(employees, key=lambda e: e["salary"], reverse=True)
    ]
    print(f"\nEmployees ranked by salary (desc): {ranked}")


# =============================================================================
# 5. ENTERPRISE EXAMPLE: BATCH PROCESSING
# =============================================================================

def demo_batch_processing():
    """
    Simulate batch processing of log records.
    Each log entry is a dict with timestamp, level, and message.
    """
    print("=" * 60)
    print("5. ENTERPRISE EXAMPLE: BATCH PROCESSING")
    print("=" * 60)

    import random
    import datetime

    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    messages = [
        "User login successful",
        "Database connection timeout",
        "Disk usage above 90%",
        "Null pointer exception in module X",
        "Service restarted",
        "Cache miss for key user_session",
        "Unhandled exception in worker thread",
        "Configuration reloaded",
    ]

    # Generate a batch of 20 synthetic log entries
    base_time = datetime.datetime(2026, 6, 2, 8, 0, 0)
    logs = [
        {
            "timestamp": base_time + datetime.timedelta(seconds=random.randint(0, 3600)),
            "level": random.choice(levels),
            "message": random.choice(messages),
        }
        for _ in range(20)
    ]

    # Sort by timestamp
    logs.sort(key=lambda entry: entry["timestamp"])

    # Filter errors and criticals using comprehension
    critical_logs = [
        entry for entry in logs if entry["level"] in ("ERROR", "CRITICAL")
    ]
    print(f"Total log entries : {len(logs)}")
    print(f"Errors / Criticals: {len(critical_logs)}")
    print()

    # Group counts by level
    print("Log level distribution:")
    for level in levels:
        count = sum(1 for entry in logs if entry["level"] == level)
        bar = "#" * count
        print(f"  {level:10s} [{count:2d}] {bar}")

    # Extract just timestamps of errors for alerting
    error_timestamps = [
        entry["timestamp"].strftime("%H:%M:%S")
        for entry in logs
        if entry["level"] in ("ERROR", "CRITICAL")
    ]
    print(f"\nError timestamps: {error_timestamps}")


# =============================================================================
# 6. LIST AS STACK AND QUEUE
# =============================================================================
# Python lists work naturally as stacks (LIFO) via append / pop.
# For queues (FIFO), prefer collections.deque for O(1) popleft.
# Using list.pop(0) for dequeue is O(n) because all remaining elements shift.


def demo_stack():
    """Using a list as a stack (last-in, first-out)."""
    print("=" * 60)
    print("6a. LIST AS STACK (LIFO)")
    print("=" * 60)

    stack = []
    for item in ["page_a", "page_b", "page_c"]:
        stack.append(item)
        print(f"  push({item})  -> stack: {stack}")

    print()
    while stack:
        item = stack.pop()
        print(f"  pop() => {item:8s}  -> stack: {stack}")


def demo_queue():
    """Using collections.deque as a queue (first-in, first-out)."""
    from collections import deque

    print("=" * 60)
    print("6b. LIST AS QUEUE (FIFO) -- using deque")
    print("=" * 60)

    queue = deque()
    for task in ["task_1", "task_2", "task_3"]:
        queue.append(task)
        print(f"  enqueue({task})  -> queue: {list(queue)}")

    print()
    while queue:
        task = queue.popleft()
        print(f"  dequeue() => {task:8s}  -> queue: {list(queue)}")


# =============================================================================
# 7. SLICING TRICKS
# =============================================================================
# Slicing is one of Python's most powerful features for sequences.
# Syntax: seq[start:stop:step]
#   - start defaults to 0 (or len-1 if step < 0)
#   - stop  defaults to len (or -1-before-start if step < 0)
#   - step  defaults to 1


def demo_slicing_tricks():
    """Showcase useful slicing idioms."""
    print("=" * 60)
    print("7. SLICING TRICKS")
    print("=" * 60)

    data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    print(f"Original       : {data}")

    # 7a. Reverse a list
    print(f"Reversed       : {data[::-1]}")

    # 7b. Every other element
    print(f"Every other    : {data[::2]}")

    # 7c. Every other element, starting from index 1
    print(f"Odd indices    : {data[1::2]}")

    # 7d. Copy a list (shallow copy)
    copy = data[:]
    print(f"Shallow copy   : {copy}")

    # 7e. Replace a slice
    letters = list("ABCDEFGH")
    letters[2:5] = list("xyz")
    print(f"Replace [2:5]  : {letters}")

    # 7f. Delete a slice
    letters = list("ABCDEFGH")
    del letters[2:5]
    print(f"Delete  [2:5]  : {letters}")

    # 7g. Insert via slice assignment
    nums = [1, 2, 5, 6]
    nums[2:2] = [3, 4]       # insert 3, 4 before index 2
    print(f"Insert via slice: {nums}")

    # 7h. Chunk a list into groups of N
    def chunk(lst, n):
        return [lst[i:i + n] for i in range(0, len(lst), n)]

    print(f"Chunk by 3     : {chunk(data, 3)}")

    # 7i. Sliding window of size 3
    window_size = 3
    windows = [data[i:i + window_size] for i in range(len(data) - window_size + 1)]
    print(f"Sliding win(3) : {windows}")

    # 7j. Rotate left by 2
    rotated = data[2:] + data[:2]
    print(f"Rotate left  2 : {rotated}")

    # 7k. Negative step -- extract from end
    print(f"Last 3 elements: {data[-3:]}")
    print(f"Skip last 2    : {data[:-2]}")


# =============================================================================
# 8. PERFORMANCE NOTE: LIST COMPREHENSION vs FOR-LOOP+APPEND
# =============================================================================

def demo_performance_comparison():
    """
    Demonstrate that list comprehension is faster than
    an equivalent for-loop with append.
    """
    import time

    print("=" * 60)
    print("8. PERFORMANCE: COMPREHENSION vs FOR-LOOP+APPEND")
    print("=" * 60)

    n = 1_000_000

    # for-loop + append
    start = time.perf_counter()
    result_loop = []
    for i in range(n):
        result_loop.append(i * i)
    time_loop = time.perf_counter() - start

    # list comprehension
    start = time.perf_counter()
    result_comp = [i * i for i in range(n)]
    time_comp = time.perf_counter() - start

    assert result_loop == result_comp
    print(f"  for-loop + append : {time_loop:.4f}s")
    print(f"  list comprehension: {time_comp:.4f}s")
    speedup = time_loop / time_comp if time_comp > 0 else float("inf")
    print(f"  Speedup           : {speedup:.2f}x")


# =============================================================================
# 9. LOTTERY EXAMPLE (from tutorial) -- simplified
# =============================================================================

def demo_lottery():
    """
    Generate random lottery numbers (Chinese 'Shuangseqiu' style).
    6 red balls from 1-33, 1 blue ball from 1-16.
    """
    import random

    print("=" * 60)
    print("9. LOTTERY NUMBER GENERATOR")
    print("=" * 60)

    red_balls = list(range(1, 34))
    blue_balls = list(range(1, 17))

    n = 5
    print(f"Generating {n} sets:\n")
    for i in range(n):
        selected = sorted(random.sample(red_balls, 6))
        blue = random.choice(blue_balls)
        red_str = " ".join(f"{b:02d}" for b in selected)
        print(f"  Set {i + 1}: [ {red_str} ]  +  Blue: {blue:02d}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    demo_basic_list_comprehension()
    print()

    demo_nested_lists()
    print()

    demo_matrix_operations()
    print()

    demo_data_filtering()
    print()

    demo_batch_processing()
    print()

    demo_stack()
    print()

    demo_queue()
    print()

    demo_slicing_tricks()
    print()

    demo_performance_comparison()
    print()

    demo_lottery()
