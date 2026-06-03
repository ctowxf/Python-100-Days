"""
机器学习实战 - 泰坦尼克号生存预测

本模块实现了完整的机器学习流水线，包括：
- 数据加载与探索性分析 (EDA)
- 特征工程（数据清洗、特征转换、特征构造）
- 模型训练与评估（逻辑回归、XGBoost）
- 模型持久化与预测 API 部署

数据来源: Kaggle Titanic - Machine Learning from Disaster
https://www.kaggle.com/competitions/titanic/
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据模型与常量
# ---------------------------------------------------------------------------

# 称谓映射表
TITLE_MAPPING: Dict[str, int] = {
    "Mr": 0,
    "Miss": 1,
    "Mrs": 2,
    "Master": 3,
    "Dr": 4,
    "Rev": 5,
    "Col": 6,
    "Major": 7,
    "Mlle": 8,
    "Ms": 9,
    "Lady": 10,
    "Sir": 11,
    "Jonkheer": 12,
    "Don": 13,
    "Dona": 14,
    "Countess": 15,
}

# 特征列（训练完成后使用）
FEATURE_COLUMNS: List[str] = [
    "Pclass",
    "Age",
    "Fare",
    "Cabin",
    "Sex_male",
    "Embarked_Q",
    "Embarked_S",
    "Title",
    "FamilySize",
]


@dataclass
class ModelMetrics:
    """模型评估指标容器。"""

    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion_matrix: np.ndarray = field(repr=False)

    def summary(self) -> str:
        """返回可读的指标摘要。"""
        return (
            f"Accuracy:  {self.accuracy:.4f}\n"
            f"Precision: {self.precision:.4f}\n"
            f"Recall:    {self.recall:.4f}\n"
            f"F1-Score:  {self.f1:.4f}\n"
            f"ROC-AUC:   {self.roc_auc:.4f}\n"
            f"Confusion Matrix:\n{self.confusion_matrix}"
        )


@dataclass
class PipelineResult:
    """流水线执行结果。"""

    model_name: str
    metrics: ModelMetrics
    model: Any = field(repr=False)
    scaler: StandardScaler = field(repr=False)


# ---------------------------------------------------------------------------
# 数据加载模块
# ---------------------------------------------------------------------------


class DataLoader:
    """数据加载器，负责读取和初步检查原始数据。"""

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)

    def load_train(self) -> pd.DataFrame:
        """加载训练数据集。

        Returns:
            以 PassengerId 为索引的训练 DataFrame。
        """
        path = self.data_dir / "train.csv"
        logger.info("加载训练数据: %s", path)
        df = pd.read_csv(path, index_col="PassengerId")
        logger.info("训练集形状: %s", df.shape)
        return df

    def load_test(self) -> pd.DataFrame:
        """加载测试数据集。

        Returns:
            以 PassengerId 为索引的测试 DataFrame。
        """
        path = self.data_dir / "test.csv"
        logger.info("加载测试数据: %s", path)
        df = pd.read_csv(path, index_col="PassengerId")
        logger.info("测试集形状: %s", df.shape)
        return df

    @staticmethod
    def data_overview(df: pd.DataFrame) -> None:
        """打印数据概览信息。"""
        print("=" * 60)
        print("数据概览")
        print("=" * 60)
        print("\n前 5 行:")
        print(df.head())
        print("\n数据类型与缺失值:")
        print(df.info())
        print("\n数值列统计描述:")
        print(df.describe())
        print("\n缺失值统计:")
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        missing_df = pd.DataFrame({
            "缺失数量": missing,
            "缺失比例(%)": missing_pct,
        })
        print(missing_df[missing_df["缺失数量"] > 0])


# ---------------------------------------------------------------------------
# 探索性数据分析 (EDA)
# ---------------------------------------------------------------------------


class ExploratoryAnalysis:
    """探索性数据分析器，提供可视化和统计分析功能。"""

    @staticmethod
    def setup_chinese_font() -> None:
        """配置 matplotlib 中文字体支持。"""
        plt.rcParams["font.sans-serif"].insert(0, "SimHei")
        plt.rcParams["axes.unicode_minus"] = False

    @staticmethod
    def plot_survival_distribution(df: pd.DataFrame) -> None:
        """绘制获救情况分布图。"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12), dpi=150)

        # 1. 获救情况分布
        ax = axes[0, 0]
        ser = df["Survived"].value_counts()
        ser.plot(kind="bar", color=["#BE3144", "#3A7D44"], ax=ax)
        ax.set_xticklabels(["遇难", "幸存"], rotation=0)
        ax.set_title("获救情况分布")
        ax.set_ylabel("人数")
        for i, v in enumerate(ser):
            ax.text(i, v, str(v), ha="center", va="bottom")

        # 2. 客舱等级分布
        ax = axes[0, 1]
        ser = df["Pclass"].value_counts().sort_index()
        ser.plot(kind="bar", color=["#FA4032", "#FA812F", "#FAB12F"], ax=ax)
        ax.set_xticklabels(["一等舱", "二等舱", "三等舱"], rotation=0)
        ax.set_title("客舱等级分布")
        ax.set_ylabel("人数")
        for i, v in enumerate(ser):
            ax.text(i, v, str(v), ha="center", va="bottom")

        # 3. 性别分布
        ax = axes[0, 2]
        ser = df["Sex"].value_counts()
        ser.plot(kind="bar", color=["#16404D", "#D84040"], ax=ax)
        ax.set_xticklabels(["男性", "女性"], rotation=0)
        ax.set_title("性别分布")
        ax.set_ylabel("人数")
        for i, v in enumerate(ser):
            ax.text(i, v, str(v), ha="center", va="bottom")

        # 4. 年龄箱线图
        ax = axes[1, 0]
        df["Age"].plot(kind="box", showmeans=True, notch=True, ax=ax)
        ax.set_title("乘客年龄分布")

        # 5. 船票价格箱线图
        ax = axes[1, 1]
        df["Fare"].plot(kind="box", showmeans=True, notch=True, ax=ax)
        ax.set_title("船票价格分布")

        # 6. 不同性别幸存率
        ax = axes[1, 2]
        survival_by_sex = df.groupby("Sex")["Survived"].mean()
        survival_by_sex.plot(kind="bar", color=["#D84040", "#16404D"], ax=ax)
        ax.set_xticklabels(["女性", "男性"], rotation=0)
        ax.set_title("不同性别幸存率")
        ax.set_ylabel("幸存率")
        for i, v in enumerate(survival_by_sex):
            ax.text(i, v, f"{v:.2%}", ha="center", va="bottom")

        plt.tight_layout()
        plt.savefig("eda_overview.png", bbox_inches="tight")
        plt.show()

    @staticmethod
    def plot_survival_by_features(df: pd.DataFrame) -> None:
        """绘制不同特征维度下的幸存情况。"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6), dpi=150)

        # 不同客舱等级幸存情况
        ax = axes[0]
        surv_by_class = pd.crosstab(df["Pclass"], df["Survived"])
        surv_by_class.columns = ["遇难", "幸存"]
        surv_by_class.plot(kind="bar", stacked=True, color=["#BE3144", "#3A7D44"], ax=ax)
        ax.set_xticklabels(["一等舱", "二等舱", "三等舱"], rotation=0)
        ax.set_title("不同客舱等级幸存情况")
        for idx in surv_by_class.index:
            total = surv_by_class.loc[idx].sum()
            cum = 0
            for col in surv_by_class.columns:
                val = surv_by_class.loc[idx, col]
                pct = val / total
                ax.text(idx - 1, cum + val / 2, f"{pct:.1%}", ha="center", va="center")
                cum += val

        # 不同登船港口幸存情况
        ax = axes[1]
        surv_by_embark = pd.crosstab(df["Embarked"], df["Survived"])
        surv_by_embark.columns = ["遇难", "幸存"]
        surv_by_embark.plot(kind="bar", stacked=True, color=["#BE3144", "#3A7D44"], ax=ax)
        ax.set_title("不同登船港口幸存情况")

        # 年龄与幸存关系（小提琴图替代）
        ax = axes[2]
        survived = df[df["Survived"] == 1]["Age"].dropna()
        not_survived = df[df["Survived"] == 0]["Age"].dropna()
        ax.boxplot(
            [not_survived, survived],
            labels=["遇难", "幸存"],
            showmeans=True,
            notch=True,
        )
        ax.set_title("年龄与幸存关系")
        ax.set_ylabel("年龄")

        plt.tight_layout()
        plt.savefig("eda_survival_features.png", bbox_inches="tight")
        plt.show()

    @staticmethod
    def correlation_heatmap(df: pd.DataFrame) -> None:
        """绘制数值特征相关性热力图。"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        corr = df[numeric_cols].corr()

        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        im = ax.imshow(corr, cmap="RdYlGn", aspect="auto", vmin=-1, vmax=1)

        ax.set_xticks(range(len(numeric_cols)))
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha="right")
        ax.set_yticklabels(numeric_cols)

        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)

        fig.colorbar(im, ax=ax, shrink=0.8)
        ax.set_title("数值特征相关性矩阵")
        plt.tight_layout()
        plt.savefig("eda_correlation.png", bbox_inches="tight")
        plt.show()


