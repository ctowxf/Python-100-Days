"""
Day 66 - Data Analysis Overview
================================
Demonstrates:
  1. Data analysis workflow (end-to-end pipeline)
  2. Tools ecosystem overview (NumPy, Pandas, Matplotlib, etc.)
  3. Enterprise project structure for analytics teams
  4. Type hints and __main__ guard best practices

Based on: Python-100-Days Day66-80 / 66.数据分析概述.md
"""

from __future__ import annotations

import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# ─────────────────────────────────────────────
# Section 1: Data Analysis Roles & Responsibilities
# ─────────────────────────────────────────────


class AnalysisRole(Enum):
    """Career directions in the data analysis domain."""

    BUSINESS_ANALYST = auto()       # 业务数据分析师
    DATA_ENGINEER = auto()          # 数据治理方向
    DATA_SCIENTIST = auto()         # 数据挖掘方向
    DATA_DEVELOPER = auto()         # 数据开发方向
    DATA_PRODUCT_MANAGER = auto()   # 数据产品经理
    BI_ENGINEER = auto()            # BI 工程师
    DATA_OPERATION = auto()         # 数据运营


@dataclass(frozen=True)
class RoleProfile:
    """Describes a data-analysis role and its responsibilities."""

    role: AnalysisRole
    title_cn: str
    focus_area: str
    key_skills: tuple[str, ...]
    typical_jd: tuple[str, ...]  # typical job-description items

    def summary(self) -> str:
        skills = ", ".join(self.key_skills)
        return f"[{self.title_cn}] Focus: {self.focus_area} | Skills: {skills}"


# Canonical role profiles as referenced in the markdown
ROLE_PROFILES: dict[AnalysisRole, RoleProfile] = {
    AnalysisRole.BUSINESS_ANALYST: RoleProfile(
        role=AnalysisRole.BUSINESS_ANALYST,
        title_cn="业务数据分析师",
        focus_area="business insights & reporting",
        key_skills=("SQL", "Excel", "Python", "statistics", "business acumen"),
        typical_jd=(
            "负责相关报表的输出",
            "建立和优化指标体系",
            "监控数据波动和异常，找出问题",
            "优化和驱动业务，推动数字化运营",
            "找出潜在的市场和产品的上升空间",
        ),
    ),
    AnalysisRole.DATA_ENGINEER: RoleProfile(
        role=AnalysisRole.DATA_ENGINEER,
        title_cn="数据治理工程师",
        focus_area="data warehouse / data lake construction",
        key_skills=("SQL", "HiveSQL", "ETL", "Hadoop ecosystem"),
        typical_jd=(
            "建设数据仓库或数据湖",
            "实现数据从源系统到仓库的ETL",
            "保障数据质量与元数据管理",
        ),
    ),
    AnalysisRole.DATA_SCIENTIST: RoleProfile(
        role=AnalysisRole.DATA_SCIENTIST,
        title_cn="数据挖掘工程师",
        focus_area="machine learning & algorithm development",
        key_skills=("Python", "scikit-learn", "statistics", "feature engineering"),
        typical_jd=(
            "构建预测/分类模型",
            "特征工程与模型调优",
            "A/B 测试设计与分析",
        ),
    ),
}


# ─────────────────────────────────────────────
# Section 2: Data Analysis Workflow (Pipeline)
# ─────────────────────────────────────────────


class AnalysisStage(Enum):
    """Stages of a standard data-analysis workflow."""

    DEFINE_OBJECTIVE = "确定目标"
    DATA_ACQUISITION = "获取数据"
    DATA_CLEANING = "清洗数据"
    DATA_PIVOTING = "数据透视"
    VISUALIZATION = "数据呈现"
    INSIGHT = "分析洞察"


class MiningStage(Enum):
    """Stages of a deeper data-mining workflow."""

    DEFINE_OBJECTIVE = "确定目标"
    DATA_PREPARATION = "数据准备"
    DATA_ENGINEERING = "数据加工"
    MODELING = "数据建模"
    EVALUATION = "模型评估"
    DEPLOYMENT = "模型部署"


