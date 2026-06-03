"""
Day 89 - 自然语言处理入门 (Introduction to Natural Language Processing)
=====================================================================

This file demonstrates core NLP techniques in Python:

1. Text Preprocessing & Cleaning
2. Tokenization (English & Chinese with jieba)
3. Bag-of-Words and TF-IDF Vectorization
4. Word Embeddings (Word2Vec with gensim)
5. Cosine Similarity for Text Comparison
6. Chinese Text Classification
7. Keyword Extraction (TF-IDF based)
8. Text Similarity Search

Comparison: Python NLP vs C++ Text Processing
----------------------------------------------
Python:
  - Rich ecosystem: jieba, gensim, scikit-learn, transformers, spaCy
  - Dynamic typing, rapid prototyping, REPL-driven exploration
  - C extensions under the hood (NumPy, Cython) give near-C performance
  - Ideal for research, data pipelines, production ML serving

C++ text processing:
  - Libraries: ICU (Unicode), Boost.Locale, Stanford CoreNLP (JNI)
  - Manual memory management, explicit data structures
  - No built-in regex until C++11 (<regex>), no native tokenization
  - Higher throughput for raw byte-level parsing at scale
  - Sparse ecosystem for ML-based NLP; typically wraps Python via pybind11
  - Better for embedded systems or latency-critical inference engines

When to choose which:
  - Use Python for 95% of NLP tasks (prototyping through production)
  - Use C++ for: custom tokenizer in a search engine, real-time speech
    pipelines, or when embedding NLP into a C++ application server

Enterprise Use Cases Demonstrated:
  - Chinese news text classification (topic categorization)
  - Keyword extraction from business documents
  - Similar document retrieval (search / recommendation)

Requirements:
  pip install jieba scikit-learn gensim numpy

Note: Word2Vec training on full IMDB corpus requires `datasets` library:
  pip install datasets
  (Skipped by default to keep demo lightweight; a synthetic corpus is used.)

Author: Python-100-Days Project
"""

from __future__ import annotations

import re
import math
import warnings
from collections import Counter
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import numpy as np

# ---------------------------------------------------------------------------
# Suppress noisy warnings from gensim / sklearn during demo runs
# ---------------------------------------------------------------------------
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================================
# 1. TEXT PREPROCESSING
# ============================================================================

# Common Chinese stop words (abbreviated set; production systems use the
# full HIT stop-word list: https://github.com/goto456/stopwords)
CHINESE_STOP_WORDS: Set[str] = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
    "它", "们", "那", "里", "为", "什么", "怎么", "如何", "可以",
    "能", "对", "但", "而", "与", "或", "如果", "因为", "所以",
    "虽然", "但是", "然后", "这个", "那个", "这些", "那些",
}

# Common English stop words (abbreviated; sklearn has a full list)
ENGLISH_STOP_WORDS: Set[str] = {
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
    "she", "her", "it", "its", "they", "them", "a", "an", "the",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "must", "can", "could",
    "of", "in", "to", "for", "with", "on", "at", "from", "by",
    "about", "as", "into", "through", "during", "before", "after",
    "and", "but", "or", "nor", "not", "so", "if", "then", "than",
    "too", "very", "just", "that", "this", "these", "those",
}


def clean_english_text(text: str) -> str:
    """Basic English text cleaning: lowercase, remove punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_chinese_text(text: str) -> str:
    """Basic Chinese text cleaning: remove non-Chinese chars except punctuation, normalize."""
    # Keep Chinese characters, Chinese punctuation, and alphanumeric
    text = re.sub(r"[^一-鿿　-〿a-zA-Z0-9]", "", text)
    text = re.sub(r"\s+", "", text)
    return text


def remove_stopwords(
    tokens: List[str], stop_words: Set[str]
) -> List[str]:
    """Remove stop words from a token list."""
    return [t for t in tokens if t not in stop_words]


# ============================================================================
# 2. TOKENIZATION
# ============================================================================

def tokenize_english(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer for English."""
    cleaned = clean_english_text(text)
    return cleaned.split()


