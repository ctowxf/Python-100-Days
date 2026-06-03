"""
59_unit_test.py - Django单元测试 (Unit Testing in Django)
=========================================================

本模块全面演示Python/Django的单元测试技术,包括:
- unittest标准库(Django默认测试框架)
- pytest(第三方测试框架,更Pythonic)
- Django测试工具(TestCase, Client, fixtures)
- Mock/patch模拟对象
- 测试覆盖率(coverage)
- API接口测试
- 模型层测试
- 集成测试

C++对比: Python pytest vs C++ Google Test/Catch2
-------------------------------------------------
1. Google Test (gtest):
   - C++最流行的测试框架,由Google维护
   - 使用TEST()宏定义测试用例
   - 断言: EXPECT_EQ, ASSERT_TRUE, EXPECT_THROW等
   - 支持Test Fixtures(类似setUp/tearDown)
   - 需要编译,测试运行较慢

   TEST(CalculatorTest, Addition) {
       Calculator calc;
       EXPECT_EQ(calc.add(2, 3), 5);
   }

2. Catch2:
   - C++单头文件测试框架(现代C++风格)
   - 使用SECTION实现子测试
   - 断言: REQUIRE, CHECK, REQUIRE_THROWS
   - 编译速度快,头文件-only

   TEST_CASE("Calculator addition") {
       Calculator calc;
       REQUIRE(calc.add(2, 3) == 5);
   }

3. Python pytest:
   - 不需要编译,测试运行极快
   - 使用assert语句(原生Python,无需宏)
   - fixture系统比setUp/tearDown更灵活
   - 参数化测试(@pytest.mark.parametrize)
   - 插件生态丰富(pytest-django, pytest-cov, pytest-mock)

   def test_addition():
       assert calculator.add(2, 3) == 5

4. 关键差异:
   - Python测试运行速度: 毫秒级(无需编译)
   - C++测试运行速度: 秒到分钟级(需要编译)
   - Python测试编写速度: 极快(动态类型,无需模板实例化)
   - C++测试类型安全: 更强(编译时检查)
   - Python Mock: 内置unittest.mock,运行时猴子补丁
   - C++ Mock: 需要gmock(Google Mock),基于虚函数接口

企业级测试策略:
- 单元测试: 覆盖核心业务逻辑(目标覆盖率>80%)
- API测试: 验证接口的输入输出格式
- 集成测试: 验证模块间的协作
- 性能测试: 验证关键路径的性能指标

依赖安装:
    pip install django pytest pytest-django pytest-cov coverage
"""

from __future__ import annotations

import os
import sys
import json
import unittest
import datetime
from decimal import Decimal
from typing import Any, Optional, List, Dict
from unittest.mock import patch, MagicMock, PropertyMock, call
from io import StringIO

# ============================================================================
# Django环境配置
# ============================================================================

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
        SECRET_KEY='test-secret-key',
        ROOT_URLCONF=__name__,
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
        ],
    )
    django.setup()

from django.db import models, connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.test import TestCase, RequestFactory, Client, override_settings
from django.db.models import Sum, Count


# ============================================================================
# 第一部分: 被测试的业务代码
# ============================================================================

class Product(models.Model):
    """商品模型"""
    name: models.CharField = models.CharField(max_length=200, verbose_name='商品名称')
    price: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='价格',
    )
    stock: models.IntegerField = models.IntegerField(default=0, verbose_name='库存')
    is_active: models.BooleanField = models.BooleanField(default=True, verbose_name='是否上架')
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'test_app'

    def __str__(self) -> str:
        return f'{self.name} (¥{self.price})'

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0

    def reduce_stock(self, quantity: int) -> bool:
        """扣减库存"""
        if quantity <= 0:
            raise ValueError('扣减数量必须为正整数')
        if self.stock < quantity:
            return False
        self.stock -= quantity
        self.save(update_fields=['stock'])
        return True