@dataclass
class PipelineStep:
    """A single step in an analytics pipeline."""

    stage: str
    description: str
    tools: list[str] = field(default_factory=list)
    completed: bool = False

    def mark_done(self) -> None:
        self.completed = True

    def __str__(self) -> str:
        status = "DONE" if self.completed else "PENDING"
        tools_str = ", ".join(self.tools) if self.tools else "N/A"
        return f"[{status}] {self.stage}: {self.description} (tools: {tools_str})"


@dataclass
class AnalysisPipeline:
    """Represents an end-to-end data analysis pipeline."""

    name: str
    objective: str
    steps: list[PipelineStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    # -- builder pattern --------------------------------------------------
    def add_step(
        self,
        stage: str,
        description: str,
        tools: list[str] | None = None,
    ) -> AnalysisPipeline:
        self.steps.append(
            PipelineStep(stage=stage, description=description, tools=tools or [])
        )
        return self

    # -- execution --------------------------------------------------------
    def advance(self) -> bool:
        """Mark the next pending step as completed. Returns False when done."""
        for step in self.steps:
            if not step.completed:
                step.mark_done()
                return True
        return False

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        done = sum(1 for s in self.steps if s.completed)
        return done / len(self.steps)

    def report(self) -> str:
        lines = [
            f"Pipeline: {self.name}",
            f"Objective: {self.objective}",
            f"Created : {self.created_at:%Y-%m-%d %H:%M}",
            f"Progress: {self.progress:.0%}",
            "-" * 50,
        ]
        lines.extend(str(s) for s in self.steps)
        return "\n".join(lines)


def build_standard_analysis_pipeline(objective: str = "Q2 sales performance analysis") -> AnalysisPipeline:
    """Factory for a standard (narrow) data-analysis pipeline."""
    pipe = AnalysisPipeline(name="Standard Analysis", objective=objective)
    pipe.add_step(
        AnalysisStage.DEFINE_OBJECTIVE.value,
        "理解业务，确定指标口径",
        tools=["business docs", "stakeholder interviews"],
    )
    pipe.add_step(
        AnalysisStage.DATA_ACQUISITION.value,
        "从数据仓库/电子表格/三方接口获取数据",
        tools=["SQL", "pandas", "APIs"],
    )
    pipe.add_step(
        AnalysisStage.DATA_CLEANING.value,
        "处理缺失值、重复值、异常值；格式化、离散化、二值化",
        tools=["pandas", "numpy"],
    )
    pipe.add_step(
        AnalysisStage.DATA_PIVOTING.value,
        "排序、统计、分组聚合、交叉表、透视表",
        tools=["pandas", "groupby", "pivot_table"],
    )
    pipe.add_step(
        AnalysisStage.VISUALIZATION.value,
        "数据可视化，发布数据分析报告",
        tools=["matplotlib", "seaborn", "plotly"],
    )
    pipe.add_step(
        AnalysisStage.INSIGHT.value,
        "解释数据变化，提出对应方案",
        tools=["business knowledge", "presentation"],
    )
    return pipe


def build_data_mining_pipeline(objective: str = "Customer churn prediction") -> AnalysisPipeline:
    """Factory for a data-mining (broad / advanced) pipeline."""
    pipe = AnalysisPipeline(name="Data Mining Pipeline", objective=objective)
    pipe.add_step(
        MiningStage.DEFINE_OBJECTIVE.value,
        "理解业务，明确挖掘目标",
        tools=["business docs"],
    )
    pipe.add_step(
        MiningStage.DATA_PREPARATION.value,
        "数据采集、描述、探索、质量判定",
        tools=["pandas", "pandas-profiling"],
    )
    pipe.add_step(
        MiningStage.DATA_ENGINEERING.value,
        "提取、清洗、变换、编码、降维、特征选择",
        tools=["pandas", "scikit-learn", "numpy"],
    )
    pipe.add_step(
        MiningStage.MODELING.value,
        "模型比较、选择、算法应用",
        tools=["scikit-learn", "xgboost", "lightgbm"],
    )
    pipe.add_step(
        MiningStage.EVALUATION.value,
        "交叉检验、参数调优、结果评价",
        tools=["scikit-learn", "statsmodels"],
    )
    pipe.add_step(
        MiningStage.DEPLOYMENT.value,
        "模型落地、业务改进、运营监控",
        tools=["Flask/FastAPI", "Docker", "Airflow"],
    )
    return pipe


# ─────────────────────────────────────────────
# Section 3: Python Data-Science Tools Ecosystem
# ─────────────────────────────────────────────


@dataclass(frozen=True)
class ToolInfo:
    """Metadata about a data-science library."""

    name: str
    pypi_name: str
    category: str
    description: str
    website: str


TOOL_CATALOG: dict[str, ToolInfo] = {
    "numpy": ToolInfo(
        name="NumPy",
        pypi_name="numpy",
        category="core",
        description="Multi-dimensional arrays, linear algebra, random numbers. "
        "Foundation for nearly every other data library.",
        website="https://numpy.org/",
    ),
    "pandas": ToolInfo(
        name="Pandas",
        pypi_name="pandas",
        category="core",
        description="DataFrame & Series for tabular / time-series data. "
        "Data loading, slicing, reshaping, cleaning, aggregation.",
        website="https://pandas.pydata.org/",
    ),
    "matplotlib": ToolInfo(
        name="Matplotlib",
        pypi_name="matplotlib",
        category="visualization",
        description="Comprehensive 2-D plotting library; MATLAB-like interface via pylab.",
        website="https://matplotlib.org/",
    ),
    "seaborn": ToolInfo(
        name="Seaborn",
        pypi_name="seaborn",
        category="visualization",
        description="High-level statistical graphics built on matplotlib.",
        website="https://seaborn.pydata.org/",
    ),
    "scipy": ToolInfo(
        name="SciPy",
        pypi_name="scipy",
        category="scientific",
        description="Linear algebra, statistics, sparse matrices, signal/image processing, "
        "optimization, FFT.",
        website="https://scipy.org/",
    ),
    "scikit-learn": ToolInfo(
        name="Scikit-learn",
        pypi_name="scikit-learn",
        category="machine-learning",
        description="Classification, regression, clustering, dimensionality reduction, "
        "model selection, preprocessing.",
        website="https://scikit-learn.org/",
    ),
    "statsmodels": ToolInfo(
        name="Statsmodels",
        pypi_name="statsmodels",
        category="statistics",
        description="Classical statistics and econometrics: regression, hypothesis tests, "
        "time-series analysis.",
        website="https://www.statsmodels.org/",
    ),
    "polars": ToolInfo(
        name="Polars",
        pypi_name="polars",
        category="core",
        description="High-performance DataFrame library; Rust backend, multi-threaded. "
        "Drop-in alternative to pandas for large datasets.",
        website="https://pola.rs/",
    ),
    "pyspark": ToolInfo(
        name="PySpark",
        pypi_name="pyspark",
        category="big-data",
        description="Python API for Apache Spark; distributed data processing at scale.",
        website="https://spark.apache.org/",
    ),
    "tensorflow": ToolInfo(
        name="TensorFlow",
        pypi_name="tensorflow",
        category="deep-learning",
        description="Open-source deep learning framework by Google.",
        website="https://www.tensorflow.org/",
    ),
    "keras": ToolInfo(
        name="Keras",
        pypi_name="keras",
        category="deep-learning",
        description="High-level neural network API; simple model building and training.",
        website="https://keras.io/",
    ),
    "pytorch": ToolInfo(
        name="PyTorch",
        pypi_name="torch",
        category="deep-learning",
        description="Open-source deep learning framework by Meta; popular in research.",
        website="https://pytorch.org/",
    ),
    "nltk": ToolInfo(
        name="NLTK",
        pypi_name="nltk",
        category="nlp",
        description="Natural Language Toolkit; tokenization, stemming, tagging, parsing.",
        website="https://www.nltk.org/",
    ),
    "spacy": ToolInfo(
        name="SpaCy",
        pypi_name="spacy",
        category="nlp",
        description="Industrial-strength NLP; fast tokenization, NER, dependency parsing.",
        website="https://spacy.io/",
    ),
}


def tools_by_category(category: str) -> list[ToolInfo]:
    """Return all tools matching a given category."""
    return [t for t in TOOL_CATALOG.values() if t.category == category]


def tool_categories() -> list[str]:
    """Return sorted unique category names."""
    return sorted({t.category for t in TOOL_CATALOG.values()})


def check_library_availability() -> dict[str, bool]:
    """Check which data-science libraries are importable in the current env."""
    results: dict[str, bool] = {}
    for key, info in TOOL_CATALOG.items():
        try:
            __import__(info.pypi_name.split("[")[0])
            results[key] = True
        except ImportError:
            results[key] = False
    return results


# ─────────────────────────────────────────────
# Section 4: Enterprise Project Structure
# ─────────────────────────────────────────────


ENTERPRISE_PROJECT_TEMPLATE: dict[str, str | dict] = {
    "project_root/": {
        "README.md": "Project overview, setup instructions",
        "pyproject.toml": "Build system & dependency management (PEP 621)",
        "Makefile": "Common commands: install, test, lint, format",
        ".env.example": "Template for environment variables",
        ".gitignore": "Ignore patterns for Python / data / IDE files",
        "docs/": {
            "analysis_report.md": "Final analysis report",
            "data_dictionary.md": "Column definitions, data sources",
            "methodology.md": "Statistical methods used",
        },
        "data/": {
            "raw/": "Original, immutable data dumps",
            "interim/": "Intermediate transformed data",
            "processed/": "Final, canonical datasets for analysis",
            "external/": "Third-party / reference data",
        },
        "notebooks/": {
            "01_data_exploration.ipynb": "EDA and profiling",
            "02_feature_engineering.ipynb": "Feature creation & selection",
            "03_modeling.ipynb": "Model training experiments",
            "04_evaluation.ipynb": "Model comparison & validation",
        },
        "src/": {
            "__init__.py": "",
            "config.py": "Paths, constants, feature flags",
            "pipeline.py": "ETL / analysis orchestration",
            "data/": {
                "__init__.py": "",
                "ingest.py": "Data loading (SQL, API, files)",
                "clean.py": "Missing values, outliers, dedup",
                "transform.py": "Feature engineering, encoding",
            },
            "analysis/": {
                "__init__.py": "",
                "descriptive.py": "Summary statistics, distributions",
                "diagnostic.py": "Correlation, hypothesis tests",
                "predictive.py": "ML model training & inference",
            },
            "visualization/": {
                "__init__.py": "",
                "charts.py": "Reusable chart builders",
                "report.py": "Report generation (HTML / PDF)",
            },
            "utils/": {
                "__init__.py": "",
                "logger.py": "Structured logging setup",
                "io_helpers.py": "File read / write abstractions",
                "decorators.py": "Timing, caching, retry decorators",
            },
        },
        "tests/": {
            "conftest.py": "Shared pytest fixtures",
            "test_ingest.py": "Data ingestion tests",
            "test_clean.py": "Cleaning logic tests",
            "test_pipeline.py": "End-to-end pipeline tests",
        },
        "scripts/": {
            "run_pipeline.py": "CLI entry point for the full pipeline",
            "generate_report.py": "CLI entry point for report generation",
        },
    },
}


def render_project_tree(
    tree: dict[str, str | dict],
    prefix: str = "",
    is_last: bool = True,
) -> str:
    """Render a nested dict as an ASCII project-tree string."""
    lines: list[str] = []
    items = list(tree.items())
    for idx, (name, value) in enumerate(items):
        last = idx == len(items) - 1
        connector = "+-- " if not last else "`-- "
        line_prefix = prefix + connector
        if isinstance(value, dict):
            lines.append(f"{line_prefix}{name}")
            extension = "    " if last else "|   "
            lines.append(render_project_tree(value, prefix + extension, last))
        else:
            desc = f"  # {value}" if value else ""
            lines.append(f"{line_prefix}{name}{desc}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Section 5: Protocol-based Abstractions
# ─────────────────────────────────────────────


@runtime_checkable
class DataSource(Protocol):
    """Any object that can provide tabular data."""

    def load(self) -> dict[str, list[Any]]:
        ...

    @property
    def row_count(self) -> int:
        ...


@runtime_checkable
class Analyzer(Protocol):
    """Any object that can perform analysis on a dataset."""

    def fit(self, data: dict[str, list[Any]]) -> None:
        ...

    def summary(self) -> str:
        ...


class BaseVisualizer(ABC):
    """Abstract base for visualization backends."""

    @abstractmethod
    def render(self, data: dict[str, Any], title: str) -> str:
        ...

    @abstractmethod
    def save(self, path: str | Path) -> None:
        ...


# ─────────────────────────────────────────────
# Section 6: Skill Stack Reference
# ─────────────────────────────────────────────


@dataclass(frozen=True)
class SkillCategory:
    name: str
    items: tuple[str, ...]
    importance: str  # "essential", "important", "nice-to-have"


SKILL_STACK: tuple[SkillCategory, ...] = (
    SkillCategory(
        name="Computer Science",
        items=("data analysis tools", "programming languages", "databases"),
        importance="essential",
    ),
    SkillCategory(
        name="Mathematics & Statistics",
        items=("data thinking", "statistical thinking", "probability"),
        importance="essential",
    ),
    SkillCategory(
        name="Artificial Intelligence",
        items=("machine learning", "deep learning", "NLP"),
        importance="important",
    ),
    SkillCategory(
        name="Business Understanding",
        items=("communication", "domain expertise", "stakeholder management"),
        importance="essential",
    ),
    SkillCategory(
        name="Presentation & Reporting",
        items=("executive summaries", "business PPTs", "storytelling with data"),
        importance="important",
    ),
)


def skill_stack_summary() -> str:
    lines = ["=" * 55, "  DATA ANALYST SKILL STACK", "=" * 55]
    for cat in SKILL_STACK:
        tag = cat.importance.upper()
        lines.append(f"\n  [{tag}] {cat.name}")
        for item in cat.items:
            lines.append(f"    - {item}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Section 7: __main__ Guard - Demo / Integration
# ─────────────────────────────────────────────


def _demo_pipeline() -> None:
    """Walk through both pipeline types step-by-step."""
    print("=" * 60)
    print("  DEMO: Standard Analysis Pipeline")
    print("=" * 60)
    std = build_standard_analysis_pipeline("Monthly revenue trend analysis")
    print(std.report())
    print()
    # Simulate advancing through 3 steps
    for _ in range(3):
        std.advance()
    print(f"--- After 3 advances (progress = {std.progress:.0%}) ---")
    print(std.report())

    print("\n" + "=" * 60)
    print("  DEMO: Data Mining Pipeline")
    print("=" * 60)
    mining = build_data_mining_pipeline("Customer churn prediction")
    print(mining.report())
    # Run to completion
    while mining.advance():
        pass
    print(f"\n--- After full run (progress = {mining.progress:.0%}) ---")
    print(mining.report())


def _demo_tools_catalog() -> None:
    """Print the tools catalog grouped by category."""
    print("\n" + "=" * 60)
    print("  PYTHON DATA-SCIENCE TOOLS ECOSYSTEM")
    print("=" * 60)
    for cat in tool_categories():
        tools = tools_by_category(cat)
        print(f"\n  [{cat.upper()}]")
        for t in tools:
            print(f"    {t.name:16s} - {t.description[:72]}...")
            print(f"    {'':16s}   {t.website}")


def _demo_library_check() -> None:
    """Check which libraries are available in the current environment."""
    print("\n" + "=" * 60)
    print("  LIBRARY AVAILABILITY CHECK")
    print("=" * 60)
    availability = check_library_availability()
    for lib, ok in sorted(availability.items()):
        status = "INSTALLED" if ok else "NOT FOUND"
        symbol = "+" if ok else "x"
        print(f"    [{symbol}] {lib:16s} {status}")


def _demo_project_structure() -> None:
    """Render the enterprise project structure."""
    print("\n" + "=" * 60)
    print("  ENTERPRISE DATA ANALYSIS PROJECT STRUCTURE")
    print("=" * 60)
    tree_str = render_project_tree(ENTERPRISE_PROJECT_TEMPLATE)
    print(tree_str)


def _demo_roles() -> None:
    """Print role profiles."""
    print("\n" + "=" * 60)
    print("  DATA ANALYSIS ROLE PROFILES")
    print("=" * 60)
    for role_enum, profile in ROLE_PROFILES.items():
        print(f"\n  {profile.summary()}")
        print(f"    JD items:")
        for item in profile.typical_jd:
            print(f"      - {item}")


def _demo_skill_stack() -> None:
    """Print the skill stack."""
    print(f"\n{skill_stack_summary()}")


def main() -> int:
    """Entry point orchestrating all demos."""
    _demo_roles()
    _demo_skill_stack()
    _demo_tools_catalog()
    _demo_library_check()
    _demo_pipeline()
    _demo_project_structure()

    print("\n" + "=" * 60)
    print("  All demos completed successfully.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