# ---------------------------------------------------------------------------
# 特征工程
# ---------------------------------------------------------------------------


class FeatureEngineer:
    """特征工程处理器。

    处理流程:
    1. 缺失值处理
    2. 特征转换（标准化、编码）
    3. 特征构造（衍生新特征）
    4. 特征筛选
    """

    def __init__(self) -> None:
        self.scaler: StandardScaler = StandardScaler()
        self._is_fitted: bool = False

    def fit_transform(self, df: pd.DataFrame, is_train: bool = True) -> pd.DataFrame:
        """对数据进行特征工程处理。

        Args:
            df: 原始数据 DataFrame。
            is_train: 是否为训练数据。训练数据会 fit scaler，测试数据只 transform。

        Returns:
            处理后的 DataFrame。
        """
        df = df.copy()

        # 步骤 1: 处理缺失值
        df = self._handle_missing_values(df)

        # 步骤 2: 特征转换
        df = self._encode_categorical(df)
        df = self._scale_numeric(df, fit=is_train)

        # 步骤 3: 特征构造
        df = self._engineer_title(df)
        df = self._engineer_family(df)

        # 步骤 4: 删除原始文本列
        df = self._drop_raw_columns(df)

        return df

    @staticmethod
    def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值。

        策略:
        - Age: 中位数填充
        - Fare: 中位数填充
        - Embarked: 众数填充
        - Cabin: 二值化（有值为1，缺失为0）
        """
        df["Age"] = df["Age"].fillna(df["Age"].median())
        df["Fare"] = df["Fare"].fillna(df["Fare"].median())
        df["Embarked"] = df["Embarked"].fillna(df["Embarked"].mode()[0])
        df["Cabin"] = df["Cabin"].replace(r".+", "1", regex=True).replace(np.nan, 0).astype("int64")
        return df

    @staticmethod
    def _encode_categorical(df: pd.DataFrame) -> pd.DataFrame:
        """对分类变量进行独热编码。"""
        df = pd.get_dummies(df, columns=["Sex", "Embarked"], drop_first=True)
        return df

    def _scale_numeric(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """对数值特征进行标准化。"""
        cols = ["Fare", "Age"]
        if fit:
            df[cols] = self.scaler.fit_transform(df[cols])
            self._is_fitted = True
        else:
            if not self._is_fitted:
                raise RuntimeError("Scaler 尚未 fit，请先对训练数据调用 fit_transform")
            df[cols] = self.scaler.transform(df[cols])
        return df

    @staticmethod
    def _engineer_title(df: pd.DataFrame) -> pd.DataFrame:
        """从乘客姓名中提取称谓并编码。"""
        df["Title"] = (
            df["Name"]
            .apply(lambda x: x.split(",")[1].split(".")[0].strip())
            .map(TITLE_MAPPING)
            .fillna(-1)
        )
        return df

    @staticmethod
    def _engineer_family(df: pd.DataFrame) -> pd.DataFrame:
        """构造家庭规模特征。"""
        df["FamilySize"] = df["SibSp"] + df["Parch"] + 1
        return df

    @staticmethod
    def _drop_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
        """删除不再需要的原始文本列。"""
        drop_cols = ["Name", "SibSp", "Parch", "Ticket"]
        existing = [c for c in drop_cols if c in df.columns]
        df.drop(columns=existing, inplace=True)
        return df


# ---------------------------------------------------------------------------
# 模型训练与评估
# ---------------------------------------------------------------------------


class ModelTrainer:
    """模型训练器，支持多种算法的训练和评估。"""

    @staticmethod
    def get_models() -> Dict[str, BaseEstimator]:
        """返回候选模型字典。"""
        return {
            "LogisticRegression": LogisticRegression(
                penalty="l1",
                tol=1e-6,
                solver="liblinear",
                max_iter=1000,
                random_state=42,
            ),
            "RandomForest": RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,
            ),
            "GradientBoosting": GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            ),
        }

    @staticmethod
    def evaluate_model(
        model: BaseEstimator,
        X_valid: pd.DataFrame,
        y_valid: pd.Series,
    ) -> ModelMetrics:
        """评估模型在验证集上的表现。

        Args:
            model: 已训练的模型。
            X_valid: 验证集特征。
            y_valid: 验证集标签。

        Returns:
            包含各项指标的 ModelMetrics 对象。
        """
        y_pred = model.predict(X_valid)
        y_proba = model.predict_proba(X_valid)[:, 1] if hasattr(model, "predict_proba") else y_pred.astype(float)

        return ModelMetrics(
            accuracy=accuracy_score(y_valid, y_pred),
            precision=precision_score(y_valid, y_pred, zero_division=0),
            recall=recall_score(y_valid, y_pred, zero_division=0),
            f1=f1_score(y_valid, y_pred, zero_division=0),
            roc_auc=roc_auc_score(y_valid, y_proba),
            confusion_matrix=confusion_matrix(y_valid, y_pred),
        )

    @staticmethod
    def cross_validate_model(
        model: BaseEstimator,
        X: pd.DataFrame,
        y: pd.Series,
        cv: int = 5,
    ) -> Dict[str, float]:
        """对模型进行交叉验证。

        Args:
            model: 模型实例。
            X: 特征数据。
            y: 标签数据。
            cv: 折数。

        Returns:
            包含均值和标准差的字典。
        """
        scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
        return {
            "mean_accuracy": scores.mean(),
            "std_accuracy": scores.std(),
            "scores": scores.tolist(),
        }


# ---------------------------------------------------------------------------
# 完整 ML 流水线
# ---------------------------------------------------------------------------


class MLPipeline:
    """端到端机器学习流水线。

    整合数据加载、特征工程、模型训练、评估与持久化。
    """

    def __init__(
        self,
        data_dir: str = "data",
        model_output: str = "model.pkl",
        scaler_output: str = "scaler.pkl",
    ) -> None:
        self.data_loader = DataLoader(data_dir)
        self.feature_engineer = FeatureEngineer()
        self.trainer = ModelTrainer()
        self.model_output = Path(model_output)
        self.scaler_output = Path(scaler_output)

        self.train_df: Optional[pd.DataFrame] = None
        self.test_df: Optional[pd.DataFrame] = None
        self.best_model: Optional[BaseEstimator] = None
        self.best_model_name: str = ""
        self.results: List[PipelineResult] = []

    def run(self) -> List[PipelineResult]:
        """执行完整的 ML 流水线。

        Returns:
            各模型的评估结果列表。
        """
        logger.info("=" * 60)
        logger.info("开始执行 ML 流水线")
        logger.info("=" * 60)

        # 1. 加载数据
        self.train_df = self.data_loader.load_train()
        self.data_loader.data_overview(self.train_df)

        # 2. 探索性分析（可选，生产中可跳过）
        self._run_eda()

        # 3. 特征工程
        logger.info("执行特征工程...")
        processed_df = self.feature_engineer.fit_transform(self.train_df, is_train=True)

        # 分离特征和标签
        X = processed_df.drop(columns=["Survived"])
        y = processed_df["Survived"]

        # 4. 划分训练集和验证集
        X_train, X_valid, y_train, y_valid = train_test_split(
            X, y, train_size=0.9, random_state=42, stratify=y
        )
        logger.info("训练集大小: %d, 验证集大小: %d", len(X_train), len(X_valid))

        # 5. 训练和评估多个模型
        models = self.trainer.get_models()
        best_f1 = -1.0

        for name, model in models.items():
            logger.info("训练模型: %s", name)
            model.fit(X_train, y_train)

            # 评估
            metrics = self.trainer.evaluate_model(model, X_valid, y_valid)
            logger.info("\n%s 评估结果:\n%s", name, metrics.summary())

            # 交叉验证
            cv_result = self.trainer.cross_validate_model(model, X, y, cv=5)
            logger.info(
                "%s 交叉验证: mean=%.4f, std=%.4f",
                name,
                cv_result["mean_accuracy"],
                cv_result["std_accuracy"],
            )

            result = PipelineResult(
                model_name=name,
                metrics=metrics,
                model=model,
                scaler=self.feature_engineer.scaler,
            )
            self.results.append(result)

            # 跟踪最佳模型
            if metrics.f1 > best_f1:
                best_f1 = metrics.f1
                self.best_model = model
                self.best_model_name = name

        logger.info("最佳模型: %s (F1=%.4f)", self.best_model_name, best_f1)

        # 6. 持久化最佳模型
        self._save_artifacts()

        # 7. 对测试集进行预测
        self._predict_test()

        return self.results

    def _run_eda(self) -> None:
        """运行探索性数据分析（仅在训练数据上）。"""
        if self.train_df is None:
            return

        try:
            ExploratoryAnalysis.setup_chinese_font()
            ExploratoryAnalysis.plot_survival_distribution(self.train_df)
            ExploratoryAnalysis.plot_survival_by_features(self.train_df)
            ExploratoryAnalysis.correlation_heatmap(self.train_df)
        except Exception as e:
            logger.warning("EDA 可视化跳过（可能缺少图形环境）: %s", e)

    def _save_artifacts(self) -> None:
        """保存模型和 scaler 到磁盘。"""
        if self.best_model is None:
            return

        joblib.dump(self.best_model, self.model_output)
        joblib.dump(self.feature_engineer.scaler, self.scaler_output)
        logger.info("模型已保存到: %s", self.model_output)
        logger.info("Scaler 已保存到: %s", self.scaler_output)

    def _predict_test(self) -> None:
        """对测试集进行预测并生成提交文件。"""
        if self.best_model is None:
            return

        try:
            self.test_df = self.data_loader.load_test()
        except FileNotFoundError:
            logger.warning("测试数据文件不存在，跳过测试集预测")
            return

        # 对测试数据执行相同的特征工程
        processed_test = self.feature_engineer.fit_transform(self.test_df, is_train=False)

        # 确保测试集包含所有训练特征
        train_features = [c for c in self.results[0].model.feature_names_in_ if c != "Survived"]
        for col in train_features:
            if col not in processed_test.columns:
                processed_test[col] = 0
        processed_test = processed_test[train_features]

        # 预测
        y_pred = self.best_model.predict(processed_test)

        # 生成提交文件
        submission = pd.DataFrame({
            "PassengerId": self.test_df.index,
            "Survived": y_pred,
        })
        submission_path = "submission.csv"
        submission.to_csv(submission_path, index=False)
        logger.info("预测结果已保存到: %s", submission_path)


# ---------------------------------------------------------------------------
# 模型持久化与预测 API
# ---------------------------------------------------------------------------


class ModelSerializer:
    """模型序列化与反序列化工具。"""

    @staticmethod
    def save(model: Any, filepath: str | Path) -> Path:
        """将模型序列化保存到文件。

        Args:
            model: 训练好的模型对象。
            filepath: 保存路径。

        Returns:
            保存的文件路径。
        """
        path = Path(filepath)
        joblib.dump(model, path)
        logger.info("模型已保存: %s", path)
        return path

    @staticmethod
    def load(filepath: str | Path) -> Any:
        """从文件加载模型。

        Args:
            filepath: 模型文件路径。

        Returns:
            反序列化后的模型对象。
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"模型文件不存在: {path}")
        model = joblib.load(path)
        logger.info("模型已加载: %s", path)
        return model


