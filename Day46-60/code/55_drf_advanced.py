"""
Day 55 - RESTful架构和DRF进阶 综合示例

本模块演示 Django REST Framework 的进阶功能:
  - ModelViewSet 和 ReadOnlyModelViewSet
  - 自定义分页 (PageNumberPagination)
  - 数据筛选 (django-filter + 自定义 get_queryset)
  - 嵌套序列化器 (Nested Serializers)
  - 权限控制 (Permissions)
  - 限流/节流 (Throttling)
  - 自定义动作 (@action)

运行前请确保已安装:
  pip install django djangorestframework django-filter

启动方式:
  python 55_drf_advanced.py runserver 8000
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any, Optional

import django
from django.conf import settings
from django.conf.urls import include
from django.db import models
from django.http import Http404, JsonResponse
from django.urls import path
from rest_framework import (
    filters,
    generics,
    mixins,
    permissions,
    serializers,
    status,
    throttling,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView

# ---------------------------------------------------------------------------
# Django 最小化配置
# ---------------------------------------------------------------------------
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="day55-drf-advanced-secret-key-change-in-production",
        ROOT_URLCONF=__name__,
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "rest_framework",
            "django_filters",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(os.path.dirname(__file__), "db_day55.sqlite3"),
            }
        },
        REST_FRAMEWORK={
            # 全局默认分页
            "PAGE_SIZE": 10,
            "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
            # 全局默认限流
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
                "rest_framework.throttling.UserRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "anon": "20/minute",
                "user": "100/minute",
                "enterprise_upload": "5/hour",
            },
            # 全局默认权限
            "DEFAULT_PERMISSION_CLASSES": [
                "rest_framework.permissions.AllowAny",
            ],
            # 全局过滤后端
            "DEFAULT_FILTER_BACKENDS": [
                "django_filters.rest_framework.DjangoFilterBackend",
                "rest_framework.filters.SearchFilter",
                "rest_framework.filters.OrderingFilter",
            ],
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )

django.setup()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Department(models.Model):
    """部门模型 - 企业组织架构中的部门"""

    name: str = models.CharField("部门名称", max_length=64, unique=True)
    code: str = models.CharField("部门编码", max_length=16, unique=True)
    description: str = models.TextField("部门描述", blank=True, default="")
    created_at: datetime = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "day55_department"
        verbose_name = "部门"
        verbose_name_plural = verbose_name
        ordering: list[str] = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Employee(models.Model):
    """员工模型 - 关联到部门 (多对一)"""

    class Role(models.TextChoices):
        INTERN = "intern", "实习生"
        JUNIOR = "junior", "初级工程师"
        SENIOR = "senior", "高级工程师"
        LEAD = "lead", "技术主管"
        MANAGER = "manager", "经理"

    name: str = models.CharField("姓名", max_length=64)
    email: str = models.EmailField("邮箱", unique=True)
    department: Department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="employees",
        verbose_name="所属部门",
    )
    role: str = models.CharField(
        "职级", max_length=16, choices=Role.choices, default=Role.JUNIOR
    )
    salary: float = models.DecimalField(
        "薪资", max_digits=10, decimal_places=2, default=0
    )
    is_active: bool = models.BooleanField("在职", default=True)
    hire_date: datetime = models.DateField("入职日期", auto_now_add=True)

    class Meta:
        db_table = "day55_employee"
        verbose_name = "员工"
        verbose_name_plural = verbose_name
        ordering: list[str] = ["-hire_date"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_role_display()})"


class Project(models.Model):
    """项目模型 - 多对多关联员工"""

    class Status(models.TextChoices):
        PLANNING = "planning", "规划中"
        ACTIVE = "active", "进行中"
        COMPLETED = "completed", "已完成"
        ARCHIVED = "archived", "已归档"

    name: str = models.CharField("项目名称", max_length=128)
    code: str = models.CharField("项目编码", max_length=32, unique=True)
    status: str = models.CharField(
        "项目状态", max_length=16, choices=Status.choices, default=Status.PLANNING
    )
    members: models.ManyToManyField = models.ManyToManyField(
        Employee,
        related_name="projects",
        verbose_name="项目成员",
        blank=True,
    )
    budget: float = models.DecimalField(
        "预算", max_digits=12, decimal_places=2, default=0
    )
    start_date: Optional[datetime] = models.DateField("开始日期", null=True, blank=True)
    end_date: Optional[datetime] = models.DateField("结束日期", null=True, blank=True)

    class Meta:
        db_table = "day55_project"
        verbose_name = "项目"
        verbose_name_plural = verbose_name
        ordering: list[str] = ["-start_date"]

    def __str__(self) -> str:
        return f"[{self.code}] {self.name}"


# ---------------------------------------------------------------------------
# 自定义权限类
# ---------------------------------------------------------------------------


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    自定义权限: 管理员可读写, 其他用户只读.
    适用于部门管理等需要保护写操作的场景.
    """

    message: str = "仅管理员可以执行写操作."

    def has_permission(self, request: Request, view: APIView) -> bool:
        # GET / HEAD / OPTIONS 请求始终允许
        if request.method in permissions.SAFE_METHODS:
            return True
        # 写操作需要管理员权限
        return bool(request.user and request.user.is_staff)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    对象级权限: 仅对象所有者或管理员可修改.
    演示 DRF 的对象级权限控制.
    """

    message: str = "您没有权限修改此对象."

    def has_object_permission(
        self, request: Request, view: APIView, obj: Any
    ) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        # 管理员拥有所有权限
        if request.user and request.user.is_staff:
            return True
        # 普通用户只能修改自己的数据 (假设有 owner 字段)
        owner = getattr(obj, "owner", None)
        if owner is not None:
            return owner == request.user
        return False


# ---------------------------------------------------------------------------
# 自定义限流类
# ---------------------------------------------------------------------------


class EmployeeCreateRateThrottle(throttling.BaseThrottle):
    """
    自定义限流: 控制员工创建接口的请求频率.
    企业场景: 防止批量误操作或恶意创建数据.

    简化实现: 使用类变量模拟内存中的访问记录.
    """

    # 内存中记录最近访问 (生产环境应使用 Redis)
    _access_log: dict[str, list[float]] = {}
    RATE_LIMIT: int = 5  # 每分钟最多 5 次
    WINDOW_SECONDS: int = 60

    def allow_request(self, request: Request, view: APIView) -> bool:
        if request.method != "POST":
            return True

        ident: str = self.get_ident(request)
        now: float = datetime.now().timestamp()

        # 清理过期记录
        if ident in self._access_log:
            self._access_log[ident] = [
                t for t in self._access_log[ident] if now - t < self.WINDOW_SECONDS
            ]
        else:
            self._access_log[ident] = []

        if len(self._access_log[ident]) >= self.RATE_LIMIT:
            return False

        self._access_log[ident].append(now)
        return True

    def wait(self) -> float:
        """返回建议等待的秒数"""
        return self.WINDOW_SECONDS


class EnterpriseUploadThrottle(throttling.UserRateThrottle):
    """
    企业文件上传限流 - 使用 DRF 内置的 UserRateThrottle.
    在 settings 中配置速率为 '5/hour'.
    """

    scope: str = "enterprise_upload"


# ---------------------------------------------------------------------------
# 自定义分页器
# ---------------------------------------------------------------------------


class StandardResultsPagination(PageNumberPagination):
    """
    标准分页器 - 可通过查询参数自定义页码和每页条数.
    ?page=2&page_size=20
    """

    page_size: int = 10
    page_size_query_param: str = "page_size"
    max_page_size: int = 100


class SmallResultsPagination(PageNumberPagination):
    """小分页器 - 适用于返回少量数据的接口"""

    page_size: int = 5
    page_size_query_param: str = "page_size"
    max_page_size: int = 20


# ---------------------------------------------------------------------------
# 序列化器 (含嵌套)
# ---------------------------------------------------------------------------


class DepartmentBriefSerializer(serializers.ModelSerializer):
    """部门简要序列化器 - 用于嵌套显示, 只含核心字段"""

    class Meta:
        model = Department
        fields: list[str] = ["id", "name", "code"]
        read_only_fields: list[str] = fields


class EmployeeBriefSerializer(serializers.ModelSerializer):
    """员工简要序列化器 - 用于嵌套显示"""

    role_display: str = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Employee
        fields: list[str] = ["id", "name", "email", "role", "role_display"]
        read_only_fields: list[str] = fields


class DepartmentDetailSerializer(serializers.ModelSerializer):
    """
    部门详细序列化器 - 嵌套显示该部门的员工列表.
    演示反向关系的嵌套序列化.
    """

    employees: EmployeeBriefSerializer = EmployeeBriefSerializer(
        many=True, read_only=True
    )
    employee_count: int = serializers.IntegerField(
        source="employees.count", read_only=True
    )

    class Meta:
        model = Department
        fields: list[str] = [
            "id",
            "name",
            "code",
            "description",
            "employee_count",
            "employees",
            "created_at",
        ]
        read_only_fields: list[str] = ["id", "created_at"]


class EmployeeSerializer(serializers.ModelSerializer):
    """
    员工序列化器 - 嵌套显示所属部门信息.
    演示正向外键的嵌套序列化.
    """

    department_detail: DepartmentBriefSerializer = DepartmentBriefSerializer(
        source="department", read_only=True
    )
    role_display: str = serializers.CharField(source="get_role_display", read_only=True)
    project_count: int = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields: list[str] = [
            "id",
            "name",
            "email",
            "department",
            "department_detail",
            "role",
            "role_display",
            "salary",
            "is_active",
            "hire_date",
            "project_count",
        ]
        read_only_fields: list[str] = ["id", "hire_date"]

    def get_project_count(self, obj: Employee) -> int:
        """计算员工参与的项目数量"""
        return obj.projects.count()

    def validate_salary(self, value: float) -> float:
        """薪资不能为负数"""
        if value < 0:
            raise serializers.ValidationError("薪资不能为负数.")
        return value

    def validate_email(self, value: str) -> str:
        """邮箱域名校验 - 企业场景限制公司域名"""
        allowed_domains = ["example.com", "company.cn"]
        domain = value.split("@")[-1].lower()
        if domain not in allowed_domains:
            raise serializers.ValidationError(
                f"仅允许以下域名: {', '.join(allowed_domains)}"
            )
        return value


class ProjectSerializer(serializers.ModelSerializer):
    """
    项目序列化器 - 嵌套显示项目成员信息.
    演示多对多关系的嵌套序列化.
    """

    members_detail: EmployeeBriefSerializer = EmployeeBriefSerializer(
        source="members", many=True, read_only=True
    )
    member_count: int = serializers.SerializerMethodField()
    status_display: str = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Project
        fields: list[str] = [
            "id",
            "name",
            "code",
            "status",
            "status_display",
            "budget",
            "members",
            "members_detail",
            "member_count",
            "start_date",
            "end_date",
        ]
        read_only_fields: list[str] = ["id"]

    def get_member_count(self, obj: Project) -> int:
        return obj.members.count()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """跨字段校验: 结束日期必须晚于开始日期"""
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "结束日期不能早于开始日期."}
            )
        return attrs


# ---------------------------------------------------------------------------
# Views - 基于 ModelViewSet 的完整 CRUD
# ---------------------------------------------------------------------------


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    部门视图集 - 完整 CRUD + 自定义动作.

    权限: 管理员可读写, 其他用户只读 (IsAdminOrReadOnly).
    分页: 使用小分页器.
    筛选: 支持按名称搜索、按编码精确筛选.
    """

    queryset: models.QuerySet = Department.objects.all()
    permission_classes: list[type[permissions.BasePermission]] = [IsAdminOrReadOnly]
    pagination_class: type[PageNumberPagination] = SmallResultsPagination
    filterset_fields: list[str] = ["code"]
    search_fields: list[str] = ["name", "code", "description"]
    ordering_fields: list[str] = ["code", "name", "created_at"]

    def get_serializer_class(self) -> type[serializers.ModelSerializer]:
        """根据动作选择序列化器"""
        if self.action == "retrieve":
            return DepartmentDetailSerializer
        return DepartmentDetailSerializer

    @action(detail=True, methods=["get"], url_path="employees")
    def department_employees(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        自定义动作: 获取指定部门下的所有在职员工.
        GET /api/departments/{id}/employees/
        """
        department: Department = self.get_object()
        employees: models.QuerySet = department.employees.filter(is_active=True)

        # 支持按职级筛选
        role_filter: str = request.query_params.get("role", "")
        if role_filter:
            employees = employees.filter(role=role_filter)

        serializer: EmployeeBriefSerializer = EmployeeBriefSerializer(
            employees, many=True
        )
        return Response(
            {
                "department": DepartmentBriefSerializer(department).data,
                "employee_count": employees.count(),
                "employees": serializer.data,
            }
        )

    @action(detail=False, methods=["get"], url_path="statistics")
    def department_statistics(self, request: Request) -> Response:
        """
        自定义动作: 获取部门统计信息.
        GET /api/departments/statistics/
        """
        departments: models.QuerySet = Department.objects.all()
        stats: list[dict[str, Any]] = []
        for dept in departments:
            active_count: int = dept.employees.filter(is_active=True).count()
            stats.append(
                {
                    "id": dept.id,
                    "name": dept.name,
                    "code": dept.code,
                    "active_employees": active_count,
                }
            )
        return Response({"total_departments": len(stats), "details": stats})


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    员工视图集 - 完整 CRUD + 复杂筛选 + 自定义限流.

    限流: 创建操作使用自定义限流 (5次/分钟).
    筛选: 支持按部门、职级、在职状态筛选, 支持姓名搜索.
    """

    queryset: models.QuerySet = Employee.objects.select_related("department").all()
    serializer_class: type[serializers.ModelSerializer] = EmployeeSerializer
    pagination_class: type[PageNumberPagination] = StandardResultsPagination
    filterset_fields: list[str] = ["department", "role", "is_active"]
    search_fields: list[str] = ["name", "email"]
    ordering_fields: list[str] = ["name", "salary", "hire_date"]

    def get_throttles(self) -> list[throttling.BaseThrottle]:
        """根据动作选择限流策略"""
        if self.action == "create":
            return [EmployeeCreateRateThrottle()]
        return super().get_throttles()

    def get_queryset(self) -> models.QuerySet:
        """
        自定义查询集 - 支持复杂筛选参数.
        ?min_salary=10000&max_salary=50000&department_code=ENG
        """
        queryset: models.QuerySet = super().get_queryset()

        # 薪资范围筛选
        min_salary: Optional[str] = self.request.query_params.get("min_salary")
        max_salary: Optional[str] = self.request.query_params.get("max_salary")
        if min_salary is not None:
            queryset = queryset.filter(salary__gte=min_salary)
        if max_salary is not None:
            queryset = queryset.filter(salary__lte=max_salary)

        # 部门编码筛选 (模糊匹配)
        dept_code: str = self.request.query_params.get("department_code", "")
        if dept_code:
            queryset = queryset.filter(department__code__icontains=dept_code)

        # 入职日期范围
        hire_after: str = self.request.query_params.get("hire_after", "")
        if hire_after:
            queryset = queryset.filter(hire_date__gte=hire_after)

        return queryset

    @action(detail=False, methods=["get"], url_path="by-role-summary")
    def role_summary(self, request: Request) -> Response:
        """
        自定义动作: 按职级统计员工数量和平均薪资.
        GET /api/employees/by-role-summary/
        """
        from django.db.models import Avg, Count

        summary: models.QuerySet = (
            Employee.objects.filter(is_active=True)
            .values("role")
            .annotate(count=Count("id"), avg_salary=Avg("salary"))
            .order_by("role")
        )

        result: list[dict[str, Any]] = []
        for item in summary:
            result.append(
                {
                    "role": item["role"],
                    "role_display": dict(Employee.Role.choices).get(item["role"], ""),
                    "count": item["count"],
                    "avg_salary": round(float(item["avg_salary"]), 2),
                }
            )

        return Response({"role_summary": result})


class ProjectViewSet(viewsets.ModelViewSet):
    """
    项目视图集 - 完整 CRUD + 成员管理自定义动作.

    权限: 使用 AllowAny (演示目的, 生产环境应更严格).
    """

    queryset: models.QuerySet = Project.objects.prefetch_related("members").all()
    serializer_class: type[serializers.ModelSerializer] = ProjectSerializer
    pagination_class: type[PageNumberPagination] = StandardResultsPagination
    filterset_fields: list[str] = ["status"]
    search_fields: list[str] = ["name", "code"]
    ordering_fields: list[str] = ["name", "budget", "start_date"]

    @action(detail=True, methods=["post", "delete"], url_path="members")
    def manage_members(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        自定义动作: 管理项目成员.
        POST   /api/projects/{id}/members/  -> 添加成员 (body: {"employee_id": 1})
        DELETE /api/projects/{id}/members/  -> 移除成员 (body: {"employee_id": 1})
        """
        project: Project = self.get_object()

        if request.method == "POST":
            employee_id: Optional[int] = request.data.get("employee_id")
            if not employee_id:
                return Response(
                    {"error": "请提供 employee_id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                employee: Employee = Employee.objects.get(pk=employee_id, is_active=True)
            except Employee.DoesNotExist:
                return Response(
                    {"error": "员工不存在或已离职."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if project.members.filter(pk=employee_id).exists():
                return Response(
                    {"error": f"员工 {employee.name} 已在项目中."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            project.members.add(employee)
            return Response(
                {
                    "message": f"已将员工 {employee.name} 添加到项目.",
                    "member_count": project.members.count(),
                },
                status=status.HTTP_200_OK,
            )

        # DELETE
        employee_id = request.data.get("employee_id")
        if not employee_id:
            return Response(
                {"error": "请提供 employee_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not project.members.filter(pk=employee_id).exists():
            return Response(
                {"error": "该员工不在项目中."},
                status=status.HTTP_404_NOT_FOUND,
            )

        employee = Employee.objects.get(pk=employee_id)
        project.members.remove(employee)
        return Response(
            {
                "message": f"已将员工 {employee.name} 从项目中移除.",
                "member_count": project.members.count(),
            }
        )

    @action(detail=True, methods=["post"], url_path="close")
    def close_project(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        自定义动作: 关闭项目 (状态变更为已完成).
        POST /api/projects/{id}/close/
        """
        project: Project = self.get_object()
        if project.status == Project.Status.COMPLETED:
            return Response(
                {"error": "项目已经是完成状态."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project.status = Project.Status.COMPLETED
        project.end_date = datetime.now().date()
        project.save(update_fields=["status", "end_date"])

        return Response(
            {
                "message": f"项目 {project.name} 已关闭.",
                "project": ProjectSerializer(project).data,
            }
        )


# ---------------------------------------------------------------------------
# 使用函数视图演示数据筛选 (对应文档中的 FBV 方式)
# ---------------------------------------------------------------------------


def employee_search_view(request: Request) -> JsonResponse:
    """
    FBV 方式实现员工搜索 - 演示文档中提到的重写 get_queryset 方式.
    GET /api/employee-search/?department=1&role=senior
    """
    queryset: models.QuerySet = Employee.objects.select_related("department").all()

    department_id: str = request.GET.get("department", "")
    if department_id:
        try:
            queryset = queryset.filter(department__id=int(department_id))
        except ValueError:
            raise Http404("无效的部门编号.")

    role: str = request.GET.get("role", "")
    if role:
        queryset = queryset.filter(role=role)

    is_active: str = request.GET.get("is_active", "")
    if is_active:
        queryset = queryset.filter(is_active=is_active.lower() == "true")

    data: list[dict[str, Any]] = list(
        queryset.values("id", "name", "email", "role", "department__name")
    )
    return JsonResponse({"count": len(data), "results": data})


# ---------------------------------------------------------------------------
# 使用 GenericAPIView 演示文档中的 CBV 方式
# ---------------------------------------------------------------------------


class DepartmentListView(generics.ListAPIView):
    """
    基于 ListAPIView 的部门列表视图 - 文档中 SubjectView 的企业版.
    支持自定义分页和筛选.
    """

    queryset: models.QuerySet = Department.objects.all()
    serializer_class: type[serializers.ModelSerializer] = DepartmentBriefSerializer
    pagination_class: type[PageNumberPagination] = SmallResultsPagination

    def get_queryset(self) -> models.QuerySet:
        queryset: models.QuerySet = super().get_queryset()
        keyword: str = self.request.query_params.get("q", "")
        if keyword:
            queryset = queryset.filter(name__icontains=keyword)
        return queryset


class EmployeeCreateView(generics.CreateAPIView):
    """
    基于 CreateAPIView 的员工创建视图 - 支持自定义限流.
    POST /api/employee-create/
    """

    serializer_class: type[serializers.ModelSerializer] = EmployeeSerializer
    throttle_classes: list[type[throttling.BaseThrottle]] = [EmployeeCreateRateThrottle]

    def perform_create(self, serializer: serializers.ModelSerializer) -> None:
        """创建后的钩子 - 可用于发送通知等"""
        instance: Employee = serializer.save()
        print(f"[通知] 新员工 {instance.name} 已入职, 所属部门: {instance.department.name}")


# ---------------------------------------------------------------------------
# URL 配置 (使用 Router 注册 ViewSet)
# ---------------------------------------------------------------------------

router: DefaultRouter = DefaultRouter()
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"projects", ProjectViewSet, basename="project")

urlpatterns: list[path] = [
    # Router 自动生成的 CRUD URL
    path("api/", include(router.urls)),
    # GenericAPIView 方式 (文档中 CBV 示例的企业版)
    path("api/department-list/", DepartmentListView.as_view(), name="department-list"),
    path("api/employee-create/", EmployeeCreateView.as_view(), name="employee-create"),
    # FBV 方式 (文档中 FBV 数据筛选的企业版)
    path("api/employee-search/", employee_search_view, name="employee-search"),
]


# ---------------------------------------------------------------------------
# 数据初始化辅助函数
# ---------------------------------------------------------------------------


def init_demo_data() -> None:
    """初始化演示数据"""
    from django.core.management import call_command

    # 执行数据库迁移
    call_command("migrate", "--run-syncdb", verbosity=0)

    # 如果已有数据则跳过
    if Department.objects.exists():
        print("[信息] 演示数据已存在, 跳过初始化.")
        return

    print("[信息] 正在初始化演示数据...")

    # 创建部门
    eng: Department = Department.objects.create(
        name="工程部", code="ENG", description="负责产品研发和技术架构"
    )
    hr: Department = Department.objects.create(
        name="人力资源部", code="HR", description="负责招聘和员工关系"
    )
    sales: Department = Department.objects.create(
        name="销售部", code="SALES", description="负责市场拓展和客户维护"
    )
    fin: Department = Department.objects.create(
        name="财务部", code="FIN", description="负责财务核算和资金管理"
    )

    # 创建员工
    employees: list[Employee] = [
        Employee.objects.create(
            name="张三", email="zhangsan@example.com", department=eng,
            role=Employee.Role.SENIOR, salary=30000,
        ),
        Employee.objects.create(
            name="李四", email="lisi@example.com", department=eng,
            role=Employee.Role.LEAD, salary=40000,
        ),
        Employee.objects.create(
            name="王五", email="wangwu@example.com", department=eng,
            role=Employee.Role.JUNIOR, salary=18000,
        ),
        Employee.objects.create(
            name="赵六", email="zhaoliu@example.com", department=hr,
            role=Employee.Role.MANAGER, salary=35000,
        ),
        Employee.objects.create(
            name="钱七", email="qianqi@example.com", department=sales,
            role=Employee.Role.JUNIOR, salary=15000,
        ),
        Employee.objects.create(
            name="孙八", email="sunba@example.com", department=sales,
            role=Employee.Role.SENIOR, salary=28000,
        ),
        Employee.objects.create(
            name="周九", email="zhoujiu@example.com", department=fin,
            role=Employee.Role.SENIOR, salary=32000,
        ),
        Employee.objects.create(
            name="吴十", email="wushi@example.com", department=eng,
            role=Employee.Role.INTERN, salary=8000,
        ),
    ]

    # 创建项目并分配成员
    proj_alpha: Project = Project.objects.create(
        name="Alpha 平台重构", code="ALPHA-001",
        status=Project.Status.ACTIVE, budget=500000,
        start_date="2026-01-15",
    )
    proj_alpha.members.add(employees[0], employees[1], employees[2], employees[7])

    proj_beta: Project = Project.objects.create(
        name="Beta 移动应用", code="BETA-002",
        status=Project.Status.PLANNING, budget=300000,
        start_date="2026-04-01",
    )
    proj_beta.members.add(employees[0], employees[4])

    proj_gamma: Project = Project.objects.create(
        name="Gamma 数据分析", code="GAMMA-003",
        status=Project.Status.COMPLETED, budget=200000,
        start_date="2025-06-01", end_date="2025-12-31",
    )
    proj_gamma.members.add(employees[1], employees[6])

    print(f"[信息] 已创建 {Department.objects.count()} 个部门")
    print(f"[信息] 已创建 {Employee.objects.count()} 名员工")
    print(f"[信息] 已创建 {Project.objects.count()} 个项目")
    print("[信息] 演示数据初始化完成!")


# ---------------------------------------------------------------------------
# API 文档 - 列出所有可用接口
# ---------------------------------------------------------------------------


def print_api_docs() -> None:
    """打印 API 接口文档"""
    docs: str = """
======================================================================
  Day 55 - DRF 进阶 API 接口文档
======================================================================

--- Router 自动生成的 CRUD 接口 ---

  部门 (Departments):
    GET    /api/departments/                  - 部门列表 (分页)
    POST   /api/departments/                  - 创建部门 (需管理员)
    GET    /api/departments/{id}/             - 部门详情 (含嵌套员工)
    PUT    /api/departments/{id}/             - 更新部门 (需管理员)
    PATCH  /api/departments/{id}/             - 部分更新 (需管理员)
    DELETE /api/departments/{id}/             - 删除部门 (需管理员)
    GET    /api/departments/{id}/employees/   - 获取部门在职员工
    GET    /api/departments/statistics/       - 部门统计信息

  员工 (Employees):
    GET    /api/employees/                    - 员工列表 (分页+筛选)
    POST   /api/employees/                    - 创建员工 (限流: 5次/分)
    GET    /api/employees/{id}/               - 员工详情 (含嵌套部门)
    PUT    /api/employees/{id}/               - 更新员工
    DELETE /api/employees/{id}/               - 删除员工
    GET    /api/employees/by-role-summary/    - 按职级统计

  项目 (Projects):
    GET    /api/projects/                     - 项目列表
    POST   /api/projects/                     - 创建项目
    GET    /api/projects/{id}/                - 项目详情 (含嵌套成员)
    PUT    /api/projects/{id}/                - 更新项目
    DELETE /api/projects/{id}/                - 删除项目
    POST   /api/projects/{id}/members/        - 添加项目成员
    DELETE /api/projects/{id}/members/        - 移除项目成员
    POST   /api/projects/{id}/close/          - 关闭项目

--- GenericAPIView 方式 ---

    GET    /api/department-list/              - 部门列表 (CBV方式)
    POST   /api/employee-create/             - 创建员工 (CBV+限流)

--- FBV 方式 ---

    GET    /api/employee-search/              - 员工搜索 (函数视图)

--- 查询参数 ---

  员工筛选:
    ?department={id}       - 按部门筛选
    ?role={role}           - 按职级筛选 (intern/junior/senior/lead/manager)
    ?is_active=true/false  - 按在职状态筛选
    ?min_salary=10000      - 最低薪资
    ?max_salary=50000      - 最高薪资
    ?department_code=ENG   - 按部门编码模糊搜索
    ?hire_after=2025-01-01 - 入职日期之后
    ?search=张三           - 全文搜索 (姓名/邮箱)
    ?ordering=salary       - 排序 (加 - 前缀为降序: ?ordering=-salary)
    ?page=2&page_size=20   - 分页

  部门筛选:
    ?code=ENG              - 按部门编码精确筛选
    ?search=工程           - 搜索部门名称/编码/描述

======================================================================
"""
    print(docs)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        init_demo_data()
        print_api_docs()

        port: str = sys.argv[2] if len(sys.argv) > 2 else "8000"
        print(f"[信息] 启动开发服务器 http://127.0.0.1:{port}/api/")
        print("[提示] 按 Ctrl+C 停止服务器\n")

        from django.core.management import execute_from_command_line

        execute_from_command_line([sys.argv[0], "runserver", f"127.0.0.1:{port}", "--noreload"])
    else:
        print("用法: python 55_drf_advanced.py runserver [port]")
        print("示例: python 55_drf_advanced.py runserver 8000")
