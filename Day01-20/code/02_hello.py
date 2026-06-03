#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一个Python程序 - Hello World
===============================

本模块演示Python编程的基础知识，包括：
- 第一个Python程序：hello, world
- print() 函数的基本用法
- Python与C++的语法差异对比
- 注释的使用方式（单行注释与多行注释）
- 字符串的基本操作
- 企业级代码结构最佳实践

C++ 对比说明:
- C++ 需要 #include <iostream>，Python 不需要引入头文件
- C++ 需要 int main() {} 入口函数，Python 使用 if __name__ == '__main__'
- C++ 使用分号结束语句，Python 使用换行符
- C++ 使用 std::cout，Python 使用 print()

Version: 2.0
Author: Python-100-Days Contributors
License: MIT
Created: 2024-01-01
"""

from typing import Optional, List, Dict, Any, Union
import sys
import os
from datetime import datetime
from dataclasses import dataclass, field


# =============================================================================
# 常量定义 (Constants)
# =============================================================================
# C++: const std::string APP_NAME = "HelloApp";
# Python: 使用全大写命名约定表示常量
APP_NAME: str = "HelloApp"
APP_VERSION: str = "2.0.0"
DEFAULT_GREETING: str = "hello, world"


# =============================================================================
# 第一部分：最简单的Python程序
# =============================================================================

def hello_world_basic() -> None:
    """
    最基础的 hello, world 程序

    这是学习任何编程语言的第一个程序，源自 Dennis Ritchie 和 Brian Kernighan
    的经典著作《The C Programming Language》。

    C++ 版本:
        #include <iostream>
        int main() {
            std::cout << "hello, world" << std::endl;
            return 0;
        }

    Python 版本:
        print('hello, world')
    """
    # 单行注释：以 # 和空格开头
    # C++: // 单行注释
    # Python: # 单行注释

    print('hello, world')
    print("goodbye, world")  # 可以使用单引号或双引号表示字符串


def hello_world_with_comments() -> None:
    """
    演示Python注释的使用方式

    Python有两种注释形式：
    1. 单行注释：以 # 开头
    2. 多行注释：使用三个引号（文档字符串）

    C++ 注释:
        // 单行注释
        /* 多行注释 */

    Python 注释:
        # 单行注释
        \"\"\" 多行注释（文档字符串）\"\"\"
    """
    # 这是单行注释，不会被执行
    # print('这行代码被注释掉了')

    """
    这是多行注释的示例
    通常用于函数、类、模块的文档说明
    Python中称为 docstring（文档字符串）
    """

    print("你好，世界！")  # 输出中文内容


# =============================================================================
# 第二部分：print() 函数详解
# =============================================================================

def demonstrate_print_function() -> None:
    """
    演示 print() 函数的各种用法

    print() 是Python内置函数，用于输出内容到标准输出（控制台）。

    C++ 对比:
        std::cout << "Hello" << std::endl;  // C++ 输出
        print("Hello")                       # Python 输出

    Python 的 print() 比 C++ 的 cout 更简洁易用。
    """
    # 基本输出
    print("=== print() 函数基本用法 ===")

    # 1. 输出字符串
    print("Hello, Python!")        # 双引号
    print('Hello, Python!')        # 单引号（推荐，更简洁）

    # 2. 输出数字
    # C++: std::cout << 42 << std::endl;
    print(42)                      # 输出整数
    print(3.14)                    # 输出浮点数

    # 3. 输出多个值（默认用空格分隔）
    # C++: std::cout << "Name:" << " Alice" << " Age:" << 25 << std::endl;
    print("Name:", "Alice", "Age:", 25)

    # 4. 使用 sep 参数自定义分隔符
    # C++ 没有直接等价的便捷方式
    print("2024", "01", "01", sep="-")        # 输出: 2024-01-01
    print("Hello", "World", sep=" -> ")       # 输出: Hello -> World

    # 5. 使用 end 参数自定义结尾符（默认是换行 \n）
    # C++: std::cout << "Hello" << " "; // 不换行
    print("Hello", end=" ")
    print("World")                           # 输出: Hello World（在同一行）

    # 6. 输出到文件
    # C++: 使用 ofstream
    # Python: 使用 file 参数
    with open("output.txt", "w", encoding="utf-8") as f:
        print("写入文件的内容", file=f)

    # 7. 格式化输出（f-string，Python 3.6+）
    # C++: std::cout << "Name: " << name << ", Age: " << age << std::endl;
    # C++20: std::format("Name: {}, Age: {}", name, age)
    name: str = "Alice"
    age: int = 25
    print(f"Name: {name}, Age: {age}")       # f-string 格式化

    # 清理临时文件
    if os.path.exists("output.txt"):
        os.remove("output.txt")


# =============================================================================
# 第三部分：字符串基础
# =============================================================================

def demonstrate_strings() -> None:
    """
    演示Python字符串的基本用法

    Python中字符串可以用单引号或双引号表示，两者等价。

    C++ 对比:
        std::string s1 = "Hello";       // 双引号
        char s2[] = "Hello";            // C风格字符串
        // C++ 单引号用于单个字符: char c = 'A';

    Python:
        s1 = "Hello"    # 双引号
        s2 = 'Hello'    # 单引号（推荐）
        s3 = """Hello""" # 三引号（多行字符串）
    """
    # 单引号和双引号等价
    greeting1: str = 'hello, world'
    greeting2: str = "hello, world"
    print(greeting1)
    print(greeting2)

    # 多行字符串（三引号）
    # C++: 可以使用 raw string literal: R"(多行内容)"
    multi_line: str = """这是第一行
