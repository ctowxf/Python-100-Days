"""
Day 58 - 异步任务和定时任务 (Asynchronous Tasks and Scheduled Tasks)
=====================================================================

Celery 是 Python 中最流行的分布式任务队列框架，用于处理异步任务和定时任务。
在 Web 应用中，耗时操作（如发送邮件、生成报表、文件上传）应异步化处理，
避免阻塞主线程，提升用户体验和系统吞吐量。

核心概念:
    - Broker (消息代理): 传递任务消息的中间件，常用 Redis 或 RabbitMQ
    - Worker (工作者): 执行任务的进程
    - Backend (结果后端): 存储任务执行结果，常用 Redis 或数据库
    - Beat (定时调度器): 按照配置的计划触发定时任务

架构:
    Producer -> Broker (Redis) -> Worker -> Backend (Redis/DB)

安装依赖:
    pip install celery redis

启动 Worker:
    celery -A tasks worker --loglevel=info

启动定时任务调度器:
    celery -A tasks beat --loglevel=info

C++ 对比:
    Python Celery 相当于 C++ 中 Celery 之于 Python，C++ 生态中类似的库有:
    - Boost.Asio + 自定义队列: 底层异步 I/O 框架，需自行封装任务队列
    - Intel TBB (Threading Building Blocks): 并行任务调度库
    - Celery C++ 无直接对应，通常用消息队列中间件 (RabbitMQ/Kafka) + 自定义 worker
    - C++ 方案性能更高但开发成本大，Python Celery 开箱即用生态完善
"""

from __future__ import annotations

import os
import sys
import time
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import deque
from threading import Thread, Lock
import concurrent.futures

# ============================================================================
# 配置常量
# ============================================================================

REDIS_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("async_tasks")


# ============================================================================
# Part 1: Celery 配置与任务定义 (生产环境使用)
# ============================================================================

def create_celery_app(name: str = "async_tasks") -> Any:
    """
    创建并配置 Celery 应用实例。

    生产环境中实际使用 Celery 框架的配置方式。
    此函数展示标准配置模式，需要 pip install celery redis 后运行。

    Args:
        name: Celery 应用名称

    Returns:
        配置好的 Celery 应用实例
    """
    from celery import Celery

    app = Celery(
        name,
        broker=REDIS_URL,
        backend=RESULT_BACKEND,
    )

    # Celery 配置
    app.conf.update(
        # 序列化方式
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],

        # 时区设置
        timezone="Asia/Shanghai",
        enable_utc=True,

        # 任务结果过期时间 (秒)
        result_expires=3600,

        # Worker 并发数
        worker_concurrency=4,

        # 任务限流 (每秒最多执行 100 个任务)
        task_rate_limit="100/s",

        # 任务超时时间 (秒)
        task_time_limit=300,
        task_soft_time_limit=240,

        # 任务重试配置
        task_acks_late=True,
        task_reject_on_worker_lost=True,

        # 队列路由
        task_routes={
            "tasks.send_email": {"queue": "email"},
            "tasks.generate_report": {"queue": "reports"},
            "tasks.sync_data": {"queue": "sync"},
        },

        # 默认队列
        task_default_queue="default",
    )

    # 定时任务 (Celery Beat) 配置
    app.conf.beat_schedule = {
        # 每天凌晨 2 点执行数据同步
        "daily-data-sync": {
            "task": "tasks.sync_data",
            "schedule": crontab(hour=2, minute=0),
            "args": ("full",),
        },
        # 每小时清理过期缓存
        "hourly-cache-cleanup": {
            "task": "tasks.cleanup_cache",
            "schedule": timedelta(hours=1),
        },
        # 每周一早上 9 点生成周报
        "weekly-report": {
            "task": "tasks.generate_report",
            "schedule": crontab(hour=9, minute=0, day_of_week=1),
            "kwargs": {"report_type": "weekly"},
        },
    }

    return app


# 以下为实际 Celery 任务定义 (需要 Celery 环境)
# 取消注释以在生产环境中使用:

# from celery import Celery
# from celery.schedules import crontab
#
# app = create_celery_app()
#
# @app.task(bind=True, max_retries=3, default_retry_delay=60)
# def send_email_task(self, to: str, subject: str, body: str) -> dict:
#     """异步发送邮件任务"""
#     try:
#         # 模拟邮件发送
#         time.sleep(2)
#         return {"status": "sent", "to": to, "subject": subject}
#     except Exception as exc:
#         raise self.retry(exc=exc)
#
# @app.task(bind=True, time_limit=600)
# def generate_report_task(self, report_type: str, params: dict) -> dict:
#     """异步生成报表任务"""
#     # 耗时的报表生成逻辑
#     return {"report_type": report_type, "file_path": "/reports/xxx.pdf"}
#
# @app.task
# def sync_data_task(mode: str = "incremental") -> dict:
#     """数据同步任务"""
#     return {"mode": mode, "synced_records": 1000}


# ============================================================================
# Part 2: 模拟任务队列系统 (无需 Redis/Celery 即可运行演示)
# ============================================================================

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "PENDING"           # 等待执行
    STARTED = "STARTED"           # 已开始
    SUCCESS = "SUCCESS"           # 成功
    FAILURE = "FAILURE"           # 失败
    RETRY = "RETRY"               # 重试中
    REVOKED = "REVOKED"           # 已撤销


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    retries: int = 0
    queue: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retries": self.retries,
            "queue": self.queue,
        }


@dataclass
class Task:
    """任务定义"""
    task_id: str
    func_name: str
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    queue: str = "default"
    max_retries: int = 3
    retry_delay: float = 5.0
    priority: int = 0  # 0=最高优先级
    eta: Optional[datetime] = None  # 预定执行时间


class Broker(ABC):
    """消息代理抽象基类 (对应 Celery 中的 Broker 概念)"""

    @abstractmethod
    def publish(self, task: Task) -> None:
        """发布任务到队列"""
        pass

    @abstractmethod
    def consume(self, queue: str) -> Optional[Task]:
        """从队列消费任务"""
        pass

    @abstractmethod
    def queue_size(self, queue: str) -> int:
        """获取队列长度"""
        pass


class InMemoryBroker(Broker):
    """
    内存消息代理 (用于演示，生产环境使用 Redis/RabbitMQ)

    对比 C++:
        C++ 中通常使用 std::queue + std::mutex 或 lock-free queue
        如 MoodyCamel::ConcurrentQueue 实现类似功能
    """

    def __init__(self) -> None:
        self._queues: dict[str, deque[Task]] = {}
        self._lock: Lock = Lock()
        logger.info("InMemoryBroker 初始化完成")

    def publish(self, task: Task) -> None:
        with self._lock:
            if task.queue not in self._queues:
                self._queues[task.queue] = deque()
            self._queues[task.queue].append(task)
            logger.info(f"[Broker] 任务 {task.task_id} 已发布到队列 '{task.queue}'")

    def consume(self, queue: str) -> Optional[Task]:
        with self._lock:
            if queue in self._queues and self._queues[queue]:
                task = self._queues[queue].popleft()
                logger.info(f"[Broker] 任务 {task.task_id} 已从队列 '{queue}' 取出")
                return task
            return None

    def queue_size(self, queue: str) -> int:
        with self._lock:
            return len(self._queues.get(queue, []))


class ResultBackend:
    """
    任务结果后端 (对应 Celery 中的 Result Backend)

    生产环境通常使用 Redis 或数据库存储结果。
    """

    def __init__(self) -> None:
        self._results: dict[str, TaskResult] = {}
        self._lock: Lock = Lock()

    def store(self, result: TaskResult) -> None:
        with self._lock:
            self._results[result.task_id] = result
            logger.info(
                f"[Backend] 任务 {result.task_id} 结果已存储: {result.status.value}"
            )

    def get(self, task_id: str) -> Optional[TaskResult]:
        with self._lock:
            return self._results.get(task_id)

    def list_all(self) -> list[TaskResult]:
        with self._lock:
            return list(self._results.values())

    def cleanup(self, before: datetime) -> int:
        """清理指定时间之前的结果"""
        with self._lock:
            to_remove = [
                tid for tid, r in self._results.items()
                if r.completed_at and r.completed_at < before
            ]
            for tid in to_remove:
                del self._results[tid]
            return len(to_remove)