class Order(models.Model):
    """订单模型"""
    STATUS_CHOICES = [
        ('pending', '待付款'),
        ('paid', '已付款'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    order_no: models.CharField = models.CharField(max_length=32, unique=True)
    total_amount: models.DecimalField = models.DecimalField(max_digits=12, decimal_places=2)
    status: models.CharField = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'test_app'


# ------ 业务逻辑类(被测试的核心代码) ------

class PriceCalculator:
    """
    价格计算器 - 封装价格计算业务逻辑

    包含: 折扣计算、满减计算、VIP优惠等
    """

    @staticmethod
    def apply_discount(price: Decimal, discount_rate: float) -> Decimal:
        """
        应用折扣

        Args:
            price: 原价
            discount_rate: 折扣率(0.0~1.0,如0.8表示八折)

        Returns:
            折后价格(四舍五入到分)
        """
        if price < 0:
            raise ValueError('价格不能为负数')
        if not (0 < discount_rate <= 1):
            raise ValueError('折扣率必须在0(不含)到1(含)之间')
        return (price * Decimal(str(discount_rate))).quantize(Decimal('0.01'))

    @staticmethod
    def apply_full_reduction(total: Decimal, threshold: Decimal, reduction: Decimal) -> Decimal:
        """
        满减计算

        Args:
            total: 总金额
            threshold: 满减门槛(如满100)
            reduction: 减免金额(如减10)

        Returns:
            满减后的金额
        """
        if total < 0 or threshold <= 0 or reduction < 0:
            raise ValueError('参数值无效')
        if total >= threshold:
            result = total - reduction
            return max(result, Decimal('0.00'))
        return total

    @staticmethod
    def calculate_vip_discount(price: Decimal, vip_level: int) -> Decimal:
        """
        VIP折扣计算

        VIP0: 无折扣
        VIP1: 95折
        VIP2: 9折
        VIP3: 85折
        """
        vip_discounts = {0: 1.0, 1: 0.95, 2: 0.90, 3: 0.85}
        if vip_level not in vip_discounts:
            raise ValueError(f'无效的VIP等级: {vip_level}')
        return PriceCalculator.apply_discount(price, vip_discounts[vip_level])


class OrderService:
    """
    订单服务 - 封装订单业务逻辑
    """

    @staticmethod
    def create_order_no() -> str:
        """生成订单号"""
        import uuid
        now = datetime.datetime.now()
        return f'ORD-{now.strftime("%Y%m%d%H%M%S")}-{uuid.uuid4().hex[:6].upper()}'

    @staticmethod
    def calculate_total(items: List[Dict[str, Any]]) -> Decimal:
        """
        计算订单总金额

        Args:
            items: [{"price": Decimal, "quantity": int}, ...]

        Returns:
            总金额
        """
        if not items:
            raise ValueError('订单商品列表不能为空')
        total = Decimal('0.00')
        for item in items:
            if item['quantity'] <= 0:
                raise ValueError(f'商品数量必须为正整数: {item}')
            if item['price'] < 0:
                raise ValueError(f'商品价格不能为负: {item}')
            total += item['price'] * item['quantity']
        return total.quantize(Decimal('0.01'))


# ------ API视图函数 ------

def product_list_api(request: HttpRequest) -> JsonResponse:
    """商品列表API"""
    products = Product.objects.filter(is_active=True)
    data = [
        {
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
            'stock': p.stock,
            'is_in_stock': p.is_in_stock,
        }
        for p in products
    ]
    return JsonResponse({'code': 200, 'data': data})


def product_detail_api(request: HttpRequest, product_id: int) -> JsonResponse:
    """商品详情API"""
    try:
        product = Product.objects.get(pk=product_id)
        return JsonResponse({
            'code': 200,
            'data': {
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'stock': product.stock,
                'is_in_stock': product.is_in_stock,
            },
        })
    except Product.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '商品不存在'}, status=404)