这是第二行
这是第三行"""
    print(multi_line)

    # 字符串中的转义字符
    # C++ 同样使用反斜杠转义
    print("Hello\tWorld")       # 制表符
    print("Hello\nWorld")       # 换行符
    print("He said \"Hi\"")     # 双引号转义
    print('It\'s Python')       # 单引号转义

    # 原始字符串（不处理转义）
    # C++: R"(\n\t)" 或 R"raw(\n\t)raw"
    path: str = r"C:\Users\forest\Documents"
    print(f"路径: {path}")

    # 字符串拼接
    # C++: 使用 + 运算符或 std::string::append()
    first_name: str = "John"
    last_name: str = "Doe"
    full_name: str = first_name + " " + last_name
    print(f"全名: {full_name}")

    # 字符串重复
    # C++: 没有直接的重复运算符
    separator: str = "-" * 40
    print(separator)


# =============================================================================
# 第四部分：Python 与 C++ 语法差异对比
# =============================================================================

def compare_python_cpp() -> None:
    """
    Python 与 C++ 语法差异对比

    本函数通过实际代码示例展示两种语言的关键差异。
    """
    print("\n=== Python vs C++ 语法对比 ===\n")

    # -------------------------------------------------------------------------
    # 差异1：入口函数
    # -------------------------------------------------------------------------
    # C++ 必须有 main 函数:
    #     int main() {
    #         // 程序入口
    #         return 0;
    #     }
    #
    # Python 不需要 main 函数，但推荐使用 __name__ 守卫:
    #     if __name__ == '__main__':
    #         # 程序入口
    print("[差异1] 入口函数")
    print("  C++:    需要 int main() {} 入口函数")
    print("  Python: 使用 if __name__ == '__main__' 守卫")

    # -------------------------------------------------------------------------
    # 差异2：语句结束符
    # -------------------------------------------------------------------------
    # C++: int x = 10;  // 必须有分号
    # Python: x = 10    # 不需要分号
    print("\n[差异2] 语句结束符")
    x: int = 10  # 不需要分号
    print(f"  Python: x = {x}（不需要分号）")

    # -------------------------------------------------------------------------
    # 差异3：变量声明
    # -------------------------------------------------------------------------
    # C++: int x = 10; std::string name = "Alice";
    # Python: x = 10; name = "Alice"  (动态类型)
    print("\n[差异3] 变量声明")
    dynamic_var = 10        # 动态类型
    dynamic_var = "Hello"   # 可以改变类型（C++ 不行）
    print(f"  Python 动态类型: {dynamic_var}")

    # -------------------------------------------------------------------------
    # 差异4：代码块
    # -------------------------------------------------------------------------
    # C++: 使用花括号 {}
    #     if (x > 0) {
    #         printf("Positive");
    #     }
    #
    # Python: 使用缩进（通常是4个空格）
    #     if x > 0:
    #         print("Positive")
    print("\n[差异4] 代码块")
    print("  C++:    使用花括号 {} 定义代码块")
    print("  Python: 使用缩进（4个空格）定义代码块")

    # -------------------------------------------------------------------------
    # 差异5：输出函数
    # -------------------------------------------------------------------------
    # C++: std::cout << "Hello" << std::endl;
    # Python: print("Hello")
    print("\n[差异5] 输出函数")
    print("  C++:    std::cout << \"Hello\" << std::endl;")
    print("  Python: print(\"Hello\")")

    # -------------------------------------------------------------------------
    # 差异6：头文件
    # -------------------------------------------------------------------------
    # C++: #include <iostream>  #include <string>
    # Python: import 模块名（按需导入）
    print("\n[差异6] 头文件/模块导入")
    print("  C++:    #include <iostream>（编译时包含）")
    print("  Python: import sys（运行时导入，按需加载）")


# =============================================================================
# 第五部分：企业级代码结构示例
# =============================================================================

@dataclass
class Greeter:
    """
    问候语生成器类

    演示Python类的基本结构，包含：
    - 类型注解（Type Hints）
    - 文档字符串（Docstring）
    - 数据类（Dataclass）

    C++ 对比:
        class Greeter {
        private:
            std::string name;
            std::string language;
        public:
            Greeter(std::string n, std::string lang)
                : name(n), language(lang) {}
            std::string greet() const;
        };
    """
    name: str
    language: str = "en"
    _greeting_templates: Dict[str, str] = field(
        default_factory=lambda: {
            "en": "Hello, {name}!",
            "zh": "你好，{name}！",
            "ja": "こんにちは、{name}！",
            "es": "¡Hola, {name}!",
            "fr": "Bonjour, {name}!",
        }
    )

    def greet(self) -> str:
        """
        生成问候语

        Returns:
            str: 格式化后的问候语

        Raises:
            ValueError: 当不支持的语言被指定时
        """
        template: Optional[str] = self._greeting_templates.get(self.language)
        if template is None:
            supported: str = ", ".join(self._greeting_templates.keys())
            raise ValueError(
                f"不支持的语言: {self.language}。支持的语言: {supported}"
            )
        return template.format(name=self.name)

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return list(self._greeting_templates.keys())

    def add_language(self, code: str, template: str) -> None:
        """
        添加新的语言支持

        Args:
            code: 语言代码（如 'de'）
            template: 问候语模板，使用 {name} 作为占位符
        """
        self._greeting_templates[code] = template


@dataclass
class AppConfig:
    """
    应用配置类

    演示Python数据类的使用，类似于C++的结构体但更强大。

    C++ 对比:
        struct AppConfig {
            std::string app_name;
            std::string version;
            bool debug_mode;
            int max_connections;
        };
    """
    app_name: str = APP_NAME
    version: str = APP_VERSION
    debug_mode: bool = False
    max_connections: int = 100
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        """初始化后的验证"""
        if self.max_connections < 1:
            raise ValueError("max_connections 必须大于 0")
        valid_log_levels: List[str] = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"log_level 必须是 {valid_log_levels} 之一")

    def is_debug(self) -> bool:
        """检查是否为调试模式"""
        return self.debug_mode

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "debug_mode": self.debug_mode,
            "max_connections": self.max_connections,
            "log_level": self.log_level,
        }


class HelloApplication:
    """
    Hello World 应用程序主类

    演示企业级Python应用的基本结构：
    - 单例模式思想
    - 依赖注入
    - 日志记录
    - 异常处理
    - 类型安全

    C++ 对比:
        class HelloApplication {
        private:
            AppConfig config;
            std::vector<Greeter> greeters;
        public:
            HelloApplication(const AppConfig& cfg);
            void run();
            void add_greeter(const Greeter& g);
        };
    """

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        """
        初始化应用

        Args:
            config: 应用配置，如果为None则使用默认配置
        """
        self._config: AppConfig = config or AppConfig()
        self._greeters: List[Greeter] = []
        self._start_time: Optional[datetime] = None

    @property
    def config(self) -> AppConfig:
        """获取应用配置"""
        return self._config

    def add_greeter(self, greeter: Greeter) -> None:
        """
        添加问候器

        Args:
            greeter: Greeter 实例
        """
        self._greeters.append(greeter)
        if self._config.is_debug():
            print(f"[DEBUG] 添加问候器: {greeter.name} ({greeter.language})")

    def run(self) -> None:
        """运行应用程序"""
        self._start_time = datetime.now()
        self._print_banner()

        for greeter in self._greeters:
            try:
                greeting: str = greeter.greet()
                print(greeting)
            except ValueError as e:
                print(f"[ERROR] {e}")

        self._print_summary()

    def _print_banner(self) -> None:
        """打印应用横幅"""
        separator: str = "=" * 50
        print(separator)
        print(f"  {self._config.app_name} v{self._config.version}")
        print(f"  Debug Mode: {self._config.debug_mode}")
        print(separator)

    def _print_summary(self) -> None:
        """打印运行摘要"""
        if self._start_time:
            elapsed = (datetime.now() - self._start_time).total_seconds()
            print(f"\n运行完成，共处理 {len(self._greeters)} 个问候器")
            print(f"耗时: {elapsed:.4f} 秒")


# =============================================================================
# 第六部分：实用工具函数
# =============================================================================

def format_greeting(
    name: str,
    template: str = "Hello, {name}!",
    uppercase: bool = False
) -> str:
    """
    格式化问候语

    Args:
        name: 要问候的人名
        template: 问候语模板，{name} 会被替换
        uppercase: 是否转换为大写

    Returns:
        str: 格式化后的问候语

    Examples:
        >>> format_greeting("World")
        'Hello, World!'
        >>> format_greeting("Python", uppercase=True)
        'HELLO, PYTHON!'
    """
    result: str = template.format(name=name)
    return result.upper() if uppercase else result


def print_table(
    headers: List[str],
    rows: List[List[Any]],
    column_width: int = 15
) -> None:
    """
    打印格式化表格

    Args:
        headers: 表头列表
        rows: 数据行列表
        column_width: 列宽
    """
    # 打印表头
    header_line: str = "".join(h.ljust(column_width) for h in headers)
    print(header_line)
    print("-" * (column_width * len(headers)))

    # 打印数据行
    for row in rows:
        row_line: str = "".join(str(cell).ljust(column_width) for cell in row)
        print(row_line)


def get_system_info() -> Dict[str, str]:
    """
    获取系统信息

    Returns:
        Dict[str, str]: 包含系统信息的字典
    """
    return {
        "Python版本": sys.version,
        "操作系统": sys.platform,
        "当前目录": os.getcwd(),
        "编码": sys.getdefaultencoding(),
    }


# =============================================================================
# 第七部分：高级示例
# =============================================================================

def demonstrate_advanced_hello() -> None:
    """
    高级 Hello World 示例

    演示更多Python特性：
    - 列表推导式
    - Lambda 函数
    - 高阶函数
    - 字符串格式化
    """
    print("\n=== 高级 Hello World 示例 ===\n")

    # 列表推导式生成问候语
    # C++: 使用 std::transform 或循环
    names: List[str] = ["Alice", "Bob", "Charlie", "Diana"]
    greetings: List[str] = [f"Hello, {name}!" for name in names]
    print("列表推导式生成问候语:")
    for g in greetings:
        print(f"  {g}")

    # Lambda 函数
    # C++: 使用 lambda 表达式 (C++11+)
    # Python: lambda 参数: 表达式
    shout = lambda s: s.upper() + "!!!"
    print(f"\nLambda 函数: {shout('hello')}")

    # 高阶函数 map/filter
    # C++: std::transform, std::filter (C++20 ranges)
    upper_greetings: List[str] = list(map(lambda g: g.upper(), greetings))
    print(f"\nmap 转换大写: {upper_greetings}")

    long_names: List[str] = list(filter(lambda n: len(n) > 4, names))
    print(f"filter 过滤: {long_names}")

    # 多行格式化
    banner: str = f"""
    {'=' * 40}
    欢迎使用 {APP_NAME}
    版本: {APP_VERSION}
    Python: {sys.version.split()[0]}
    时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    {'=' * 40}
    """
    print(banner)


def demonstrate_error_handling() -> None:
    """
    演示错误处理

    Python 使用 try/except 处理异常，类似 C++ 的 try/catch。

    C++ 对比:
        try {
            // 可能抛出异常的代码
        } catch (const std::exception& e) {
            std::cerr << e.what() << std::endl;
        }

    Python:
        try:
            # 可能抛出异常的代码
        except Exception as e:
            print(f"Error: {e}")
    """
    print("\n=== 错误处理演示 ===\n")

    # 示例1: 除零错误
    try:
        result: float = 10 / 0
    except ZeroDivisionError as e:
        print(f"捕获除零错误: {e}")

    # 示例2: 类型错误
    try:
        greeting: str = "Hello" + 42
    except TypeError as e:
        print(f"捕获类型错误: {e}")

    # 示例3: 使用 Greeter 的错误处理
    greeter: Greeter = Greeter(name="World", language="xx")
    try:
        greeter.greet()
    except ValueError as e:
        print(f"捕获值错误: {e}")

    # 示例4: finally 子句（总是执行）
    # C++: 使用 RAII 或 finally（C++ 没有 finally，使用析构函数）
    print("\nfinally 子句演示:")
    try:
        print("  尝试执行...")
        raise ValueError("测试异常")
    except ValueError as e:
        print(f"  捕获异常: {e}")
    finally:
        print("  finally 总是执行（类似 C++ 的 RAII）")


# =============================================================================
# 主程序入口
# =============================================================================

def main() -> None:
    """
    主程序入口函数

    演示所有功能的集成运行。

    C++ 对比:
        int main() {
            // 程序入口
            return 0;
        }

    Python 使用 if __name__ == '__main__' 守卫，
    确保代码只在直接运行时执行，被导入时不执行。
    """
    print(f"\n{'=' * 60}")
    print(f"  {APP_NAME} v{APP_VERSION}")
    print(f"  第一个Python程序 - 综合演示")
    print(f"{'=' * 60}\n")

    # 1. 基础 Hello World
    print("\n[1] 基础 Hello World")
    print("-" * 40)
    hello_world_basic()

    # 2. 带注释的 Hello World
    print("\n[2] 带注释的 Hello World")
    print("-" * 40)
    hello_world_with_comments()

    # 3. print() 函数演示
    print("\n[3] print() 函数详解")
    print("-" * 40)
    demonstrate_print_function()

    # 4. 字符串演示
    print("\n[4] 字符串基础")
    print("-" * 40)
    demonstrate_strings()

    # 5. Python vs C++ 对比
    compare_python_cpp()

    # 6. 企业级代码示例
    print("\n[6] 企业级代码示例")
    print("-" * 40)

    # 使用 Greeter 类
    greeters_data: List[Dict[str, str]] = [
        {"name": "Alice", "language": "en"},
        {"name": "小明", "language": "zh"},
        {"name": "太郎", "language": "ja"},
        {"name": "Carlos", "language": "es"},
    ]

    for data in greeters_data:
        greeter: Greeter = Greeter(**data)
        print(greeter.greet())

    # 使用 AppConfig
    config: AppConfig = AppConfig(debug_mode=True)
    print(f"\n应用配置: {config.to_dict()}")

    # 使用 HelloApplication
    app: HelloApplication = HelloApplication(config=config)
    for data in greeters_data:
        app.add_greeter(Greeter(**data))
    app.run()

    # 7. 高级示例
    demonstrate_advanced_hello()

    # 8. 错误处理
    demonstrate_error_handling()

    # 9. 系统信息
    print("\n[9] 系统信息")
    print("-" * 40)
    sys_info: Dict[str, str] = get_system_info()
    print_table(
        headers=["项目", "值"],
        rows=list(sys_info.items()),
        column_width=20
    )

    # 10. 实用函数演示
    print("\n[10] 实用函数演示")
    print("-" * 40)
    print(format_greeting("World"))
    print(format_greeting("Python", uppercase=True))
    print(format_greeting("Python", template="Hi {name}, welcome!"))

    print(f"\n{'=' * 60}")
    print("  演示完成！")
    print(f"{'=' * 60}")


# =============================================================================
# __name__ 守卫
# =============================================================================
# C++ 有 int main() 作为程序入口
# Python 使用 if __name__ == '__main__' 来判断是否直接运行
#
# 当文件被直接运行时: __name__ == '__main__'
# 当文件被导入时: __name__ == '模块名'
#
# 这是Python的最佳实践，类似于C++的 main 函数

if __name__ == '__main__':
    main()