class TaskWorker:
    """
    任务工作者 (对应 Celery Worker)

    负责从 Broker 消费任务并执行。

    C++ 对比:
        C++ 中通常使用线程池 (如 std::thread 或 ThreadPool) 实现类似功能。
        Celery Worker 是独立进程，通过消息队列通信；
        C++ 线程池通常在进程内通过共享内存通信，延迟更低但扩展性较差。
    """

    def __init__(
        self,
        broker: Broker,
        backend: ResultBackend,
        task_registry: dict[str, callable],
        concurrency: int = 4,
        queues: list[str] | None = None,
    ) -> None:
        self.broker = broker
        self.backend = backend
        self.task_registry = task_registry
        self.concurrency = concurrency
        self.queues = queues or ["default"]
        self._running = False
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        logger.info(f"TaskWorker 初始化完成 (并发数: {concurrency}, 队列: {self.queues})")

    def start(self) -> None:
        """启动 Worker"""
        self._running = True
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.concurrency
        )
        logger.info("Worker 已启动，等待任务...")

        # 在独立线程中运行消费循环
        self._consume_thread = Thread(target=self._consume_loop, daemon=True)
        self._consume_thread.start()

    def stop(self) -> None:
        """停止 Worker"""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=True)
        logger.info("Worker 已停止")

    def _consume_loop(self) -> None:
        """消费循环"""
        while self._running:
            task_found = False
            for queue in self.queues:
                task = self.broker.consume(queue)
                if task:
                    task_found = True
                    self._executor.submit(self._execute_task, task)
            if not task_found:
                time.sleep(0.1)  # 避免空轮询

    def _execute_task(self, task: Task) -> None:
        """执行单个任务"""
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.STARTED,
            queue=task.queue,
        )
        self.backend.store(result)

        try:
            # 检查是否是定时任务 (ETA)
            if task.eta and task.eta > datetime.now():
                wait_seconds = (task.eta - datetime.now()).total_seconds()
                logger.info(f"任务 {task.task_id} 等待 {wait_seconds:.1f} 秒后执行")
                time.sleep(wait_seconds)

            # 执行任务函数
            if task.func_name not in self.task_registry:
                raise ValueError(f"未注册的任务函数: {task.func_name}")

            func = self.task_registry[task.func_name]
            task_result = func(*task.args, **task.kwargs)

            result.status = TaskStatus.SUCCESS
            result.result = task_result
            result.completed_at = datetime.now()
            logger.info(f"任务 {task.task_id} 执行成功")

        except Exception as e:
            logger.error(f"任务 {task.task_id} 执行失败: {e}")
            if task.retries < task.max_retries:
                # 重试
                task.retries += 1
                result.status = TaskStatus.RETRY
                result.retries = task.retries
                result.error = str(e)
                logger.info(
                    f"任务 {task.task_id} 将在 {task.retry_delay} 秒后重试 "
                    f"(第 {task.retries}/{task.max_retries} 次)"
                )
                time.sleep(task.retry_delay)
                self.broker.publish(task)
            else:
                result.status = TaskStatus.FAILURE
                result.error = str(e)
                result.completed_at = datetime.now()

        self.backend.store(result)