# ------ URL配置 ------

from django.urls import path

urlpatterns = [
    path('api/products/', product_list_api, name='product_list'),
    path('api/products/<int:product_id>/', product_detail_api, name='product_detail'),
]


# ============================================================================
# 第二部分: unittest测试(Django TestCase)
# ============================================================================

class TestProductModel(TestCase):
    """
    商品模型测试

    Django TestCase特点:
    - 自动创建测试数据库(每个测试用例独立事务)
    - 测试结束后自动回滚(不影响其他测试)
    - 提供setUp/tearDown钩子
    - 内置assert方法(assertEqual, assertRaises等)
    """

    def setUp(self) -> None:
        """每个测试方法执行前的准备工作"""
        self.product = Product.objects.create(
            name='测试商品',
            price=Decimal('99.99'),
            stock=100,
            is_active=True,
        )

    def tearDown(self) -> None:
        """每个测试方法执行后的清理工作"""
        pass  # Django TestCase自动回滚,通常不需要手动清理

    def test_product_creation(self) -> None:
        """测试商品创建"""
        self.assertEqual(self.product.name, '测试商品')
        self.assertEqual(self.product.price, Decimal('99.99'))
        self.assertEqual(self.product.stock, 100)
        self.assertTrue(self.product.is_active)

    def test_product_str(self) -> None:
        """测试__str__方法"""
        expected = f'测试商品 (¥99.99)'
        self.assertEqual(str(self.product), expected)

    def test_is_in_stock_true(self) -> None:
        """测试有库存时is_in_stock为True"""
        self.assertTrue(self.product.is_in_stock)

    def test_is_in_stock_false(self) -> None:
        """测试无库存时is_in_stock为False"""
        self.product.stock = 0
        self.assertFalse(self.product.is_in_stock)

    def test_reduce_stock_success(self) -> None:
        """测试正常扣减库存"""
        result = self.product.reduce_stock(10)
        self.assertTrue(result)
        self.assertEqual(self.product.stock, 90)

    def test_reduce_stock_insufficient(self) -> None:
        """测试库存不足时扣减失败"""
        result = self.product.reduce_stock(200)
        self.assertFalse(result)
        self.assertEqual(self.product.stock, 100)

    def test_reduce_stock_zero_raises(self) -> None:
        """测试扣减数量为0时抛出异常"""
        with self.assertRaises(ValueError) as context:
            self.product.reduce_stock(0)
        self.assertIn('正整数', str(context.exception))

    def test_reduce_stock_negative_raises(self) -> None:
        """测试扣减数量为负数时抛出异常"""
        with self.assertRaises(ValueError):
            self.product.reduce_stock(-5)

    def test_product_count(self) -> None:
        """测试商品计数"""
        Product.objects.create(name='商品2', price=Decimal('50.00'), stock=10)
        self.assertEqual(Product.objects.count(), 2)

    def test_filter_active_products(self) -> None:
        """测试筛选上架商品"""
        Product.objects.create(name='下架商品', price=Decimal('10.00'), stock=5, is_active=False)
        active_products = Product.objects.filter(is_active=True)
        self.assertEqual(active_products.count(), 1)


