"""
朴素贝叶斯算法 (Naive Bayes Algorithm)
=====================================

朴素贝叶斯算法是基于贝叶斯定理和特征条件独立性假设的分类算法，
因其简单高效而受到广泛应用。

本文件涵盖：
1. 贝叶斯定理基础
2. 手动实现朴素贝叶斯分类器
3. scikit-learn 的 GaussianNB、MultinomialNB、BernoulliNB
4. 文本分类应用
5. 企业级应用示例（垃圾邮件过滤、情感分析、文档分类）
6. C++ 对比：朴素贝叶斯概率计算 vs C++ 贝叶斯推断
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from collections import defaultdict
import re
import math


# ============================================================================
# 第一部分：贝叶斯定理基础
# ============================================================================

class BayesTheorem:
    """
    贝叶斯定理计算器

    贝叶斯定理公式：
    P(A|B) = P(B|A) * P(A) / P(B)

    其中：
    - P(A) 是先验概率（prior probability）
    - P(B|A) 是似然性（likelihood）
    - P(B) 是证据（evidence）
    - P(A|B) 是后验概率（posterior probability）
    """

    @staticmethod
    def calculate_posterior(
        prior: float,
        likelihood: float,
        evidence: float
    ) -> float:
        """
        计算后验概率

        Args:
            prior: 先验概率 P(A)
            likelihood: 似然性 P(B|A)
            evidence: 证据 P(B)

        Returns:
            后验概率 P(A|B)
        """
        if evidence == 0:
            raise ValueError("证据概率 P(B) 不能为零")
        return (likelihood * prior) / evidence

    @staticmethod
    def flight_delay_example() -> Dict[str, float]:
        """
        航班延误险示例

        假设历史数据：
        - 航班延误的先验概率 P(延误) = 0.15
        - 小雨天气时延误的似然性 P(小雨|延误) = 0.6
        - 小雨天气的全概率 P(小雨) = 0.25

        返回:
            包含各概率值的字典
        """
        # 先验概率：航班延误的历史概率
        p_delay: float = 0.15

        # 似然性：延误时出现小雨的概率
        p_rain_given_delay: float = 0.6

        # 证据：出现小雨的全概率
        p_rain: float = 0.25

        # 计算后验概率：小雨时延误的概率
        p_delay_given_rain: float = BayesTheorem.calculate_posterior(
            prior=p_delay,
            likelihood=p_rain_given_delay,
            evidence=p_rain
        )

        return {
            "先验概率 P(延误)": p_delay,
            "似然性 P(小雨|延误)": p_rain_given_delay,
            "证据 P(小雨)": p_rain,
            "后验概率 P(延误|小雨)": p_delay_given_rain
        }


# ============================================================================
# 第二部分：手动实现朴素贝叶斯分类器
# ============================================================================

class SimpleNaiveBayes:
    """
    简单朴素贝叶斯分类器实现

    朴素贝叶斯假设：
    P(X|C) = P(x1|C) * P(x2|C) * ... * P(xn|C)

    这个假设大大简化了计算复杂性
    """

    def __init__(self, n_bins: int = 5):
        """
        初始化分类器

        Args:
            n_bins: 特征离散化的分箱数量
        """
        self.n_bins: int = n_bins
        self.prior_probs: Optional[pd.Series] = None
        self.likelihoods: Optional[Dict[Tuple[int, int, float], float]] = None
        self.bin_edges: Optional[List[np.ndarray]] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'SimpleNaiveBayes':
        """
        训练朴素贝叶斯分类器

        Args:
            X: 训练样本特征，形状 (n_samples, n_features)
            y: 训练样本标签，形状 (n_samples,)

        Returns:
            self
        """
        # 计算先验概率
        clazz_labels, clazz_counts = np.unique(y, return_counts=True)
        self.prior_probs = pd.Series(
            {k: v / y.size for k, v in zip(clazz_labels, clazz_counts)}
        )

        # 拷贝数组创建副本
        X = np.copy(X)

        # 保存似然性计算结果的字典
        self.likelihoods = {}
        self.bin_edges = []

        for j in range(X.shape[1]):
            # 对特征进行等宽分箱（离散化处理）
            binned = pd.cut(X[:, j], bins=self.n_bins, labels=np.arange(1, self.n_bins + 1))
            X[:, j] = binned
            self.bin_edges.append(np.linspace(X[:, j].min(), X[:, j].max(), self.n_bins + 1))

            for i in self.prior_probs.index:
                # 按标签类别拆分数据并统计每个特征值出现的频次
                x_prime = X[y == i, j]
                x_values, x_counts = np.unique(x_prime, return_counts=True)
                for k, value in enumerate(x_values):
                    # 计算似然性并保存在字典中
                    self.likelihoods[(i, j, value)] = x_counts[k] / x_prime.size

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测样本类别

        Args:
            X: 待预测样本特征，形状 (n_samples, n_features)

        Returns:
            预测的类别标签数组
        """
        if self.prior_probs is None or self.likelihoods is None:
            raise ValueError("模型尚未训练，请先调用 fit() 方法")

        # 对特征进行等宽分箱（离散化处理）
        X = np.copy(X)
        for j in range(X.shape[1]):
            X[:, j] = pd.cut(X[:, j], bins=self.n_bins, labels=np.arange(1, self.n_bins + 1))

        # 保存每个样本对应每个类别后验概率的二维数组
        results = np.zeros((X.shape[0], self.prior_probs.size))
        clazz_labels = self.prior_probs.index.values

        for k in range(X.shape[0]):
            for i, label in enumerate(clazz_labels):
                # 获得先验概率（训练的结果）
                prob = self.prior_probs.loc[label]
                # 计算获得特征数据后的后验概率
                for j in range(X.shape[1]):
                    # 如果没有对应的似然性就取值为0
                    prob *= self.likelihoods.get((i, j, X[k, j]), 0)
                results[k, i] = prob

        # 根据每个样本对应类别最大的概率选择预测标签
        return clazz_labels[results.argmax(axis=1)]