class CeleryLike:
    """
    类 Celery 的任务调度系统 (简化模拟版)

    展示 Celery 的核心工作原理，无需安装 Redis/Celery 即可运行。

    C++ 对比:
        类似于 C++ 中使用 ZeroMQ + Protocol Buffers 构建的任务分发系统，
        或使用 Boost.MPI 进行分布式计算。C++ 方案性能更高但开发周期长。
    """

    def __init__(self, name: str = "demo") -> None:
        self.name = name
        self.broker = InMemoryBroker()
        self.backend = ResultBackend()
        self.task_registry: dict[str, callable] = {}
        self._worker: Optional[TaskWorker] = None
        self._scheduled_tasks: list[tuple[datetime, Task]] = []
        logger.info(f"CeleryLike 应用 '{name}' 已创建")

    def task(
        self,
        name: str | None = None,
        bind: bool = False,
        max_retries: int = 3,
        queue: str = "default",
    ) -> callable:
        """任务装饰器，类似 @app.task"""

        def decorator(func: callable) -> callable:
            task_name = name or f"{func.__module__}.{func.__qualname__}"
            self.task_registry[task_name] = func

            def delay(*args: Any, **kwargs: Any) -> str:
                """异步延迟执行 (类似 Celery 的 .delay())"""
                task_id = str(uuid.uuid4())
                task = Task(
                    task_id=task_id,
                    func_name=task_name,
                    args=args,
                    kwargs=kwargs,
                    queue=queue,
                    max_retries=max_retries,
                )
                self.broker.publish(task)
                return task_id

            def apply_async(
                args: tuple = (),
                kwargs: dict | None = None,
                eta: datetime | None = None,
                countdown: float | None = None,
                priority: int = 0,
            ) -> str:
                """异步执行 (类似 Celery 的 .apply_async())"""
                task_id = str(uuid.uuid4())
                scheduled_eta = eta
                if countdown is not None:
                    scheduled_eta = datetime.now() + timedelta(seconds=countdown)
                task = Task(
                    task_id=task_id,
                    func_name=task_name,
                    args=args,
                    kwargs=kwargs or {},
                    queue=queue,
                    max_retries=max_retries,
                    eta=scheduled_eta,
                    priority=priority,
                )
                self.broker.publish(task)
                return task_id

            func.delay = delay  # type: ignore
            func.apply_async = apply_async  # type: ignore
            func.task_name = task_name  # type: ignore
            logger.info(f"任务 '{task_name}' 已注册")
            return func

        return decorator

    def start_worker(self, concurrency: int = 4) -> None:
        """启动 Worker"""
        self._worker = TaskWorker(
            broker=self.broker,
            backend=self.backend,
            task_registry=self.task_registry,
            concurrency=concurrency,
        )
        self._worker.start()

    def stop_worker(self) -> None:
        """停止 Worker"""
        if self._worker:
            self._worker.stop()

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果 (类似 Celery 的 AsyncResult)"""
        return self.backend.get(task_id)

    def wait_for_result(
        self, task_id: str, timeout: float = 30.0
    ) -> TaskResult:
        """等待任务完成"""
        start = time.time()
        while time.time() - start < timeout:
            result = self.backend.get(task_id)
            if result and result.status in (
                TaskStatus.SUCCESS,
                TaskStatus.FAILURE,
            ):
                return result
            time.sleep(0.1)
        raise TimeoutError(f"等待任务 {task_id} 超时 ({timeout}秒)")


# ============================================================================
# Part 3: 企业级应用场景示例
# ============================================================================

# --- 场景 1: 邮件发送队列 ---

@dataclass
class EmailMessage:
    """邮件消息数据结构"""
    to: str
    subject: str
    body: str
    cc: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    priority: str = "normal"  # low, normal, high


class EmailService:
    """
    邮件发送服务

    企业应用中，邮件发送是典型的异步任务场景:
    - 用户注册后发送欢迎邮件
    - 密码重置邮件
    - 订单确认邮件
    - 批量营销邮件

    将邮件发送异步化可以:
    1. 提升 API 响应速度 (用户无需等待邮件发送完成)
    2. 支持重试机制 (SMTP 服务不可用时自动重试)
    3. 支持限流 (避免被邮件服务商封禁)
    """

    def __init__(self, smtp_host: str = "smtp.example.com") -> None:
        self.smtp_host = smtp_host
        self.sent_count = 0

    def send(self, message: EmailMessage) -> dict[str, Any]:
        """同步发送邮件 (模拟)"""
        # 实际实现中这里会连接 SMTP 服务器
        time.sleep(0.5)  # 模拟网络延迟
        self.sent_count += 1
        return {
            "message_id": str(uuid.uuid4()),
            "to": message.to,
            "subject": message.subject,
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
        }


def demo_email_queue(app: CeleryLike) -> None:
    """演示邮件发送队列"""
    print("\n" + "=" * 70)
    print("场景 1: 邮件发送队列")
    print("=" * 70)

    email_service = EmailService()

    @app.task(name="send_email", queue="email", max_retries=3)
    def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
        """异步邮件发送任务"""
        message = EmailMessage(to=to, subject=subject, body=body)
        return email_service.send(message)

    # 模拟用户注册后发送欢迎邮件
    emails = [
        ("alice@example.com", "欢迎注册", "您好 Alice，欢迎加入我们的平台！"),
        ("bob@example.com", "欢迎注册", "您好 Bob，欢迎加入我们的平台！"),
        ("charlie@example.com", "密码重置", "您好 Charlie，您的验证码是: 123456"),
    ]

    task_ids: list[str] = []
    for to, subject, body in emails:
        task_id = send_email.delay(to, subject, body)
        task_ids.append(task_id)
        print(f"  已提交邮件任务: {to} - {subject} (ID: {task_id[:8]}...)")

    return task_ids


# --- 场景 2: 报表生成 ---

@dataclass
class ReportRequest:
    """报表请求"""
    report_type: str  # daily, weekly, monthly
    date_range: tuple[str, str]
    format: str = "pdf"  # pdf, xlsx, csv
    filters: dict[str, Any] = field(default_factory=dict)


class ReportGenerator:
    """
    报表生成器

    报表生成是典型的耗时任务:
    - 日报/周报/月报
    - 数据分析报告
    - 财务报表
    - 用户行为分析

    异步化优势:
    1. 用户提交请求后立即返回，后台生成
    2. 生成完成后通知用户下载
    3. 支持大报表的分批处理
    """

    def generate(self, request: ReportRequest) -> dict[str, Any]:
        """生成报表 (模拟)"""
        # 模拟耗时的数据查询和报表生成
        time.sleep(1.0)
        return {
            "report_id": str(uuid.uuid4()),
            "type": request.report_type,
            "format": request.format,
            "file_size": "2.5MB",
            "file_path": f"/reports/{request.report_type}_{datetime.now():%Y%m%d}.{request.format}",
            "generated_at": datetime.now().isoformat(),
        }


def demo_report_generation(app: CeleryLike) -> None:
    """演示报表生成队列"""
    print("\n" + "=" * 70)
    print("场景 2: 异步报表生成")
    print("=" * 70)

    generator = ReportGenerator()

    @app.task(name="generate_report", queue="reports", max_retries=1)
    def generate_report(
        report_type: str,
        date_start: str,
        date_end: str,
        fmt: str = "pdf",
    ) -> dict[str, Any]:
        """异步报表生成任务"""
        request = ReportRequest(
            report_type=report_type,
            date_range=(date_start, date_end),
            format=fmt,
        )
        return generator.generate(request)

    # 提交多个报表生成请求
    reports = [
        ("daily", "2026-06-01", "2026-06-01", "pdf"),
        ("weekly", "2026-05-26", "2026-06-01", "xlsx"),
        ("monthly", "2026-05-01", "2026-05-31", "pdf"),
    ]

    task_ids: list[str] = []
    for report_type, start, end, fmt in reports:
        task_id = generate_report.delay(report_type, start, end, fmt)
        task_ids.append(task_id)
        print(f"  已提交报表任务: {report_type} ({start} ~ {end}) [{fmt}] (ID: {task_id[:8]}...)")

    return task_ids


# --- 场景 3: 数据同步 ---

@dataclass
class SyncConfig:
    """数据同步配置"""
    source: str
    target: str
    mode: str = "incremental"  # full, incremental
    batch_size: int = 1000
    last_sync_id: int = 0


class DataSynchronizer:
    """
    数据同步服务

    数据同步场景:
    - 数据库之间的数据迁移
    - 第三方 API 数据拉取
    - 缓存与数据库同步
    - 数据仓库 ETL

    异步化优势:
    1. 大量数据同步不阻塞主业务
    2. 支持断点续传
    3. 支持增量同步
    4. 失败自动重试
    """

    def sync(self, config: SyncConfig) -> dict[str, Any]:
        """执行数据同步 (模拟)"""
        # 模拟批量数据同步
        total_synced = 0
        batches = 3  # 模拟 3 个批次
        for i in range(batches):
            time.sleep(0.3)
            batch_count = config.batch_size
            total_synced += batch_count
            logger.info(
                f"  同步进度: 批次 {i + 1}/{batches}, "
                f"已同步 {total_synced} 条记录"
            )

        return {
            "sync_id": str(uuid.uuid4()),
            "source": config.source,
            "target": config.target,
            "mode": config.mode,
            "total_synced": total_synced,
            "batches": batches,
            "completed_at": datetime.now().isoformat(),
        }


def demo_data_sync(app: CeleryLike) -> None:
    """演示数据同步队列"""
    print("\n" + "=" * 70)
    print("场景 3: 数据同步队列")
    print("=" * 70)

    synchronizer = DataSynchronizer()

    @app.task(name="sync_data", queue="sync", max_retries=5)
    def sync_data(
        source: str,
        target: str,
        mode: str = "incremental",
        batch_size: int = 1000,
    ) -> dict[str, Any]:
        """异步数据同步任务"""
        config = SyncConfig(
            source=source,
            target=target,
            mode=mode,
            batch_size=batch_size,
        )
        return synchronizer.sync(config)

    # 提交数据同步任务
    sync_tasks = [
        ("mysql_users", "elasticsearch_users", "incremental", 500),
        ("api_orders", "warehouse_orders", "full", 2000),
        ("redis_cache", "postgresql_cache_backup", "incremental", 1000),
    ]

    task_ids: list[str] = []
    for source, target, mode, batch_size in sync_tasks:
        task_id = sync_data.delay(source, target, mode, batch_size)
        task_ids.append(task_id)
        print(
            f"  已提交同步任务: {source} -> {target} "
            f"({mode}, batch={batch_size}) (ID: {task_id[:8]}...)"
        )

    return task_ids


# --- 场景 4: 定时任务 ---

def demo_scheduled_tasks(app: CeleryLike) -> None:
    """
    演示定时任务 (Celery Beat)

    定时任务场景:
    - 每日数据备份
    - 定期清理过期数据
    - 定时发送报告
    - 监控告警检查
    """
    print("\n" + "=" * 70)
    print("场景 4: 定时任务 (Celery Beat)")
    print("=" * 70)

    @app.task(name="cleanup_expired_data", queue="default")
    def cleanup_expired_data(days: int = 30) -> dict[str, Any]:
        """清理过期数据"""
        time.sleep(0.3)
        return {
            "cleaned_records": 1500,
            "older_than_days": days,
            "cleaned_at": datetime.now().isoformat(),
        }

    @app.task(name="health_check", queue="default")
    def health_check() -> dict[str, Any]:
        """系统健康检查"""
        return {
            "status": "healthy",
            "cpu_usage": "45%",
            "memory_usage": "62%",
            "disk_usage": "38%",
            "checked_at": datetime.now().isoformat(),
        }

    # 模拟定时任务的 ETA (预计执行时间)
    print("\n  定时任务配置示例 (Celery Beat schedule):")
    print("  - 每天凌晨 2:00  执行数据备份")
    print("  - 每小时执行       清理过期数据")
    print("  - 每 5 分钟执行    系统健康检查")

    # 使用 countdown 模拟延迟执行
    task_id1 = cleanup_expired_data.apply_async(args=(30,), countdown=2)
    task_id2 = health_check.apply_async(countdown=1)

    print(f"\n  已提交定时任务: cleanup_expired_data (ETA: 2秒后, ID: {task_id1[:8]}...)")
    print(f"  已提交定时任务: health_check (ETA: 1秒后, ID: {task_id2[:8]}...)")

    return [task_id1, task_id2]


# ============================================================================
# Part 4: Celery vs C++ 任务队列库对比
# ============================================================================

def print_cpp_comparison() -> None:
    """
    Celery vs C++ 任务队列库对比分析
    """
    print("\n" + "=" * 70)
    print("Celery vs C++ 任务队列库 对比")
    print("=" * 70)

    comparison = """
    +------------------+----------------------------------------+----------------------------------------+
    | 特性             | Python Celery                          | C++ 方案                               |
    +------------------+----------------------------------------+----------------------------------------+
    | 消息代理         | Redis, RabbitMQ, SQS (内置支持)        | ZeroMQ, RabbitMQ-C, Kafka (需自行集成) |
    | 任务序列化       | JSON, Pickle, YAML (开箱即用)          | Protocol Buffers, FlatBuffers, JSON    |
    | 并发模型         | 多进程/协程 (prefork/eventlet/gevent)  | 多线程/异步 I/O (std::thread/asio)     |
    | 定时任务         | Celery Beat (内置)                     | 需自行实现或使用 cron/APScheduler      |
    | 监控工具         | Flower (Web 监控界面)                  | 需自建监控系统                         |
    | 任务重试         | 内置支持 (max_retries, retry_backoff)  | 需自行实现                             |
    | 任务路由         | 内置支持 (按队列/类型路由)             | 需自行设计路由逻辑                     |
    | 优先级队列       | 支持 (Redis/RabbitMQ)                  | 需自行实现或使用消息队列特性           |
    | 任务链/工作流    | Canvas (chain, group, chord, map)      | 需自行编排                             |
    | 开发效率         | 高 (开箱即用，生态丰富)                | 中低 (需更多底层实现)                  |
    | 运行性能         | 中等 (受 GIL 限制)                     | 高 (原生编译，无 GIL)                  |
    | 内存占用         | 较高 (Python 解释器开销)               | 低 (原生内存管理)                      |
    | 适用场景         | Web 后台任务、数据处理、定时任务        | 高频交易、实时系统、嵌入式             |
    +------------------+----------------------------------------+----------------------------------------+

    C++ 常用任务队列库:
    ───────────────────
    1. Intel TBB (Threading Building Blocks)
       - 并行任务调度框架
       - 支持 task_group, parallel_for, pipeline
       - 适合 CPU 密集型并行计算

    2. Boost.Asio
       - 异步 I/O 框架
       - 可构建异步任务队列
       - 适合 I/O 密集型任务

    3. Folly (Facebook)
       - 包含 Futures/Executors 框架
       - 高性能任务调度
       - 适合大规模分布式系统

    4. Seastar (ScyllaDB)
       - 异步编程框架
       - 共享无锁 (share-nothing) 架构
       - 适合高性能网络服务

    5. Disruptor (C++ 移植)
       - 无锁环形缓冲区
       - 超低延迟任务传递
       - 适合高频交易系统

    选择建议:
    ─────────
    - 需要快速开发、生态丰富 -> Python Celery
    - 需要极致性能、低延迟 -> C++ (TBB/Folly/Seastar)
    - 需要平衡 -> Python 做调度 + C++ 做计算密集型子任务
    """
    print(comparison)


# ============================================================================
# Part 5: 主程序入口
# ============================================================================

def run_demo() -> None:
    """运行完整演示"""
    print("=" * 70)
    print("Day 58: 异步任务和定时任务 - Celery 演示")
    print("=" * 70)
    print(f"当前时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"Broker:   {REDIS_URL}")
    print(f"Backend:  {RESULT_BACKEND}")

    # 创建任务应用
    app = CeleryLike(name="demo_app")

    # 收集所有任务 ID
    all_task_ids: list[str] = []

    # 运行各场景演示
    all_task_ids.extend(demo_email_queue(app))
    all_task_ids.extend(demo_report_generation(app))
    all_task_ids.extend(demo_data_sync(app))
    all_task_ids.extend(demo_scheduled_tasks(app))

    # 启动 Worker
    print("\n" + "=" * 70)
    print("启动 Worker 处理任务...")
    print("=" * 70)
    app.start_worker(concurrency=2)

    # 等待所有任务完成
    print("\n等待任务执行完成...\n")
    for task_id in all_task_ids:
        try:
            result = app.wait_for_result(task_id, timeout=10.0)
            status_icon = "OK" if result.status == TaskStatus.SUCCESS else "FAIL"
            print(
                f"  [{status_icon}] 任务 {task_id[:8]}... "
                f"状态: {result.status.value} "
                f"耗时: {(result.completed_at - result.created_at).total_seconds():.2f}s"
                if result.completed_at
                else f"  [??] 任务 {task_id[:8]}... 状态: {result.status.value}"
            )
        except TimeoutError:
            print(f"  [TIMEOUT] 任务 {task_id[:8]}... 等待超时")

    # 停止 Worker
    app.stop_worker()

    # 打印 C++ 对比
    print_cpp_comparison()

    # 打印任务统计
    print("\n" + "=" * 70)
    print("任务执行统计")
    print("=" * 70)
    results = app.backend.list_all()
    status_counts: dict[str, int] = {}
    for r in results:
        status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1

    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    print(f"  总计: {len(results)}")

    print("\n演示完成！")


if __name__ == "__main__":
    # 检查是否在 Celery 环境中运行
    # 生产环境中使用以下命令启动:
    #   celery -A tasks worker --loglevel=info
    #   celery -A tasks beat --loglevel=info
    #
    # 本演示使用模拟的任务队列系统，无需 Redis/Celery 即可运行

    if "--celery" in sys.argv:
        # 生产模式: 使用真实 Celery
        print("以 Celery 模式启动...")
        print("请使用以下命令:")
        print("  celery -A 58_async_task worker --loglevel=info")
        print("  celery -A 58_async_task beat --loglevel=info")
    else:
        # 演示模式: 使用模拟任务队列
        run_demo()
