"""
Pandas DataFrame 数据访问与筛选
===============================
演示 loc、iloc、布尔索引和 query 方法的数据访问与企业级数据筛选。
"""

from typing import Optional

import pandas as pd


def create_employee_dataframe() -> pd.DataFrame:
    """创建企业员工示例 DataFrame。"""
    data: dict[str, list] = {
        "emp_id": [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],
        "name": [
            "Alice", "Bob", "Charlie", "Diana", "Eve",
            "Frank", "Grace", "Helen", "Ivan", "Jack",
        ],
        "department": [
            "Engineering", "Marketing", "Engineering", "Sales",
            "Engineering", "Marketing", "Sales", "Engineering",
            "Marketing", "Sales",
        ],
        "title": [
            "Senior Engineer", "Marketing Manager", "Engineer", "Sales Rep",
            "Staff Engineer", "Marketing Analyst", "Sales Manager",
            "Junior Engineer", "Marketing Director", "Senior Sales Rep",
        ],
        "salary": [
            95000, 82000, 72000, 65000, 110000,
            68000, 78000, 55000, 90000, 70000,
        ],
        "years_exp": [6, 8, 3, 2, 10, 4, 7, 1, 9, 5],
        "performance_score": [4.2, 3.8, 4.5, 3.5, 4.8, 4.0, 3.9, 4.1, 4.6, 3.7],
    }
    df = pd.DataFrame(data)
    df.set_index("emp_id", inplace=True)
    return df


# ---------- loc：基于标签的数据访问 ----------


def demo_loc_single_cell(df: pd.DataFrame) -> None:
    """使用 loc 获取单个单元格的值。"""
    print("=== loc: 获取单个单元格 ===")
    # 获取员工 1001 的姓名（推荐用法，一次索引运算）
    value: str = df.loc[1001, "name"]
    print(f"员工 1001 的姓名: {value}")
    print()


def demo_loc_row_slicing(df: pd.DataFrame) -> None:
    """使用 loc 切片获取多行。"""
    print("=== loc: 行切片（标签切片包含两端）===")
    # loc 的切片是闭区间，两端都包含
    subset: pd.DataFrame = df.loc[1003:1007]
    print(subset)
    print()


def demo_loc_multi_select(df: pd.DataFrame) -> None:
    """使用 loc 花式索引选择多行多列。"""
    print("=== loc: 花式索引选择多行多列 ===")
    selected: pd.DataFrame = df.loc[[1001, 1005, 1010], ["name", "salary"]]
    print(selected)
    print()


def demo_loc_modify(df: pd.DataFrame) -> None:
    """使用 loc 修改数据。"""
    print("=== loc: 修改数据 ===")
    print(f"修改前员工 1003 的薪资: {df.loc[1003, 'salary']}")
    df.loc[1003, "salary"] = 78000
    print(f"修改后员工 1003 的薪资: {df.loc[1003, 'salary']}")
    # 恢复原值
    df.loc[1003, "salary"] = 72000
    print()


# ---------- iloc：基于整数位置的数据访问 ----------


def demo_iloc_single_row(df: pd.DataFrame) -> None:
    """使用 iloc 按整数位置获取单行。"""
    print("=== iloc: 获取单行 ===")
    # 获取第 2 行（索引从 0 开始）
    row: pd.Series = df.iloc[1]
    print(f"第 2 行数据:\n{row}")
    print()


def demo_iloc_row_slicing(df: pd.DataFrame) -> None:
    """使用 iloc 切片获取多行。"""
    print("=== iloc: 行切片（左闭右开）===")
    # iloc 的切片是左闭右开区间
    subset: pd.DataFrame = df.iloc[0:3]
    print(subset)
    print()


def demo_iloc_multi_select(df: pd.DataFrame) -> None:
    """使用 iloc 按位置选择特定行列。"""
    print("=== iloc: 选择特定行列 ===")
    # 选择第 0、4、9 行的第 0、3 列（name, salary）
    selected: pd.DataFrame = df.iloc[[0, 4, 9], [0, 3]]
    print(selected)
    print()


# ---------- 布尔索引：条件筛选 ----------


def demo_boolean_single_condition(df: pd.DataFrame) -> None:
    """单条件布尔索引筛选。"""
    print("=== 布尔索引: 单条件筛选 ===")
    # 筛选薪资高于 80000 的员工
    high_salary: pd.DataFrame = df[df["salary"] > 80000]
    print(f"薪资 > 80000 的员工:\n{high_salary}")
    print()


def demo_boolean_multi_condition(df: pd.DataFrame) -> None:
    """多条件布尔索引筛选。"""
    print("=== 布尔索引: 多条件筛选 ===")
    # 筛选工程部门且绩效 >= 4.0 的员工
    mask: pd.Series = (df["department"] == "Engineering") & (
        df["performance_score"] >= 4.0
    )
    top_engineers: pd.DataFrame = df[mask]
    print(f"工程部门绩效 >= 4.0 的员工:\n{top_engineers}")
    print()