# ============================================================================
# 第三部分：scikit-learn 朴素贝叶斯变体
# ============================================================================

def demonstrate_gaussian_nb() -> Dict[str, Any]:
    """
    高斯朴素贝叶斯示例

    适用于连续特征，假设特征服从高斯分布（正态分布）

    Returns:
        包含模型评估结果的字典
    """
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.naive_bayes import GaussianNB
    from sklearn.metrics import classification_report, accuracy_score

    # 加载鸢尾花数据集
    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=0.8, random_state=3
    )

    # 创建高斯朴素贝叶斯模型
    model = GaussianNB()
    model.fit(X_train, y_train)

    # 预测
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    return {
        "model_name": "GaussianNB",
        "accuracy": accuracy_score(y_test, y_pred),
        "classification_report": classification_report(y_test, y_pred),
        "predict_proba_sample": y_proba[:5].round(3),
        "feature_names": iris.feature_names,
        "target_names": iris.target_names.tolist()
    }


def demonstrate_multinomial_nb() -> Dict[str, Any]:
    """
    多项式朴素贝叶斯示例

    适用于计数特征（如词频），常用于文本分类

    Returns:
        包含模型评估结果的字典
    """
    from sklearn.datasets import fetch_20newsgroups
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.model_selection import train_test_split

    # 加载新闻组数据集（选取部分类别）
    categories = ['alt.atheism', 'sci.space', 'comp.graphics', 'rec.sport.baseball']
    newsgroups = fetch_20newsgroups(
        subset='all',
        categories=categories,
        remove=('headers', 'footers', 'quotes')
    )

    # TF-IDF 向量化
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    X = vectorizer.fit_transform(newsgroups.data)
    y = newsgroups.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 创建多项式朴素贝叶斯模型
    model = MultinomialNB(alpha=1.0)  # alpha 是拉普拉斯平滑参数
    model.fit(X_train, y_train)

    # 预测
    y_pred = model.predict(X_test)

    return {
        "model_name": "MultinomialNB",
        "categories": categories,
        "accuracy": accuracy_score(y_test, y_pred),
        "classification_report": classification_report(
            y_test, y_pred, target_names=categories
        ),
        "vocabulary_size": len(vectorizer.vocabulary_),
        "feature_names_sample": vectorizer.get_feature_names_out()[:20].tolist()
    }


