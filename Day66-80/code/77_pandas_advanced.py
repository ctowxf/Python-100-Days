"""
深入浅出pandas-6: 高级索引与性能优化
=====================================
涵盖: 时间序列分析、分类数据、多级索引、性能优化
企业案例: 金融时间序列分析、大规模数据集优化
"""

from typing import Any, Optional, Union, List, Tuple, Dict
import numpy as np
import pandas as pd
from pandas import (
    DataFrame,
    Series,
    Index,
    RangeIndex,
    CategoricalIndex,
    MultiIndex,
    IntervalIndex,
    DatetimeIndex,
)


# =============================================================================
# 1. 范围索引 (RangeIndex)
# =============================================================================


def demo_range_index() -> Series:
    """演示范围索引的创建和使用。"""
    sales_data: np.ndarray = np.random.randint(400, 1000, 12)
    index: RangeIndex = pd.RangeIndex(1, 13, name='月份')
    ser: Series = pd.Series(data=sales_data, index=index)
    print("=== 范围索引示例 ===")
    print(ser)
    return ser


# =============================================================================
# 2. 分类索引 (CategoricalIndex)
# =============================================================================


def demo_categorical_index() -> Series:
    """演示分类索引的创建、分组聚合和排序。"""
    sales_data: List[int] = [6, 6, 7, 6, 8, 6]
    index: CategoricalIndex = pd.CategoricalIndex(
        data=['苹果', '香蕉', '苹果', '苹果', '桃子', '香蕉'],
        categories=['苹果', '香蕉', '桃子'],
        ordered=True,
    )
    ser: Series = pd.Series(data=sales_data, index=index)
    print("\n=== 分类索引示例 ===")
    print(ser)

    # 基于索引分组求和
    grouped: Series = ser.groupby(level=0).sum()
    print("\n分组求和:")
    print(grouped)

    # 指定索引顺序后重新分组
    ser.index = index.reorder_categories(['香蕉', '桃子', '苹果'])
    reordered_grouped: Series = ser.groupby(level=0).sum()
    print("\n重排顺序后分组求和:")
    print(reordered_grouped)
    return ser


# =============================================================================
# 3. 多级索引 (MultiIndex)
# =============================================================================


def demo_multi_index() -> DataFrame:
    """演示多级索引的创建和高级分组聚合操作。"""
    print("\n=== 多级索引示例 ===")

    # 从元组创建多级索引
    tuples: List[Tuple[int, str]] = [
        (1, 'red'), (1, 'blue'), (2, 'red'), (2, 'blue')
    ]
    index: MultiIndex = pd.MultiIndex.from_tuples(
        tuples, names=['no', 'color']
    )
    sales_data: np.ndarray = np.random.randint(1, 100, 4)
    ser: Series = pd.Series(data=sales_data, index=index)
    print("\n从元组创建的多级索引 Series:")
    print(ser)

    # 按第一级分组
    print("\n按 no 分组求和:")
    print(ser.groupby('no').sum())

    # 按第二级分组
    print("\n按 color 分组求和:")
    print(ser.groupby(level=1).sum())

    # 从笛卡尔积创建多级索引 — 学生成绩场景
    stu_ids: np.ndarray = np.arange(1001, 1006)
    semesters: List[str] = ['期中', '期末']
    index_product: MultiIndex = pd.MultiIndex.from_product(
        (stu_ids, semesters), names=['学号', '学期']
    )
    courses: List[str] = ['语文', '数学', '英语']
    scores: np.ndarray = np.random.randint(60, 101, (10, 3))
    df: DataFrame = pd.DataFrame(data=scores, columns=courses, index=index_product)
    print("\n学生成绩 DataFrame (多级索引):")
    print(df)

    # 加权成绩计算: 期中 25%, 期末 75%
    weighted: DataFrame = df.groupby(level=0).agg(
        lambda x: x.values[0] * 0.25 + x.values[1] * 0.75
    )
    print("\n加权成绩 (期中25% + 期末75%):")
    print(weighted)
    return df