class TestPriceCalculator(TestCase):
    """
    价格计算器测试

    测试纯业务逻辑(不依赖数据库)
    """

    def test_apply_discount_normal(self) -> None:
        """测试正常折扣"""
        result = PriceCalculator.apply_discount(Decimal('100.00'), 0.8)
        self.assertEqual(result, Decimal('80.00'))

    def test_apply_discount_rounding(self) -> None:
        """测试折扣四舍五入"""
        result = PriceCalculator.apply_discount(Decimal('99.99'), 0.75)
        self.assertEqual(result, Decimal('74.99'))

    def test_apply_discount_negative_price_raises(self) -> None:
        """测试负价格抛出异常"""
        with self.assertRaises(ValueError):
            PriceCalculator.apply_discount(Decimal('-10.00'), 0.8)

    def test_apply_discount_invalid_rate_raises(self) -> None:
        """测试无效折扣率抛出异常"""
        with self.assertRaises(ValueError):
            PriceCalculator.apply_discount(Decimal('100.00'), 0.0)

        with self.assertRaises(ValueError):
            PriceCalculator.apply_discount(Decimal('100.00'), 1.5)

    def test_apply_full_reduction_qualify(self) -> None:
        """测试满足满减条件"""
        result = PriceCalculator.apply_full_reduction(
            Decimal('200.00'), Decimal('100.00'), Decimal('20.00')
        )
        self.assertEqual(result, Decimal('180.00'))

    def test_apply_full_reduction_not_qualify(self) -> None:
        """测试不满足满减条件"""
        result = PriceCalculator.apply_full_reduction(
            Decimal('50.00'), Decimal('100.00'), Decimal('20.00')
        )
        self.assertEqual(result, Decimal('50.00'))

    def test_apply_full_reduction_exact_threshold(self) -> None:
        """测试刚好达到满减门槛"""
        result = PriceCalculator.apply_full_reduction(
            Decimal('100.00'), Decimal('100.00'), Decimal('20.00')
        )
        self.assertEqual(result, Decimal('80.00'))

    def test_vip_discount_levels(self) -> None:
        """测试各级VIP折扣"""
        test_cases = [
            (Decimal('100.00'), 0, Decimal('100.00')),
            (Decimal('100.00'), 1, Decimal('95.00')),
            (Decimal('100.00'), 2, Decimal('90.00')),
            (Decimal('100.00'), 3, Decimal('85.00')),
        ]
        for price, level, expected in test_cases:
            with self.subTest(price=price, level=level):
                result = PriceCalculator.calculate_vip_discount(price, level)
                self.assertEqual(result, expected)

    def test_vip_discount_invalid_level_raises(self) -> None:
        """测试无效VIP等级抛出异常"""
        with self.assertRaises(ValueError):
            PriceCalculator.calculate_vip_discount(Decimal('100.00'), 99)


class TestOrderService(TestCase):
    """订单服务测试"""

    def test_create_order_no_format(self) -> None:
        """测试订单号格式"""
        order_no = OrderService.create_order_no()
        self.assertTrue(order_no.startswith('ORD-'))
        self.assertGreater(len(order_no), 15)

    def test_create_order_no_unique(self) -> None:
        """测试订单号唯一性"""
        order_nos = {OrderService.create_order_no() for _ in range(100)}
        self.assertEqual(len(order_nos), 100)

    def test_calculate_total_normal(self) -> None:
        """测试正常计算订单总金额"""
        items = [
            {'price': Decimal('10.00'), 'quantity': 2},
            {'price': Decimal('20.00'), 'quantity': 3},
        ]
        result = OrderService.calculate_total(items)
        self.assertEqual(result, Decimal('80.00'))

    def test_calculate_total_empty_raises(self) -> None:
        """测试空商品列表抛出异常"""
        with self.assertRaises(ValueError):
            OrderService.calculate_total([])

    def test_calculate_total_invalid_quantity_raises(self) -> None:
        """测试无效数量抛出异常"""
        with self.assertRaises(ValueError):
            OrderService.calculate_total([{'price': Decimal('10.00'), 'quantity': 0}])

    def test_calculate_total_negative_price_raises(self) -> None:
        """测试负价格抛出异常"""
        with self.assertRaises(ValueError):
            OrderService.calculate_total([{'price': Decimal('-10.00'), 'quantity': 1}])


# ============================================================================
# 第三部分: API测试(Django Test Client)
# ============================================================================