def demonstrate_bernoulli_nb() -> Dict[str, Any]:
    """
    伯努利朴素贝叶斯示例

    适用于二元特征（0/1），适用于文本分类中的二值化特征

    Returns:
        包含模型评估结果的字典
    """
    from sklearn.datasets import fetch_20newsgroups
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.naive_bayes import BernoulliNB
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.model_selection import train_test_split

    # 加载新闻组数据集
    categories = ['alt.atheism', 'sci.space']
    newsgroups = fetch_20newsgroups(
        subset='all',
        categories=categories,
        remove=('headers', 'footers', 'quotes')
    )

    # 二值化词频向量化
    vectorizer = CountVectorizer(
        max_features=3000,
        stop_words='english',
        binary=True  # 二值化
    )
    X = vectorizer.fit_transform(newsgroups.data)
    y = newsgroups.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 创建伯努利朴素贝叶斯模型
    model = BernoulliNB(alpha=1.0)
    model.fit(X_train, y_train)

    # 预测
    y_pred = model.predict(X_test)

    return {
        "model_name": "BernoulliNB",
        "categories": categories,
        "accuracy": accuracy_score(y_test, y_pred),
        "classification_report": classification_report(
            y_test, y_pred, target_names=categories
        ),
        "vocabulary_size": len(vectorizer.vocabulary_)
    }


# ============================================================================
# 第四部分：文本分类应用
# ============================================================================

class TextClassifier:
    """
    基于朴素贝叶斯的文本分类器

    支持垃圾邮件过滤、情感分析、文档分类等任务
    """

    def __init__(self, alpha: float = 1.0):
        """
        初始化文本分类器

        Args:
            alpha: 拉普拉斯平滑参数，防止零概率问题
        """
        self.alpha: float = alpha
        self.vocabulary: Dict[str, int] = {}
        self.class_priors: Dict[str, float] = {}
        self.word_likelihoods: Dict[str, Dict[str, float]] = {}
        self.classes: List[str] = []

    def _tokenize(self, text: str) -> List[str]:
        """
        文本分词

        Args:
            text: 输入文本

        Returns:
            分词结果列表
        """
        # 简单分词：转小写，去除标点，按空格分割
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()

    def fit(self, texts: List[str], labels: List[str]) -> 'TextClassifier':
        """
        训练文本分类器

        Args:
            texts: 训练文本列表
            labels: 对应的类别标签列表

        Returns:
            self
        """
        # 统计每个类别的文档数和词频
        class_doc_counts: Dict[str, int] = defaultdict(int)
        class_word_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        all_words: set = set()

        for text, label in zip(texts, labels):
            class_doc_counts[label] += 1
            words = self._tokenize(text)
            for word in words:
                class_word_counts[label][word] += 1
                all_words.add(word)

        # 建立词汇表
        self.vocabulary = {word: idx for idx, word in enumerate(sorted(all_words))}

        # 计算先验概率
        total_docs = len(texts)
        self.classes = list(class_doc_counts.keys())
        self.class_priors = {
            cls: count / total_docs
            for cls, count in class_doc_counts.items()
        }

        # 计算似然性（带拉普拉斯平滑）
        vocab_size = len(self.vocabulary)
        for cls in self.classes:
            total_words_in_class = sum(class_word_counts[cls].values())
            self.word_likelihoods[cls] = {}

            for word in self.vocabulary:
                word_count = class_word_counts[cls].get(word, 0)
                # 拉普拉斯平滑
                self.word_likelihoods[cls][word] = (
                    (word_count + self.alpha) /
                    (total_words_in_class + self.alpha * vocab_size)
                )

        return self

    def predict(self, text: str) -> Tuple[str, Dict[str, float]]:
        """
        预测文本类别

        Args:
            text: 待分类文本

        Returns:
            (预测类别, 各类别概率字典)
        """
        words = self._tokenize(text)
        class_scores: Dict[str, float] = {}

        for cls in self.classes:
            # 使用对数概率避免下溢
            score = math.log(self.class_priors[cls])

            for word in words:
                if word in self.vocabulary:
                    score += math.log(self.word_likelihoods[cls][word])

            class_scores[cls] = score

        # 转换为概率（softmax）
        max_score = max(class_scores.values())
        exp_scores = {cls: math.exp(score - max_score) for cls, score in class_scores.items()}
        total = sum(exp_scores.values())
        probabilities = {cls: score / total for cls, score in exp_scores.items()}

        predicted_class = max(probabilities, key=probabilities.get)
        return predicted_class, probabilities


