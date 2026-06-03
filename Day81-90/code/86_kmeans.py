"""
86. K-Means 聚类算法 - 综合示例
==============================

本文件涵盖：
  1. 从零实现 K-Means 算法
  2. 肘部法则（Elbow Method）选择最优 K 值
  3. 轮廓系数（Silhouette Score）评估聚类质量
  4. DBSCAN 基于密度的聚类算法对比
  5. C++ 迭代优化对比分析（注释说明）
  6. 企业级应用：客户分群、购物篮分析、图像压缩

依赖安装：
  pip install numpy matplotlib scikit-learn

作者：Python-100-Days 项目
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from numpy.typing import NDArray
from typing import Tuple, List, Optional, Dict, Any
from sklearn.cluster import KMeans, DBSCAN
from sklearn.datasets import load_iris, make_blobs
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


# ---------------------------------------------------------------------------
# 1. 从零实现 K-Means（不依赖 sklearn）
# ---------------------------------------------------------------------------

def euclidean_distance(u: NDArray[np.floating], v: NDArray[np.floating]) -> float:
    """计算两个向量之间的欧氏距离。

    Args:
        u: 第一个向量。
        v: 第二个向量。

    Returns:
        两个向量之间的欧氏距离标量值。
    """
    return float(np.sqrt(np.sum((u - v) ** 2)))


def init_centroids_random(
    X: NDArray[np.floating], k: int
) -> NDArray[np.floating]:
    """随机选择 k 个样本作为初始质心。

    Args:
        X: 形状为 (n_samples, n_features) 的数据矩阵。
        k: 簇的数量。

    Returns:
        形状为 (k, n_features) 的初始质心矩阵。
    """
    indices: NDArray[np.int_] = np.random.choice(len(X), size=k, replace=False)
    return X[indices].copy()


def assign_clusters(
    X: NDArray[np.floating], centroids: NDArray[np.floating]
) -> NDArray[np.intp]:
    """将每个样本分配到距离最近的质心所属簇。

    Args:
        X: 数据矩阵。
        centroids: 当前质心矩阵。

    Returns:
        形状为 (n_samples,) 的簇标签数组。
    """
    labels: NDArray[np.intp] = np.empty(len(X), dtype=np.intp)
    for i, sample in enumerate(X):
        distances = [euclidean_distance(sample, c) for c in centroids]
        labels[i] = np.argmin(distances)
    return labels


def compute_centroids(
    X: NDArray[np.floating],
    labels: NDArray[np.intp],
    k: int,
) -> NDArray[np.floating]:
    """根据簇标签重新计算每个簇的质心。

    Args:
        X: 数据矩阵。
        labels: 簇标签数组。
        k: 簇的数量。

    Returns:
        更新后的质心矩阵。
    """
    new_centroids: NDArray[np.floating] = np.empty((k, X.shape[1]))
    for i in range(k):
        members = X[labels == i]
        if len(members) > 0:
            new_centroids[i] = members.mean(axis=0)
        else:
            # 空簇处理：重新随机选一个样本
            new_centroids[i] = X[np.random.randint(len(X))]
    return new_centroids


def kmeans_from_scratch(
    X: NDArray[np.floating],
    k: int,
    max_iter: int = 300,
    tol: float = 1e-4,
) -> Tuple[NDArray[np.intp], NDArray[np.floating], int]:
    """纯 Python/NumPy 实现的 K-Means 聚类算法。

    算法流程：
      1. 随机选取 k 个样本作为初始质心
      2. 将每个样本分配到最近的质心所在簇
      3. 重新计算每个簇的质心（簇内均值）
      4. 若质心变化量 < tol 或达到 max_iter 则停止

    Args:
        X: 数据矩阵 (n_samples, n_features)。
        k: 簇数量。
        max_iter: 最大迭代次数。
        tol: 质心收敛容忍度。

    Returns:
        (labels, centroids, n_iterations) 三元组：
        - labels: 每个样本的簇标签
        - centroids: 最终质心
        - n_iterations: 实际迭代次数
    """
    centroids: NDArray[np.floating] = init_centroids_random(X, k)

    for iteration in range(1, max_iter + 1):
        labels = assign_clusters(X, centroids)
        new_centroids = compute_centroids(X, labels, k)

        # 使用 np.allclose 检测收敛
        if np.allclose(new_centroids, centroids, atol=tol):
            return labels, new_centroids, iteration

        centroids = new_centroids

    return labels, centroids, max_iter


def compute_inertia(
    X: NDArray[np.floating],
    labels: NDArray[np.intp],
    centroids: NDArray[np.floating],
) -> float:
    """计算总误差平方和（Inertia / SSE）。

    J = sum_{i=1}^{K} sum_{x in C_i} ||x - mu_i||^2

    Args:
        X: 数据矩阵。
        labels: 簇标签。
        centroids: 质心矩阵。

    Returns:
        inertia 标量值。
    """
    inertia: float = 0.0
    for i in range(len(centroids)):
        members = X[labels == i]
        if len(members) > 0:
            inertia += float(np.sum((members - centroids[i]) ** 2))
    return inertia


# ---------------------------------------------------------------------------
# 2. 肘部法则（Elbow Method）
# ---------------------------------------------------------------------------

def elbow_method(
    X: NDArray[np.floating],
    k_range: range,
    use_sklearn: bool = True,
) -> List[float]:
    """使用肘部法则寻找最优 K 值。

    对每个 K 值运行 K-Means 并记录 inertia，绘制 inertia 随 K
    变化的曲线，拐点处即为推荐的 K 值。

    Args:
        X: 数据矩阵。
        k_range: 待测试的 K 值范围。
        use_sklearn: 是否使用 sklearn（False 则使用手写实现）。

    Returns:
        每个 K 值对应的 inertia 列表。
    """
    inertias: List[float] = []

    for k in k_range:
        if use_sklearn:
            model = KMeans(
                n_clusters=k,
                n_init=10,
                max_iter=300,
                random_state=42,
            )
            model.fit(X)
            inertias.append(float(model.inertia_))
        else:
            labels, centroids, _ = kmeans_from_scratch(X, k)
            inertias.append(compute_inertia(X, labels, centroids))

    return inertias


def plot_elbow(
    k_range: range,
    inertias: List[float],
    save_path: Optional[str] = None,
) -> None:
    """绘制肘部法则图。

    Args:
        k_range: K 值范围。
        inertias: 对应 inertia 值列表。
        save_path: 图片保存路径（None 则直接显示）。
    """
    plt.figure(figsize=(8, 5), dpi=120)
    plt.plot(list(k_range), inertias, "bo-", linewidth=2, markersize=8)
    plt.xlabel("K (簇数量)", fontsize=12)
    plt.ylabel("Inertia (总误差平方和)", fontsize=12)
    plt.title("肘部法则 - 选择最优 K 值", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xticks(list(k_range))
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[INFO] 肘部法则图已保存至: {save_path}")
    else:
        plt.show()
    plt.close()


# ---------------------------------------------------------------------------
# 3. 轮廓系数（Silhouette Score）
# ---------------------------------------------------------------------------

def silhouette_analysis(
    X: NDArray[np.floating],
    k_range: range,
) -> List[float]:
    """对不同 K 值计算平均轮廓系数。

    轮廓系数 s(i) 取值范围 [-1, 1]：
      - 接近 1：样本被很好地分配到了当前簇
      - 接近 0：样本位于两个簇的边界
      - 接近 -1：样本可能被分配到了错误的簇

    Args:
        X: 数据矩阵。
        k_range: 待测试的 K 值范围（需 k >= 2）。

    Returns:
        每个 K 值对应的平均轮廓系数。
    """
    scores: List[float] = []

    for k in k_range:
        if k < 2:
            scores.append(-1.0)
            continue
        model = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = model.fit_predict(X)
        score = silhouette_score(X, labels)
        scores.append(float(score))

    return scores


def plot_silhouette(
    k_range: range,
    scores: List[float],
    save_path: Optional[str] = None,
) -> None:
    """绘制轮廓系数随 K 值变化的曲线。

    Args:
        k_range: K 值范围。
        scores: 轮廓系数列表。
        save_path: 保存路径（None 则直接显示）。
    """
    plt.figure(figsize=(8, 5), dpi=120)
    plt.plot(list(k_range), scores, "rs-", linewidth=2, markersize=8)
    plt.xlabel("K (簇数量)", fontsize=12)
    plt.ylabel("平均轮廓系数", fontsize=12)
    plt.title("轮廓系数分析 - 选择最优 K 值", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xticks(list(k_range))
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[INFO] 轮廓系数图已保存至: {save_path}")
    else:
        plt.show()
    plt.close()


def plot_silhouette_per_sample(
    X: NDArray[np.floating],
    labels: NDArray[np.intp],
    k: int,
    save_path: Optional[str] = None,
) -> None:
    """绘制每个簇的轮廓系数分布图。

    Args:
        X: 数据矩阵。
        labels: 簇标签。
        k: 簇数量。
        save_path: 保存路径。
    """
    sample_silhouette_values = silhouette_samples(X, labels)
    avg_score = float(np.mean(sample_silhouette_values))

    fig, ax = plt.subplots(figsize=(8, 6), dpi=120)
    y_lower = 10

    for i in range(k):
        ith_values = sample_silhouette_values[labels == i]
        ith_values.sort()

        size_cluster_i = len(ith_values)
        y_upper = y_lower + size_cluster_i

        color = plt.cm.nipy_spectral(float(i) / k)
        ax.fill_betweenx(
            np.arange(y_lower, y_upper),
            0,
            ith_values,
            facecolor=color,
            edgecolor=color,
            alpha=0.7,
        )
        ax.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i), fontsize=10)
        y_lower = y_upper + 10

    ax.set_title(f"轮廓系数分布图 (K={k}, 平均={avg_score:.3f})", fontsize=14)
    ax.set_xlabel("轮廓系数值", fontsize=12)
    ax.set_ylabel("簇标签", fontsize=12)
    ax.axvline(x=avg_score, color="red", linestyle="--", label=f"平均={avg_score:.3f}")
    ax.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[INFO] 轮廓分布图已保存至: {save_path}")
    else:
        plt.show()
    plt.close()


# ---------------------------------------------------------------------------
# 4. DBSCAN 基于密度的聚类
# ---------------------------------------------------------------------------

def dbscan_clustering(
    X: NDArray[np.floating],
    eps: float = 0.5,
    min_samples: int = 5,
) -> Tuple[NDArray[np.intp], Dict[str, Any]]:
    """使用 DBSCAN 进行基于密度的聚类。

    DBSCAN 的优势：
      - 不需要预先指定簇数量
      - 能发现任意形状的簇
      - 自动识别噪声点（标签为 -1）
      - 对离群点鲁棒

    Args:
        X: 数据矩阵。
        eps: 邻域半径。
        min_samples: 核心点的最小邻居数。

    Returns:
        (labels, info) 元组：
        - labels: 簇标签（-1 表示噪声点）
        - info: 包含聚类统计信息的字典
    """
    model = DBSCAN(eps=eps, min_samples=min_samples)
    labels: NDArray[np.intp] = model.fit_predict(X)

    n_clusters: int = len(set(labels) - {-1})
    n_noise: int = int(np.sum(labels == -1))

    info: Dict[str, Any] = {
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "labels": labels,
        "core_sample_indices": model.core_sample_indices_,
    }

    print(f"[DBSCAN] 发现 {n_clusters} 个簇, {n_noise} 个噪声点")
    return labels, info


# ---------------------------------------------------------------------------
# 5. C++ 对比说明
# ---------------------------------------------------------------------------

def print_cpp_comparison() -> None:
    """打印 K-Means 在 C++ 与 Python 中的迭代优化对比分析。

    C++ 实现 K-Means 的典型做法：
      - 使用 Eigen 或自定义矩阵库做向量化距离计算
      - 内存布局采用 SoA（Structure of Arrays）提升缓存命中率
      - 使用 OpenMP 多线程并行化分配步骤
      - 模板元编程在编译期展开距离计算循环

    Python 实现的优势：
      - NumPy 底层调用 BLAS/LAPACK，小规模数据的矩阵运算效率不逊于 C++
      - sklearn 的 KMeans 使用 Elkan 算法（三角不等式优化），减少冗余距离计算
      - 开发效率远高于 C++，适合原型验证和数据分析场景

    性能对比要点：
      1. 小规模数据（< 10万样本）：Python + NumPy 与 C++ 差距很小
      2. 大规模数据（> 100万样本）：C++ 的多线程并行 + 缓存优化优势明显
      3. sklearn 的 Elkan 算法通过三角不等式跳过不必要的距离计算，
         在高维数据上比朴素 Lloyd 算法快 2-5 倍
    """
    comparison: str = """
    =====================================================================
    K-Means 收敛性：Python vs C++ 迭代优化对比
    =====================================================================

    [收敛判定]
      - Python (sklearn): np.allclose(new_centroids, old_centroids, rtol=1e-4)
      - C++ 典型实现:    手动遍历比较每个维度差值 < epsilon
      - 两者数学等价，均为 L2 范数下的收敛检测

    [迭代核心 - 距离计算]
      - Python/NumPy:  np.linalg.norm(X[:, None] - centroids[None, :], axis=2)
                       底层调用 BLAS，对中小规模数据效率极高
      - C++ (Eigen):   (X.rowwise() - centroid).rowwise().squaredNorm()
                       编译期展开，无 Python 解释器开销

    [质心更新]
      - Python: np.mean(X[labels == k], axis=0)   # 向量化聚合
      - C++:    手动累加后除以计数，可利用 SIMD 指令

    [大规模场景 C++ 优势]
      1. OpenMP 并行: #pragma omp parallel for 分配样本到最近质心
      2. 缓存友好: SoA 布局，连续内存访问
      3. 无 GIL: 真正的多核并行，Python 受 GIL 限制

    [sklearn 的 Elkan 算法优化]
      利用三角不等式: 若 d(x, c1) 已知且 d(c1, c2) > 2*d(x, c1),
      则无需计算 d(x, c2)，直接排除 c2。
      这在 K 值较大时显著减少计算量。

    结论: 生产环境中推荐使用 sklearn，其底层 C/Cython 实现
          已经过高度优化。仅在超大规模或嵌入式场景考虑纯 C++。
    =====================================================================
    """
    print(comparison)


# ---------------------------------------------------------------------------
# 6. 企业级应用示例
# ---------------------------------------------------------------------------

def customer_segmentation_demo() -> Tuple[NDArray[np.floating], NDArray[np.intp]]:
    """客户分群（Customer Segmentation）示例。

    模拟电商客户数据，基于消费金额和消费频率进行客户分群：
      - 高价值客户（高消费 + 高频）
      - 潜力客户（低消费 + 高频）
      - 流失风险客户（低消费 + 低频）
      - 一般客户

    Returns:
        (features, labels) 元组。
    """
    print("\n" + "=" * 60)
    print("企业应用 1：电商客户分群 (Customer Segmentation)")
    print("=" * 60)

    np.random.seed(42)

    # 模拟 4 类客户
    # 特征：[年度消费金额（万元）, 月均访问次数, 平均客单价（元）]
    cluster_centers = np.array([
        [8.0, 25, 500],    # 高价值客户
        [2.0, 20, 150],    # 潜力客户
        [0.5, 3, 80],      # 流失风险客户
        [4.0, 12, 300],    # 一般客户
    ])

    X_customers, y_true = make_blobs(
        n_samples=600,
        centers=cluster_centers,
        cluster_std=[0.8, 1.0, 0.5, 1.2],
        random_state=42,
    )

    # 标准化
    scaler = StandardScaler()
    X_scaled: NDArray[np.floating] = scaler.fit_transform(X_customers)

    # K-Means 聚类
    km = KMeans(n_clusters=4, n_init=10, random_state=42)
    labels: NDArray[np.intp] = km.fit_predict(X_scaled)

    # 分析结果
    segment_names = ["高价值客户", "潜力客户", "流失风险客户", "一般客户"]
    for i in range(4):
        mask = labels == i
        cluster_data = X_customers[mask]
        print(f"\n  簇 {i} ({len(cluster_data)} 人):")
        print(f"    平均消费: {cluster_data[:, 0].mean():.1f} 万元")
        print(f"    平均访问: {cluster_data[:, 1].mean():.1f} 次/月")
        print(f"    平均客单价: {cluster_data[:, 2].mean():.0f} 元")

    return X_scaled, labels


def market_basket_analysis_demo() -> Tuple[NDArray[np.floating], NDArray[np.intp]]:
    """购物篮分析（Market Basket Analysis）示例。

    使用聚类对商品组合模式进行分组，发现典型购物篮特征。
    模拟超市购物数据，每个样本代表一次交易的商品特征向量。

    Returns:
        (features, labels) 元组。
    """
    print("\n" + "=" * 60)
    print("企业应用 2：购物篮分析 (Market Basket Analysis)")
    print("=" * 60)

    np.random.seed(42)

    # 模拟交易数据：[生鲜占比, 零食占比, 日用品占比, 饮品占比, 总金额]
    cluster_params = np.array([
        [0.6, 0.05, 0.2, 0.15, 150],  # 生鲜为主的交易
        [0.1, 0.5, 0.2, 0.2, 80],     # 零食为主的交易
        [0.15, 0.1, 0.6, 0.15, 200],  # 日用品为主的大额交易
        [0.1, 0.15, 0.1, 0.65, 60],   # 饮品为主的交易
    ])

    X_basket, _ = make_blobs(
        n_samples=400,
        centers=cluster_params,
        cluster_std=[0.05, 0.05, 0.05, 0.05],
        random_state=42,
    )

    scaler = StandardScaler()
    X_scaled: NDArray[np.floating] = scaler.fit_transform(X_basket)

    # 肘部法则确定 K
    k_range = range(2, 9)
    inertias = elbow_method(X_scaled, k_range)
    best_k = 4  # 根据肘部法则选定

    km = KMeans(n_clusters=best_k, n_init=10, random_state=42)
    labels: NDArray[np.intp] = km.fit_predict(X_scaled)

    basket_labels = ["生鲜购物篮", "零食购物篮", "日用品购物篮", "饮品购物篮"]
    for i in range(best_k):
        mask = labels == i
        cluster_data = X_basket[mask]
        print(f"\n  {basket_labels[i]} ({len(cluster_data)} 笔交易):")
        print(f"    生鲜占比: {cluster_data[:, 0].mean():.0%}")
        print(f"    零食占比: {cluster_data[:, 1].mean():.0%}")
        print(f"    日用品占比: {cluster_data[:, 2].mean():.0%}")
        print(f"    饮品占比: {cluster_data[:, 3].mean():.0%}")
        print(f"    平均金额: {cluster_data[:, 4].mean():.0f} 元")

    return X_scaled, labels


def image_compression_demo() -> None:
    """图像压缩示例（Image Compression with K-Means）。

    使用 K-Means 对图像像素进行量化，将颜色数量从 2^24 降至 K 种，
    实现有损压缩。这是 K-Means 在计算机视觉中的经典应用。

    原理：
      - 将图像每个像素的 RGB 值视为 3 维空间中的一个点
      - 用 K-Means 将所有像素聚为 K 类
      - 同一类的所有像素用其质心颜色替代
      - 压缩比 = 原始位深 / log2(K)
    """
    print("\n" + "=" * 60)
    print("企业应用 3：图像压缩 (Image Compression)")
    print("=" * 60)

    # 生成模拟图像（100x100 像素，3 通道）
    np.random.seed(42)
    img_height, img_width = 100, 100

    # 创建一个有多块颜色区域的模拟图像
    image = np.zeros((img_height, img_width, 3), dtype=np.uint8)
    image[:50, :50] = [220, 50, 50]      # 红色区域
    image[:50, 50:] = [50, 180, 50]      # 绿色区域
    image[50:, :50] = [50, 50, 220]      # 蓝色区域
    image[50:, 50:] = [220, 220, 50]     # 黄色区域

    # 添加噪声使图像更真实
    noise = np.random.normal(0, 15, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # 展平为 (n_pixels, 3)
    pixels: NDArray[np.floating] = image.reshape(-1, 3).astype(np.float64) / 255.0
    print(f"  原始图像: {img_height}x{img_width} = {len(pixels)} 像素")
    print(f"  原始颜色数: 最多 {256**3:,} 种")

    # 用不同 K 值压缩
    for k in [4, 8, 16]:
        km = KMeans(n_clusters=k, n_init=5, max_iter=100, random_state=42)
        labels = km.fit_predict(pixels)

        # 用质心颜色替换
        compressed_pixels = km.cluster_centers_[labels]
        compressed_image = (compressed_pixels * 255).astype(np.uint8)
        compressed_image = compressed_image.reshape(img_height, img_width, 3)

        # 计算压缩效果
        unique_colors = len(np.unique(compressed_image.reshape(-1, 3), axis=0))
        compression_ratio = 24 / np.log2(k) if k > 1 else float("inf")

        print(f"\n  K={k}:")
        print(f"    颜色数: {unique_colors}")
        print(f"    压缩比: {compression_ratio:.1f}:1")
        print(f"    Inertia: {km.inertia_:.4f}")


# ---------------------------------------------------------------------------
# 7. 完整流程演示：鸢尾花数据集
# ---------------------------------------------------------------------------

def iris_full_pipeline() -> None:
    """鸢尾花数据集上的完整 K-Means 分析流程。

    步骤：
      1. 加载数据并标准化
      2. 肘部法则确定 K
      3. 轮廓系数验证
      4. K-Means 聚类 + 可视化
      5. 与 DBSCAN 对比
      6. 手写 K-Means 验证
    """
    print("\n" + "=" * 60)
    print("完整流程：鸢尾花数据集聚类分析")
    print("=" * 60)

    # 加载数据
    iris = load_iris()
    X: NDArray[np.floating] = iris.data
    y: NDArray[np.intp] = iris.target
    feature_names: list[str] = list(iris.feature_names)

    # 标准化
    scaler = StandardScaler()
    X_scaled: NDArray[np.floating] = scaler.fit_transform(X)

    # --- 肘部法则 ---
    k_range = range(2, 10)
    inertias = elbow_method(X_scaled, k_range)
    print("\n[肘部法则] 各 K 值对应的 Inertia:")
    for k, inertia in zip(k_range, inertias):
        marker = " <-- 推荐" if k == 3 else ""
        print(f"  K={k}: {inertia:.2f}{marker}")

    # --- 轮廓系数 ---
    sil_scores = silhouette_analysis(X_scaled, k_range)
    print("\n[轮廓系数] 各 K 值对应的平均轮廓系数:")
    best_k_idx = int(np.argmax(sil_scores))
    for k, score in zip(k_range, sil_scores):
        marker = " <-- 最优" if k == list(k_range)[best_k_idx] else ""
        print(f"  K={k}: {score:.4f}{marker}")

    # --- K-Means 聚类 ---
    optimal_k: int = 3
    km_model = KMeans(
        n_clusters=optimal_k,
        n_init=10,
        max_iter=300,
        init="k-means++",
        algorithm="lloyd",
        tol=1e-4,
        random_state=42,
    )
    km_labels: NDArray[np.intp] = km_model.fit_predict(X_scaled)

    print(f"\n[K-Means 结果] K={optimal_k}")
    print(f"  Inertia: {km_model.inertia_:.4f}")
    print(f"  迭代次数: {km_model.n_iter_}")
    print(f"  轮廓系数: {silhouette_score(X_scaled, km_labels):.4f}")

    # --- DBSCAN 对比 ---
    print("\n[DBSCAN 对比]")
    dbscan_labels, dbscan_info = dbscan_clustering(X_scaled, eps=0.8, min_samples=5)
    if dbscan_info["n_clusters"] > 1:
        # 过滤噪声点计算轮廓系数
        non_noise_mask = dbscan_labels != -1
        if len(set(dbscan_labels[non_noise_mask])) > 1:
            db_score = silhouette_score(
                X_scaled[non_noise_mask], dbscan_labels[non_noise_mask]
            )
            print(f"  DBSCAN 轮廓系数（不含噪声）: {db_score:.4f}")

    # --- 手写 K-Means 验证 ---
    print("\n[手写 K-Means 验证]")
    scratch_labels, scratch_centers, n_iters = kmeans_from_scratch(X_scaled, k=3)
    scratch_inertia = compute_inertia(X_scaled, scratch_labels, scratch_centers)
    print(f"  迭代次数: {n_iters}")
    print(f"  Inertia: {scratch_inertia:.4f}")
    print(f"  轮廓系数: {silhouette_score(X_scaled, scratch_labels):.4f}")

    # --- PCA 降维可视化 ---
    pca = PCA(n_components=2)
    X_pca: NDArray[np.floating] = pca.fit_transform(X_scaled)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=120)

    # 子图1：真实标签
    scatter1 = axes[0].scatter(
        X_pca[:, 0], X_pca[:, 1], c=y, cmap="viridis", alpha=0.7, edgecolors="k", s=40
    )
    axes[0].set_title("真实标签", fontsize=13)
    axes[0].set_xlabel("PC1")
    axes[0].set_ylabel("PC2")
    plt.colorbar(scatter1, ax=axes[0])

    # 子图2：K-Means 结果
    scatter2 = axes[1].scatter(
        X_pca[:, 0], X_pca[:, 1], c=km_labels, cmap="viridis", alpha=0.7,
        edgecolors="k", s=40,
    )
    centers_pca = pca.transform(km_model.cluster_centers_)
    axes[1].scatter(
        centers_pca[:, 0], centers_pca[:, 1], c="red", marker="*",
        s=200, edgecolors="k", linewidths=1.5, label="质心",
    )
    axes[1].set_title(f"K-Means (K={optimal_k})", fontsize=13)
    axes[1].set_xlabel("PC1")
    axes[1].set_ylabel("PC2")
    axes[1].legend()
    plt.colorbar(scatter2, ax=axes[1])

    # 子图3：DBSCAN 结果
    scatter3 = axes[2].scatter(
        X_pca[:, 0], X_pca[:, 1], c=dbscan_labels, cmap="viridis",
        alpha=0.7, edgecolors="k", s=40,
    )
    axes[2].set_title("DBSCAN", fontsize=13)
    axes[2].set_xlabel("PC1")
    axes[2].set_ylabel("PC2")
    plt.colorbar(scatter3, ax=axes[2])

    plt.suptitle("鸢尾花数据集聚类分析对比", fontsize=15, y=1.02)
    plt.tight_layout()
    plt.show()
    plt.close()


# ---------------------------------------------------------------------------
# 8. K-Means 超参数说明
# ---------------------------------------------------------------------------

def print_hyperparameter_guide() -> None:
    """打印 KMeans 常用超参数及调优建议。"""
    guide: str = """
    =====================================================
    sklearn.cluster.KMeans 超参数速查
    =====================================================
    n_clusters  : int = 8
        簇数量 K，需根据业务需求或肘部法则/轮廓系数确定。
    max_iter    : int = 300
        单次初始化的最大迭代次数。大数据集可适当增大。
    n_init      : int = 10
        使用不同初始质心运行算法的次数，取最优结果。
        值越大结果越稳定，但耗时线性增加。
    init        : {'k-means++', 'random'} or ndarray = 'k-means++'
        k-means++: 智能初始化，选择彼此距离较远的初始质心
        random:  随机选择样本作为初始质心
    algorithm   : {'lloyd', 'elkan'} = 'lloyd'
        lloyd:  经典 EM 迭代算法
        elkan:  利用三角不等式加速，K 较大时效果显著
    tol         : float = 1e-4
        收敛容忍度，质心变化量小于此值时停止迭代。
    random_state: int = None
        随机种子，设固定值保证结果可复现。
    =====================================================
    """
    print(guide)


# ---------------------------------------------------------------------------
# main 入口
# ---------------------------------------------------------------------------

def main() -> None:
    """主函数：依次运行所有演示。"""
    print("K-Means 聚类算法 - 综合示例")
    print("=" * 60)

    # 超参数说明
    print_hyperparameter_guide()

    # C++ 对比
    print_cpp_comparison()

    # 鸢尾花完整流程
    iris_full_pipeline()

    # 企业应用 1：客户分群
    customer_segmentation_demo()

    # 企业应用 2：购物篮分析
    market_basket_analysis_demo()

    # 企业应用 3：图像压缩
    image_compression_demo()

    print("\n" + "=" * 60)
    print("所有演示完成。")
    print("=" * 60)


if __name__ == "__main__":
    main()
