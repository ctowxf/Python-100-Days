"""
深入浅出pandas-5: 多表整合与数据合并
=====================================
演示 pandas 中 merge / join / concat 三大合并操作，
并结合企业级多表整合场景（ERP、CRM、WMS 等系统数据融合）。
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional


# ---------------------------------------------------------------------------
# 1. merge —— 基于键的数据库风格合并（类似 SQL JOIN）
# ---------------------------------------------------------------------------

def demo_merge_basic() -> None:
    """演示 merge 的四种连接方式：inner / outer / left / right。"""
    # 模拟：订单主表（ERP 系统）
    orders: pd.DataFrame = pd.DataFrame({
        "order_id": [1001, 1002, 1003, 1004, 1005],
        "customer_id": ["C01", "C02", "C03", "C04", "C06"],
        "amount": [2500.0, 1800.0, 3200.0, 900.0, 4100.0],
    })
    # 模拟：客户信息表（CRM 系统）
    customers: pd.DataFrame = pd.DataFrame({
        "customer_id": ["C01", "C02", "C03", "C05", "C06"],
        "name": ["张三", "李四", "王五", "赵六", "钱七"],
        "level": ["金牌", "银牌", "铜牌", "金牌", "银牌"],
    })

    print("=" * 60)
    print("【merge 基础演示】")
    print("=" * 60)
    print("\n订单主表 (ERP):")
    print(orders.to_string(index=False))
    print("\n客户信息表 (CRM):")
    print(customers.to_string(index=False))

    # inner join —— 仅保留两张表中都存在的 customer_id
    inner_df: pd.DataFrame = pd.merge(orders, customers, on="customer_id", how="inner")
    print("\n>>> inner join（交集）:")
    print(inner_df.to_string(index=False))

    # outer join —— 保留所有 customer_id，缺失处填 NaN
    outer_df: pd.DataFrame = pd.merge(orders, customers, on="customer_id", how="outer")
    print("\n>>> outer join（并集）:")
    print(outer_df.to_string(index=False))

    # left join —— 以左表 orders 为主，右表匹配不上则填 NaN
    left_df: pd.DataFrame = pd.merge(orders, customers, on="customer_id", how="left")
    print("\n>>> left join（左表为主）:")
    print(left_df.to_string(index=False))

    # right join —— 以右表 customers 为主，左表匹配不上则填 NaN
    right_df: pd.DataFrame = pd.merge(orders, customers, on="customer_id", how="right")
    print("\n>>> right join（右表为主）:")
    print(right_df.to_string(index=False))


def demo_merge_advanced() -> None:
    """演示 merge 的高级用法：多键合并、后缀处理、indicator 标记。"""
    # 模拟：仓库库存表（WMS 系统）
    inventory: pd.DataFrame = pd.DataFrame({
        "warehouse": ["北京仓", "北京仓", "上海仓", "上海仓", "广州仓"],
        "product_id": ["P01", "P02", "P01", "P03", "P02"],
        "stock": [500, 300, 200, 150, 400],
    })
    # 模拟：采购订单表
    purchase: pd.DataFrame = pd.DataFrame({
        "warehouse": ["北京仓", "上海仓", "广州仓", "深圳仓"],
        "product_id": ["P01", "P01", "P02", "P04"],
        "qty": [100, 200, 150, 300],
    })

    print("\n" + "=" * 60)
    print("【merge 高级演示 —— 多键合并与 indicator】")
    print("=" * 60)
    print("\n仓库库存表 (WMS):")
    print(inventory.to_string(index=False))
    print("\n采购订单表:")
    print(purchase.to_string(index=False))

    # 多键合并：同时按 warehouse + product_id 匹配
    multi_key_df: pd.DataFrame = pd.merge(
        inventory, purchase,
        on=["warehouse", "product_id"],
        how="outer",
        suffixes=("_库存", "_采购"),       # 自动处理同名列后缀
        indicator=True,                     # 新增 _merge 列标记来源
    )
    print("\n>>> 多键 outer merge + indicator:")
    print(multi_key_df.to_string(index=False))


def demo_merge_on_index() -> None:
    """演示基于索引的 merge（left_index / right_index）。"""
    # 模拟：5日均线 vs 10日均线（来自 Day76 文档中的股票场景）
    dates: pd.DatetimeIndex = pd.date_range("2022-01-04", periods=12, freq="B")
    np.random.seed(42)
    close: np.ndarray = np.random.uniform(100, 150, size=12).round(2)
    close_series: pd.Series = pd.Series(close, index=dates, name="Close")

    ma5: pd.Series = close_series.rolling(5).mean().rename("MA5")
    ma10: pd.Series = close_series.rolling(10).mean().rename("MA10")

    print("\n" + "=" * 60)
    print("【merge 基于索引 —— 股票双均线合并】")
    print("=" * 60)

    # 基于左右索引合并（等价于文档中 pd.merge(close_ma5, close_ma10, ...)）
    ma_df: pd.DataFrame = pd.merge(
        ma5, ma10,
        left_index=True,
        right_index=True,
    )
    print("\n收盘价:")
    print(close_series.to_string())
    print("\n合并后的均线表:")
    print(ma_df.dropna().to_string())


# ---------------------------------------------------------------------------
# 2. join —— 基于索引的便捷合并
# ---------------------------------------------------------------------------

def demo_join() -> None:
    """演示 DataFrame.join 的用法，包括同名列处理与多表链式 join。"""
    # 模拟：部门表
    dept: pd.DataFrame = pd.DataFrame({
        "dept_id": ["D01", "D02", "D03"],
        "dept_name": ["技术部", "市场部", "财务部"],
    }).set_index("dept_id")

    # 模拟：员工表
    emp: pd.DataFrame = pd.DataFrame({
        "emp_id": ["E001", "E002", "E003", "E004", "E005"],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "dept_id": ["D01", "D02", "D01", "D03", "D02"],
        "salary": [15000, 12000, 18000, 13000, 11000],
    }).set_index("emp_id")

    # 模拟：绩效表
    perf: pd.DataFrame = pd.DataFrame({
        "emp_id": ["E001", "E002", "E003", "E004"],
        "score": [92, 78, 88, 95],
    }).set_index("emp_id")

    print("\n" + "=" * 60)
    print("【join 演示 —— 基于索引的链式合并】")
    print("=" * 60)
    print("\n部门表:")
    print(dept.to_string())
    print("\n员工表:")
    print(emp.to_string())
    print("\n绩效表:")
    print(perf.to_string())

    # 链式 join：员工 -> 部门 -> 绩效
    result: pd.DataFrame = (
        emp
        .join(dept, on="dept_id", how="left")          # 员工关联部门
        .join(perf, how="left")                         # 再关联绩效
        .reset_index()
    )
    print("\n>>> 链式 join 结果（员工 + 部门 + 绩效）:")
    print(result.to_string(index=False))


# ---------------------------------------------------------------------------
# 3. concat —— 沿轴拼接
# ---------------------------------------------------------------------------

def demo_concat() -> None:
    """演示 concat 沿行 / 列方向拼接，以及 ignore_index 与 keys 参数。"""
    # 模拟：Q1 和 Q2 销售数据（来自不同分支系统导出）
    q1: pd.DataFrame = pd.DataFrame({
        "product": ["A", "B", "C"],
        "revenue": [10000, 15000, 8000],
    })
    q2: pd.DataFrame = pd.DataFrame({
        "product": ["A", "B", "D"],
        "revenue": [12000, 14000, 5000],
    })

    print("\n" + "=" * 60)
    print("【concat 演示 —— 纵向拼接（季度数据汇总）】")
    print("=" * 60)
    print("\nQ1 数据:")
    print(q1.to_string(index=False))
    print("\nQ2 数据:")
    print(q2.to_string(index=False))

    # 纵向拼接并重置索引
    yearly: pd.DataFrame = pd.concat(
        [q1, q2],
        ignore_index=True,
    )
    print("\n>>> concat 纵向拼接（不区分来源）:")
    print(yearly.to_string(index=False))

    # 使用 keys 参数保留来源标记
    tagged: pd.DataFrame = pd.concat(
        [q1, q2],
        keys=["Q1", "Q2"],
    )
    print("\n>>> concat 纵向拼接（keys 标记来源季度）:")
    print(tagged.to_string())


def demo_concat_columns() -> None:
    """演示 concat 沿列方向拼接（横向合并）。"""
    # 模拟：不同系统的指标数据（列方向拼接）
    metrics_a: pd.DataFrame = pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=5),
        "uv": [1200, 1350, 1100, 1450, 1600],
    }).set_index("date")

    metrics_b: pd.DataFrame = pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=5),
        "pv": [5600, 6200, 4800, 7000, 7500],
        "bounce_rate": [0.42, 0.38, 0.45, 0.35, 0.33],
    }).set_index("date")

    print("\n" + "=" * 60)
    print("【concat 横向拼接 —— 多系统指标融合】")
    print("=" * 60)
    print("\n指标表 A (UV):")
    print(metrics_a.to_string())
    print("\n指标表 B (PV / 跳出率):")
    print(metrics_b.to_string())

    combined: pd.DataFrame = pd.concat([metrics_a, metrics_b], axis=1)
    print("\n>>> concat axis=1 横向拼接:")
    print(combined.to_string())


# ---------------------------------------------------------------------------
# 4. 企业级综合场景：多系统数据整合
# ---------------------------------------------------------------------------

def enterprise_multi_table_integration() -> None:
    """
    模拟企业真实场景：将 ERP（订单）、CRM（客户）、WMS（物流）
    三个系统的数据整合为一张分析宽表。
    """
    # ERP 订单系统
    erp_orders: pd.DataFrame = pd.DataFrame({
        "order_id": ["SO-001", "SO-002", "SO-003", "SO-004", "SO-005"],
        "customer_id": [101, 102, 103, 101, 104],
        "order_date": pd.to_datetime([
            "2025-03-01", "2025-03-02", "2025-03-02",
            "2025-03-05", "2025-03-06",
        ]),
        "total_amount": [8500.0, 3200.0, 12000.0, 4600.0, 7800.0],
    })

    # CRM 客户系统
    crm_customers: pd.DataFrame = pd.DataFrame({
        "customer_id": [101, 102, 103, 104, 105],
        "customer_name": ["华创科技", "明远贸易", "鼎盛重工", "星辰物流", "远景咨询"],
        "region": ["北京", "上海", "广州", "深圳", "成都"],
        "credit_level": ["A", "B", "A", "C", "B"],
    })

    # WMS 物流系统
    wms_shipments: pd.DataFrame = pd.DataFrame({
        "order_id": ["SO-001", "SO-002", "SO-003", "SO-005"],
        "ship_date": pd.to_datetime([
            "2025-03-03", "2025-03-04", "2025-03-05", "2025-03-08",
        ]),
        "carrier": ["顺丰", "京东物流", "顺丰", "中通"],
        "tracking_no": [
            "SF20250303001", "JD20250304002",
            "SF20250305003", "ZT20250308004",
        ],
    })

    print("\n" + "=" * 60)
    print("【企业级多表整合 —— ERP + CRM + WMS 融合分析】")
    print("=" * 60)

    print("\n--- ERP 订单表 ---")
    print(erp_orders.to_string(index=False))
    print("\n--- CRM 客户表 ---")
    print(crm_customers.to_string(index=False))
    print("\n--- WMS 物流表 ---")
    print(wms_shipments.to_string(index=False))

    # 第 1 步：订单 关联 客户信息（merge left join）
    step1: pd.DataFrame = pd.merge(
        erp_orders, crm_customers,
        on="customer_id",
        how="left",
    )

    # 第 2 步：再关联物流信息（merge left join）
    step2: pd.DataFrame = pd.merge(
        step1, wms_shipments[["order_id", "ship_date", "carrier", "tracking_no"]],
        on="order_id",
        how="left",
    )

    # 第 3 步：计算衍生指标
    step2["delivery_days"] = (step2["ship_date"] - step2["order_date"]).dt.days
    step2["is_shipped"] = step2["tracking_no"].notna().map({True: "已发货", False: "待发货"})

    print("\n>>> 整合后的分析宽表:")
    print(step2.to_string(index=False))

    # 汇总统计：按区域统计订单量和金额
    summary: pd.DataFrame = (
        step2
        .groupby("region")
        .agg(
            order_count=("order_id", "count"),
            total_revenue=("total_amount", "sum"),
            avg_delivery_days=("delivery_days", "mean"),
        )
        .sort_values("total_revenue", ascending=False)
    )
    print("\n>>> 按区域汇总统计:")
    print(summary.to_string())


# ---------------------------------------------------------------------------
# 5. 验证 merge 与 join 的等价关系
# ---------------------------------------------------------------------------

def demo_merge_join_equivalence() -> None:
    """演示 merge 和 join 在基于索引合并时的等价性。"""
    left: pd.DataFrame = pd.DataFrame(
        {"val_a": [10, 20, 30]},
        index=["x", "y", "z"],
    )
    right: pd.DataFrame = pd.DataFrame(
        {"val_b": [100, 200, 300]},
        index=["x", "y", "w"],
    )

    print("\n" + "=" * 60)
    print("【merge vs join 等价性验证】")
    print("=" * 60)
    print("\nLeft:")
    print(left.to_string())
    print("\nRight:")
    print(right.to_string())

    via_merge: pd.DataFrame = pd.merge(
        left, right,
        left_index=True,
        right_index=True,
        how="inner",
    )
    via_join: pd.DataFrame = left.join(right, how="inner")

    print("\n>>> merge (inner on index):")
    print(via_merge.to_string())
    print("\n>>> join (inner on index):")
    print(via_join.to_string())
    print(f"\n两者结果一致: {via_merge.equals(via_join)}")


# ---------------------------------------------------------------------------
# main 入口
# ---------------------------------------------------------------------------

def main() -> None:
    """主函数：依次运行所有演示。"""
    pd.set_option("display.unicode.east_asian_width", True)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)

    demo_merge_basic()
    demo_merge_advanced()
    demo_merge_on_index()
    demo_join()
    demo_concat()
    demo_concat_columns()
    demo_merge_join_equivalence()
    enterprise_multi_table_integration()

    print("\n" + "=" * 60)
    print("所有演示执行完毕。")
    print("=" * 60)


if __name__ == "__main__":
    main()