class TestProductAPI(TestCase):
    """
    商品API接口测试

    使用Django的Test Client模拟HTTP请求
    Test Client特点:
    - 模拟GET/POST/PUT/DELETE请求
    - 自动处理Cookie/Session
    - 返回Response对象(可检查status_code, content等)
    """

    def setUp(self) -> None:
        self.client = Client()
        self.product = Product.objects.create(
            name='API测试商品',
            price=Decimal('199.99'),
            stock=50,
            is_active=True,
        )

    def test_product_list_api_status(self) -> None:
        """测试商品列表API状态码"""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)

    def test_product_list_api_content_type(self) -> None:
        """测试商品列表API响应类型"""
        response = self.client.get('/api/products/')
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_product_list_api_data(self) -> None:
        """测试商品列表API返回数据"""
        response = self.client.get('/api/products/')
        data = json.loads(response.content)
        self.assertEqual(data['code'], 200)
        self.assertIsInstance(data['data'], list)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['name'], 'API测试商品')

    def test_product_list_excludes_inactive(self) -> None:
        """测试商品列表不包含下架商品"""
        Product.objects.create(name='下架商品', price=Decimal('10.00'), is_active=False)
        response = self.client.get('/api/products/')
        data = json.loads(response.content)
        names = [item['name'] for item in data['data']]
        self.assertNotIn('下架商品', names)

    def test_product_detail_api_found(self) -> None:
        """测试商品详情API(存在)"""
        response = self.client.get(f'/api/products/{self.product.id}/')
        data = json.loads(response.content)
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['data']['name'], 'API测试商品')
        self.assertEqual(data['data']['price'], '199.99')

    def test_product_detail_api_not_found(self) -> None:
        """测试商品详情API(不存在)"""
        response = self.client.get('/api/products/9999/')
        self.assertEqual(response.status_code, 404)


# ============================================================================
# 第四部分: Mock测试
# ============================================================================

class TestMockExamples(TestCase):
    """
    Mock(模拟对象)测试示例

    Mock使用场景:
    - 模拟外部API调用(避免真实网络请求)
    - 模拟数据库操作(加速测试)
    - 模拟文件系统操作
    - 模拟时间相关逻辑

    C++对比:
    - Python: unittest.mock.patch, MagicMock
    - C++: Google Mock(gmock), 需要定义Mock类继承接口
    - Python的Mock更灵活(运行时猴子补丁),C++的Mock类型更安全

    Python Mock:
        @patch('module.external_api_call')
        def test_with_mock(self, mock_api):
            mock_api.return_value = {'status': 'ok'}
            result = my_function()
            mock_api.assert_called_once()

    C++ Google Mock:
        class MockService : public IService {
        public:
            MOCK_METHOD(ApiResponse, fetchData, (), (override));
        };
        TEST(MyTest, TestWithMock) {
            MockService mock;
            EXPECT_CALL(mock, fetchData()).WillOnce(Return(ApiResponse{200, "ok"}));
            auto result = processRequest(mock);
            EXPECT_EQ(result.status, 200);
        }
    """

    def test_mock_product_stock(self) -> None:
        """测试使用Mock模拟库存不足场景"""
        product = MagicMock(spec=Product)
        product.stock = 0
        product.is_in_stock = False
        product.reduce_stock.return_value = False

        result = product.reduce_stock(1)
        self.assertFalse(result)
        product.reduce_stock.assert_called_once_with(1)

    def test_patch_external_service(self) -> None:
        """测试使用patch模拟外部服务"""
        # 模拟一个外部价格查询服务
        with patch.object(PriceCalculator, 'apply_discount') as mock_discount:
            mock_discount.return_value = Decimal('50.00')
            result = PriceCalculator.apply_discount(Decimal('100.00'), 0.5)
            self.assertEqual(result, Decimal('50.00'))
            mock_discount.assert_called_once_with(Decimal('100.00'), 0.5)

    def test_mock_datetime(self) -> None:
        """测试使用Mock模拟固定时间"""
        mock_now = datetime.datetime(2024, 1, 15, 10, 30, 0)
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now
            mock_dt.strftime = datetime.datetime.strftime

            result = OrderService.create_order_no()
            # 验证订单号中包含模拟的日期
            self.assertIn('20240115', result)

    def test_mock_with_side_effect(self) -> None:
        """测试Mock的side_effect(模拟异常)"""
        mock_func = MagicMock(side_effect=ValueError('模拟的错误'))
        with self.assertRaises(ValueError) as context:
            mock_func()
        self.assertIn('模拟的错误', str(context.exception))