def tokenize_chinese_jieba(text: str, use_stopwords: bool = True) -> List[str]:
    """
    Chinese tokenization using jieba.

    jieba supports three modes:
      - 精确模式 (default): attempts to produce the most accurate segmentation
      - 全模式: extracts all possible words (faster but ambiguous)
      - 搜索引擎模式: further splits long words for search indexing

    Args:
        text: Raw Chinese text.
        use_stopwords: Whether to filter out Chinese stop words.

    Returns:
        List of Chinese tokens.
    """
    import jieba

    tokens: List[str] = list(jieba.cut(text, cut_all=False))
    # Filter single-char noise and stop words
    tokens = [t.strip() for t in tokens if len(t.strip()) > 0]
    if use_stopwords:
        tokens = remove_stopwords(tokens, CHINESE_STOP_WORDS)
    return tokens


# ============================================================================
# 3. BAG-OF-WORDS & TF-IDF
# ============================================================================

@dataclass
class TFIDFResult:
    """Container for TF-IDF computation results."""
    vocabulary: List[str]
    tfidf_matrix: np.ndarray  # shape: (n_docs, n_terms)
    doc_count: int
    term_count: int

    def get_top_terms(self, doc_index: int, top_n: int = 5) -> List[Tuple[str, float]]:
        """Return the top-N terms for a given document by TF-IDF score."""
        row = self.tfidf_matrix[doc_index]
        indices = row.argsort()[::-1][:top_n]
        return [(self.vocabulary[i], row[i]) for i in indices if row[i] > 0]


def build_tfidf_from_scratch(
    documents: List[str],
    tokenizer: Callable[[str], List[str]],
) -> TFIDFResult:
    """
    Build a TF-IDF matrix from scratch (educational implementation).

    TF(t, d)  = count(t in d) / total_terms(d)
    IDF(t)    = log(N / df(t))  where N = total docs, df(t) = docs containing t
    TF-IDF    = TF * IDF

    For production, use sklearn.feature_extraction.text.TfidfVectorizer.
    """
    # Step 1: Tokenize all documents
    tokenized_docs: List[List[str]] = [tokenizer(doc) for doc in documents]

    # Step 2: Build vocabulary
    all_tokens: Set[str] = set()
    for doc_tokens in tokenized_docs:
        all_tokens.update(doc_tokens)
    vocabulary: List[str] = sorted(all_tokens)
    term_to_idx: Dict[str, int] = {t: i for i, t in enumerate(vocabulary)}

    n_docs: int = len(documents)
    n_terms: int = len(vocabulary)

    # Step 3: Compute TF
    tf_matrix: np.ndarray = np.zeros((n_docs, n_terms), dtype=np.float64)
    for doc_idx, doc_tokens in enumerate(tokenized_docs):
        counter: Counter = Counter(doc_tokens)
        total: int = len(doc_tokens)
        if total == 0:
            continue
        for token, count in counter.items():
            if token in term_to_idx:
                tf_matrix[doc_idx, term_to_idx[token]] = count / total

    # Step 4: Compute IDF
    doc_freq: np.ndarray = np.zeros(n_terms, dtype=np.float64)
    for term_idx in range(n_terms):
        doc_freq[term_idx] = np.sum(tf_matrix[:, term_idx] > 0)
    # Smooth to avoid division by zero
    idf: np.ndarray = np.log((n_docs + 1) / (doc_freq + 1)) + 1

    # Step 5: TF-IDF = TF * IDF
    tfidf_matrix: np.ndarray = tf_matrix * idf

    # Step 6: L2 normalize each row
    norms: np.ndarray = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    tfidf_matrix = tfidf_matrix / norms

    return TFIDFResult(
        vocabulary=vocabulary,
        tfidf_matrix=tfidf_matrix,
        doc_count=n_docs,
        term_count=n_terms,
    )


