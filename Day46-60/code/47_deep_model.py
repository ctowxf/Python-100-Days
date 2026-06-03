"""
47_deep_model.py - Django深入模型 (Deep Dive into Django Models)
===============================================================

本模块演示Django模型的高级用法,包括:
- 各种模型字段类型及属性配置
- ForeignKey / ManyToManyField / OneToOneField 关系映射
- 复杂查询: F对象、Q对象、聚合函数、子查询
- QuerySet惰性求值与链式调用
- 自定义Manager与QuerySet
- 模型继承(抽象基类、多表继承、代理模型)
- 数据库事务与信号机制

C++对比: Django ORM vs C++ ODB/Hibernate
----------------------------------------
在C++生态中,对象关系映射(ORM)的实现远比Python复杂:
- C++ ODB: 需要预处理器(pragmas)或代码生成器来定义映射,
  编译时类型检查严格,但开发效率远低于Django ORM
- Hibernate(C++无直接对标): Java生态的Hibernate是ORM标杆,
  C++中需要借助SOCI、Qt SQL等库手动编写SQL映射
- Django ORM的优势: Python的动态类型+元类机制让ORM定义极其简洁,
  模型类声明即完成映射,无需额外配置文件或代码生成步骤
- 性能权衡: C++ ORM编译时优化带来更高运行时性能,
  但Django ORM通过QuerySet惰性求值和select_related/prefetch_related
  在实际Web场景中性能已足够优秀

企业级应用场景: 电商平台数据模型设计
- 商品分类(多级树形结构)、商品SPU/SKU模型
- 订单系统(一对多+多对多复杂关系)
- 用户-角色-权限(RBAC)模型
- 库存管理与价格策略

依赖安装:
    pip install django mysqlclient
"""

from __future__ import annotations

import os
import sys
import datetime
from decimal import Decimal
from typing import Any, Optional, List, Dict, Tuple, Set, Union

# ============================================================================
# Django环境配置 (独立运行时需要)
# ============================================================================
# 注意: 在实际Django项目中,这些配置在settings.py中完成
# 此处为演示目的,模拟Django环境的初始化

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
        USE_TZ=True,
        TIME_ZONE='Asia/Shanghai',
    )
    django.setup()

from django.db import models, connection, transaction
from django.db.models import (
    F, Q, Count, Sum, Avg, Max, Min, StdDev, Variance,
    Case, When, Value, IntegerField, CharField, DecimalField as DField,
    Subquery, OuterRef, Exists, Prefetch,
)
from django.db.models.functions import (
    Coalesce, Concat, Length, Upper, Lower, Substr,
    TruncMonth, TruncYear, Extract,
)
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone


# ============================================================================
# 第一部分: 电商模型设计 (Enterprise E-Commerce Model Design)
# ============================================================================

# ------ 抽象基类 ------

class TimestampMixin(models.Model):
    """
    时间戳抽象基类 - 所有模型共享的创建/更新时间字段

    C++对比: 类似于C++中的CRTP(Curiously Recurring Template Pattern)
    或者抽象基类中的默认实现:
        template<typename Derived>
        class TimestampMixin {
            std::chrono::system_clock::time_point created_at;
            std::chrono::system_clock::time_point updated_at;
        };
    """
    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        db_comment='记录创建的时间戳',
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        db_comment='最后更新的时间戳',
    )

    class Meta:
        abstract = True  # 抽象基类,不会创建数据库表
        ordering = ['-created_at']