# =============================================================================
# 4. 间隔索引 (IntervalIndex)
# =============================================================================


def demo_interval_index() -> None:
    """演示间隔索引的创建及其 contains / overlaps 检查方法。"""
    print("\n=== 间隔索引示例 ===")

    # 默认右闭区间
    index: IntervalIndex = pd.interval_range(start=0, end=5)
    print(f"默认间隔索引: {index}")
    print(f"contains(1.5): {index.contains(1.5)}")
    print(f"overlaps(1.5, 3.5): {index.overlaps(pd.Interval(1.5, 3.5))}")

    # 左闭区间
    left_closed: IntervalIndex = pd.interval_range(
        start=0, end=5, closed='left'
    )
    print(f"\n左闭间隔索引: {left_closed}")

    # 日期间隔索引 (双闭区间)
    date_interval: IntervalIndex = pd.interval_range(
        start=pd.Timestamp('2022-01-01'),
        end=pd.Timestamp('2022-01-04'),
        closed='both',
    )
    print(f"\n日期间隔索引 (双闭): {date_interval}")


# =============================================================================
# 5. 日期时间索引 (DatetimeIndex) 与时间序列
# =============================================================================


def demo_datetime_index() -> None:
    """演示日期时间索引的创建、采样、重采样和时区操作。"""
    print("\n=== 日期时间索引示例 ===")

    # 用 periods 指定生成点数
    idx_periods: DatetimeIndex = pd.date_range(
        '2021-1-1', '2021-6-30', periods=10
    )
    print(f"periods=10:\n{idx_periods}")

    # 用 freq 指定采样频率
    idx_weekly: DatetimeIndex = pd.date_range(
        '2021-1-1', '2021-6-30', freq='W'
    )
    print(f"\nfreq='W' (每周日):\n{idx_weekly}")

    # DateOffset 偏移运算
    shifted: DatetimeIndex = idx_weekly - pd.DateOffset(days=2)
    print(f"\n每周日 - 2天 (周五):\n{shifted}")

    advanced: DatetimeIndex = idx_weekly + pd.DateOffset(hours=2, minutes=10)
    print(f"\n每周日 + 2h10m:\n{advanced}")


# =============================================================================
# 6. 企业案例: 金融时间序列分析
# =============================================================================


def generate_stock_data(
    ticker: str = 'AAPL',
    start: str = '2023-01-01',
    end: str = '2023-12-31',
    seed: int = 42,
) -> DataFrame:
    """生成模拟股票数据用于演示。

    Parameters
    ----------
    ticker : str
        股票代码。
    start, end : str
        起止日期。
    seed : int
        随机种子, 保证可重复性。

    Returns
    -------
    DataFrame
        包含 Open, High, Low, Close, Volume 的日频股票数据。
    """
    np.random.seed(seed)
    dates: DatetimeIndex = pd.bdate_range(start, end)
    n: int = len(dates)

    # 模拟价格随机游走
    close: np.ndarray = 150 + np.cumsum(np.random.randn(n) * 1.5)
    open_: np.ndarray = close + np.random.randn(n) * 0.5
    high: np.ndarray = np.maximum(open_, close) + np.abs(np.random.randn(n))
    low: np.ndarray = np.minimum(open_, close) - np.abs(np.random.randn(n))
    volume: np.ndarray = np.random.randint(20_000_000, 80_000_000, n)

    df: DataFrame = pd.DataFrame({
        'Open': open_,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume,
    }, index=dates)
    df.index.name = 'Date'
    df.attrs['ticker'] = ticker
    return df