def demo_boolean_or_condition(df: pd.DataFrame) -> None:
    """或条件布尔索引筛选。"""
    print("=== 布尔索引: 或条件筛选 ===")
    # 筛选销售部门或薪资高于 90000 的员工
    mask: pd.Series = (df["department"] == "Sales") | (df["salary"] > 90000)
    result: pd.DataFrame = df[mask]
    print(f"销售部门 OR 薪资 > 90000 的员工:\n{result}")
    print()


# ---------- query：字符串表达式筛选 ----------


def demo_query_basic(df: pd.DataFrame) -> None:
    """使用 query 进行基本条件筛选。"""
    print("=== query: 基本条件筛选 ===")
    result: pd.DataFrame = df.query("salary > 80000")
    print(f"薪资 > 80000:\n{result}")
    print()


def demo_query_compound(df: pd.DataFrame) -> None:
    """使用 query 进行复合条件筛选。"""
    print("=== query: 复合条件筛选 ===")
    # 筛选工程部门且薪资在 60000-100000 之间的员工
    result: pd.DataFrame = df.query(
        "department == 'Engineering' and 60000 <= salary <= 100000"
    )
    print(f"工程部门薪资 60000-100000:\n{result}")
    print()


def demo_query_with_variable(df: pd.DataFrame) -> None:
    """在 query 中引用外部变量。"""
    print("=== query: 引用外部变量 ===")
    min_exp: int = 5
    target_dept: str = "Marketing"
    # 使用 @ 引用外部变量
    result: pd.DataFrame = df.query(
        "years_exp >= @min_exp and department == @target_dept"
    )
    print(f"市场部且经验 >= {min_exp} 年:\n{result}")
    print()


def demo_query_not_in(df: pd.DataFrame) -> None:
    """使用 query 的 not in 进行排除筛选。"""
    print("=== query: not in 排除筛选 ===")
    excluded_depts: list[str] = ["Sales", "Marketing"]
    result: pd.DataFrame = df.query("department not in @excluded_depts")
    print(f"排除销售和市场部的员工:\n{result}")
    print()


# ---------- 企业场景：综合数据筛选 ----------


def enterprise_filter_high_performers(
    df: pd.DataFrame,
    min_score: float = 4.0,
    dept: Optional[str] = None,
) -> pd.DataFrame:
    """
    企业场景：筛选高绩效员工。

    Args:
        df: 员工 DataFrame。
        min_score: 最低绩效分数阈值，默认 4.0。
        dept: 可选的部门过滤，None 表示所有部门。

    Returns:
        符合条件的员工 DataFrame。
    """
    if dept is not None:
        return df.query(
            "performance_score >= @min_score and department == @dept"
        )
    return df.query("performance_score >= @min_score")


def enterprise_salary_analysis(df: pd.DataFrame) -> None:
    """企业场景：按部门统计薪资信息。"""
    print("=== 企业场景: 部门薪资统计 ===")
    stats: pd.DataFrame = df.groupby("department")["salary"].agg(
        ["mean", "min", "max", "count"]
    )
    stats.columns = ["平均薪资", "最低薪资", "最高薪资", "人数"]
    print(stats.round(0).astype(int))
    print()


def enterprise_top_n_by_dept(df: pd.DataFrame, n: int = 2) -> None:
    """企业场景：每个部门薪资前 N 名员工。"""
    print(f"=== 企业场景: 每个部门薪资前 {n} 名 ===")
    # 按部门分组后取薪资最高的 n 人
    top_earners: pd.DataFrame = (
        df.sort_values("salary", ascending=False)
        .groupby("department")
        .head(n)
        .sort_values(["department", "salary"], ascending=[True, False])
    )
    print(top_earners[["name", "department", "title", "salary"]])
    print()


# ---------- 主程序入口 ----------


def main() -> None:
    """主函数：演示 DataFrame 的数据访问与筛选。"""
    df: pd.DataFrame = create_employee_dataframe()
    print(f"员工数据概览 ({df.shape[0]} 行 x {df.shape[1]} 列):")
    print(df)
    print()

    # loc 演示
    demo_loc_single_cell(df)
    demo_loc_row_slicing(df)
    demo_loc_multi_select(df)
    demo_loc_modify(df)

    # iloc 演示
    demo_iloc_single_row(df)
    demo_iloc_row_slicing(df)
    demo_iloc_multi_select(df)

    # 布尔索引演示
    demo_boolean_single_condition(df)
    demo_boolean_multi_condition(df)
    demo_boolean_or_condition(df)

    # query 演示
    demo_query_basic(df)
    demo_query_compound(df)
    demo_query_with_variable(df)
    demo_query_not_in(df)

    # 企业场景
    print("=== 企业场景: 高绩效员工筛选 ===")
    top_all: pd.DataFrame = enterprise_filter_high_performers(df)
    print(f"全公司高绩效员工 (>= 4.0):\n{top_all}")
    print()

    top_eng: pd.DataFrame = enterprise_filter_high_performers(
        df, min_score=4.2, dept="Engineering"
    )
    print(f"工程部高绩效员工 (>= 4.2):\n{top_eng}")
    print()

    enterprise_salary_analysis(df)
    enterprise_top_n_by_dept(df, n=2)


if __name__ == "__main__":
    main()