# ============================================================================
# 第五部分: RequestFactory测试
# ============================================================================

class TestWithRequestFactory(TestCase):
    """
    使用RequestFactory测试视图函数

    RequestFactory vs Test Client:
    - RequestFactory: 创建假的HttpRequest对象,直接调用视图函数
    - Test Client: 模拟完整的HTTP请求流程(包括中间件)
    - RequestFactory更轻量,适合单元测试
    - Test Client更适合集成测试
    """

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.product = Product.objects.create(
            name='Factory测试商品',
            price=Decimal('299.99'),
            stock=30,
        )

    def test_product_list_with_factory(self) -> None:
        """使用RequestFactory测试商品列表视图"""
        request = self.factory.get('/api/products/')
        response = product_list_api(request)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 200)

    def test_product_detail_with_factory(self) -> None:
        """使用RequestFactory测试商品详情视图"""
        request = self.factory.get(f'/api/products/{self.product.id}/')
        response = product_detail_api(request, self.product.id)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['data']['name'], 'Factory测试商品')


# ============================================================================
# 第六部分: 参数化测试(subTest)
# ============================================================================

class TestParameterized(TestCase):
    """
    参数化测试 - 使用subTest实现数据驱动测试

    C++对比:
    - C++ Google Test: 使用TEST_P + INSTANTIATE_TEST_SUITE_P
    - C++ Catch2: 使用GENERATE
    - Python pytest: 使用@pytest.mark.parametrize(更简洁)
    """

    def test_discount_various_rates(self) -> None:
        """参数化测试: 不同折扣率"""
        test_cases = [
            (Decimal('100.00'), 0.1, Decimal('10.00')),
            (Decimal('100.00'), 0.5, Decimal('50.00')),
            (Decimal('100.00'), 0.8, Decimal('80.00')),
            (Decimal('100.00'), 0.99, Decimal('99.00')),
            (Decimal('100.00'), 1.0, Decimal('100.00')),
        ]
        for price, rate, expected in test_cases:
            with self.subTest(price=price, rate=rate):
                result = PriceCalculator.apply_discount(price, rate)
                self.assertEqual(result, expected)

    def test_full_reduction_various_totals(self) -> None:
        """参数化测试: 不同金额的满减"""
        test_cases = [
            (Decimal('50'), Decimal('100'), Decimal('10'), Decimal('50')),    # 不满足
            (Decimal('100'), Decimal('100'), Decimal('10'), Decimal('90')),   # 刚好满足
            (Decimal('150'), Decimal('100'), Decimal('10'), Decimal('140')),  # 超过
            (Decimal('200'), Decimal('100'), Decimal('10'), Decimal('190')),  # 大幅超过
        ]
        for total, threshold, reduction, expected in test_cases:
            with self.subTest(total=total, threshold=threshold):
                result = PriceCalculator.apply_full_reduction(total, threshold, reduction)
                self.assertEqual(result, expected)


# ============================================================================
# 第七部分: 集成测试示例
# ============================================================================