def financial_time_series_analysis(df: DataFrame) -> Dict[str, DataFrame]:
    """对金融时间序列进行常见分析。

    包含: 移动平均、波动率、收益率、月度重采样。

    Parameters
    ----------
    df : DataFrame
        含 DatetimeIndex 的股票日频数据。

    Returns
    -------
    dict[str, DataFrame]
        各项分析结果的字典。
    """
    results: Dict[str, DataFrame] = {}

    # --- 移动平均 ---
    ma_windows: List[int] = [5, 20, 60]
    for w in ma_windows:
        df[f'MA{w}'] = df['Close'].rolling(window=w).mean()
    results['moving_averages'] = df[['Close'] + [f'MA{w}' for w in ma_windows]]

    # --- 日收益率 & 累计收益率 ---
    df['DailyReturn'] = df['Close'].pct_change()
    df['CumReturn'] = (1 + df['DailyReturn']).cumprod() - 1
    results['returns'] = df[['DailyReturn', 'CumReturn']]

    # --- 波动率 (20日滚动标准差年化) ---
    df['Volatility20'] = (
        df['DailyReturn'].rolling(window=20).std() * np.sqrt(252)
    )
    results['volatility'] = df[['Volatility20']]

    # --- 月度重采样聚合 ---
    monthly: DataFrame = df.resample('ME').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum',
    })
    monthly['MonthlyReturn'] = monthly['Close'].pct_change()
    results['monthly_summary'] = monthly

    return results


# =============================================================================
# 7. 企业案例: 多维度销售数据分析 (MultiIndex + Categorical)
# =============================================================================


def build_sales_cube(
    n_records: int = 10_000, seed: int = 42
) -> DataFrame:
    """构建多维度销售数据立方体。

    维度: (Region, ProductCategory, Quarter)
    指标: Revenue, Cost, UnitsSold

    Parameters
    ----------
    n_records : int
        记录条数。
    seed : int
        随机种子。

    Returns
    -------
    DataFrame
        带有 MultiIndex 的销售数据。
    """
    np.random.seed(seed)

    regions: List[str] = ['华东', '华南', '华北', '西南', '西北']
    categories: List[str] = ['电子产品', '服装', '食品', '家居']
    quarters: List[str] = ['Q1', 'Q2', 'Q3', 'Q4']

    region_cat: CategoricalIndex = pd.CategoricalIndex(
        np.random.choice(regions, n_records),
        categories=regions,
        ordered=True,
    )
    category_cat: CategoricalIndex = pd.CategoricalIndex(
        np.random.choice(categories, n_records),
        categories=categories,
        ordered=True,
    )
    quarter_cat: CategoricalIndex = pd.CategoricalIndex(
        np.random.choice(quarters, n_records),
        categories=quarters,
        ordered=True,
    )

    multi_idx: MultiIndex = pd.MultiIndex(
        [region_cat, category_cat, quarter_cat],
        names=['Region', 'Category', 'Quarter'],
    )

    df: DataFrame = pd.DataFrame({
        'Revenue': np.random.uniform(1000, 50000, n_records).round(2),
        'Cost': np.random.uniform(500, 30000, n_records).round(2),
        'UnitsSold': np.random.randint(1, 500, n_records),
    }, index=multi_idx)

    df['Profit'] = (df['Revenue'] - df['Cost']).round(2)
    df['Margin'] = (df['Profit'] / df['Revenue'] * 100).round(2)
    return df


def analyze_sales_cube(df: DataFrame) -> Dict[str, DataFrame]:
    """对多维销售数据进行切片、切块和聚合分析。

    Parameters
    ----------
    df : DataFrame
        带有 MultiIndex 的销售数据。

    Returns
    -------
    dict[str, DataFrame]
        多种聚合视角的结果。
    """
    results: Dict[str, DataFrame] = {}

    # 按区域 + 品类汇总
    results['region_category'] = df.groupby(
        level=['Region', 'Category']
    ).agg({
        'Revenue': 'sum',
        'Cost': 'sum',
        'Profit': 'sum',
        'UnitsSold': 'sum',
    })

    # 按季度汇总
    results['by_quarter'] = df.groupby(
        level='Quarter'
    ).agg({
        'Revenue': ['sum', 'mean'],
        'Profit': ['sum', 'mean'],
        'Margin': 'mean',
    })

    # 各区域利润率排名
    region_margin: Series = df.groupby(level='Region')['Margin'].mean()
    results['region_margin_ranking'] = region_margin.sort_values(
        ascending=False
    ).to_frame('AvgMargin%')

    # unstack 透视: 区域 x 季度 的收入矩阵
    results['pivot_revenue'] = df.groupby(
        level=['Region', 'Quarter']
    )['Revenue'].sum().unstack(level='Quarter')

    return results