class SoftDeleteManager(models.Manager):
    """
    软删除管理器 - 只返回未删除的记录

    企业级实践: 重要业务数据不做物理删除,通过is_deleted标记
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteMixin(models.Model):
    """
    软删除混入类

    C++对比: 类似于C++中的代理模式(Proxy Pattern),
    在数据访问层拦截删除操作:
        class SoftDeleteProxy : public IDataAccess {
            void remove(int id) override {
                // 不真正删除,只标记
                db.update(id, {{"is_deleted", true}});
            }
        };
    """
    is_deleted: models.BooleanField = models.BooleanField(
        default=False,
        verbose_name='是否已删除',
        db_index=True,
    )
    deleted_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='删除时间',
    )

    objects = SoftDeleteManager()  # 默认管理器只返回未删除记录
    all_objects = models.Manager()  # 包含所有记录的管理器

    def soft_delete(self) -> None:
        """软删除: 标记为已删除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    def restore(self) -> None:
        """恢复已软删除的记录"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    class Meta:
        abstract = True


# ------ 商品分类模型(树形结构) ------

class Category(TimestampMixin, SoftDeleteMixin):
    """
    商品分类模型 - 支持多级树形结构

    使用ForeignKey自关联实现无限层级分类树
    C++对比: 类似于Composite模式的树形结构
        struct Category {
            int id;
            std::string name;
            std::optional<int> parent_id;  // C++17 std::optional
            std::vector<Category> children;
        };

    Django ForeignKey vs C++指针:
    - Django ForeignKey通过数据库外键约束保证引用完整性
    - C++中通常使用原始指针或智能指针管理父子关系,
      引用完整性需要手动维护
    """
    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='分类ID')
    name: models.CharField = models.CharField(
        max_length=100,
        verbose_name='分类名称',
        db_index=True,
    )
    slug: models.SlugField = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name='URL别名',
        help_text='用于生成SEO友好的URL',
    )
    parent: models.ForeignKey = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='父分类',
        db_comment='自关联实现树形结构,null表示顶级分类',
    )
    level: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='层级深度',
    )
    sort_order: models.IntegerField = models.IntegerField(
        default=0,
        verbose_name='排序权重',
        help_text='数值越大排序越靠前',
    )
    is_active: models.BooleanField = models.BooleanField(
        default=True,
        verbose_name='是否启用',
        db_index=True,
    )
    icon_url: models.URLField = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='分类图标URL',
    )

    class Meta:
        db_table = 'ecom_category'
        verbose_name = '商品分类'
        verbose_name_plural = '商品分类列表'
        ordering = ['level', '-sort_order', 'name']
        indexes = [
            models.Index(fields=['parent', 'sort_order'], name='idx_category_parent_sort'),
            models.Index(fields=['level', 'is_active'], name='idx_category_level_active'),
        ]
        unique_together = [('parent', 'name')]  # 同级分类名称不能重复

    def __str__(self) -> str:
        prefix = '  ' * self.level
        return f'{prefix}{self.name} (L{self.level})'

    def get_full_path(self) -> str:
        """获取分类的完整路径: 电子产品 > 手机 > 智能手机"""
        path_parts: List[str] = []
        node = self
        while node is not None:
            path_parts.append(node.name)
            node = node.parent
        return ' > '.join(reversed(path_parts))

    def get_descendants(self, include_self: bool = False) -> models.QuerySet:
        """获取所有后代分类(递归)"""
        from django.db.models import Q
        q = Q(parent=self)
        if include_self:
            q = q | Q(pk=self.pk)
        descendants = Category.objects.filter(q)
        for child in self.children.all():
            descendants = descendants | child.get_descendants()
        return descendants


# ------ 品牌模型 ------

class Brand(TimestampMixin):
    """
    品牌模型

    C++对比: 值对象(Value Object)模式
    """
    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='品牌ID')
    name: models.CharField = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='品牌名称',
    )
    name_en: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='品牌英文名',
    )
    logo_url: models.URLField = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='品牌Logo',
    )
    description: models.TextField = models.TextField(
        blank=True,
        default='',
        verbose_name='品牌介绍',
    )
    is_hot: models.BooleanField = models.BooleanField(
        default=False,
        verbose_name='是否热门品牌',
        db_index=True,
    )

    class Meta:
        db_table = 'ecom_brand'
        verbose_name = '品牌'
        verbose_name_plural = '品牌列表'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


# ------ 商品SPU模型(标准产品单元) ------

class Product(TimestampMixin, SoftDeleteMixin):
    """
    商品SPU(Standard Product Unit)模型

    SPU代表一类商品的抽象,如"iPhone 15 Pro"
    关系: Product -> Category (ForeignKey, 多对一)
          Product -> Brand    (ForeignKey, 多对一)
          Product -> Tag      (ManyToManyField, 多对多)

    C++对比: 组合模式(Composition)
    在C++中需要手动管理关联关系和级联操作:
        class Product {
            Category* category;  // 多对一: 需手动管理生命周期
            Brand* brand;
            std::vector<Tag*> tags;  // 多对多: 需维护中间表
        };
    Django ORM通过ForeignKey和ManyToManyField自动处理:
    - 数据库层面的外键约束
    - 级联删除策略(CASCADE/PROTECT/SET_NULL等)
    - 中间表的自动创建和管理
    """
    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='商品ID')
    title: models.CharField = models.CharField(
        max_length=200,
        verbose_name='商品标题',
        db_index=True,
    )
    subtitle: models.CharField = models.CharField(
        max_length=300,
        blank=True,
        default='',
        verbose_name='副标题',
    )
    category: models.ForeignKey = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # 保护模式: 有商品的分类不能被删除
        related_name='products',
        verbose_name='所属分类',
    )
    brand: models.ForeignKey = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,  # 品牌删除后商品不删除,置空
        null=True,
        blank=True,
        related_name='products',
        verbose_name='所属品牌',
    )
    # ManyToManyField: Django自动创建中间表
    tags: models.ManyToManyField = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='products',
        verbose_name='商品标签',
        db_table='ecom_product_tag',  # 自定义中间表名
    )
    description: models.TextField = models.TextField(
        blank=True,
        default='',
        verbose_name='商品详情(HTML)',
    )
    main_image: models.URLField = models.URLField(
        max_length=500,
        verbose_name='主图URL',
    )
    is_on_sale: models.BooleanField = models.BooleanField(
        default=True,
        verbose_name='是否上架',
        db_index=True,
    )
    sales_count: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0,
        verbose_name='累计销量',
    )
    view_count: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0,
        verbose_name='浏览次数',
    )

    class Meta:
        db_table = 'ecom_product'
        verbose_name = '商品(SPU)'
        verbose_name_plural = '商品列表'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_on_sale'], name='idx_product_cat_sale'),
            models.Index(fields=['brand', 'is_on_sale'], name='idx_product_brand_sale'),
            models.Index(fields=['-sales_count'], name='idx_product_sales_desc'),
            models.Index(fields=['title'], name='idx_product_title'),
        ]

    def __str__(self) -> str:
        return f'[{self.id}] {self.title}'

    @property
    def min_price(self) -> Optional[Decimal]:
        """获取该商品所有SKU的最低价"""
        result = self.skus.aggregate(min_price=Min('price'))
        return result['min_price']

    @property
    def total_stock(self) -> int:
        """获取该商品所有SKU的总库存"""
        result = self.skus.aggregate(total=Sum('stock'))
        return result['total'] or 0


# ------ 商品SKU模型(库存量单位) ------

class ProductSKU(TimestampMixin):
    """
    商品SKU(Stock Keeping Unit)模型

    SKU是最小库存单位,如"iPhone 15 Pro 256GB 暗夜紫"
    一个SPU可以有多个SKU(不同规格/颜色/套餐)

    使用DecimalField存储价格: 企业级最佳实践
    绝不使用FloatField存储货币数据(浮点精度问题)
    """
    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='SKU ID')
    product: models.ForeignKey = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,  # 商品删除,其所有SKU级联删除
        related_name='skus',
        verbose_name='所属商品SPU',
    )
    sku_code: models.CharField = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='SKU编码',
        help_text='唯一标识一个SKU的编码,如: SKU-20240101-001',
    )
    title: models.CharField = models.CharField(
        max_length=200,
        verbose_name='SKU标题',
        help_text='如: iPhone 15 Pro 256GB 暗夜紫',
    )
    # DecimalField: 精确的货币计算, max_digits=10, decimal_places=2
    # C++对比: C++中通常用整数(分)或专用Decimal库存储货币
    price: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='售价(元)',
    )
    original_price: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='原价(划线价)',
    )
    cost_price: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='成本价(元)',
    )
    stock: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0,
        verbose_name='库存数量',
    )
    sales_count: models.PositiveIntegerField = models.PositiveIntegerField(
        default=0,
        verbose_name='该SKU销量',
    )
    weight: models.DecimalField = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='重量(kg)',
    )
    is_active: models.BooleanField = models.BooleanField(
        default=True,
        verbose_name='是否有效',
    )
    # JSONField存储SKU的规格属性(颜色、尺寸等)
    attributes: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='规格属性(JSON)',
        help_text='如: {"颜色": "暗夜紫", "存储": "256GB", "网络": "全网通"}',
    )

    class Meta:
        db_table = 'ecom_product_sku'
        verbose_name = '商品SKU'
        verbose_name_plural = 'SKU列表'
        ordering = ['price']
        indexes = [
            models.Index(fields=['product', 'is_active'], name='idx_sku_product_active'),
            models.Index(fields=['sku_code'], name='idx_sku_code'),
        ]

    def __str__(self) -> str:
        return f'{self.title} (¥{self.price})'

    @property
    def profit_margin(self) -> Optional[Decimal]:
        """计算毛利率"""
        if self.cost_price and self.price:
            return ((self.price - self.cost_price) / self.price * 100).quantize(Decimal('0.01'))
        return None

    def reduce_stock(self, quantity: int) -> bool:
        """
        扣减库存(使用F对象实现原子操作)

        F对象的优势: 直接在数据库层面执行运算,避免竞态条件
        C++对比: 类似于数据库层面的原子操作,
        C++中需要使用std::atomic或互斥锁实现:
            std::atomic<int> stock{100};
            bool success = stock.compare_exchange_strong(expected, expected - quantity);
        """
        if quantity <= 0:
            raise ValueError('扣减数量必须为正整数')
        # F对象: 在SQL层面执行 stock = stock - quantity,是原子操作
        affected = ProductSKU.objects.filter(
            pk=self.pk,
            stock__gte=quantity,  # 库存充足才扣减
        ).update(stock=F('stock') - quantity)
        if affected > 0:
            self.refresh_from_db()  # 刷新内存中的对象状态
            return True
        return False


# ------ 标签模型(ManyToManyField对端) ------

class Tag(models.Model):
    """
    标签模型 - 与Product构成多对多关系

    Django ManyToManyField自动管理中间表,
    无需像C++/Java中那样手动定义关联表:
        // C++中需要额外定义关联表
        CREATE TABLE product_tag (
            product_id BIGINT REFERENCES product(id),
            tag_id BIGINT REFERENCES tag(id),
            PRIMARY KEY (product_id, tag_id)
        );
    """
    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='标签ID')
    name: models.CharField = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='标签名称',
    )

    class Meta:
        db_table = 'ecom_tag'
        verbose_name = '标签'
        verbose_name_plural = '标签列表'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


# ------ 用户模型 ------

class UserProfile(TimestampMixin, SoftDeleteMixin):
    """
    用户资料模型 - OneToOneField示例

    OneToOneField: 一对一关系,本质上是具有唯一约束的ForeignKey
    用途: 扩展Django内置User模型(避免修改auth.User)

    C++对比:
    - OneToOneField类似于C++中的组合关系(Composition)
    - 在C++中可以用嵌入对象或unique_ptr实现:
        class UserProfile {
            User& user;  // 1:1引用,生命周期绑定
            std::string phone;
        };
    """
    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='用户ID')
    username: models.CharField = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='用户名',
        db_index=True,
    )
    email: models.EmailField = models.EmailField(
        unique=True,
        verbose_name='邮箱',
    )
    phone: models.CharField = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='手机号',
    )
    avatar_url: models.URLField = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='头像URL',
    )
    # 此字段模拟Django内置User模型的OneToOne扩展
    # 在实际项目中: user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    vip_level: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='VIP等级',
        choices=[(0, '普通用户'), (1, 'VIP'), (2, 'SVIP'), (3, '至尊VIP')],
    )
    balance: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='账户余额',
    )
    # JSONField存储非结构化数据
    preferences: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='用户偏好设置(JSON)',
    )

    class Meta:
        db_table = 'ecom_user_profile'
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料列表'

    def __str__(self) -> str:
        return f'{self.username} (VIP{self.vip_level})'


# ------ 收货地址模型(一对多) ------

class Address(TimestampMixin):
    """
    收货地址模型 - 与UserProfile构成一对多关系

    一个用户可以有多个收货地址
    """
    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='地址ID')
    user: models.ForeignKey = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name='所属用户',
    )
    receiver_name: models.CharField = models.CharField(
        max_length=50,
        verbose_name='收货人姓名',
    )
    phone: models.CharField = models.CharField(
        max_length=20,
        verbose_name='联系电话',
    )
    province: models.CharField = models.CharField(max_length=50, verbose_name='省')
    city: models.CharField = models.CharField(max_length=50, verbose_name='市')
    district: models.CharField = models.CharField(max_length=50, verbose_name='区')
    detail: models.CharField = models.CharField(
        max_length=300,
        verbose_name='详细地址',
    )
    is_default: models.BooleanField = models.BooleanField(
        default=False,
        verbose_name='是否默认地址',
    )

    class Meta:
        db_table = 'ecom_address'
        verbose_name = '收货地址'
        verbose_name_plural = '收货地址列表'
        ordering = ['-is_default', '-updated_at']
        # 每个用户最多只能有一个默认地址(业务约束)
        indexes = [
            models.Index(fields=['user', 'is_default'], name='idx_addr_user_default'),
        ]

    def __str__(self) -> str:
        return f'{self.receiver_name}: {self.province}{self.city}{self.district}{self.detail}'


# ------ 订单模型(一对多+状态机) ------

class Order(TimestampMixin):
    """
    订单模型

    订单状态机:
    PENDING -> PAID -> SHIPPED -> DELIVERED -> COMPLETED
         \\-> CANCELLED (任意未完成状态可取消)

    C++对比: 状态模式(State Pattern)
    在C++中实现状态机更常见的方式是使用State Pattern:
        class OrderState {
        public:
            virtual void pay(Order&) = 0;
            virtual void ship(Order&) = 0;
            virtual void cancel(Order&) = 0;
        };
        class PendingState : public OrderState { ... };
        class PaidState : public OrderState { ... };
    Django中通常使用状态字段+业务方法实现,
    也可以使用django-fsm库实现完整的状态机。
    """

    class Status(models.TextChoices):
        PENDING = 'pending', '待付款'
        PAID = 'paid', '已付款'
        SHIPPED = 'shipped', '已发货'
        DELIVERED = 'delivered', '已收货'
        COMPLETED = 'completed', '已完成'
        CANCELLED = 'cancelled', '已取消'
        REFUNDING = 'refunding', '退款中'
        REFUNDED = 'refunded', '已退款'

    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='订单ID')
    order_no: models.CharField = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='订单编号',
        db_index=True,
        help_text='格式: ORD-YYYYMMDD-XXXXXX',
    )
    user: models.ForeignKey = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,  # 有订单的用户不能被删除
        related_name='orders',
        verbose_name='下单用户',
    )
    # 快照字段: 记录下单时的收货地址信息(地址可能后续被修改)
    address_snapshot: models.JSONField = models.JSONField(
        verbose_name='收货地址快照(JSON)',
        help_text='下单时的完整地址信息,防止地址修改影响历史订单',
    )
    status: models.CharField = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='订单状态',
        db_index=True,
    )
    total_amount: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='订单总金额',
    )
    discount_amount: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='优惠金额',
    )
    shipping_fee: models.DecimalField = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='运费',
    )
    actual_amount: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='实付金额',
        help_text='total_amount - discount_amount + shipping_fee',
    )
    paid_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='付款时间',
    )
    shipped_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='发货时间',
    )
    completed_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='完成时间',
    )
    remark: models.TextField = models.TextField(
        blank=True,
        default='',
        verbose_name='订单备注',
    )

    class Meta:
        db_table = 'ecom_order'
        verbose_name = '订单'
        verbose_name_plural = '订单列表'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='idx_order_user_status'),
            models.Index(fields=['status', 'created_at'], name='idx_order_status_time'),
            models.Index(fields=['-created_at'], name='idx_order_created_desc'),
        ]

    def __str__(self) -> str:
        return f'订单 {self.order_no} ({self.get_status_display()})'

    def can_pay(self) -> bool:
        return self.status == self.Status.PENDING

    def can_ship(self) -> bool:
        return self.status == self.Status.PAID

    def can_cancel(self) -> bool:
        return self.status in {self.Status.PENDING, self.Status.PAID}

    @transaction.atomic
    def pay(self) -> bool:
        """
        订单付款 - 使用数据库事务保证一致性

        @transaction.atomic确保以下操作要么全部成功,要么全部回滚
        C++对比: 类似于C++ RAII风格的事务管理:
            {
                auto tx = db.beginTransaction();
                try {
                    order.status = PAID;
                    order.paid_at = now();
                    // 扣减库存...
                    tx.commit();
                } catch (...) {
                    tx.rollback();
                    throw;
                }
            }
        """
        if not self.can_pay():
            return False
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at', 'updated_at'])
        return True

    @transaction.atomic
    def cancel(self, reason: str = '') -> bool:
        """订单取消 - 恢复库存"""
        if not self.can_cancel():
            return False
        old_status = self.status
        self.status = self.Status.CANCELLED
        self.remark = f'{self.remark}\n[取消原因] {reason}' if reason else self.remark
        self.save(update_fields=['status', 'remark', 'updated_at'])
        # 恢复库存(已在付款时扣减)
        if old_status == self.Status.PAID:
            for item in self.items.all():
                ProductSKU.objects.filter(pk=item.sku_id).update(stock=F('stock') + item.quantity)
        return True


# ------ 订单明细模型 ------

class OrderItem(models.Model):
    """
    订单明细模型 - 订单与SKU的多对多关系(带额外字段)

    注意: 虽然订单和SKU是多对多关系,但因为中间表需要存储
    数量、单价等额外字段,所以不能使用ManyToManyField,
    而是手动创建中间模型。

    C++对比: 这种"带属性的关联"在C++中也需要独立的关联类:
        struct OrderItem {
            Order* order;
            ProductSKU* sku;
            int quantity;
            Decimal unit_price;  // 下单时的单价快照
        };
    """
    id: models.BigAutoField = models.BigAutoField(primary_key=True, verbose_name='明细ID')
    order: models.ForeignKey = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='所属订单',
    )
    sku: models.ForeignKey = models.ForeignKey(
        ProductSKU,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='商品SKU',
    )
    quantity: models.PositiveIntegerField = models.PositiveIntegerField(
        verbose_name='购买数量',
    )
    unit_price: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='成交单价(快照)',
        help_text='下单时的价格,不受后续调价影响',
    )
    subtotal: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='小计金额',
    )

    class Meta:
        db_table = 'ecom_order_item'
        verbose_name = '订单明细'
        verbose_name_plural = '订单明细列表'

    def __str__(self) -> str:
        return f'{self.sku.title} x{self.quantity} = ¥{self.subtotal}'


# ------ 自定义QuerySet ------

class ProductQuerySet(models.QuerySet):
    """
    自定义QuerySet - 封装常用查询逻辑

    支持链式调用,类似C++中的Builder模式或流式API
    C++对比:
        auto results = ProductQuery(db)
            .onSale()
            .inCategory(catId)
            .priceRange(min, max)
            .orderBy("-sales")
            .limit(20)
            .execute();
    """
    def on_sale(self) -> ProductQuerySet:
        """只查询上架商品"""
        return self.filter(is_on_sale=True)

    def in_category(self, category: Union[Category, int]) -> ProductQuerySet:
        """查询指定分类及其子分类的商品"""
        if isinstance(category, int):
            category = Category.objects.get(pk=category)
        descendant_ids = list(
            category.get_descendants(include_self=True).values_list('id', flat=True)
        )
        return self.filter(category_id__in=descendant_ids)

    def price_range(self, min_price: Decimal, max_price: Decimal) -> ProductQuerySet:
        """按SKU价格范围筛选"""
        return self.filter(
            skus__price__gte=min_price,
            skus__price__lte=max_price,
        ).distinct()

    def with_stock(self) -> ProductQuerySet:
        """只查询有库存的商品"""
        return self.filter(skus__stock__gt=0).distinct()

    def hot_products(self, limit: int = 10) -> ProductQuerySet:
        """热销商品"""
        return self.on_sale().order_by('-sales_count')[:limit]

    def search(self, keyword: str) -> ProductQuerySet:
        """商品搜索"""
        return self.filter(
            Q(title__icontains=keyword) |
            Q(subtitle__icontains=keyword) |
            Q(description__icontains=keyword) |
            Q(brand__name__icontains=keyword)
        ).distinct()


class ProductManager(models.Manager):
    """自定义Manager,使用自定义QuerySet"""

    def get_queryset(self) -> ProductQuerySet:
        return ProductQuerySet(self.model, using=self._db)

    def on_sale(self) -> ProductQuerySet:
        return self.get_queryset().on_sale()

    def search(self, keyword: str) -> ProductQuerySet:
        return self.get_queryset().search(keyword)


# ---- 为Product模型添加自定义Manager ----
# 注意: 在实际项目中,应在Product类定义时直接声明
# 此处为演示目的,在类定义后动态添加
Product.add_to_class('custom_objects', ProductManager())


# ============================================================================
# 第二部分: 数据库表创建与数据填充
# ============================================================================

def create_tables() -> None:
    """创建所有模型对应的数据库表"""
    with connection.schema_editor() as schema_editor:
        models_to_create = [
            Category, Brand, Tag, Product, ProductSKU,
            UserProfile, Address, Order, OrderItem,
        ]
        for model in models_to_create:
            try:
                schema_editor.create_model(model)
                print(f'  [OK] 创建表: {model._meta.db_table}')
            except Exception as e:
                print(f'  [SKIP] {model._meta.db_table}: {e}')


def populate_sample_data() -> Dict[str, Any]:
    """
    填充示例数据 - 模拟电商平台初始数据

    返回创建的模型对象字典,供后续演示使用
    """
    data: Dict[str, Any] = {}

    # ------ 品牌 ------
    brands = []
    brand_data = [
        ('Apple', 'Apple Inc.', True),
        ('华为', 'Huawei Technologies', True),
        ('小米', 'Xiaomi Corporation', True),
        ('三星', 'Samsung Electronics', False),
        ('OPPO', 'OPPO Digital', False),
    ]
    for name, name_en, is_hot in brand_data:
        brand, _ = Brand.objects.get_or_create(
            name=name,
            defaults={'name_en': name_en, 'is_hot': is_hot},
        )
        brands.append(brand)
    data['brands'] = brands

    # ------ 分类(树形结构) ------
    # 一级分类
    electronics, _ = Category.objects.get_or_create(
        slug='electronics', defaults={'name': '电子产品', 'level': 0}
    )
    clothing, _ = Category.objects.get_or_create(
        slug='clothing', defaults={'name': '服装鞋帽', 'level': 0}
    )
    food, _ = Category.objects.get_or_create(
        slug='food', defaults={'name': '食品饮料', 'level': 0}
    )

    # 二级分类
    phones, _ = Category.objects.get_or_create(
        slug='phones', defaults={'name': '手机通讯', 'level': 1, 'parent': electronics}
    )
    laptops, _ = Category.objects.get_or_create(
        slug='laptops', defaults={'name': '笔记本电脑', 'level': 1, 'parent': electronics}
    )
    tablets, _ = Category.objects.get_or_create(
        slug='tablets', defaults={'name': '平板电脑', 'level': 1, 'parent': electronics}
    )

    # 三级分类
    smartphones, _ = Category.objects.get_or_create(
        slug='smartphones', defaults={'name': '智能手机', 'level': 2, 'parent': phones}
    )
    folding_phones, _ = Category.objects.get_or_create(
        slug='folding-phones', defaults={'name': '折叠屏手机', 'level': 2, 'parent': phones}
    )

    data['categories'] = {
        'electronics': electronics, 'clothing': clothing, 'food': food,
        'phones': phones, 'laptops': laptops, 'tablets': tablets,
        'smartphones': smartphones, 'folding_phones': folding_phones,
    }

    # ------ 标签 ------
    tag_names = ['新品首发', '限时特惠', '5G', 'AI手机', '轻薄本', '游戏本',
                 '长续航', '快充', '高刷新率', '拍照旗舰']
    tags = []
    for name in tag_names:
        tag, _ = Tag.objects.get_or_create(name=name)
        tags.append(tag)
    data['tags'] = tags

    # ------ 商品SPU ------
    products = []
    product_data = [
        ('iPhone 15 Pro Max', '钛金属设计,A17 Pro芯片', smartphones, brands[0]),
        ('iPhone 15', '动态岛,USB-C', smartphones, brands[0]),
        ('Huawei Mate 60 Pro', '卫星通信,麒麟芯片', smartphones, brands[1]),
        ('Huawei Mate X5', '超轻薄折叠旗舰', folding_phones, brands[1]),
        ('Xiaomi 14 Ultra', '徕卡光学,骁龙8 Gen3', smartphones, brands[2]),
        ('Samsung Galaxy S24 Ultra', 'Galaxy AI,S Pen', smartphones, brands[3]),
        ('MacBook Pro 14"', 'M3 Pro芯片,18小时续航', laptops, brands[0]),
        ('Huawei MateBook X Pro', '超轻薄商务本', laptops, brands[1]),
    ]
    for title, subtitle, cat, brand in product_data:
        product, _ = Product.objects.get_or_create(
            title=title,
            defaults={
                'subtitle': subtitle,
                'category': cat,
                'brand': brand,
                'main_image': f'https://example.com/images/{title.lower().replace(" ", "-")}.jpg',
                'is_on_sale': True,
            },
        )
        products.append(product)
    data['products'] = products

    # 为商品添加标签(M2M关系)
    products[0].tags.add(tags[0], tags[2], tags[3], tags[9])  # iPhone 15 Pro Max
    products[1].tags.add(tags[2], tags[7])  # iPhone 15
    products[2].tags.add(tags[0], tags[2], tags[3])  # Mate 60 Pro
    products[3].tags.add(tags[0])  # Mate X5
    products[4].tags.add(tags[8], tags[9])  # Xiaomi 14 Ultra

    # ------ 商品SKU ------
    sku_data = [
        # (product_index, sku_code, title, price, original, cost, stock, attrs)
        (0, 'SKU-IP15PM-256-BL', 'iPhone 15 Pro Max 256GB 蓝色钛金属',
         Decimal('9999.00'), Decimal('9999.00'), Decimal('6500.00'), 500,
         '{"颜色": "蓝色钛金属", "存储": "256GB"}'),
        (0, 'SKU-IP15PM-512-BK', 'iPhone 15 Pro Max 512GB 黑色钛金属',
         Decimal('11999.00'), Decimal('11999.00'), Decimal('7800.00'), 300,
         '{"颜色": "黑色钛金属", "存储": "512GB"}'),
        (1, 'SKU-IP15-128-PK', 'iPhone 15 128GB 粉色',
         Decimal('5999.00'), Decimal('5999.00'), Decimal('3800.00'), 800,
         '{"颜色": "粉色", "存储": "128GB"}'),
        (1, 'SKU-IP15-256-BL', 'iPhone 15 256GB 蓝色',
         Decimal('6999.00'), Decimal('6999.00'), Decimal('4500.00'), 600,
         '{"颜色": "蓝色", "存储": "256GB"}'),
        (2, 'SKU-M60P-256-GR', 'Huawei Mate 60 Pro 256GB 雅丹黑',
         Decimal('6999.00'), Decimal('6999.00'), Decimal('4200.00'), 400,
         '{"颜色": "雅丹黑", "存储": "256GB"}'),
        (3, 'SKU-MX5-512-BK', 'Huawei Mate X5 512GB 幻影黑',
         Decimal('12999.00'), Decimal('13999.00'), Decimal('8500.00'), 200,
         '{"颜色": "幻影黑", "存储": "512GB"}'),
        (4, 'SKU-MI14U-256-BK', 'Xiaomi 14 Ultra 256GB 黑色',
         Decimal('5999.00'), Decimal('6499.00'), Decimal('3600.00'), 500,
         '{"颜色": "黑色", "存储": "256GB"}'),
        (5, 'SKU-S24U-256-GR', 'Samsung Galaxy S24 Ultra 256GB 钛灰',
         Decimal('9699.00'), Decimal('9699.00'), Decimal('6000.00'), 350,
         '{"颜色": "钛灰", "存储": "256GB"}'),
        (6, 'SKU-MBP14-M3P-512', 'MacBook Pro 14" M3 Pro 512GB',
         Decimal('14999.00'), Decimal('14999.00'), Decimal('9800.00'), 200,
         '{"芯片": "M3 Pro", "内存": "18GB", "存储": "512GB SSD"}'),
        (7, 'SKU-MBXP-U7-1TB', 'Huawei MateBook X Pro Ultra7 1TB',
         Decimal('11999.00'), Decimal('12999.00'), Decimal('7500.00'), 150,
         '{"处理器": "Ultra 7", "内存": "32GB", "存储": "1TB SSD"}'),
    ]
    skus = []
    for prod_idx, code, title, price, orig, cost, stock, attrs in sku_data:
        import json
        sku, _ = ProductSKU.objects.get_or_create(
            sku_code=code,
            defaults={
                'product': products[prod_idx],
                'title': title,
                'price': price,
                'original_price': orig,
                'cost_price': cost,
                'stock': stock,
                'attributes': json.loads(attrs),
            },
        )
        skus.append(sku)
    data['skus'] = skus

    # ------ 用户 ------
    users = []
    user_data = [
        ('zhangsan', 'zhangsan@example.com', '13800138001', 2),
        ('lisi', 'lisi@example.com', '13800138002', 1),
        ('wangwu', 'wangwu@example.com', '13800138003', 0),
    ]
    for uname, email, phone, vip in user_data:
        user, _ = UserProfile.objects.get_or_create(
            username=uname,
            defaults={'email': email, 'phone': phone, 'vip_level': vip},
        )
        users.append(user)
    data['users'] = users

    return data


# ============================================================================
# 第三部分: 复杂查询演示
# ============================================================================

def demo_basic_queries() -> None:
    """基础CRUD查询演示"""
    print('\n' + '=' * 70)
    print('  基础查询演示 (Basic CRUD Queries)')
    print('=' * 70)

    # ---- 查询所有上架商品 ----
    print('\n--- 1. 查询所有上架商品 ---')
    products = Product.objects.filter(is_on_sale=True)
    for p in products:
        print(f'  {p.title} | 分类: {p.category.name} | 品牌: {p.brand.name if p.brand else "无品牌"}')

    # ---- 条件过滤: 多条件AND ----
    print('\n--- 2. 多条件AND查询: 品牌=Apple 且 上架中 ---')
    apple_products = Product.objects.filter(
        brand__name='Apple',
        is_on_sale=True,
    )
    for p in apple_products:
        print(f'  {p.title}')

    # ---- 模糊查询 ----
    print('\n--- 3. 模糊查询: 标题包含"Huawei" ---')
    huawei = Product.objects.filter(title__icontains='Huawei')
    for p in huawei:
        print(f'  {p.title}')

    # ---- 范围查询 ----
    print('\n--- 4. 价格区间查询: SKU价格在5000-10000之间 ---')
    mid_range = ProductSKU.objects.filter(
        price__gte=Decimal('5000'),
        price__lte=Decimal('10000'),
    ).order_by('price')
    for sku in mid_range:
        print(f'  {sku.title} - ¥{sku.price}')

    # ---- 排序与切片 ----
    print('\n--- 5. 按销量降序排列,取前3 ---')
    top3 = Product.objects.order_by('-sales_count')[:3]
    for p in top3:
        print(f'  {p.title} (销量: {p.sales_count})')

    # ---- 计数 ----
    total_products = Product.objects.count()
    total_skus = ProductSKU.objects.count()
    print(f'\n--- 6. 统计: 商品SPU总数={total_products}, SKU总数={total_skus} ---')


def demo_advanced_queries() -> None:
    """
    高级查询演示: F对象、Q对象、聚合、子查询

    C++对比:
    - F对象: 在C++中需要使用存储过程或应用层运算,
      无法在SQL层面优雅地引用其他列
    - Q对象: C++中构建动态WHERE条件需要拼接SQL字符串,
      容易产生SQL注入; Django的Q对象是类型安全的
    - 聚合: C++中通常在SQL中直接写GROUP BY和聚合函数,
      Django ORM提供了Pythonic的aggregate/annotate接口
    """
    print('\n' + '=' * 70)
    print('  高级查询演示 (Advanced Queries: F/Q/Aggregation)')
    print('=' * 70)

    # ---- F对象: 列之间的比较 ----
    print('\n--- F对象: 找出售价低于原价的商品SKU(有折扣) ---')
    discounted = ProductSKU.objects.filter(
        original_price__isnull=False,
    ).annotate(
        discount_ratio=ExpressionWrapper(
            (F('original_price') - F('price')) / F('original_price') * 100,
            output_field=DField(),
        )
    ).filter(
        price__lt=F('original_price'),
    ).order_by('-discount_ratio')

    for sku in discounted:
        print(f'  {sku.title}: ¥{sku.price} (原价¥{sku.original_price}, 折扣{sku.discount_ratio:.1f}%)')

    # ---- Q对象: 复杂OR/NOT条件 ----
    print('\n--- Q对象: 标题包含"iPhone" 或 (品牌是华为 且 上架中) ---')
    complex_query = Q(title__icontains='iPhone') | Q(brand__name='华为', is_on_sale=True)
    results = Product.objects.filter(complex_query)
    for p in results:
        print(f'  {p.title} | {p.brand.name if p.brand else "无品牌"}')

    # ---- Q对象: NOT条件 ----
    print('\n--- Q对象(NOT): 非Apple品牌的上架商品 ---')
    non_apple = Product.objects.filter(
        ~Q(brand__name='Apple'),
        is_on_sale=True,
    )
    for p in non_apple:
        print(f'  {p.title} | {p.brand.name}')

    # ---- 聚合函数: aggregate() ----
    print('\n--- 聚合函数: 全局统计 ---')
    from django.db.models import ExpressionWrapper
    stats = ProductSKU.objects.aggregate(
        total_skus=Count('id'),
        avg_price=Avg('price'),
        max_price=Max('price'),
        min_price=Min('price'),
        total_stock=Sum('stock'),
        price_stddev=StdDev('price'),
    )
    for key, value in stats.items():
        if isinstance(value, Decimal):
            print(f'  {key}: ¥{value:.2f}')
        elif value is not None:
            print(f'  {key}: {value}')

    # ---- annotate(): 分组聚合 ----
    print('\n--- annotate(): 每个品牌的商品数量和平均价格 ---')
    from django.db.models import ExpressionWrapper
    brand_stats = Brand.objects.annotate(
        product_count=Count('products'),
        avg_price=Avg('products__skus__price'),
        min_price=Min('products__skus__price'),
        max_price=Max('products__skus__price'),
    ).filter(product_count__gt=0).order_by('-product_count')

    for brand in brand_stats:
        avg = f'¥{brand.avg_price:.2f}' if brand.avg_price else 'N/A'
        print(f'  {brand.name}: {brand.product_count}个商品, 均价{avg}')

    # ---- 每个分类的商品数量 ----
    print('\n--- annotate(): 每个分类的商品数量(含子分类关联) ---')
    cat_stats = Category.objects.annotate(
        product_count=Count('products'),
    ).filter(level=0).order_by('-product_count')

    for cat in cat_stats:
        print(f'  {cat.name}: {cat_count}个商品'.replace('{cat_count}', str(cat.product_count)))

    # ---- 子查询: Subquery ----
    print('\n--- Subquery: 每个品牌的最新商品 ---')
    latest_product = Product.objects.filter(
        brand=OuterRef('brand'),
    ).order_by('-created_at')

    brands_with_latest = Brand.objects.annotate(
        latest_product_name=Subquery(latest_product.values('title')[:1]),
    ).filter(products__isnull=False).distinct()

    for brand in brands_with_latest:
        print(f'  {brand.name}: 最新商品 - {brand.latest_product_name}')

    # ---- Exists子查询 ----
    print('\n--- Exists: 有库存>100的SKU的品牌 ---')
    brands_with_stock = Brand.objects.filter(
        Exists(
            ProductSKU.objects.filter(
                product__brand=OuterRef('pk'),
                stock__gt=100,
            )
        )
    )
    for brand in brands_with_stock:
        print(f'  {brand.name}')

    # ---- 多表关联查询(JOIN) ----
    print('\n--- 多表关联: 某分类下所有SKU的价格信息 ---')
    try:
        smartphone_cat = Category.objects.get(slug='smartphones')
        smartphone_skus = ProductSKU.objects.filter(
            product__category=smartphone_cat,
            is_active=True,
        ).select_related('product', 'product__brand').order_by('price')

        for sku in smartphone_skus:
            print(f'  {sku.product.brand.name} {sku.title} - ¥{sku.price} (库存: {sku.stock})')
    except Category.DoesNotExist:
        print('  [跳过] 智能手机分类不存在')

    # ---- prefetch_related: 优化N+1查询 ----
    print('\n--- prefetch_related: 预加载减少N+1查询 ---')
    products_with_tags = Product.objects.prefetch_related('tags', 'skus').all()[:5]
    for product in products_with_tags:
        tag_names = ', '.join(t.name for t in product.tags.all())
        sku_count = product.skus.count()
        print(f'  {product.title} | 标签: [{tag_names}] | SKU数: {sku_count}')


def demo_custom_queryset() -> None:
    """自定义QuerySet链式调用演示"""
    print('\n' + '=' * 70)
    print('  自定义QuerySet链式调用演示')
    print('=' * 70)

    # 链式调用: 类似C++的Builder模式
    print('\n--- 链式查询: 上架 + 价格范围 + 有库存 ---')
    try:
        results = (
            Product.custom_objects.on_sale()
            .price_range(Decimal('5000'), Decimal('10000'))
            .with_stock()
        )
        for p in results:
            print(f'  {p.title} (最低价: ¥{p.min_price})')
    except Exception as e:
        print(f'  [演示] 自定义Manager查询: {e}')

    # 搜索
    print('\n--- 商品搜索: 关键词"Pro" ---')
    search_results = Product.objects.filter(
        Q(title__icontains='Pro') | Q(subtitle__icontains='Pro')
    ).distinct()
    for p in search_results:
        print(f'  {p.title} - {p.subtitle}')


def demo_transactions() -> None:
    """
    事务操作演示

    C++对比: Django的@transaction.atomic装饰器
    类似于C++中的RAII事务管理:
        class ScopedTransaction {
            DatabaseConnection& db;
        public:
            ScopedTransaction(DatabaseConnection& db) : db(db) { db.begin(); }
            ~ScopedTransaction() { if (!committed) db.rollback(); }
            void commit() { db.commit(); committed = true; }
        };
    """
    print('\n' + '=' * 70)
    print('  事务操作演示 (Transaction Demos)')
    print('=' * 70)

    # 创建测试用户和订单
    try:
        user = UserProfile.objects.first()
        if not user:
            print('  [跳过] 无用户数据,跳过事务演示')
            return

        # 模拟下单流程
        print('\n--- 模拟下单流程(事务) ---')
        sku = ProductSKU.objects.filter(stock__gt=0).first()
        if not sku:
            print('  [跳过] 无可用SKU')
            return

        with transaction.atomic():
            # 1. 创建订单
            order = Order.objects.create(
                order_no=f'ORD-{timezone.now().strftime("%Y%m%d%H%M%S")}-TEST',
                user=user,
                address_snapshot={'province': '北京市', 'city': '北京市', 'detail': '测试地址'},
                total_amount=sku.price,
                actual_amount=sku.price,
                status=Order.Status.PENDING,
            )
            print(f'  创建订单: {order.order_no}')

            # 2. 创建订单明细
            OrderItem.objects.create(
                order=order,
                sku=sku,
                quantity=1,
                unit_price=sku.price,
                subtotal=sku.price,
            )
            print(f'  添加订单项: {sku.title} x1')

            # 3. 扣减库存(F对象原子操作)
            sku.reduce_stock(1)
            print(f'  扣减库存: {sku.title} 剩余库存={sku.stock}')

            # 4. 付款
            order.pay()
            print(f'  订单状态: {order.get_status_display()}')

        print('  [OK] 事务提交成功')

        # 5. 取消订单(恢复库存)
        print('\n--- 模拟取消订单(恢复库存) ---')
        old_stock = sku.stock
        order.cancel(reason='用户主动取消')
        sku.refresh_from_db()
        print(f'  库存恢复: {old_stock} -> {sku.stock}')
        print(f'  订单状态: {order.get_status_display()}')

    except Exception as e:
        print(f'  [错误] 事务演示失败: {e}')


# ============================================================================
# 第四部分: Django Admin 配置演示
# ============================================================================

def demo_admin_config() -> None:
    """
    Django Admin后台管理配置示例

    展示如何通过ModelAdmin自定义后台管理界面
    """
    print('\n' + '=' * 70)
    print('  Django Admin配置示例 (参考代码)')
    print('=' * 70)

    admin_code = '''
# polls/admin.py - Django Admin配置

from django.contrib import admin
from .models import (
    Category, Brand, Product, ProductSKU,
    UserProfile, Order, OrderItem, Tag
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent', 'level', 'is_active', 'sort_order')
    list_filter = ('level', 'is_active')
    search_fields = ('name', 'slug')
    list_editable = ('sort_order', 'is_active')
    ordering = ('level', 'sort_order')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'name_en', 'is_hot', 'created_at')
    list_filter = ('is_hot',)
    search_fields = ('name', 'name_en')


class ProductSKUInline(admin.TabularInline):
    model = ProductSKU
    extra = 1
    fields = ('sku_code', 'title', 'price', 'cost_price', 'stock', 'is_active')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'brand', 'is_on_sale',
                    'sales_count', 'view_count', 'created_at')
    list_filter = ('is_on_sale', 'category', 'brand')
    search_fields = ('title', 'subtitle')
    list_editable = ('is_on_sale',)
    filter_horizontal = ('tags',)  # M2M字段的友好选择界面
    inlines = [ProductSKUInline]   # 内联编辑SKU
    date_hierarchy = 'created_at'
    readonly_fields = ('sales_count', 'view_count', 'created_at', 'updated_at')

    # 自定义动作
    actions = ['make_on_sale', 'make_off_sale']

    @admin.action(description='批量上架')
    def make_on_sale(self, request, queryset):
        queryset.update(is_on_sale=True)

    @admin.action(description='批量下架')
    def make_off_sale(self, request, queryset):
        queryset.update(is_on_sale=False)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_no', 'user', 'status', 'actual_amount',
                    'paid_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('order_no', 'user__username')
    readonly_fields = ('order_no', 'user', 'total_amount', 'actual_amount',
                       'created_at', 'updated_at')
    date_hierarchy = 'created_at'
'''
    print(admin_code)


# ============================================================================
# 第五部分: 模型最佳实践总结
# ============================================================================

def print_best_practices() -> None:
    """打印Django模型最佳实践"""
    print('\n' + '=' * 70)
    print('  Django模型最佳实践 (Best Practices)')
    print('=' * 70)

    practices = """
    1. 使用DecimalField存储货币数据,绝不使用FloatField
    2. 为ForeignKey设置合理的on_delete策略:
       - CASCADE: 父记录删除,子记录级联删除(如: 订单->订单明细)
       - PROTECT: 有子记录时阻止父记录删除(如: 有商品的分类)
       - SET_NULL: 父记录删除,子记录外键置空(如: 商品->品牌)
    3. 定义__str__方法,方便调试和Admin显示
    4. 使用related_name设置反向查询属性名
    5. 使用db_index=True为常用查询字段建立索引
    6. 使用Meta.ordering设置默认排序
    7. 使用select_related/prefetch_related优化N+1查询
    8. 使用F对象实现原子更新,避免竞态条件
    9. 使用Q对象构建复杂查询条件
    10. 使用@transaction.atomic保证数据一致性
    11. 使用自定义Manager和QuerySet封装业务查询逻辑
    12. 软删除优于物理删除(重要业务数据)
    13. 关键业务数据使用JSONField快照(如订单地址)
    14. 模型中放置业务逻辑,而非全部放在视图中

    C++对比总结:
    ┌─────────────────────┬──────────────────────────────────┐
    │     Django ORM      │     C++ ORM (ODB/SOCI/Qt SQL)    │
    ├─────────────────────┼──────────────────────────────────┤
    │ Python动态类型+元类  │ C++模板+预处理器/代码生成        │
    │ 声明式模型定义       │ 需要pragma注解或XML映射文件       │
    │ 自动迁移(migrate)   │ 通常需要手动编写DDL或迁移脚本     │
    │ QuerySet惰性求值    │ 编译时确定查询,运行时直接执行     │
    │ 运行时类型检查       │ 编译时严格类型检查               │
    │ 开发效率极高         │ 运行性能极高                     │
    │ 适合Web快速迭代      │ 适合性能敏感的系统级应用          │
    └─────────────────────┴──────────────────────────────────┘
    """
    print(practices)


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    """主函数: 创建表、填充数据、运行所有查询演示"""
    print('=' * 70)
    print('  Django深入模型 - 电商数据模型实战演示')
    print('  (Deep Django Models - E-Commerce Model Demo)')
    print('=' * 70)

    # 1. 创建数据库表
    print('\n[Step 1] 创建数据库表...')
    create_tables()

    # 2. 填充示例数据
    print('\n[Step 2] 填充示例数据...')
    data = populate_sample_data()
    print(f'  品牌: {len(data["brands"])}个')
    print(f'  分类: {len(data["categories"])}个')
    print(f'  标签: {len(data["tags"])}个')
    print(f'  商品: {len(data["products"])}个')
    print(f'  SKU: {len(data["skus"])}个')
    print(f'  用户: {len(data["users"])}个')

    # 3. 运行查询演示
    demo_basic_queries()
    demo_advanced_queries()
    demo_custom_queryset()
    demo_transactions()
    demo_admin_config()
    print_best_practices()

    print('\n' + '=' * 70)
    print('  所有演示执行完毕!')
    print('=' * 70)


if __name__ == '__main__':
    main()