class TestIntegration(TestCase):
    """
    集成测试 - 验证多个组件协作

    测试完整的业务流程:
    创建商品 -> 计算价格 -> 下单 -> 扣减库存
    """

    def test_complete_order_flow(self) -> None:
        """测试完整的下单流程"""
        # 1. 创建商品
        product = Product.objects.create(
            name='集成测试商品',
            price=Decimal('100.00'),
            stock=50,
        )

        # 2. 计算VIP价格
        vip_price = PriceCalculator.calculate_vip_discount(product.price, 2)
        self.assertEqual(vip_price, Decimal('90.00'))

        # 3. 计算满减
        final_price = PriceCalculator.apply_full_reduction(
            vip_price, Decimal('80.00'), Decimal('10.00')
        )
        self.assertEqual(final_price, Decimal('80.00'))

        # 4. 创建订单
        order_items = [{'price': final_price, 'quantity': 2}]
        total = OrderService.calculate_total(order_items)
        self.assertEqual(total, Decimal('160.00'))

        # 5. 扣减库存
        result = product.reduce_stock(2)
        self.assertTrue(result)
        self.assertEqual(product.stock, 48)

        # 6. 验证订单号唯一
        order_no = OrderService.create_order_no()
        self.assertTrue(order_no.startswith('ORD-'))


# ============================================================================
# 第八部分: 测试覆盖率与pytest配置
# ============================================================================

def print_pytest_guide() -> None:
    """打印pytest使用指南"""
    print('\n' + '=' * 70)
    print('  pytest使用指南')
    print('=' * 70)

    guide = """
    # ------ pytest基本用法 ------
    # 运行所有测试
    pytest

    # 运行指定文件
    pytest tests/test_models.py

    # 运行指定类/方法
    pytest tests/test_models.py::TestProductModel::test_reduce_stock_success

    # 显示详细输出
    pytest -v

    # 显示print输出
    pytest -s

    # 运行匹配关键字的测试
    pytest -k "stock"

    # ------ pytest参数化 ------
    @pytest.mark.parametrize("price,rate,expected", [
        (Decimal('100'), 0.8, Decimal('80')),
        (Decimal('200'), 0.5, Decimal('100')),
    ])
    def test_discount(price, rate, expected):
        assert PriceCalculator.apply_discount(price, rate) == expected

    # ------ pytest fixture ------
    @pytest.fixture
    def sample_product():
        return Product.objects.create(
            name='Fixture商品', price=Decimal('99.99'), stock=100
        )

    def test_with_fixture(sample_product):
        assert sample_product.stock == 100

    # ------ 测试覆盖率 ------
    # 安装: pip install pytest-cov coverage
    # 运行: pytest --cov=. --cov-report=html
    # 查看: 打开 htmlcov/index.html

    # ------ conftest.py(共享fixture) ------
    # tests/conftest.py:
    import pytest
    @pytest.fixture(scope='session')
    def django_db_setup():
        """测试数据库设置"""
        pass

    @pytest.fixture
    def api_client():
        """API测试客户端"""
        from django.test import Client
        return Client()

    # ------ pytest.ini配置 ------
    [pytest]
    DJANGO_SETTINGS_MODULE = myproject.settings
    python_files = tests.py test_*.py *_tests.py
    python_classes = Test*
    python_functions = test_*
    addopts = -v --tb=short
    """
    print(guide)


def print_coverage_guide() -> None:
    """打印测试覆盖率指南"""
    print('\n' + '=' * 70)
    print('  测试覆盖率指南')
    print('=' * 70)

    guide = """
    # 1. 使用coverage测量覆盖率
    coverage run --source='.' manage.py test
    coverage report    # 终端报告
    coverage html      # HTML报告(htmlcov/)

    # 2. 使用pytest-cov(推荐)
    pytest --cov=. --cov-report=term-missing --cov-report=html

    # 3. 覆盖率指标
    - 语句覆盖率: 每条语句是否被执行
    - 分支覆盖率: 每个if/else分支是否都被执行
    - 函数覆盖率: 每个函数是否都被调用
    - 企业目标: 核心业务逻辑 > 80%,整体 > 60%

    # 4. 覆盖率排除
    # 在代码中添加注释排除不需要测试的代码:
    def debug_only():  # pragma: no cover
        pass
    """
    print(guide)