# =============================================================================
# 8. 性能优化技巧
# =============================================================================


def optimize_dtypes(df: DataFrame, verbose: bool = True) -> DataFrame:
    """自动优化 DataFrame 的数据类型以降低内存占用。

    策略:
    - 整数列: 用最小可容纳的整数类型 (int8/16/32)
    - 浮点列: 如无精度损失则降为 float32
    - 低基数字符串列: 转为 Categorical

    Parameters
    ----------
    df : DataFrame
        待优化的 DataFrame。
    verbose : bool
        是否打印优化前后内存对比。

    Returns
    -------
    DataFrame
        优化后的 DataFrame。
    """
    before_mb: float = df.memory_usage(deep=True).sum() / 1024**2
    optimized: DataFrame = df.copy()

    for col in optimized.columns:
        col_type: str = optimized[col].dtype.name

        # 整数列优化
        if col_type.startswith('int'):
            col_min: int = optimized[col].min()
            col_max: int = optimized[col].max()
            if col_min >= np.iinfo(np.int8).min and col_max <= np.iinfo(np.int8).max:
                optimized[col] = optimized[col].astype(np.int8)
            elif col_min >= np.iinfo(np.int16).min and col_max <= np.iinfo(np.int16).max:
                optimized[col] = optimized[col].astype(np.int16)
            elif col_min >= np.iinfo(np.int32).min and col_max <= np.iinfo(np.int32).max:
                optimized[col] = optimized[col].astype(np.int32)

        # 浮点列降精度
        elif col_type.startswith('float'):
            f32: np.ndarray = optimized[col].astype(np.float32)
            if np.allclose(optimized[col].values, f32, rtol=1e-5, equal_nan=True):
                optimized[col] = f32

        # 低基数字符串列转分类
        elif col_type == 'object':
            nunique: int = optimized[col].nunique()
            if nunique / len(optimized) < 0.5:
                optimized[col] = optimized[col].astype('category')

    after_mb: float = optimized.memory_usage(deep=True).sum() / 1024**2

    if verbose:
        print(f"\n=== 内存优化 ===")
        print(f"优化前: {before_mb:.2f} MB")
        print(f"优化后: {after_mb:.2f} MB")
        print(f"节省:   {before_mb - after_mb:.2f} MB ({(1 - after_mb/before_mb)*100:.1f}%)")

    return optimized


def benchmark_groupby(
    n_rows: int = 500_000, seed: int = 42
) -> None:
    """对比不同 groupby 策略的性能。

    比较:
    1. 默认 groupby
    2. 使用 Categorical 类型分组键
    3. 使用 sort=False 跳过排序

    Parameters
    ----------
    n_rows : int
        数据行数。
    seed : int
        随机种子。
    """
    import time

    np.random.seed(seed)
    groups: List[str] = [f'G{i:03d}' for i in range(100)]
    keys: np.ndarray = np.random.choice(groups, n_rows)
    values: np.ndarray = np.random.randn(n_rows)

    print(f"\n=== GroupBy 性能对比 ({n_rows:,} 行) ===")

    # 1. 默认 groupby (字符串键, 排序)
    df_str: DataFrame = pd.DataFrame({'key': keys, 'value': values})
    t0: float = time.perf_counter()
    _ = df_str.groupby('key', sort=True)['value'].agg(['mean', 'std', 'sum'])
    t1: float = time.perf_counter()
    print(f"字符串键 + sort=True:  {(t1-t0)*1000:.1f} ms")

    # 2. Categorical 键
    df_cat: DataFrame = df_str.copy()
    df_cat['key'] = df_cat['key'].astype('category')
    t0 = time.perf_counter()
    _ = df_cat.groupby('key', sort=True)['value'].agg(['mean', 'std', 'sum'])
    t1 = time.perf_counter()
    print(f"Categorical 键 + sort=True:  {(t1-t0)*1000:.1f} ms")

    # 3. sort=False
    t0 = time.perf_counter()
    _ = df_str.groupby('key', sort=False)['value'].agg(['mean', 'std', 'sum'])
    t1 = time.perf_counter()
    print(f"字符串键 + sort=False: {(t1-t0)*1000:.1f} ms")