# ============================================================================
# 第五部分：企业级应用示例
# ============================================================================

class SpamFilter:
    """
    垃圾邮件过滤器

    使用朴素贝叶斯算法进行垃圾邮件检测
    """

    def __init__(self):
        """初始化垃圾邮件过滤器"""
        self.classifier = TextClassifier(alpha=1.0)
        self.is_trained: bool = False

    def train(self, emails: List[str], labels: List[str]) -> None:
        """
        训练垃圾邮件过滤器

        Args:
            emails: 邮件内容列表
            labels: 标签列表（'spam' 或 'ham'）
        """
        self.classifier.fit(emails, labels)
        self.is_trained = True

    def classify(self, email: str) -> Dict[str, Any]:
        """
        分类邮件

        Args:
            email: 邮件内容

        Returns:
            分类结果字典
        """
        if not self.is_trained:
            raise ValueError("过滤器尚未训练")

        predicted_class, probabilities = self.classifier.predict(email)

        return {
            "is_spam": predicted_class == "spam",
            "confidence": probabilities.get("spam", 0.0),
            "spam_probability": probabilities.get("spam", 0.0),
            "ham_probability": probabilities.get("ham", 0.0)
        }


class SentimentAnalyzer:
    """
    情感分析器

    使用朴素贝叶斯算法进行文本情感分析
    """

    def __init__(self):
        """初始化情感分析器"""
        self.classifier = TextClassifier(alpha=1.0)
        self.is_trained: bool = False

    def train(self, texts: List[str], sentiments: List[str]) -> None:
        """
        训练情感分析器

        Args:
            texts: 文本列表
            sentiments: 情感标签列表（'positive', 'negative', 'neutral'）
        """
        self.classifier.fit(texts, sentiments)
        self.is_trained = True

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        分析文本情感

        Args:
            text: 待分析文本

        Returns:
            情感分析结果字典
        """
        if not self.is_trained:
            raise ValueError("分析器尚未训练")

        predicted_class, probabilities = self.classifier.predict(text)

        return {
            "sentiment": predicted_class,
            "confidence": max(probabilities.values()),
            "probabilities": probabilities
        }


class DocumentClassifier:
    """
    文档分类器

    使用朴素贝叶斯算法进行文档主题分类
    """

    def __init__(self):
        """初始化文档分类器"""
        self.classifier = TextClassifier(alpha=1.0)
        self.is_trained: bool = False
        self.categories: List[str] = []

    def train(self, documents: List[str], categories: List[str]) -> None:
        """
        训练文档分类器

        Args:
            documents: 文档列表
            categories: 类别标签列表
        """
        self.classifier.fit(documents, categories)
        self.categories = list(set(categories))
        self.is_trained = True

    def classify(self, document: str) -> Dict[str, Any]:
        """
        分类文档

        Args:
            document: 待分类文档

        Returns:
            分类结果字典
        """
        if not self.is_trained:
            raise ValueError("分类器尚未训练")

        predicted_class, probabilities = self.classifier.predict(document)

        return {
            "category": predicted_class,
            "confidence": max(probabilities.values()),
            "all_probabilities": probabilities
        }


def demonstrate_spam_filter() -> Dict[str, Any]:
    """
    演示垃圾邮件过滤器

    Returns:
        演示结果字典
    """
    # 训练数据
    train_emails = [
        "Get rich quick! Make money fast! Click here now!",
        "Congratulations! You've won a free iPhone! Claim now!",
        "URGENT: Your account has been compromised. Verify immediately!",
        "Buy cheap medications online! Best prices guaranteed!",
        "Free gift card! Limited time offer! Act now!",
        "Meeting at 3pm tomorrow in the conference room.",
        "Please review the attached report before Friday.",
        "Can we reschedule our lunch to next week?",
        "The project deadline has been extended to next month.",
        "Thank you for your application. We will review it shortly.",
    ]
    train_labels = ["spam", "spam", "spam", "spam", "spam",
                    "ham", "ham", "ham", "ham", "ham"]

    # 创建并训练过滤器
    spam_filter = SpamFilter()
    spam_filter.train(train_emails, train_labels)

    # 测试邮件
    test_emails = [
        "You have won a lottery! Claim your prize now!",
        "Please find the meeting notes attached.",
        "Limited time offer! Buy now and save 50%!",
        "Let's discuss the project timeline tomorrow.",
    ]

    results = []
    for email in test_emails:
        result = spam_filter.classify(email)
        results.append({
            "email": email[:50] + "..." if len(email) > 50 else email,
            "is_spam": result["is_spam"],
            "confidence": f"{result['confidence']:.2%}"
        })

    return {
        "model": "SpamFilter",
        "test_results": results
    }


def demonstrate_sentiment_analysis() -> Dict[str, Any]:
    """
    演示情感分析器

    Returns:
        演示结果字典
    """
    # 训练数据
    train_texts = [
        "This product is amazing! Best purchase ever!",
        "I love this service. Highly recommended!",
        "Excellent quality and fast delivery!",
        "Great experience, will definitely buy again!",
        "The best restaurant in town!",
        "Terrible product. Complete waste of money.",
        "Worst customer service I've ever experienced.",
        "Very disappointed with the quality.",
        "Would not recommend to anyone.",
        "Awful experience. Never coming back.",
    ]
    train_sentiments = [
        "positive", "positive", "positive", "positive", "positive",
        "negative", "negative", "negative", "negative", "negative"
    ]

    # 创建并训练分析器
    analyzer = SentimentAnalyzer()
    analyzer.train(train_texts, train_sentiments)

    # 测试文本
    test_texts = [
        "Really happy with this purchase!",
        "Not worth the price at all.",
        "It's okay, nothing special.",
    ]

    results = []
    for text in test_texts:
        result = analyzer.analyze(text)
        results.append({
            "text": text,
            "sentiment": result["sentiment"],
            "confidence": f"{result['confidence']:.2%}"
        })

    return {
        "model": "SentimentAnalyzer",
        "test_results": results
    }


def demonstrate_document_classification() -> Dict[str, Any]:
    """
    演示文档分类器

    Returns:
        演示结果字典
    """
    # 训练数据
    train_docs = [
        "The stock market rallied today with tech stocks leading gains.",
        "Federal Reserve announced new interest rate policy.",
        "Company earnings exceeded analyst expectations this quarter.",
        "New smartphone features revolutionary camera technology.",
        "Artificial intelligence transforms healthcare diagnostics.",
        "Latest laptop review shows impressive performance benchmarks.",
        "The team won the championship game in overtime.",
        "Olympic athletes break world records in swimming.",
        "Football season kicks off with exciting matchups.",
        "Basketball playoffs begin next week with top seeds competing.",
    ]
    train_categories = [
        "business", "business", "business",
        "technology", "technology", "technology",
        "sports", "sports", "sports", "sports"
    ]

    # 创建并训练分类器
    classifier = DocumentClassifier()
    classifier.train(train_docs, train_categories)

    # 测试文档
    test_docs = [
        "Stock prices surged after positive economic data release.",
        "New AI chip promises faster processing for machine learning.",
        "The soccer team qualified for the World Cup finals.",
    ]

    results = []
    for doc in test_docs:
        result = classifier.classify(doc)
        results.append({
            "document": doc[:60] + "..." if len(doc) > 60 else doc,
            "category": result["category"],
            "confidence": f"{result['confidence']:.2%}"
        })

    return {
        "model": "DocumentClassifier",
        "test_results": results
    }


# ============================================================================
# 第六部分：C++ 对比 - 朴素贝叶斯概率计算 vs C++ 贝叶斯推断
# ============================================================================

def cpp_comparison_note() -> str:
    """
    C++ 对比说明

    朴素贝叶斯概率计算 vs C++ 贝叶斯推断

    Returns:
        对比说明文本
    """
    return """
