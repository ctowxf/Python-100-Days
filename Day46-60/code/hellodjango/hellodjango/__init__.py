"""
Django 项目初始化文件
hellodjango 包的初始化模块

在 Python 中，__init__.py 文件表示该目录是一个 Python 包
类似 C++ 中的命名空间(namespace)概念

C++ 对比:
    namespace hellodjango {
        // 项目的所有模块都在这个命名空间下
    }

这个文件通常用于:
1. 包级别的初始化代码
2. 导入重要的模块
3. 设置包级别的变量
"""

# 版本信息
# 类似 C++ 中的 #define VERSION "1.0.0"
__version__: str = '1.0.0'
__author__: str = 'Python-100-Days'

# 项目名称
PROJECT_NAME: str = 'hellodjango'