def demonstrate_chunked_processing(
    n_total: int = 2_000_000, chunk_size: int = 200_000
) -> DataFrame:
    """演示分块处理大规模数据的模式。

    适用于内存不足以一次性加载全部数据的场景。

    Parameters
    ----------
    n_total : int
        模拟总行数。
    chunk_size : int
        每块行数。

    Returns
    -------
    DataFrame
        聚合后的结果。
    """
    np.random.seed(42)
    all_chunks: List[DataFrame] = []

    print(f"\n=== 分块处理 ({n_total:,} 行, 块大小={chunk_size:,}) ===")

    for start in range(0, n_total, chunk_size):
        end: int = min(start + chunk_size, n_total)
        size: int = end - start

        chunk: DataFrame = pd.DataFrame({
            'category': np.random.choice(['A', 'B', 'C', 'D'], size),
            'value': np.random.randn(size),
            'amount': np.random.uniform(10, 1000, size).round(2),
        })

        # 每块内做聚合, 减少中间内存
        agg_chunk: DataFrame = chunk.groupby('category').agg(
            count=('value', 'size'),
            value_sum=('value', 'sum'),
            value_sq_sum=('value', lambda x: (x**2).sum()),
            amount_sum=('amount', 'sum'),
        )
        all_chunks.append(agg_chunk)

    # 合并各块的聚合结果
    combined: DataFrame = pd.concat(all_chunks)
    final: DataFrame = combined.groupby(level=0).agg({
        'count': 'sum',
        'value_sum': 'sum',
        'value_sq_sum': 'sum',
        'amount_sum': 'sum',
    })

    # 从聚合统计量计算均值和标准差
    final['value_mean'] = final['value_sum'] / final['count']
    final['value_std'] = np.sqrt(
        final['value_sq_sum'] / final['count'] - final['value_mean'] ** 2
    )
    final['amount_mean'] = final['amount_sum'] / final['count']

    print(final[['count', 'value_mean', 'value_std', 'amount_mean']])
    return final


def demonstrate_eval_and_query(n_rows: int = 500_000) -> None:
    """演示 eval / query 在大规模数据上的性能优势。"""
    import time

    np.random.seed(42)
    df: DataFrame = pd.DataFrame({
        'price': np.random.uniform(10, 500, n_rows),
        'quantity': np.random.randint(1, 100, n_rows),
        'discount': np.random.uniform(0.8, 1.0, n_rows),
        'category': np.random.choice(['A', 'B', 'C'], n_rows),
    })

    print(f"\n=== eval / query 性能对比 ({n_rows:,} 行) ===")

    # 传统方式: 计算总金额
    t0: float = time.perf_counter()
    total1: Series = df['price'] * df['quantity'] * df['discount']
    t1: float = time.perf_counter()
    print(f"传统乘法:            {(t1-t0)*1000:.1f} ms")

    # eval 方式
    t0 = time.perf_counter()
    df.eval('total = price * quantity * discount', inplace=True)
    t1 = time.perf_counter()
    print(f"eval 乘法:           {(t1-t0)*1000:.1f} ms")

    # 传统布尔索引
    t0 = time.perf_counter()
    filtered1: DataFrame = df[(df['category'] == 'A') & (df['total'] > 10000)]
    t1 = time.perf_counter()
    print(f"传统布尔索引:        {(t1-t0)*1000:.1f} ms")

    # query 方式
    t0 = time.perf_counter()
    filtered2: DataFrame = df.query('category == "A" and total > 10000')
    t1 = time.perf_counter()
    print(f"query 布尔索引:      {(t1-t0)*1000:.1f} ms")


# =============================================================================
# 9. 综合演示: 金融分析全流程
# =============================================================================