========================================================================
C++ 对比：朴素贝叶斯概率计算 vs C++ 贝叶斯推断
========================================================================

Python 朴素贝叶斯实现特点：
----------------------------
1. 动态类型，代码简洁
   - 使用字典存储似然性：likelihoods[(class, feature, value)] = prob
   - 列表推导式和生成器表达式
   - 内置的 math.log 等数学函数

2. 科学计算库支持
   - NumPy 数组操作
   - Pandas 数据处理
   - scikit-learn 预实现的分类器

3. 内存管理
   - 自动垃圾回收
   - 对象引用计数

C++ 贝叶斯推断实现特点：
------------------------
1. 静态类型，性能优化
   - 使用 std::unordered_map 或自定义哈希表
   - 模板元编程优化
   - 内存池分配

2. 数值计算
   - Eigen 库进行矩阵运算
   - 自定义概率分布类
   - 手动内存管理

3. 性能对比
   - Python: 开发效率高，适合原型验证
   - C++: 运行速度快，适合生产环境

C++ 伪代码示例：
--------------
class NaiveBayesCpp {
private:
    std::unordered_map<int, double> priorProbs;
    std::unordered_map<std::tuple<int,int,double>, double> likelihoods;
    int nBins;

public:
    void fit(const Eigen::MatrixXd& X, const Eigen::VectorXi& y) {
        // 计算先验概率
        auto classes = unique(y);
        for (auto cls : classes) {
            priorProbs[cls] = count(y == cls) / y.size();
        }

        // 计算似然性（离散化处理）
        for (int j = 0; j < X.cols(); j++) {
            auto binned = discretize(X.col(j), nBins);
            for (auto cls : classes) {
                auto subset = binned(y == cls);
                auto [values, counts] = uniqueCounts(subset);
                for (int k = 0; k < values.size(); k++) {
                    likelihoods[{cls, j, values[k]}] = counts[k] / subset.size();
                }
            }
        }
    }

