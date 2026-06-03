"""
深入浅出 Pandas (一) —— Series、DataFrame 与基础操作
=====================================================
本模块以企业销售数据分析为场景，演示 Pandas 核心数据结构
（Series / DataFrame）的创建、索引、运算、统计及数据清洗等操作。

运行方式：
    python 72_pandas_basics.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 类型别名，方便在 type hints 中使用
# ---------------------------------------------------------------------------
Series = pd.Series
DataFrame = pd.DataFrame


# ============================= Series 部分 ==================================


def demo_create_series() -> None:
    """演示 Series 的多种创建方式。"""
    print("=" * 60)
    print("1. 创建 Series 对象")
    print("=" * 60)

    # 方式一：通过列表 + 自定义索引创建
    q1_sales: Series = pd.Series(
        data=[120, 380, 250, 360],
        index=["一季度", "二季度", "三季度", "四季度"],
    )
    print("\n通过列表创建 Series（各季度销售额/万元）：")
    print(q1_sales)

    # 方式二：通过字典创建（键即索引）
    q2_sales: Series = pd.Series(
        {"一季度": 320, "二季度": 180, "三季度": 300, "四季度": 405}
    )
    print("\n通过字典创建 Series（第二年各季度销售额/万元）：")
    print(q2_sales)


def demo_series_operations() -> None:
    """演示 Series 的标量运算、矢量运算。"""
    print("\n" + "=" * 60)
    print("2. Series 运算")
    print("=" * 60)

    ser1: Series = pd.Series(
        data=[120, 380, 250, 360],
        index=["一季度", "二季度", "三季度", "四季度"],
    )
    ser2: Series = pd.Series(
        {"一季度": 320, "二季度": 180, "三季度": 300, "四季度": 405}
    )

    # 标量运算：每季度统一上调 10 万元
    ser1 += 10
    print("\n标量运算 —— 每季度 +10 万：")
    print(ser1)

    # 矢量运算：两个 Series 对应元素相加
    combined: Series = ser1 + ser2
    print("\n矢量运算 —— 两年各季度合计：")
    print(combined)


def demo_series_indexing() -> None:
    """演示 Series 的普通索引、切片索引、花式索引和布尔索引。"""
    print("\n" + "=" * 60)
    print("3. Series 索引操作")
    print("=" * 60)

    ser: Series = pd.Series(
        {"一季度": 320, "二季度": 600, "三季度": 500, "四季度": 520}
    )

    # 普通索引（整数 & 标签）
    print(f"\n整数索引 ser[2]  -> {ser[2]}")
    print(f"标签索引 ser['三季度'] -> {ser['三季度']}")

    # 切片索引 —— 注意：标签切片两端都包含！
    print(f"\n切片 ser[1:3]：\n{ser[1:3]}")
    print(f"\n标签切片 ser['二季度':'四季度']：\n{ser['二季度':'四季度']}")

    # 花式索引
    print(f"\n花式索引 ser[['二季度', '四季度']]：\n{ser[['二季度', '四季度']]}")

    # 布尔索引：筛选销售额 >= 500 的季度
    mask: Series = ser >= 500
    print(f"\n布尔索引 ser[ser >= 500]：\n{ser[mask]}")


def demo_series_attributes() -> None:
    """演示 Series 常用属性。"""
    print("\n" + "=" * 60)
    print("4. Series 常用属性")
    print("=" * 60)

    ser: Series = pd.Series(
        {"一季度": 320, "二季度": 600, "三季度": 500, "四季度": 520}
    )
    print(f"dtype          : {ser.dtype}")
    print(f"hasnans        : {ser.hasnans}")
    print(f"index          : {ser.index.tolist()}")
    print(f"values         : {ser.values}")
    print(f"is_unique      : {ser.is_unique}")
    print(f"is_monotonic_increasing: {ser.is_monotonic_increasing}")
    print(f"size           : {ser.size}")


def demo_series_statistics() -> None:
    """演示 Series 的描述性统计方法。"""
    print("\n" + "=" * 60)
    print("5. Series 描述性统计")
    print("=" * 60)

    ser: Series = pd.Series(
        {"一季度": 320, "二季度": 600, "三季度": 500, "四季度": 520}
    )
    print(f"\ncount  (计数)  : {ser.count()}")
    print(f"sum    (求和)  : {ser.sum()}")
    print(f"mean   (均值)  : {ser.mean()}")
    print(f"median (中位数): {ser.median()}")
    print(f"max    (最大值): {ser.max()}")
    print(f"min    (最小值): {ser.min()}")
    print(f"std    (标准差): {ser.std():.4f}")
    print(f"var    (方差)  : {ser.var():.4f}")

    # describe() 一次性获取全部统计摘要
    print("\n--- describe() 摘要 ---")
    print(ser.describe())

    # value_counts / nunique / mode
    fruits: Series = pd.Series(
        ["apple", "banana", "apple", "pitaya", "apple", "pitaya", "durian"]
    )
    print("\n--- value_counts（水果出现次数）---")
    print(fruits.value_counts())
    print(f"\nnunique（不重复水果数）: {fruits.nunique()}")
    print(f"\nmode（众数）:\n{fruits.mode()}")


def demo_series_data_processing() -> None:
    """演示 Series 空值处理、去重、where / mask、apply / map。"""
    print("\n" + "=" * 60)
    print("6. Series 数据处理")
    print("=" * 60)

    # ---- 空值检测与填充 ----
    ser_nan: Series = pd.Series(data=[10, 20, np.nan, 30, np.nan])
    print("\n原始数据（含空值）:")
    print(ser_nan)
    print(f"\nisna():\n{ser_nan.isna()}")
    print(f"\ndropna():\n{ser_nan.dropna()}")
    print(f"\nfillna(40):\n{ser_nan.fillna(value=40)}")
    print(f"\nfillna(method='ffill'):\n{ser_nan.fillna(method='ffill')}")

    # ---- 重复值检测与删除 ----
    fruits: Series = pd.Series(
        ["apple", "banana", "apple", "pitaya", "apple", "pitaya", "durian"]
    )
    print(f"\n--- duplicated() ---\n{fruits.duplicated()}")
    print(f"\n--- drop_duplicates() ---\n{fruits.drop_duplicates()}")

    # ---- where / mask ----
    ser5: Series = pd.Series(range(5))
    print(f"\nwhere(ser5 > 1, 10):\n{ser5.where(ser5 > 1, 10)}")
    print(f"\nmask(ser5 > 1, 10):\n{ser5.mask(ser5 > 1, 10)}")

    # ---- map：字典映射 ----
    ser_pet: Series = pd.Series(["cat", "dog", np.nan, "rabbit"])
    print(f"\nmap 字典映射:\n{ser_pet.map({'cat': 'kitten', 'dog': 'puppy'})}")

    # ---- apply：函数应用 ----
    ser_temp: Series = pd.Series(
        [20, 21, 12], index=["London", "New York", "Helsinki"]
    )
    print(f"\napply(np.square):\n{ser_temp.apply(np.square)}")
    print(
        f"\napply(lambda x, v: x - v, args=(5,)):\n"
        f"{ser_temp.apply(lambda x, value: x - value, args=(5,))}"
    )


def demo_series_sorting() -> None:
    """演示 Series 排序与 Top-N 方法。"""
    print("\n" + "=" * 60)
    print("7. Series 排序与 Top-N")
    print("=" * 60)

    ser: Series = pd.Series(
        data=[35, 96, 12, 57, 25, 89],
        index=["grape", "banana", "pitaya", "apple", "peach", "orange"],
    )
    print("\nsort_values()（按值升序）:")
    print(ser.sort_values())

    print("\nsort_index(ascending=False)（按索引降序）:")
    print(ser.sort_index(ascending=False))

    print(f"\nnlargest(3):\n{ser.nlargest(3)}")
    print(f"\nnsmallest(2):\n{ser.nsmallest(2)}")


# ============================ DataFrame 部分 ================================


def demo_create_dataframe() -> DataFrame:
    """演示 DataFrame 的多种创建方式，并返回一个示例 DataFrame 供后续函数复用。"""
    print("\n" + "=" * 60)
    print("8. 创建 DataFrame 对象")
    print("=" * 60)

    # 方式一：通过字典创建（键为列名，值为列数据）
    sales_data: dict[str, list] = {
        "订单编号": ["ORD-001", "ORD-002", "ORD-003", "ORD-004", "ORD-005",
                       "ORD-006", "ORD-007", "ORD-008", "ORD-009", "ORD-010"],
        "日期": pd.date_range("2025-01-01", periods=10, freq="D"),
        "产品": ["笔记本", "显示器", "键盘", "鼠标", "笔记本",
                  "显示器", "笔记本", "键盘", "鼠标", "显示器"],
        "区域": ["华东", "华南", "华北", "华东", "华南",
                  "华北", "华东", "华南", "华北", "华东"],
        "数量": [5, 10, 20, 50, 8, 6, 3, 15, 30, 12],
        "单价": [6999, 2499, 599, 199, 6999, 2499, 6999, 599, 199, 2499],
    }
    df: DataFrame = pd.DataFrame(sales_data)

    # 计算销售额列
    df["销售额"] = df["数量"] * df["单价"]

    print("\n企业销售订单 DataFrame：")
    print(df)
    print(f"\nshape: {df.shape}  （{df.shape[0]} 行 x {df.shape[1]} 列）")
    return df


def demo_dataframe_info(df: DataFrame) -> None:
    """演示 DataFrame 的基本属性与概览方法。"""
    print("\n" + "=" * 60)
    print("9. DataFrame 基本信息")
    print("=" * 60)

    print(f"\ndtypes:\n{df.dtypes}")
    print(f"\ncolumns : {df.columns.tolist()}")
    print(f"index   : {df.index.tolist()}")
    print(f"shape   : {df.shape}")
    print(f"ndim    : {df.ndim}")
    print(f"size    : {df.size}")

    print("\n--- head(3) ---")
    print(df.head(3))

    print("\n--- tail(3) ---")
    print(df.tail(3))

    print("\n--- describe() 数值列统计摘要 ---")
    print(df.describe())


def demo_dataframe_column_selection(df: DataFrame) -> None:
    """演示 DataFrame 的列选取操作。"""
    print("\n" + "=" * 60)
    print("10. DataFrame 列选取")
    print("=" * 60)

    # 选取单列 → 返回 Series
    products: Series = df["产品"]
    print(f"\ntype(df['产品']) = {type(products)}")
    print(products)

    # 选取多列 → 返回 DataFrame
    subset: DataFrame = df[["订单编号", "产品", "销售额"]]
    print(f"\ntype(df[['订单编号','产品','销售额']]) = {type(subset)}")
    print(subset)


def demo_dataframe_row_selection(df: DataFrame) -> None:
    """演示 DataFrame 基于 loc / iloc 的行选取。"""
    print("\n" + "=" * 60)
    print("11. DataFrame 行选取（loc / iloc）")
    print("=" * 60)

    # loc：基于标签
    print("\ndf.loc[0]  （第 0 行）:")
    print(df.loc[0])

    print("\ndf.loc[0:2, ['产品', '数量']]  （第 0~2 行，指定列）:")
    print(df.loc[0:2, ["产品", "数量"]])

    # iloc：基于整数位置
    print("\ndf.iloc[-3:]  （最后 3 行）:")
    print(df.iloc[-3:])


def demo_dataframe_filtering(df: DataFrame) -> None:
    """演示 DataFrame 条件筛选（布尔索引）。"""
    print("\n" + "=" * 60)
    print("12. DataFrame 条件筛选")
    print("=" * 60)

    # 筛选销售额 > 10000 的订单
    high_value: DataFrame = df[df["销售额"] > 10000]
    print("\n销售额 > 10000 的订单：")
    print(high_value)

    # 组合条件：华东区 且 单价 >= 2000
    mask: Series = (df["区域"] == "华东") & (df["单价"] >= 2000)
    filtered: DataFrame = df[mask]
    print("\n华东区 且 单价 >= 2000 的订单：")
    print(filtered)

    # isin：筛选特定产品
    target_products: list[str] = ["笔记本", "显示器"]
    product_mask: Series = df["产品"].isin(target_products)
    print(f"\n产品属于 {target_products} 的订单：")
    print(df[product_mask])


def demo_dataframe_sorting(df: DataFrame) -> None:
    """演示 DataFrame 的排序操作。"""
    print("\n" + "=" * 60)
    print("13. DataFrame 排序")
    print("=" * 60)

    # 按销售额降序排列
    sorted_by_sales: DataFrame = df.sort_values("销售额", ascending=False)
    print("\n按销售额降序排列：")
    print(sorted_by_sales[["订单编号", "产品", "销售额"]])

    # 多列排序：先按区域升序，再按数量降序
    multi_sorted: DataFrame = df.sort_values(
        ["区域", "数量"], ascending=[True, False]
    )
    print("\n先按区域升序，再按数量降序：")
    print(multi_sorted[["订单编号", "区域", "产品", "数量"]])


def demo_dataframe_add_delete(df: DataFrame) -> DataFrame:
    """演示 DataFrame 增删列操作，返回修改后的副本。"""
    print("\n" + "=" * 60)
    print("14. DataFrame 增删列")
    print("=" * 60)

    df_copy: DataFrame = df.copy()

    # 新增列：利润率
    df_copy["利润率"] = 0.15
    df_copy["利润"] = (df_copy["销售额"] * df_copy["利润率"]).round(2)
    print("\n新增 '利润率' 和 '利润' 列后：")
    print(df_copy[["订单编号", "销售额", "利润率", "利润"]])

    # 删除列
    df_copy = df_copy.drop(columns=["利润率"])
    print("\n删除 '利润率' 列后，剩余列：")
    print(df_copy.columns.tolist())

    return df_copy


def demo_dataframe_groupby(df: DataFrame) -> None:
    """演示 DataFrame 分组聚合操作。"""
    print("\n" + "=" * 60)
    print("15. DataFrame 分组聚合（groupby）")
    print("=" * 60)

    # 按产品分组，计算各产品总销售额和平均数量
    product_stats: DataFrame = df.groupby("产品").agg(
        总销售额=("销售额", "sum"),
        平均数量=("数量", "mean"),
        订单数=("订单编号", "count"),
    )
    print("\n按产品分组统计：")
    print(product_stats)

    # 按区域分组，计算总销售额
    region_sales: DataFrame = df.groupby("区域")["销售额"].sum().reset_index()
    region_sales.columns = ["区域", "总销售额"]
    region_sales = region_sales.sort_values("总销售额", ascending=False)
    print("\n按区域分组销售额（降序）：")
    print(region_sales)


def demo_dataframe_pivot(df: DataFrame) -> None:
    """演示 DataFrame 透视表。"""
    print("\n" + "=" * 60)
    print("16. DataFrame 透视表（pivot_table）")
    print("=" * 60)

    pivot: DataFrame = df.pivot_table(
        values="销售额",
        index="区域",
        columns="产品",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="合计",
    )
    print("\n各区域各产品销售额透视表：")
    print(pivot)


def demo_dataframe_missing_values(df: DataFrame) -> None:
    """演示 DataFrame 的缺失值检测与处理。"""
    print("\n" + "=" * 60)
    print("17. DataFrame 缺失值处理")
    print("=" * 60)

    # 构造含缺失值的 DataFrame
    df_missing: DataFrame = df.copy()
    df_missing.loc[2, "数量"] = np.nan
    df_missing.loc[5, "单价"] = np.nan
    df_missing.loc[7, "区域"] = np.nan

    print("\n含缺失值的数据：")
    print(df_missing[["订单编号", "区域", "数量", "单价"]])

    # 检测缺失值
    print(f"\n各列缺失值数量：\n{df_missing.isna().sum()}")

    # 删除含缺失值的行
    dropped: DataFrame = df_missing.dropna(subset=["区域", "数量", "单价"])
    print(f"\ndropna 后剩余 {len(dropped)} 行")

    # 填充缺失值
    filled: DataFrame = df_missing.copy()
    filled["数量"] = filled["数量"].fillna(filled["数量"].median())
    filled["单价"] = filled["单价"].fillna(filled["单价"].mean())
    filled["区域"] = filled["区域"].fillna("未知")
    print("\n填充缺失值后（数量用中位数、单价用均值、区域用'未知'）：")
    print(filled[["订单编号", "区域", "数量", "单价"]])


# =========================== 企业销售分析实战 ================================


def enterprise_sales_analysis() -> None:
    """企业销售数据分析完整流程演示。"""
    print("\n" + "=" * 60)
    print("  企业销售数据分析实战")
    print("=" * 60)

    # ---- 1. 构造模拟数据 ----
    np.random.seed(42)
    n_orders: int = 50
    products: list[str] = ["笔记本", "显示器", "键盘", "鼠标", "耳机"]
    regions: list[str] = ["华东", "华南", "华北", "西南", "华中"]
    price_map: dict[str, int] = {
        "笔记本": 6999,
        "显示器": 2499,
        "键盘": 599,
        "鼠标": 199,
        "耳机": 399,
    }

    orders: DataFrame = pd.DataFrame(
        {
            "订单编号": [f"ORD-{i:04d}" for i in range(1, n_orders + 1)],
            "日期": pd.date_range("2025-01-01", periods=n_orders, freq="D"),
            "产品": np.random.choice(products, n_orders),
            "区域": np.random.choice(regions, n_orders),
            "数量": np.random.randint(1, 30, n_orders),
        }
    )
    orders["单价"] = orders["产品"].map(price_map)
    orders["销售额"] = orders["数量"] * orders["单价"]

    print(f"\n原始数据：{orders.shape[0]} 条订单")
    print(orders.head(10))

    # ---- 2. 数据概览 ----
    print("\n--- 数据类型 ---")
    print(orders.dtypes)
    print("\n--- 描述性统计 ---")
    print(orders[["数量", "单价", "销售额"]].describe().round(2))

    # ---- 3. 缺失值检查 ----
    missing_count: int = orders.isna().sum().sum()
    print(f"\n缺失值总数: {missing_count}")

    # ---- 4. 按产品分析 ----
    product_analysis: DataFrame = (
        orders.groupby("产品")
        .agg(
            订单数=("订单编号", "count"),
            总销量=("数量", "sum"),
            总销售额=("销售额", "sum"),
            平均单价=("单价", "mean"),
        )
        .sort_values("总销售额", ascending=False)
    )
    product_analysis["销售额占比"] = (
        (product_analysis["总销售额"] / product_analysis["总销售额"].sum() * 100).round(2)
    )
    print("\n--- 产品销售分析 ---")
    print(product_analysis)

    # ---- 5. 按区域分析 ----
    region_analysis: DataFrame = (
        orders.groupby("区域")
        .agg(
            订单数=("订单编号", "count"),
            总销售额=("销售额", "sum"),
        )
        .sort_values("总销售额", ascending=False)
    )
    region_analysis["销售额占比"] = (
        (region_analysis["总销售额"] / region_analysis["总销售额"].sum() * 100).round(2)
    )
    print("\n--- 区域销售分析 ---")
    print(region_analysis)

    # ---- 6. 透视表：区域 x 产品 ----
    cross_table: DataFrame = orders.pivot_table(
        values="销售额",
        index="区域",
        columns="产品",
        aggfunc="sum",
        fill_value=0,
    )
    print("\n--- 区域-产品交叉分析（销售额） ---")
    print(cross_table)

    # ---- 7. Top-N 订单 ----
    top5: DataFrame = orders.nlargest(5, "销售额")
    print("\n--- 销售额 Top 5 订单 ---")
    print(top5[["订单编号", "产品", "区域", "数量", "销售额"]])

    # ---- 8. 高价订单标记 ----
    median_sales: float = orders["销售额"].median()
    orders["等级"] = orders["销售额"].apply(
        lambda x: "高" if x >= median_sales * 2 else ("中" if x >= median_sales else "低")
    )
    level_dist: Series = orders["等级"].value_counts()
    print(f"\n--- 订单等级分布（阈值: 中位数={median_sales:.0f}） ---")
    print(level_dist)

    # ---- 9. Series 统计方法汇总 ----
    total_sales: Series = orders["销售额"]
    print("\n--- 销售额统计指标 ---")
    print(f"  总销售额  : {total_sales.sum():,.0f} 元")
    print(f"  平均订单额: {total_sales.mean():,.0f} 元")
    print(f"  中位数    : {total_sales.median():,.0f} 元")
    print(f"  标准差    : {total_sales.std():,.0f}")
    print(f"  最大单笔  : {total_sales.max():,.0f} 元")
    print(f"  最小单笔  : {total_sales.min():,.0f} 元")


# ================================ 主入口 ====================================


def main() -> None:
    """主函数：依次运行所有演示模块。"""

    # ---- Series 部分 ----
    demo_create_series()
    demo_series_operations()
    demo_series_indexing()
    demo_series_attributes()
    demo_series_statistics()
    demo_series_data_processing()
    demo_series_sorting()

    # ---- DataFrame 部分 ----
    df: DataFrame = demo_create_dataframe()
    demo_dataframe_info(df)
    demo_dataframe_column_selection(df)
    demo_dataframe_row_selection(df)
    demo_dataframe_filtering(df)
    demo_dataframe_sorting(df)
    df = demo_dataframe_add_delete(df)
    demo_dataframe_groupby(df)
    demo_dataframe_pivot(df)
    demo_dataframe_missing_values(df)

    # ---- 企业实战 ----
    enterprise_sales_analysis()

    print("\n" + "=" * 60)
    print("  全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