def print_best_practices() -> None:
    """打印测试最佳实践"""
    print('\n' + '=' * 70)
    print('  单元测试最佳实践')
    print('=' * 70)

    practices = """
    1. 测试命名规范:
       - test_<被测功能>_<场景>_<期望结果>
       - 例: test_reduce_stock_insufficient_returns_false

    2. AAA模式(Arrange-Act-Assert):
       - Arrange: 准备测试数据
       - Act: 执行被测代码
       - Assert: 验证结果

    3. 每个测试只验证一个行为(单一职责)

    4. 测试应该是独立的(不依赖执行顺序)

    5. 使用setUp/tearDown或fixture管理测试数据

    6. Mock外部依赖(API、数据库、文件系统)

    7. 测试边界条件和异常情况

    8. 保持测试代码与生产代码同等质量

    9. 持续集成(CI)中自动运行测试

    10. 定期检查测试覆盖率

    C++对比总结:
    ┌─────────────────────┬──────────────────────────────────┐
    │   Python unittest   │   C++ Google Test / Catch2       │
    │     / pytest        │                                  │
    ├─────────────────────┼──────────────────────────────────┤
    │ assert语句          │ EXPECT_EQ/REQUIRE宏              │
    │ @pytest.mark        │ TEST_P/TEST_CASE参数化           │
    │ fixture             │ SetUp/TearDown + Test Suite      │
    │ unittest.mock       │ Google Mock(gmock)              │
    │ --cov覆盖率         │ gcov/lcov/llvm-cov              │
    │ 无需编译,秒级运行    │ 需要编译,分钟级运行              │
    │ 动态类型,灵活       │ 静态类型,安全                    │
    │ 插件生态丰富         │ 工具链成熟(gdb/perf/valgrind)   │
    └─────────────────────┴──────────────────────────────────┘
    """
    print(practices)


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    """主函数: 创建表、运行测试、展示覆盖率"""
    print('=' * 70)
    print('  Django单元测试 - 企业级测试实战演示')
    print('  (Unit Testing - Enterprise Testing Demo)')
    print('=' * 70)

    # 1. 创建数据库表
    print('\n[Step 1] 创建测试数据库表...')
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Product)
        schema_editor.create_model(Order)
        print(f'  [OK] 创建表: {Product._meta.db_table}, {Order._meta.db_table}')

    # 2. 运行unittest测试
    print('\n[Step 2] 运行unittest测试套件...')
    print('-' * 50)

    # 收集并运行测试
    loader = unittest.TestLoader()
    test_classes = [
        TestProductModel,
        TestPriceCalculator,
        TestOrderService,
        TestProductAPI,
        TestMockExamples,
        TestWithRequestFactory,
        TestParameterized,
        TestIntegration,
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # 运行测试(使用自定义结果收集器)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    # 输出测试结果
    print(stream.getvalue())

    print('=' * 50)
    print(f'  测试总数: {result.testsRun}')
    print(f'  成功: {result.testsRun - len(result.failures) - len(result.errors)}')
    print(f'  失败: {len(result.failures)}')
    print(f'  错误: {len(result.errors)}')
    print(f'  跳过: {len(result.skipped)}')

    if result.failures:
        print('\n  失败详情:')
        for test, traceback in result.failures:
            print(f'    FAIL: {test}')
            print(f'    {traceback.split(chr(10))[-2]}')

    if result.errors:
        print('\n  错误详情:')
        for test, traceback in result.errors:
            print(f'    ERROR: {test}')
            print(f'    {traceback.split(chr(10))[-2]}')

    # 3. pytest指南
    print_pytest_guide()

    # 4. 覆盖率指南
    print_coverage_guide()

    # 5. 最佳实践
    print_best_practices()

    print('\n' + '=' * 70)
    print('  所有测试执行完毕!')
    print('=' * 70)


if __name__ == '__main__':
    main()