    Eigen::VectorXi predict(const Eigen::MatrixXd& X) {
        Eigen::VectorXi predictions(X.rows());
        for (int i = 0; i < X.rows(); i++) {
            double maxProb = -INFINITY;
            int bestClass = -1;
            for (auto& [cls, prior] : priorProbs) {
                double logProb = log(prior);
                for (int j = 0; j < X.cols(); j++) {
                    logProb += log(likelihoods[{cls, j, X(i,j)}]);
                }
                if (logProb > maxProb) {
                    maxProb = logProb;
                    bestClass = cls;
                }
            }
            predictions(i) = bestClass;
        }
        return predictions;
    }
};

性能对比总结：
------------
| 方面              | Python           | C++              |
|-------------------|------------------|------------------|
| 开发效率          | 高               | 低               |
| 运行速度          | 较慢             | 快 (10-100x)    |
| 内存使用          | 较高             | 较低             |
| 适用场景          | 原型/小数据集    | 生产/大数据集    |
| 库支持            | scikit-learn     | 需要手动实现     |
| 并行化            | 多进程           | 多线程/SIMD      |
========================================================================
"""


# ============================================================================
# 第七部分：主程序入口
# ============================================================================

def main() -> None:
    """主函数：演示朴素贝叶斯算法的各种应用"""

    print("=" * 70)
    print("朴素贝叶斯算法演示")
    print("=" * 70)

    # 1. 贝叶斯定理基础
    print("\n[1] 贝叶斯定理 - 航班延误险示例")
    print("-" * 50)
    flight_result = BayesTheorem.flight_delay_example()
    for key, value in flight_result.items():
        print(f"  {key}: {value:.4f}")

    # 2. 手动实现朴素贝叶斯
    print("\n[2] 手动实现朴素贝叶斯分类器 - 鸢尾花数据集")
    print("-" * 50)
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split

    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=0.8, random_state=3
    )

    simple_nb = SimpleNaiveBayes(n_bins=5)
    simple_nb.fit(X_train, y_train)
    y_pred_simple = simple_nb.predict(X_test)

    accuracy_simple = np.mean(y_pred_simple == y_test)
    print(f"  手动实现准确率: {accuracy_simple:.2%}")
    print(f"  预测结果: {y_pred_simple[:10]}...")
    print(f"  真实标签: {y_test[:10]}...")

    # 3. scikit-learn 高斯朴素贝叶斯
    print("\n[3] scikit-learn GaussianNB - 鸢尾花数据集")
    print("-" * 50)
    gaussian_result = demonstrate_gaussian_nb()
    print(f"  模型准确率: {gaussian_result['accuracy']:.2%}")
    print(f"  分类报告:")
    for line in gaussian_result['classification_report'].split('\n')[:6]:
        print(f"    {line}")

    # 4. 多项式朴素贝叶斯
    print("\n[4] scikit-learn MultinomialNB - 新闻组分类")
    print("-" * 50)
    try:
        multinomial_result = demonstrate_multinomial_nb()
        print(f"  模型准确率: {multinomial_result['accuracy']:.2%}")
        print(f"  类别: {multinomial_result['categories']}")
        print(f"  词汇表大小: {multinomial_result['vocabulary_size']}")
    except Exception as e:
        print(f"  注意: {e}")
        print("  (可能需要下载新闻组数据集)")

    # 5. 伯努利朴素贝叶斯
    print("\n[5] scikit-learn BernoulliNB - 二值化文本分类")
    print("-" * 50)
    try:
        bernoulli_result = demonstrate_bernoulli_nb()
        print(f"  模型准确率: {bernoulli_result['accuracy']:.2%}")
        print(f"  类别: {bernoulli_result['categories']}")
    except Exception as e:
        print(f"  注意: {e}")
        print("  (可能需要下载新闻组数据集)")

    # 6. 垃圾邮件过滤
    print("\n[6] 企业应用 - 垃圾邮件过滤器")
    print("-" * 50)
    spam_result = demonstrate_spam_filter()
    print(f"  模型: {spam_result['model']}")
    for item in spam_result['test_results']:
        status = "垃圾邮件" if item['is_spam'] else "正常邮件"
        print(f"  [{status}] {item['email']} (置信度: {item['confidence']})")

    # 7. 情感分析
    print("\n[7] 企业应用 - 情感分析器")
    print("-" * 50)
    sentiment_result = demonstrate_sentiment_analysis()
    print(f"  模型: {sentiment_result['model']}")
    for item in sentiment_result['test_results']:
        print(f"  [{item['sentiment']}] {item['text']} (置信度: {item['confidence']})")

    # 8. 文档分类
    print("\n[8] 企业应用 - 文档分类器")
    print("-" * 50)
    doc_result = demonstrate_document_classification()
    print(f"  模型: {doc_result['model']}")
    for item in doc_result['test_results']:
        print(f"  [{item['category']}] {item['document']} (置信度: {item['confidence']})")

    # 9. C++ 对比说明
    print("\n[9] C++ 对比说明")
    print("-" * 50)
    print(cpp_comparison_note())

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