def build_tfidf_sklearn(
    documents: List[str],
    tokenizer: Optional[Callable[[str], List[str]]] = None,
) -> Tuple[Any, Any]:
    """
    Build a TF-IDF matrix using scikit-learn's TfidfVectorizer.

    Returns:
        (vectorizer, tfidf_matrix) tuple.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    kwargs: Dict[str, Any] = {}
    if tokenizer is not None:
        kwargs["tokenizer"] = tokenizer
        kwargs["token_pattern"] = None

    vectorizer = TfidfVectorizer(**kwargs)
    tfidf_matrix = vectorizer.fit_transform(documents)
    return vectorizer, tfidf_matrix


# ============================================================================
# 4. WORD EMBEDDINGS (Word2Vec)
# ============================================================================

@dataclass
class EmbeddingDemo:
    """Demonstrates Word2Vec training and similarity queries."""

    model: Any = field(repr=False, default=None)

    def train_english(
        self,
        sentences: List[List[str]],
        vector_size: int = 100,
        window: int = 5,
        min_count: int = 1,
        epochs: int = 10,
        seed: int = 42,
    ) -> None:
        """Train a Word2Vec model on English sentences."""
        from gensim.models import Word2Vec

        self.model = Word2Vec(
            sentences=sentences,
            vector_size=vector_size,
            window=window,
            min_count=min_count,
            workers=1,
            seed=seed,
            epochs=epochs,
        )
        print(f"[Word2Vec] Trained on {len(sentences)} sentences, "
              f"vocabulary size: {len(self.model.wv)}")

    def train_chinese(
        self,
        documents: List[str],
        vector_size: int = 100,
        window: int = 5,
        min_count: int = 1,
        epochs: int = 10,
        seed: int = 42,
    ) -> None:
        """Train a Word2Vec model on Chinese documents (auto-segmented by jieba)."""
        sentences: List[List[str]] = [
            tokenize_chinese_jieba(doc, use_stopwords=False) for doc in documents
        ]
        self.train_english(sentences, vector_size, window, min_count, epochs, seed)

    def most_similar(self, word: str, topn: int = 5) -> List[Tuple[str, float]]:
        """Find the most similar words to the given word."""
        if self.model is None:
            raise RuntimeError("Model not trained yet.")
        return self.model.wv.most_similar(word, topn=topn)

    def analogy(
        self,
        positive: List[str],
        negative: List[str],
        topn: int = 3,
    ) -> List[Tuple[str, float]]:
        """
        Perform word analogy: positive - negative.

        Example: king - man + woman = queen
            positive=["king", "woman"], negative=["man"]
        """
        if self.model is None:
            raise RuntimeError("Model not trained yet.")
        return self.model.wv.most_similar(
            positive=positive, negative=negative, topn=topn
        )

    def cosine_similarity_words(self, word1: str, word2: str) -> float:
        """Compute cosine similarity between two word vectors."""
        if self.model is None:
            raise RuntimeError("Model not trained yet.")
        vec1 = self.model.wv[word1]
        vec2 = self.model.wv[word2]
        dot = np.dot(vec1, vec2)
        norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return float(dot / norm) if norm != 0 else 0.0


# ============================================================================
# 5. COSINE SIMILARITY (DOCUMENT LEVEL)
# ============================================================================

def cosine_similarity_vec(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm != 0 else 0.0


def cosine_similarity_matrix(matrix: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine similarity for all rows in a matrix."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized = matrix / norms
    return np.dot(normalized, normalized.T)


# ============================================================================
# 6. CHINESE TEXT CLASSIFICATION (Enterprise Example)
# ============================================================================

@dataclass
class TextClassifier:
    """
    Simple Chinese text classifier using TF-IDF + Naive Bayes.

    Enterprise use case: categorize Chinese news articles, customer feedback,
    or support tickets into predefined topics.
    """
    vectorizer: Any = field(repr=False, default=None)
    classifier: Any = field(repr=False, default=None)
    categories: List[str] = field(default_factory=list)

    def train(
        self,
        texts: List[str],
        labels: List[str],
        tokenizer: Optional[Callable[[str], List[str]]] = None,
    ) -> Dict[str, float]:
        """
        Train the classifier on labeled Chinese text data.

        Args:
            texts: List of raw Chinese text documents.
            labels: Corresponding category labels.
            tokenizer: Tokenization function (defaults to jieba).

        Returns:
            Dictionary with training accuracy.
        """
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.model_selection import cross_val_score

        if tokenizer is None:
            tokenizer = lambda x: tokenize_chinese_jieba(x, use_stopwords=True)

        self.vectorizer, tfidf_matrix = build_tfidf_sklearn(texts, tokenizer)
        self.categories = sorted(set(labels))

        self.classifier = MultinomialNB()
        self.classifier.fit(tfidf_matrix, labels)

        # Cross-validation score
        scores = cross_val_score(
            MultinomialNB(), tfidf_matrix, labels, cv=min(3, len(set(labels)))
        )
        accuracy = float(np.mean(scores))

        return {"cv_accuracy": accuracy, "n_categories": len(self.categories)}

    def predict(self, text: str) -> str:
        """Predict the category of a single text."""
        if self.vectorizer is None or self.classifier is None:
            raise RuntimeError("Classifier not trained yet.")
        vec = self.vectorizer.transform([text])
        return str(self.classifier.predict(vec)[0])

    def predict_proba(self, text: str) -> Dict[str, float]:
        """Get probability distribution over categories."""
        if self.vectorizer is None or self.classifier is None:
            raise RuntimeError("Classifier not trained yet.")
        vec = self.vectorizer.transform([text])
        probas = self.classifier.predict_proba(vec)[0]
        return {
            cat: float(prob)
            for cat, prob in zip(self.classifier.classes_, probas)
        }


# ============================================================================
# 7. KEYWORD EXTRACTION (Enterprise Example)
# ============================================================================

def extract_keywords_tfidf(
    documents: List[str],
    top_n: int = 10,
    tokenizer: Optional[Callable[[str], List[str]]] = None,
) -> List[List[Tuple[str, float]]]:
    """
    Extract keywords from each document using TF-IDF scores.

    Enterprise use case: automatically tag business reports, extract key
    topics from customer reviews, build document summaries.

    Args:
        documents: List of raw text documents.
        top_n: Number of top keywords per document.
        tokenizer: Tokenization function.

    Returns:
        List of keyword lists (one per document), each containing
        (keyword, score) tuples sorted by TF-IDF descending.
    """
    if tokenizer is None:
        tokenizer = tokenize_english

    result = build_tfidf_from_scratch(documents, tokenizer)
    keywords_per_doc: List[List[Tuple[str, float]]] = []
    for i in range(result.doc_count):
        top_terms = result.get_top_terms(i, top_n=top_n)
        keywords_per_doc.append(top_terms)
    return keywords_per_doc


def extract_keywords_textrank(
    text: str,
    top_n: int = 10,
) -> List[Tuple[str, float]]:
    """
    Extract keywords using TextRank (graph-based ranking, similar to PageRank).

    Enterprise use case: unsupervised keyword extraction from Chinese documents
    where labeled data is unavailable.
    """
    import jieba.analyse

    keywords_with_weight: List[Tuple[str, float]] = jieba.analyse.extract_tags(
        text, topK=top_n, withWeight=True
    )
    return keywords_with_weight


# ============================================================================
# 8. TEXT SIMILARITY SEARCH (Enterprise Example)
# ============================================================================

@dataclass
class SimilaritySearchEngine:
    """
    Find the most similar documents to a query using TF-IDF + cosine similarity.

    Enterprise use case: document recommendation, duplicate detection,
    FAQ matching in customer support systems.
    """
    documents: List[str] = field(default_factory=list)
    vectorizer: Any = field(repr=False, default=None)
    tfidf_matrix: Any = field(repr=False, default=None)

    def build_index(
        self,
        documents: List[str],
        tokenizer: Optional[Callable[[str], List[str]]] = None,
    ) -> None:
        """Build the TF-IDF index from a corpus of documents."""
        self.documents = documents
        self.vectorizer, self.tfidf_matrix = build_tfidf_sklearn(documents, tokenizer)
        print(f"[SearchEngine] Indexed {len(documents)} documents, "
              f"vocabulary size: {len(self.vectorizer.vocabulary_)}")

    def search(self, query: str, top_k: int = 3) -> List[Tuple[int, str, float]]:
        """
        Search for the most similar documents to the query.

        Returns:
            List of (doc_index, doc_text_snippet, similarity_score) tuples.
        """
        if self.vectorizer is None or self.tfidf_matrix is None:
            raise RuntimeError("Index not built. Call build_index() first.")

        query_vec = self.vectorizer.transform([query])
        # Compute cosine similarity between query and all documents
        from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

        similarities = sklearn_cosine(query_vec, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[::-1][:top_k]

        results: List[Tuple[int, str, float]] = []
        for idx in top_indices:
            score = float(similarities[idx])
            snippet = self.documents[idx][:80] + (
                "..." if len(self.documents[idx]) > 80 else ""
            )
            results.append((int(idx), snippet, score))
        return results


# ============================================================================
# DEMO: BAG-OF-WORDS WITH SKLEARN
# ============================================================================

def demo_bag_of_words() -> None:
    """Demonstrate Bag-of-Words with CountVectorizer."""
    from sklearn.feature_extraction.text import CountVectorizer

    print("=" * 70)
    print("DEMO: Bag-of-Words (CountVectorizer)")
    print("=" * 70)

    documents = [
        "I love programming.",
        "I love machine learning.",
        "I love apple.",
    ]

    cv = CountVectorizer()
    X = cv.fit_transform(documents)

    print(f"Vocabulary: {cv.get_feature_names_out()}")
    print(f"Term-frequency matrix:\n{X.toarray()}")
    print()


# ============================================================================
# DEMO: CHINESE BAG-OF-WORDS WITH JIEBA
# ============================================================================

def demo_chinese_bag_of_words() -> None:
    """Demonstrate Chinese Bag-of-Words using jieba + CountVectorizer."""
    from sklearn.feature_extraction.text import CountVectorizer

    print("=" * 70)
    print("DEMO: Chinese Bag-of-Words (jieba + CountVectorizer)")
    print("=" * 70)

    documents = [
        "我在四川大学读书",
        "四川大学是四川最好的大学",
        "大学校园里面有很多学生",
    ]

    cv = CountVectorizer(
        tokenizer=lambda x: tokenize_chinese_jieba(x, use_stopwords=False),
        token_pattern=None,
    )
    X = cv.fit_transform(documents)

    print(f"Vocabulary: {cv.get_feature_names_out()}")
    print(f"Term-frequency matrix:\n{X.toarray()}")
    print()

    # With stop words removed
    print("--- With Chinese stop words removed ---")
    cv_sw = CountVectorizer(
        tokenizer=lambda x: tokenize_chinese_jieba(x, use_stopwords=True),
        token_pattern=None,
    )
    X_sw = cv_sw.fit_transform(documents)
    print(f"Vocabulary: {cv_sw.get_feature_names_out()}")
    print(f"Term-frequency matrix:\n{X_sw.toarray()}")
    print()


# ============================================================================
# DEMO: TF-IDF
# ============================================================================

def demo_tfidf() -> None:
    """Demonstrate TF-IDF computation (from scratch and with sklearn)."""
    print("=" * 70)
    print("DEMO: TF-IDF Vectorization")
    print("=" * 70)

    documents = [
        "The cat sat on the mat.",
        "The dog sat on the log.",
        "Cats and dogs are friends.",
    ]

    # From-scratch implementation
    print("--- From-scratch TF-IDF ---")
    result = build_tfidf_from_scratch(documents, tokenize_english)
    print(f"Vocabulary ({result.term_count} terms): {result.vocabulary}")
    print(f"TF-IDF matrix shape: {result.tfidf_matrix.shape}")
    for i in range(result.doc_count):
        top = result.get_top_terms(i, top_n=3)
        print(f"  Doc {i} top terms: {top}")

    # sklearn implementation
    print("\n--- sklearn TfidfVectorizer ---")
    vectorizer, tfidf_matrix = build_tfidf_sklearn(documents, tokenize_english)
    print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
    feature_names = vectorizer.get_feature_names_out()
    for i in range(len(documents)):
        row = tfidf_matrix[i].toarray().flatten()
        top_indices = row.argsort()[::-1][:3]
        top_terms = [
            (feature_names[j], round(row[j], 4))
            for j in top_indices
            if row[j] > 0
        ]
        print(f"  Doc {i} top terms: {top_terms}")
    print()


# ============================================================================
# DEMO: WORD EMBEDDINGS
# ============================================================================

def demo_word_embeddings() -> None:
    """Demonstrate Word2Vec training and similarity queries."""
    print("=" * 70)
    print("DEMO: Word Embeddings (Word2Vec)")
    print("=" * 70)

    # Build a synthetic corpus for demo purposes.
    # In production, use a large corpus like IMDB, Wikipedia, etc.
    corpus_sentences: List[List[str]] = [
        "the king and the queen ruled the kingdom".split(),
        "the man and the woman went to the market".split(),
        "the dog and the cat played in the garden".split(),
        "the prince and the princess lived in the castle".split(),
        "a dog is a loyal pet".split(),
        "a cat is an independent animal".split(),
        "kings and queens wear crowns".split(),
        "men and women are equal".split(),
        "the sheep and the goat graze on the hill".split(),
        "programming in python is fun and productive".split(),
        "machine learning uses algorithms and data".split(),
        "deep learning is a subset of machine learning".split(),
        "natural language processing deals with text data".split(),
        "the queen admired the brave king".split(),
        "the woman helped the man".split(),
    ] * 5  # Repeat to have enough data for training

    emb = EmbeddingDemo()
    emb.train_english(
        corpus_sentences,
        vector_size=50,
        window=5,
        min_count=1,
        epochs=20,
    )

    # Most similar words
    for word in ["king", "dog", "queen", "learning"]:
        try:
            similar = emb.most_similar(word, topn=3)
            print(f"  Most similar to '{word}': {similar}")
        except KeyError:
            print(f"  '{word}' not in vocabulary.")

    # Word analogy: king - man + woman ~ queen
    try:
        analogy_result = emb.analogy(
            positive=["king", "woman"], negative=["man"], topn=3
        )
        print(f"\n  Analogy: king - man + woman = {analogy_result}")
    except KeyError as e:
        print(f"\n  Analogy skipped (missing word: {e})")

    # Cosine similarity between pairs
    pairs = [("king", "queen"), ("dog", "cat"), ("king", "dog")]
    print()
    for w1, w2 in pairs:
        try:
            sim = emb.cosine_similarity_words(w1, w2)
            print(f"  Cosine similarity({w1}, {w2}) = {sim:.4f}")
        except KeyError:
            print(f"  Pair ({w1}, {w2}) skipped (missing word).")
    print()


# ============================================================================
# DEMO: CHINESE TEXT CLASSIFICATION
# ============================================================================

def demo_chinese_classification() -> None:
    """Demonstrate Chinese text classification with TF-IDF + Naive Bayes."""
    print("=" * 70)
    print("DEMO: Chinese Text Classification (Enterprise Example)")
    print("=" * 70)

    # Simulated Chinese news dataset (sports / tech / finance)
    texts: List[str] = [
        "今天的足球比赛非常精彩，主队以三比一获胜",
        "NBA季后赛正在激烈进行中，湖人队表现出色",
        "奥运会游泳比赛打破了世界纪录",
        "世界杯预选赛中国队客场战平对手",
        "马拉松赛事吸引了数万名跑步爱好者参加",
        "篮球联赛总决赛即将开打，球迷翘首以盼",
        "人工智能技术在医疗领域取得重大突破",
        "最新发布的智能手机搭载了全新的芯片",
        "量子计算机的研发取得了新的进展",
        "自动驾驶汽车在城市道路上完成了测试",
        "深度学习算法在图像识别方面表现优异",
        "区块链技术被广泛应用于金融行业",
        "股市今日大涨，上证指数突破三千五百点",
        "央行宣布下调利率以刺激经济增长",
        "房地产市场持续调控，房价趋于稳定",
        "新能源汽车板块今日领涨大盘",
        "互联网公司发布了最新一季的财报",
        "国际油价波动对全球经济产生影响",
    ]
    labels: List[str] = [
        "体育", "体育", "体育", "体育", "体育", "体育",
        "科技", "科技", "科技", "科技", "科技", "科技",
        "财经", "财经", "财经", "财经", "财经", "财经",
    ]

    classifier = TextClassifier()
    metrics = classifier.train(texts, labels)
    print(f"  Training CV accuracy: {metrics['cv_accuracy']:.2f}")
    print(f"  Categories: {classifier.categories}")

    # Predict new texts
    test_texts = [
        "今天的篮球比赛非常激烈",
        "最新的人工智能论文发表在顶级会议上",
        "基金市场今日表现低迷",
    ]
    print("\n  Predictions:")
    for text in test_texts:
        category = classifier.predict(text)
        probas = classifier.predict_proba(text)
        proba_str = ", ".join(
            f"{k}:{v:.2f}" for k, v in sorted(probas.items())
        )
        print(f"    '{text}' => {category}  ({proba_str})")
    print()


# ============================================================================
# DEMO: KEYWORD EXTRACTION
# ============================================================================

def demo_keyword_extraction() -> None:
    """Demonstrate keyword extraction from Chinese and English documents."""
    print("=" * 70)
    print("DEMO: Keyword Extraction (Enterprise Example)")
    print("=" * 70)

    # Chinese keyword extraction with TF-IDF
    chinese_docs = [
        "四川大学是中国著名的综合性大学，位于四川省成都市",
        "机器学习是人工智能的一个重要分支，广泛应用于数据分析",
        "今天的股票市场表现良好，科技股领涨大盘",
    ]

    print("--- Chinese TF-IDF Keywords ---")
    keywords = extract_keywords_tfidf(
        chinese_docs,
        top_n=5,
        tokenizer=lambda x: tokenize_chinese_jieba(x, True),
    )
    for i, kws in enumerate(keywords):
        kw_str = ", ".join(f"{w}({s:.3f})" for w, s in kws)
        print(f"  Doc {i}: {kw_str}")

    # Chinese keyword extraction with TextRank (jieba.analyse)
    print("\n--- Chinese TextRank Keywords (jieba.analyse) ---")
    sample_text = (
        "自然语言处理是人工智能的重要方向，"
        "深度学习推动了自然语言处理的快速发展"
    )
    textrank_kws = extract_keywords_textrank(sample_text, top_n=5)
    for word, weight in textrank_kws:
        print(f"  {word}: {weight:.4f}")

    # English keyword extraction
    print("\n--- English TF-IDF Keywords ---")
    english_docs = [
        "Machine learning algorithms can automatically learn patterns from data.",
        "Natural language processing enables computers to understand human language.",
        "Deep learning uses neural networks with many layers for complex tasks.",
    ]
    en_keywords = extract_keywords_tfidf(
        english_docs, top_n=5, tokenizer=tokenize_english
    )
    for i, kws in enumerate(en_keywords):
        kw_str = ", ".join(f"{w}({s:.3f})" for w, s in kws)
        print(f"  Doc {i}: {kw_str}")
    print()


# ============================================================================
# DEMO: TEXT SIMILARITY SEARCH
# ============================================================================

def demo_similarity_search() -> None:
    """Demonstrate document similarity search engine."""
    print("=" * 70)
    print("DEMO: Text Similarity Search (Enterprise Example)")
    print("=" * 70)

    # Chinese document corpus
    corpus = [
        "Python是一种广泛使用的高级编程语言，适合快速开发",
        "Java是企业级应用开发的主流语言，拥有丰富的生态系统",
        "自然语言处理是人工智能的核心技术之一",
        "深度学习在图像识别和语音识别领域取得了突破性进展",
        "数据挖掘从大量数据中发现有价值的信息和知识",
        "云计算提供了弹性的计算资源和存储服务",
        "区块链技术保障了数据的安全性和不可篡改性",
        "物联网将各种设备连接到互联网，实现智能化管理",
        "机器学习算法能够从数据中自动学习规律并做出预测",
        "Python在数据科学和机器学习领域非常受欢迎",
    ]

    engine = SimilaritySearchEngine()
    engine.build_index(
        corpus,
        tokenizer=lambda x: tokenize_chinese_jieba(x, use_stopwords=True),
    )

    queries = [
        "Python编程语言",
        "人工智能和深度学习",
        "数据分析和挖掘",
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")
        results = engine.search(query, top_k=3)
        for rank, (idx, snippet, score) in enumerate(results, 1):
            print(f"    #{rank} [score={score:.4f}] Doc {idx}: {snippet}")
    print()


# ============================================================================
# MAIN GUARD
# ============================================================================

if __name__ == "__main__":
    print("Day 89: Introduction to Natural Language Processing")
    print("=" * 70)
    print()

    # 1. Bag-of-Words
    demo_bag_of_words()

    # 2. Chinese Bag-of-Words with jieba
    demo_chinese_bag_of_words()

    # 3. TF-IDF
    demo_tfidf()

    # 4. Word Embeddings
    demo_word_embeddings()

    # 5. Chinese Text Classification
    demo_chinese_classification()

    # 6. Keyword Extraction
    demo_keyword_extraction()

    # 7. Text Similarity Search
    demo_similarity_search()

    print("=" * 70)
    print("All demos completed successfully.")
    print()
    print("Key takeaways:")
    print("  1. Bag-of-Words and TF-IDF are foundational text representations")
    print("  2. jieba enables Chinese text segmentation for NLP pipelines")
    print("  3. Word2Vec learns dense embeddings capturing semantic relationships")
    print("  4. TF-IDF + Naive Bayes is a strong baseline for text classification")
    print("  5. TF-IDF cosine similarity powers document search and recommendation")
    print()
    print("Python vs C++ for NLP:")
    print("  - Python: rich ecosystem (jieba, gensim, sklearn, transformers)")
    print("  - C++: ICU for Unicode, Boost.Locale, but sparse ML-NLP libraries")
    print("  - Python recommended for 95% of NLP tasks; C++ for latency-critical")
    print("    engines or embedded systems requiring custom tokenization")
    print("=" * 70)
