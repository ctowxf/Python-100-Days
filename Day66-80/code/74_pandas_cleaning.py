"""
深入浅出pandas-3: 数据清洗与预处理
本模块演示缺失值处理、重复值处理、类型转换等数据清洗技术，
并构建一个企业级数据清洗管道。

依赖: pandas, numpy
安装: pip install pandas numpy
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


# ==================== 缺失值处理 ====================

class MissingStrategy(Enum):
    """缺失值处理策略枚举"""
    DROP_ROW = "drop_row"          # 删除含缺失值的行
    DROP_COLUMN = "drop_column"    # 删除含缺失值的列
    FILL_ZERO = "fill_zero"        # 用0填充
    FILL_MEAN = "fill_mean"        # 用均值填充
    FILL_MEDIAN = "fill_median"    # 用中位数填充
    FILL_MODE = "fill_mode"        # 用众数填充
    FILL_FORWARD = "fill_forward"  # 用前一个值填充
    FILL_BACKWARD = "fill_backward"  # 用后一个值填充


@dataclass
class CleaningReport:
    """数据清洗报告"""
    original_rows: int = 0
    original_cols: int = 0
    missing_values_found: Dict[str, int] = field(default_factory=dict)
    duplicates_found: int = 0
    rows_after_cleaning: int = 0
    cols_after_cleaning: int = 0
    actions_taken: List[str] = field(default_factory=list)


def detect_missing(df: pd.DataFrame) -> pd.DataFrame:
    """检测DataFrame中的缺失值

    Args:
        df: 待检测的DataFrame

    Returns:
        包含缺失值统计的DataFrame
    """
    missing = df.isnull()
    missing_summary = pd.DataFrame({
        '缺失数量': missing.sum(),
        '缺失比例(%)': (missing.sum() / len(df) * 100).round(2)
    })
    return missing_summary[missing_summary['缺失数量'] > 0]


def handle_missing(
    df: pd.DataFrame,
    strategy: MissingStrategy = MissingStrategy.FILL_ZERO,
    fill_value: Optional[Any] = None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """处理DataFrame中的缺失值

    Args:
        df: 待处理的DataFrame
        strategy: 缺失值处理策略
        fill_value: 自定义填充值(当strategy为FILL_ZERO时可选)
        columns: 需要处理的列名列表，None表示处理所有列

    Returns:
        处理后的DataFrame
    """
    result = df.copy()
    target_cols = columns if columns else result.columns.tolist()

    if strategy == MissingStrategy.DROP_ROW:
        result = result.dropna(subset=target_cols)
    elif strategy == MissingStrategy.DROP_COLUMN:
        cols_with_missing = [c for c in target_cols if result[c].isnull().any()]
        result = result.drop(columns=cols_with_missing)
    elif strategy == MissingStrategy.FILL_ZERO:
        value = fill_value if fill_value is not None else 0
        result[target_cols] = result[target_cols].fillna(value)
    elif strategy == MissingStrategy.FILL_MEAN:
        for col in target_cols:
            if pd.api.types.is_numeric_dtype(result[col]):
                result[col] = result[col].fillna(result[col].mean())
    elif strategy == MissingStrategy.FILL_MEDIAN:
        for col in target_cols:
            if pd.api.types.is_numeric_dtype(result[col]):
                result[col] = result[col].fillna(result[col].median())
    elif strategy == MissingStrategy.FILL_MODE:
        for col in target_cols:
            mode_val = result[col].mode()
            if not mode_val.empty:
                result[col] = result[col].fillna(mode_val.iloc[0])
    elif strategy == MissingStrategy.FILL_FORWARD:
        result[target_cols] = result[target_cols].ffill()
    elif strategy == MissingStrategy.FILL_BACKWARD:
        result[target_cols] = result[target_cols].bfill()

    return result


# ==================== 重复值处理 ====================

@dataclass
class DuplicateConfig:
    """重复值检测配置"""
    subset: Optional[List[str]] = None  # 判断重复的列
    keep: str = "first"                  # first, last, False


def detect_duplicates(
    df: pd.DataFrame,
    config: Optional[DuplicateConfig] = None
) -> pd.DataFrame:
    """检测DataFrame中的重复值

    Args:
        df: 待检测的DataFrame
        config: 重复值检测配置

    Returns:
        包含重复行的DataFrame
    """
    if config is None:
        config = DuplicateConfig()

    mask = df.duplicated(subset=config.subset, keep=False)
    duplicates = df[mask]

    if config.subset:
        print(f"基于列 {config.subset} 检测到 {len(duplicates)} 行重复数据")
    else:
        print(f"检测到 {len(duplicates)} 行完全重复的数据")

    return duplicates


def handle_duplicates(
    df: pd.DataFrame,
    config: Optional[DuplicateConfig] = None
) -> pd.DataFrame:
    """删除DataFrame中的重复值

    Args:
        df: 待处理的DataFrame
        config: 重复值处理配置

    Returns:
        去重后的DataFrame
    """
    if config is None:
        config = DuplicateConfig()

    return df.drop_duplicates(
        subset=config.subset,
        keep=config.keep
    )


# ==================== 类型转换 ====================

def convert_to_datetime(
    df: pd.DataFrame,
    columns: List[str],
    format: Optional[str] = None
) -> pd.DataFrame:
    """将指定列转换为日期时间类型

    Args:
        df: 待处理的DataFrame
        columns: 需要转换的列名列表
        format: 日期格式字符串，None表示自动推断

    Returns:
        转换后的DataFrame
    """
    result = df.copy()
    for col in columns:
        result[col] = pd.to_datetime(result[col], format=format)
    return result


def extract_date_features(
    df: pd.DataFrame,
    date_column: str,
    features: Optional[List[str]] = None
) -> pd.DataFrame:
    """从日期列提取时间特征

    Args:
        df: 包含日期列的DataFrame
        date_column: 日期列名
        features: 需要提取的特征列表，如 ['year', 'month', 'quarter', 'weekday']

    Returns:
        添加了时间特征的DataFrame
    """
    if features is None:
        features = ['year', 'month', 'quarter', 'weekday']

    result = df.copy()
    dt_accessor = result[date_column].dt

    feature_map = {
        'year': ('年', dt_accessor.year),
        'month': ('月', dt_accessor.month),
        'quarter': ('季度', dt_accessor.quarter),
        'weekday': ('星期', dt_accessor.weekday),
        'day': ('日', dt_accessor.day),
        'hour': ('小时', dt_accessor.hour),
    }

    for feat in features:
        if feat in feature_map:
            col_name, values = feature_map[feat]
            result[col_name] = values

    return result


def convert_salary_range(salary_str: str) -> Optional[float]:
    """将工资范围字符串转换为中间值

    Args:
        salary_str: 工资范围字符串，如 "15k-30k"

    Returns:
        工资中间值，转换失败返回None
    """
    import re
    match = re.match(r'(\d+)[kK]?-(\d+)[kK]?', str(salary_str))
    if match:
        low, high = int(match.group(1)), int(match.group(2))
        return (low + high) / 2
    return None


def convert_to_numeric(
    df: pd.DataFrame,
    columns: List[str],
    errors: str = 'coerce'
) -> pd.DataFrame:
    """将指定列转换为数值类型

    Args:
        df: 待处理的DataFrame
        columns: 需要转换的列名列表
        errors: 错误处理方式，'coerce'将无效值转为NaN

    Returns:
        转换后的DataFrame
    """
    result = df.copy()
    for col in columns:
        result[col] = pd.to_numeric(result[col], errors=errors)
    return result


def encode_ordinal(
    series: pd.Series,
    mapping: Dict[str, int]
) -> pd.Series:
    """对有序分类变量进行序号编码

    Args:
        series: 待编码的Series
        mapping: 类别到数值的映射字典

    Returns:
        编码后的Series
    """
    return series.map(mapping)


def encode_one_hot(
    df: pd.DataFrame,
    columns: List[str]
) -> pd.DataFrame:
    """对无序分类变量进行独热编码

    Args:
        df: 待编码的DataFrame
        columns: 需要编码的列名列表

    Returns:
        编码后的DataFrame
    """
    return pd.get_dummies(df, columns=columns)


# ==================== 异常值检测 ====================

def detect_outliers_zscore(
    data: pd.Series,
    threshold: float = 3.0
) -> pd.Series:
    """使用Z-score方法检测异常值

    Args:
        data: 待检测的数据Series
        threshold: Z-score阈值，默认3.0

    Returns:
        异常值的布尔掩码
    """
    mean_val = data.mean()
    std_val = data.std()
    z_scores = np.abs((data - mean_val) / std_val)
    return z_scores > threshold


def detect_outliers_iqr(
    data: pd.Series,
    whis: float = 1.5
) -> pd.Series:
    """使用IQR方法检测异常值

    Args:
        data: 待检测的数据Series
        whis: IQR倍数，默认1.5

    Returns:
        异常值的布尔掩码
    """
    q1 = data.quantile(0.25)
    q3 = data.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - whis * iqr
    upper = q3 + whis * iqr
    return (data < lower) | (data > upper)


def handle_outliers(
    df: pd.DataFrame,
    column: str,
    method: str = 'iqr',
    action: str = 'remove',
    fill_value: Optional[float] = None
) -> pd.DataFrame:
    """处理DataFrame中的异常值

    Args:
        df: 待处理的DataFrame
        column: 目标列名
        method: 检测方法，'iqr'或'zscore'
        action: 处理方式，'remove'删除，'replace'替换
        fill_value: 替换值，仅当action='replace'时有效

    Returns:
        处理后的DataFrame
    """
    result = df.copy()

    if method == 'zscore':
        mask = detect_outliers_zscore(result[column])
    else:
        mask = detect_outliers_iqr(result[column])

    outlier_count = mask.sum()

    if action == 'remove':
        result = result[~mask]
        print(f"删除了 {outlier_count} 行异常值")
    elif action == 'replace':
        if fill_value is not None:
            result.loc[mask, column] = fill_value
        else:
            result.loc[mask, column] = result[column].median()
        print(f"替换了 {outlier_count} 个异常值")

    return result


# ==================== 数据清洗管道 ====================

class DataCleaningPipeline:
    """企业级数据清洗管道

    支持链式调用，按顺序执行多个清洗步骤。
    """

    def __init__(self, df: pd.DataFrame, name: str = "DataPipeline"):
        """初始化清洗管道

        Args:
            df: 待清洗的DataFrame
            name: 管道名称
        """
        self._df = df.copy()
        self._name = name
        self._report = CleaningReport(
            original_rows=len(df),
            original_cols=len(df.columns)
        )
        self._steps: List[Callable] = []

    @property
    def data(self) -> pd.DataFrame:
        """获取当前数据"""
        return self._df

    @property
    def report(self) -> CleaningReport:
        """获取清洗报告"""
        return self._report

    def handle_missing(
        self,
        strategy: MissingStrategy = MissingStrategy.FILL_ZERO,
        columns: Optional[List[str]] = None
    ) -> 'DataCleaningPipeline':
        """添加缺失值处理步骤

        Args:
            strategy: 缺失值处理策略
            columns: 目标列

        Returns:
            self，支持链式调用
        """
        missing_info = detect_missing(self._df)
        if not missing_info.empty:
            self._report.missing_values_found = missing_info['缺失数量'].to_dict()

        def step(df: pd.DataFrame) -> pd.DataFrame:
            return handle_missing(df, strategy, columns=columns)

        self._steps.append(step)
        self._report.actions_taken.append(f"缺失值处理: {strategy.value}")
        return self

    def handle_duplicates(
        self,
        subset: Optional[List[str]] = None,
        keep: str = "first"
    ) -> 'DataCleaningPipeline':
        """添加重复值处理步骤

        Args:
            subset: 判断重复的列
            keep: 保留策略

        Returns:
            self，支持链式调用
        """
        config = DuplicateConfig(subset=subset, keep=keep)

        def step(df: pd.DataFrame) -> pd.DataFrame:
            before_count = len(df)
            result = handle_duplicates(df, config)
            removed = before_count - len(result)
            if removed > 0:
                self._report.duplicates_found += removed
                self._report.actions_taken.append(f"删除重复值: {removed}行")
            return result

        self._steps.append(step)
        return self

    def convert_types(
        self,
        type_map: Dict[str, str]
    ) -> 'DataCleaningPipeline':
        """添加类型转换步骤

        Args:
            type_map: 列名到类型的映射，如 {'age': 'int', 'date': 'datetime'}

        Returns:
            self，支持链式调用
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            result = df.copy()
            datetime_cols = []
            numeric_cols = []

            for col, dtype in type_map.items():
                if col not in result.columns:
                    continue
                if dtype == 'datetime':
                    datetime_cols.append(col)
                elif dtype in ('int', 'float', 'numeric'):
                    numeric_cols.append(col)
                else:
                    result[col] = result[col].astype(dtype)

            if datetime_cols:
                result = convert_to_datetime(result, datetime_cols)
            if numeric_cols:
                result = convert_to_numeric(result, numeric_cols)

            return result

        self._steps.append(step)
        self._report.actions_taken.append(f"类型转换: {list(type_map.keys())}")
        return self

    def handle_outliers(
        self,
        column: str,
        method: str = 'iqr',
        action: str = 'remove'
    ) -> 'DataCleaningPipeline':
        """添加异常值处理步骤

        Args:
            column: 目标列名
            method: 检测方法
            action: 处理方式

        Returns:
            self，支持链式调用
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return handle_outliers(df, column, method, action)

        self._steps.append(step)
        self._report.actions_taken.append(f"异常值处理: {column} ({method})")
        return self

    def apply_function(
        self,
        func: Callable[[pd.DataFrame], pd.DataFrame],
        description: str = "自定义函数"
    ) -> 'DataCleaningPipeline':
        """添加自定义处理函数

        Args:
            func: 处理函数，接收DataFrame返回DataFrame
            description: 步骤描述

        Returns:
            self，支持链式调用
        """
        self._steps.append(func)
        self._report.actions_taken.append(description)
        return self

    def execute(self) -> pd.DataFrame:
        """执行所有清洗步骤

        Returns:
            清洗后的DataFrame
        """
        print(f"\n{'='*50}")
        print(f"开始执行数据清洗管道: {self._name}")
        print(f"原始数据: {self._report.original_rows}行 x {self._report.original_cols}列")
        print(f"{'='*50}")

        for i, step in enumerate(self._steps, 1):
            print(f"\n步骤 {i}: 执行中...")
            self._df = step(self._df)
            print(f"当前数据: {len(self._df)}行 x {len(self._df.columns)}列")

        self._report.rows_after_cleaning = len(self._df)
        self._report.cols_after_cleaning = len(self._df.columns)

        print(f"\n{'='*50}")
        print(f"清洗完成!")
        print(f"最终数据: {self._report.rows_after_cleaning}行 x {self._report.cols_after_cleaning}列")
        print(f"执行的操作: {', '.join(self._report.actions_taken)}")
        print(f"{'='*50}\n")

        return self._df


# ==================== 示例：演示代码 ====================

def create_sample_employee_data() -> pd.DataFrame:
    """创建示例员工数据(包含缺失值和重复值)"""
    data = {
        'eno': [1359, 2056, 3088, 3211, 3233, 3244, 3251, 3344, 3577, 3588,
                4466, 5234, 5566, 7800, 3211, 2056],
        'ename': ['胡一刀', '乔峰', '李莫愁', '张无忌', '丘处机', '欧阳锋',
                  '张翠山', '黄蓉', '杨过', '朱九真', '苗人凤', '郭靖',
                  '宋远桥', '张三丰', '张无忌', '乔峰'],
        'job': ['销售员', '分析师', '设计师', '程序员', '程序员', '程序员',
                '程序员', '销售主管', '会计', '会计', '销售员', '出纳',
                '会计师', '总裁', '程序员', '分析师'],
        'mgr': [3344, 7800, 2056, 2056, 2056, 3088, 2056, 7800, 5566, 5566,
                3344, 5566, 7800, np.nan, 2056, 7800],
        'sal': [1800, 5000, 3500, 3200, 3400, 3200, 4000, 3000, 2200, 2500,
                2500, 2000, 4000, 9000, 3200, 5000],
        'comm': [200, 1500, 800, np.nan, np.nan, np.nan, np.nan, 800, np.nan,
                 np.nan, np.nan, np.nan, 1000, 1200, np.nan, 1500],
        'dno': [30, 20, 20, 20, 20, 20, 20, 30, 10, 10, 30, 10, 10, 20, 20, 20]
    }
    return pd.DataFrame(data)


def create_sample_sales_data() -> pd.DataFrame:
    """创建示例销售数据(包含日期和工资范围)"""
    data = {
        '销售日期': ['2020-01-15', '2020-02-20', '2020-03-10', '2020-04-05',
                   '2020-05-18', '2020-06-22', '2020-07-30', '2020-08-12'],
        '销售区域': ['上海', '北京', '广州', '深圳', '上海', '北京', '广州', '深圳'],
        '销售渠道': ['天猫', '京东', '拼多多', '抖音', '天猫', '京东', '拼多多', '抖音'],
        '销售额': [15000, 22000, 18000, 25000, 16000, 23000, 19000, 26000]
    }
    return pd.DataFrame(data)


def create_sample_salary_data() -> pd.DataFrame:
    """创建示例工资数据(包含范围字符串)"""
    data = {
        'city': ['北京', '北京', '上海', '上海', '广州', '广州', '深圳', '深圳'],
        'position': ['数据分析师', '数据分析师', '数据分析师', '数据分析师',
                     '数据分析师', '数据分析师', '数据分析师', '数据分析师'],
        'salary': ['15k-30k', '10k-18k', '20k-30k', '33k-50k',
                   '12k-20k', '8k-15k', '18k-25k', '25k-40k']
    }
    return pd.DataFrame(data)


def demo_missing_values():
    """演示缺失值处理"""
    print("\n" + "="*60)
    print("演示1: 缺失值处理")
    print("="*60)

    df = create_sample_employee_data()

    # 检测缺失值
    print("\n1. 检测缺失值:")
    missing_info = detect_missing(df)
    print(missing_info if not missing_info.empty else "无缺失值")

    # 用0填充缺失值
    print("\n2. 用0填充缺失值:")
    df_filled = handle_missing(df, MissingStrategy.FILL_ZERO)
    print(df_filled.head())

    # 用均值填充数值列
    print("\n3. 用均值填充数值列缺失值:")
    df_mean = handle_missing(df, MissingStrategy.FILL_MEAN, columns=['mgr', 'comm'])
    print(df_mean.head())

    # 删除含缺失值的行
    print("\n4. 删除含缺失值的行:")
    df_dropped = handle_missing(df, MissingStrategy.DROP_ROW)
    print(f"删除后剩余 {len(df_dropped)} 行")


def demo_duplicates():
    """演示重复值处理"""
    print("\n" + "="*60)
    print("演示2: 重复值处理")
    print("="*60)

    df = create_sample_employee_data()

    # 检测重复值
    print("\n1. 检测完全重复的行:")
    duplicates = detect_duplicates(df)
    print(duplicates)

    # 基于特定列检测重复
    print("\n2. 基于 ename 和 job 列检测重复:")
    config = DuplicateConfig(subset=['ename', 'job'])
    duplicates = detect_duplicates(df, config)
    print(duplicates)

    # 删除重复值
    print("\n3. 删除重复值(保留第一条):")
    df_cleaned = handle_duplicates(df, config)
    print(f"删除后剩余 {len(df_cleaned)} 行")


def demo_type_conversion():
    """演示类型转换"""
    print("\n" + "="*60)
    print("演示3: 类型转换")
    print("="*60)

    # 日期特征提取
    print("\n1. 从日期列提取时间特征:")
    sales_df = create_sample_sales_data()
    sales_df = convert_to_datetime(sales_df, ['销售日期'])
    sales_df = extract_date_features(sales_df, '销售日期')
    print(sales_df.head())

    # 工资范围转换
    print("\n2. 将工资范围转换为中间值:")
    salary_df = create_sample_salary_data()
    salary_df['salary_avg'] = salary_df['salary'].apply(convert_salary_range)
    print(salary_df)

    # 有序变量编码
    print("\n3. 有序变量编码(学历):")
    edu_series = pd.Series(['研究生', '大专', '本科', '高中', '研究生'])
    edu_mapping = {'高中': 1, '大专': 3, '本科': 5, '研究生': 10}
    encoded = encode_ordinal(edu_series, edu_mapping)
    print(encoded)

    # 独热编码
    print("\n4. 独热编码(销售渠道):")
    sales_small = sales_df[['销售区域', '销售渠道']].head()
    encoded_df = encode_one_hot(sales_small, ['销售渠道'])
    print(encoded_df)


def demo_outlier_detection():
    """演示异常值检测"""
    print("\n" + "="*60)
    print("演示4: 异常值检测")
    print("="*60)

    # 创建包含异常值的数据
    np.random.seed(42)
    salaries = pd.Series(np.random.normal(5000, 1000, 100))
    salaries.iloc[0] = 20000  # 异常高值
    salaries.iloc[1] = 500    # 异常低值

    # Z-score检测
    print("\n1. Z-score方法检测异常值:")
    outliers_z = detect_outliers_zscore(salaries, threshold=3)
    print(f"发现 {outliers_z.sum()} 个异常值")
    print(f"异常值: {salaries[outliers_z].tolist()}")

    # IQR检测
    print("\n2. IQR方法检测异常值:")
    outliers_iqr = detect_outliers_iqr(salaries)
    print(f"发现 {outliers_iqr.sum()} 个异常值")
    print(f"异常值: {salaries[outliers_iqr].tolist()}")


def demo_cleaning_pipeline():
    """演示数据清洗管道"""
    print("\n" + "="*60)
    print("演示5: 企业级数据清洗管道")
    print("="*60)

    # 创建包含各种问题的数据
    df = create_sample_employee_data()

    # 使用清洗管道
    cleaned_df = (
        DataCleaningPipeline(df, name="员工数据清洗")
        .handle_missing(strategy=MissingStrategy.FILL_ZERO)
        .handle_duplicates(subset=['ename', 'job'])
        .handle_outliers(column='sal', method='iqr', action='replace')
        .execute()
    )

    print("\n清洗后的数据:")
    print(cleaned_df)

    # 查看清洗报告
    pipeline = DataCleaningPipeline(df)
    pipeline.handle_missing(MissingStrategy.FILL_ZERO)
    pipeline.handle_duplicates(subset=['ename', 'job'])
    pipeline.execute()

    print("\n清洗报告:")
    report = pipeline.report
    print(f"  原始数据: {report.original_rows}行 x {report.original_cols}列")
    print(f"  发现缺失值: {report.missing_values_found}")
    print(f"  删除重复行: {report.duplicates_found}")
    print(f"  最终数据: {report.rows_after_cleaning}行 x {report.cols_after_cleaning}列")
    print(f"  执行操作: {report.actions_taken}")


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("pandas数据清洗与预处理 - 综合演示")
    print("="*60)

    # 运行各个演示
    demo_missing_values()
    demo_duplicates()
    demo_type_conversion()
    demo_outlier_detection()
    demo_cleaning_pipeline()

    print("\n" + "="*60)
    print("所有演示完成!")
    print("="*60)
