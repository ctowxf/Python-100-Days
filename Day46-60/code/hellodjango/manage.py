#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.
Django 的命令行管理工具，类似 C++ 中的 main() 入口点

用法示例:
    python manage.py runserver        # 启动开发服务器
    python manage.py makemigrations   # 创建数据库迁移文件
    python manage.py migrate          # 执行数据库迁移
    python manage.py createsuperuser  # 创建超级管理员
"""
import os
import sys
from typing import List


def main() -> None:
    """Run administrative tasks.
    运行管理任务，相当于 C++ 程序的 main() 函数

    在 C++ 中，main() 是程序入口；在 Django 中，manage.py 就是项目的入口点
    """
    # 设置默认的 Django 设置模块
    # 类似 C++ 中的 #include 预处理指令
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hellodjango.settings')

    try:
        # 导入 Django 的命令执行工具
        # 类似 C++ 中的函数调用
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # 异常处理，类似 C++ 中的 try-catch 机制
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # 执行命令行参数对应的 Django 命令
    # sys.argv 包含命令行参数，类似 C++ 中的 argc/argv
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Python 的入口点检查，类似 C++ 的 int main() 函数
    main()