def full_financial_workflow() -> None:
    """完整的金融时间序列分析工作流。"""
    print("=" * 70)
    print("  企业案例: 金融时间序列分析全流程")
    print("=" * 70)

    # 生成模拟数据
    stock_df: DataFrame = generate_stock_data(
        ticker='AAPL', start='2023-01-01', end='2023-12-31'
    )
    print(f"\n原始数据形状: {stock_df.shape}")
    print(stock_df.head())

    # 时区本地化与转换
    stock_df.index = stock_df.index.tz_localize('UTC')
    stock_df_ny: DataFrame = stock_df.tz_convert('America/New_York')
    print(f"\n转换为纽约时区:")
    print(stock_df_ny.head())

    # 移除时区信息以便后续操作
    stock_df_ny.index = stock_df_ny.index.tz_localize(None)

    # 时间序列分析
    analysis: Dict[str, DataFrame] = financial_time_series_analysis(stock_df_ny)

    print("\n--- 月度汇总 ---")
    print(analysis['monthly_summary'])

    print("\n--- 最近5天的移动平均 ---")
    print(analysis['moving_averages'].tail())

    print("\n--- 泚动率统计 ---")
    vol: DataFrame = analysis['volatility'].dropna()
    print(f"平均20日年化波动率: {vol['Volatility20'].mean():.4f}")
    print(f"最大波动率:         {vol['Volatility20'].max():.4f}")
    print(f"最小波动率:         {vol['Volatility20'].min():.4f}")

    # asfreq 抽样 (每5个交易日)
    sampled: DataFrame = stock_df_ny.asfreq('5B', method='ffill')
    print(f"\n5日抽样数据 (前5行):")
    print(sampled.head())


def full_sales_analysis_workflow() -> None:
    """完整的多维销售数据分析工作流。"""
    print("\n" + "=" * 70)
    print("  企业案例: 多维销售数据分析")
    print("=" * 70)

    # 构建数据
    sales_df: DataFrame = build_sales_cube(n_records=50_000)
    print(f"\n数据形状: {sales_df.shape}")
    print(f"内存占用: {sales_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # 多维分析
    analysis: Dict[str, DataFrame] = analyze_sales_cube(sales_df)

    print("\n--- 区域 x 品类 汇总 (前10行) ---")
    print(analysis['region_category'].head(10))

    print("\n--- 季度汇总 ---")
    print(analysis['by_quarter'])

    print("\n--- 区域利润率排名 ---")
    print(analysis['region_margin_ranking'])

    print("\n--- 区域 x 季度 收入透视 ---")
    print(analysis['pivot_revenue'])


def full_optimization_workflow() -> None:
    """完整的性能优化演示。"""
    print("\n" + "=" * 70)
    print("  性能优化技巧演示")
    print("=" * 70)

    # 1. dtype 优化
    np.random.seed(42)
    large_df: DataFrame = pd.DataFrame({
        'id': np.arange(1_000_000),
        'small_int': np.random.randint(0, 100, 1_000_000),
        'medium_int': np.random.randint(0, 10000, 1_000_000),
        'float_col': np.random.randn(1_000_000),
        'category_col': np.random.choice(
            ['Alpha', 'Beta', 'Gamma', 'Delta'], 1_000_000
        ),
    })
    optimized_df: DataFrame = optimize_dtypes(large_df, verbose=True)

    # 2. GroupBy 性能对比
    benchmark_groupby(n_rows=500_000)

    # 3. 分块处理
    demonstrate_chunked_processing(n_total=2_000_000, chunk_size=200_000)

    # 4. eval / query 性能
    demonstrate_eval_and_query(n_rows=500_000)


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    """主函数: 依次运行所有演示。"""
    # 基础索引类型演示
    demo_range_index()
    demo_categorical_index()
    demo_multi_index()
    demo_interval_index()
    demo_datetime_index()

    # 企业案例
    full_financial_workflow()
    full_sales_analysis_workflow()

    # 性能优化
    full_optimization_workflow()

    print("\n" + "=" * 70)
    print("  所有演示完成")
    print("=" * 70)


if __name__ == '__main__':
    main()