class PredictionService:
    """预测服务，封装模型加载与预测逻辑。

    可用于 Web API 或其他应用场景。
    """

    def __init__(
        self,
        model_path: str = "model.pkl",
        scaler_path: str = "scaler.pkl",
    ) -> None:
        self.model_path = model_path
        self.scaler_path = scaler_path
        self._model: Optional[Any] = None
        self._scaler: Optional[StandardScaler] = None
        self._feature_engineer: FeatureEngineer = FeatureEngineer()

    def load_model(self) -> None:
        """预加载模型和 scaler（应在服务启动时调用）。"""
        self._model = ModelSerializer.load(self.model_path)
        self._scaler = ModelSerializer.load(self.scaler_path)
        self._feature_engineer.scaler = self._scaler
        self._feature_engineer._is_fitted = True
        logger.info("预测服务已就绪")

    def predict(self, passenger_data: Dict[str, Any]) -> Dict[str, Any]:
        """对单个乘客数据进行预测。

        Args:
            passenger_data: 乘客特征字典，应包含以下键:
                - Pclass: int (1/2/3)
                - Name: str
                - Sex: str ('male'/'female')
                - Age: float
                - SibSp: int
                - Parch: int
                - Ticket: str
                - Fare: float
                - Cabin: str
                - Embarked: str ('C'/'Q'/'S')

        Returns:
            包含预测结果和概率的字典。
        """
        if self._model is None:
            raise RuntimeError("模型未加载，请先调用 load_model()")

        # 构造 DataFrame
        df = pd.DataFrame([passenger_data])

        # 特征工程
        processed = self._feature_engineer.fit_transform(df, is_train=False)

        # 确保特征列匹配
        if hasattr(self._model, "feature_names_in_"):
            for col in self._model.feature_names_in_:
                if col not in processed.columns:
                    processed[col] = 0
            processed = processed[list(self._model.feature_names_in_)]

        # 预测
        prediction = int(self._model.predict(processed)[0])
        probability = None
        if hasattr(self._model, "predict_proba"):
            proba = self._model.predict_proba(processed)[0]
            probability = {
                "not_survived": round(float(proba[0]), 4),
                "survived": round(float(proba[1]), 4),
            }

        return {
            "prediction": prediction,
            "label": "幸存" if prediction == 1 else "遇难",
            "probability": probability,
        }

    def predict_batch(self, passengers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量预测。

        Args:
            passengers: 乘客数据列表。

        Returns:
            预测结果列表。
        """
        return [self.predict(p) for p in passengers]


def create_flask_app(prediction_service: PredictionService) -> Any:
    """创建 Flask 预测 API 应用。

    Args:
        prediction_service: 已加载模型的预测服务实例。

    Returns:
        Flask 应用实例。
    """
    try:
        from flask import Flask, jsonify, request
    except ImportError:
        logger.error("Flask 未安装，请运行: pip install flask")
        raise

    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health() -> tuple:
        return jsonify({"status": "healthy", "model_loaded": prediction_service._model is not None}), 200

    @app.route("/predict", methods=["POST"])
    def predict() -> tuple:
        """单条预测接口。

        请求体示例:
        {
            "Pclass": 3,
            "Name": "Braund, Mr. Owen Harris",
            "Sex": "male",
            "Age": 22.0,
            "SibSp": 1,
            "Parch": 0,
            "Ticket": "A/5 21171",
            "Fare": 7.25,
            "Cabin": null,
            "Embarked": "S"
        }
        """
        try:
            data = request.get_json(force=True)
            result = prediction_service.predict(data)
            return jsonify({"status": "OK", "result": result}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route("/predict/batch", methods=["POST"])
    def predict_batch() -> tuple:
        """批量预测接口。

        请求体示例:
        [
            {"Pclass": 3, "Name": "...", ...},
            {"Pclass": 1, "Name": "...", ...}
        ]
        """
        try:
            data = request.get_json(force=True)
            if not isinstance(data, list):
                return jsonify({"status": "error", "message": "请求体必须是数组"}), 400
            results = prediction_service.predict_batch(data)
            return jsonify({"status": "OK", "results": results}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    return app


def create_fastapi_app(prediction_service: PredictionService) -> Any:
    """创建 FastAPI 预测 API 应用（需安装 fastapi 和 uvicorn）。

    Args:
        prediction_service: 已加载模型的预测服务实例。

    Returns:
        FastAPI 应用实例。
    """
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
    except ImportError:
        logger.error("FastAPI 未安装，请运行: pip install fastapi uvicorn")
        raise

    app = FastAPI(title="Titanic Survival Prediction API", version="1.0.0")

    class PassengerRequest(BaseModel):
        Pclass: int
        Name: str
        Sex: str
        Age: float
        SibSp: int = 0
        Parch: int = 0
        Ticket: str = ""
        Fare: float = 0.0
        Cabin: Optional[str] = None
        Embarked: str = "S"

    class BatchRequest(BaseModel):
        passengers: List[PassengerRequest]

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy", "model_loaded": prediction_service._model is not None}

    @app.post("/predict")
    async def predict_single(passenger: PassengerRequest) -> dict:
        try:
            result = prediction_service.predict(passenger.model_dump())
            return {"status": "OK", "result": result}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/predict/batch")
    async def predict_batch_endpoint(batch: BatchRequest) -> dict:
        try:
            data = [p.model_dump() for p in batch.passengers]
            results = prediction_service.predict_batch(data)
            return {"status": "OK", "results": results}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app


# ---------------------------------------------------------------------------
# 演示与测试
# ---------------------------------------------------------------------------


def demo_without_data() -> None:
    """无需数据文件的演示：使用 sklearn 内置数据集演示完整流程。"""
    from sklearn.datasets import load_breast_cancer

    logger.info("=" * 60)
    logger.info("演示模式: 使用乳腺癌数据集")
    logger.info("=" * 60)

    # 加载数据
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name="target")

    # 划分数据集
    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 标准化
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X.columns, index=X_train.index)
    X_valid_scaled = pd.DataFrame(scaler.transform(X_valid), columns=X.columns, index=X_valid.index)

    # 训练模型
    models = ModelTrainer.get_models()
    best_f1 = -1.0
    best_model = None
    best_name = ""

    for name, model in models.items():
        logger.info("训练: %s", name)
        model.fit(X_train_scaled, y_train)
        metrics = ModelTrainer.evaluate_model(model, X_valid_scaled, y_valid)
        logger.info("%s:\n%s", name, metrics.summary())

        if metrics.f1 > best_f1:
            best_f1 = metrics.f1
            best_model = model
            best_name = name

    logger.info("最佳模型: %s (F1=%.4f)", best_name, best_f1)

    # 保存模型
    model_path = "demo_model.pkl"
    scaler_path = "demo_scaler.pkl"
    ModelSerializer.save(best_model, model_path)
    ModelSerializer.save(scaler, scaler_path)

    # 加载并预测
    loaded_model = ModelSerializer.load(model_path)
    loaded_scaler = ModelSerializer.load(scaler_path)

    # 模拟预测服务
    sample = X_valid.iloc[:3]
    sample_scaled = pd.DataFrame(loaded_scaler.transform(sample), columns=sample.columns)
    predictions = loaded_model.predict(sample_scaled)
    logger.info("样本预测结果: %s", predictions.tolist())

    # 清理临时文件
    Path(model_path).unlink(missing_ok=True)
    Path(scaler_path).unlink(missing_ok=True)
    logger.info("演示完成")


def demo_prediction_api() -> None:
    """演示预测 API 的使用方式（无需启动服务器）。"""
    logger.info("=" * 60)
    logger.info("预测 API 使用演示")
    logger.info("=" * 60)

    print(
        """
    预测 API 支持两种框架:

    1. Flask:
        service = PredictionService("model.pkl", "scaler.pkl")
        service.load_model()
        app = create_flask_app(service)
        app.run(host="0.0.0.0", port=5000)

    2. FastAPI:
        service = PredictionService("model.pkl", "scaler.pkl")
        service.load_model()
        app = create_fastapi_app(service)
        # 运行: uvicorn module:app --host 0.0.0.0 --port 8000

    请求示例 (POST /predict):
        {
            "Pclass": 3,
            "Name": "Braund, Mr. Owen Harris",
            "Sex": "male",
            "Age": 22.0,
            "SibSp": 1,
            "Parch": 0,
            "Ticket": "A/5 21171",
            "Fare": 7.25,
            "Cabin": null,
            "Embarked": "S"
        }
    """
    )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def main() -> None:
    """主函数：根据数据文件是否存在选择执行模式。"""
    import argparse

    parser = argparse.ArgumentParser(description="泰坦尼克号生存预测 - ML 实战")
    parser.add_argument(
        "--mode",
        choices=["full", "demo", "api"],
        default="auto",
        help="运行模式: full=完整流水线, demo=演示模式, api=API示例",
    )
    parser.add_argument("--data-dir", default="data", help="数据文件目录")
    parser.add_argument("--model-output", default="model.pkl", help="模型保存路径")
    args = parser.parse_args()

    if args.mode == "api":
        demo_prediction_api()
        return

    if args.mode == "demo":
        demo_without_data()
        return

    # 自动检测数据文件
    data_path = Path(args.data_dir)
    train_exists = (data_path / "train.csv").exists()

    if args.mode == "full" or (args.mode == "auto" and train_exists):
        pipeline = MLPipeline(
            data_dir=args.data_dir,
            model_output=args.model_output,
        )
        results = pipeline.run()

        print("\n" + "=" * 60)
        print("模型比较结果")
        print("=" * 60)
        for r in results:
            print(f"\n{r.model_name}:")
            print(f"  Accuracy:  {r.metrics.accuracy:.4f}")
            print(f"  Precision: {r.metrics.precision:.4f}")
            print(f"  Recall:    {r.metrics.recall:.4f}")
            print(f"  F1-Score:  {r.metrics.f1:.4f}")
            print(f"  ROC-AUC:   {r.metrics.roc_auc:.4f}")
    else:
        logger.info("未找到训练数据，切换到演示模式")
        demo_without_data()


if __name__ == "__main__":
    main()
