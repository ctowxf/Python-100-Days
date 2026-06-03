"""
97. E-Commerce Website Technical Analysis (电商网站技术要点剖析)

Enterprise-level implementation covering:
- E-commerce architecture (B2B, C2C, B2C, O2O, B2B2C)
- SPU/SKU product model design
- Product search engine with ElasticSearch concepts
- Recommendation engine (collaborative filtering, content-based)
- Shopping cart system (session/cookie/Redis)
- Order processing with inventory management
- Payment gateway integration patterns
- Flash sale and overselling prevention

C++ Comparison: E-commerce Search vs C++ Inverted Index
============================================================
Python-based search (ElasticSearch via elasticsearch-py) provides a
high-level REST API for building inverted indexes and executing full-text
search with TF-IDF scoring. In C++, one would implement inverted indexes
directly using hash maps of posting lists (std::unordered_map<string,
vector<posting>>), with SIMD-accelerated intersection for conjunctive
queries. Python's ElasticSearch integration trades raw query latency
(~1-5ms) for rapid development and horizontal scalability, while C++
search engines like Lucene-native or custom implementations achieve
sub-millisecond lookups at the cost of development complexity.
============================================================
"""

from __future__ import annotations

import hashlib
import heapq
import json
import math
import re
import secrets
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Callable,
    Counter as CounterType,
    Dict,
    FrozenSet,
    Generator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)

# ---------------------------------------------------------------------------
# Section 1: E-Commerce Business Models (电商商业模式)
# ---------------------------------------------------------------------------


class BusinessModel(Enum):
    """Supported e-commerce business models."""
    B2B = "B2B"      # Business to Business (Alibaba)
    C2C = "C2C"      # Consumer to Consumer (Taobao, eBay)
    B2C = "B2C"      # Business to Consumer (JD.com, Amazon)
    C2B = "C2B"      # Consumer to Business (custom orders)
    O2O = "O2O"      # Online to Offline (Meituan, Uber)
    B2B2C = "B2B2C"  # Business to Business to Consumer (Tmall)


@dataclass
class EcommercePlatform:
    """Configuration for an e-commerce platform."""
    name: str
    model: BusinessModel
    features: List[str] = field(default_factory=list)
    supports_third_party_login: bool = False
    supports_flash_sale: bool = False
    supports_recommendation: bool = False
    supports_full_text_search: bool = False

    def summary(self) -> str:
        return (
            f"{self.name} [{self.model.value}]: "
            f"{len(self.features)} features, "
            f"flash_sale={self.supports_flash_sale}, "
            f"search={self.supports_full_text_search}"
        )


# ---------------------------------------------------------------------------
# Section 2: Product Model -- SPU and SKU (商品模型 -- SPU与SKU)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SPUCategory:
    """Standard Product Unit category (e.g., 'iPhone 15')."""
    spu_id: str
    name: str
    brand: str
    description: str = ""
    category_path: str = ""  # e.g., "Electronics > Phones > Apple"


@dataclass(frozen=True)
class SKU:
    """
    Stock Keeping Unit -- a specific sellable variant.

    Example: iPhone 15 Pro 256GB Natural Titanium

    Each SKU has unique inventory tracking and pricing. SPU groups
    multiple SKUs of the same base product.
    """
    sku_id: str
    spu_id: str
    name: str
    price: float
    original_price: float = 0.0
    stock: int = 0
    attributes: Dict[str, str] = field(default_factory=dict)  # e.g., {"color": "Black", "storage": "256GB"}
    image_url: str = ""
    weight_kg: float = 0.0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def discount_pct(self) -> float:
        if self.original_price > 0 and self.original_price > self.price:
            return round((1 - self.price / self.original_price) * 100, 1)
        return 0.0

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0 and self.is_active

    @property
    def attribute_display(self) -> str:
        return ", ".join(f"{k}: {v}" for k, v in self.attributes.items())


@dataclass
class ProductCatalog:
    """
    In-memory product catalog with SPU/SKU management.

    Supports:
    - SPU-level grouping
    - SKU-level inventory and pricing
    - Attribute-based filtering
    - Category browsing
    """

    spus: Dict[str, SPUCategory] = field(default_factory=dict)
    skus: Dict[str, SKU] = field(default_factory=dict)
    spu_skus: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    categories: Set[str] = field(default_factory=set)

    def add_spu(self, spu: SPUCategory) -> None:
        self.spus[spu.spu_id] = spu
        if spu.category_path:
            self.categories.add(spu.category_path)

    def add_sku(self, sku: SKU) -> None:
        self.skus[sku.sku_id] = sku
        self.spu_skus[sku.spu_id].append(sku.sku_id)

    def get_skus_for_spu(self, spu_id: str) -> List[SKU]:
        return [self.skus[sid] for sid in self.spu_skus.get(spu_id, []) if sid in self.skus]

    def get_spu(self, spu_id: str) -> Optional[SPUCategory]:
        return self.spus.get(spu_id)

    def filter_by_price(
        self, min_price: float = 0, max_price: float = float("inf")
    ) -> List[SKU]:
        return [
            s for s in self.skus.values()
            if min_price <= s.price <= max_price and s.is_active
        ]

    def filter_by_attribute(self, attr_key: str, attr_value: str) -> List[SKU]:
        return [
            s for s in self.skus.values()
            if s.attributes.get(attr_key) == attr_value and s.is_active
        ]

    def get_in_stock_skus(self) -> List[SKU]:
        return [s for s in self.skus.values() if s.is_in_stock]

    @property
    def total_products(self) -> int:
        return len(self.spus)

    @property
    def total_skus(self) -> int:
        return len(self.skus)


# ---------------------------------------------------------------------------
# Section 3: Product Search Engine (商品搜索引擎)
# ---------------------------------------------------------------------------


@dataclass
class SearchDocument:
    """A document in the search index (ElasticSearch concept)."""
    doc_id: str
    title: str
    body: str
    category: str
    brand: str
    price: float
    tags: List[str] = field(default_factory=list)
    score: float = 0.0

    @property
    def searchable_text(self) -> str:
        return f"{self.title} {self.body} {self.brand} {' '.join(self.tags)}"


class InvertedIndex:
    """
    In-memory inverted index for product search.

    Implements core ElasticSearch concepts:
    - Tokenization and normalization
    - TF-IDF scoring
    - Boolean query operators (AND, OR)
    - Field boosting

    C++ Comparison Note:
    --------------------
    This inverted index uses Python dicts and lists. In C++, the equivalent
    would use std::unordered_map<std::string, std::vector<Posting>> with
    memory-mapped files for persistence. Python's approach trades ~10x
    query latency for rapid prototyping; a C++ implementation would achieve
    sub-microsecond term lookups via direct hash table access.
    """

    def __init__(self) -> None:
        # term -> [(doc_id, term_frequency)]
        self.index: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.documents: Dict[str, SearchDocument] = {}
        self.doc_count: int = 0
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple tokenizer: lowercase, split on non-alphanumeric, remove stopwords."""
        text = text.lower()
        tokens = re.findall(r"[\w一-鿿]+", text)
        stopwords = {"的", "了", "是", "在", "和", "a", "an", "the", "is", "in", "of"}
        return [t for t in tokens if t not in stopwords and len(t) > 1]

    def add_document(self, doc: SearchDocument) -> None:
        """Index a search document."""
        self.documents[doc.doc_id] = doc
        self.doc_count += 1

        tokens = self.tokenize(doc.searchable_text)
        self.doc_lengths[doc.doc_id] = len(tokens)
        self.avg_doc_length = (
            sum(self.doc_lengths.values()) / len(self.doc_lengths)
        )

        term_counts: CounterType[str] = Counter(tokens)
        total_terms = len(tokens)

        for term, count in term_counts.items():
            tf = count / total_terms if total_terms > 0 else 0
            self.index[term].append((doc.doc_id, tf))

    def _tfidf_score(self, term: str, doc_id: str, tf: float) -> float:
        """Compute TF-IDF score for a term in a document."""
        df = len(self.index.get(term, []))
        if df == 0:
            return 0.0
        idf = math.log(self.doc_count / (1 + df))
        return tf * idf

    def search(
        self,
        query: str,
        top_k: int = 10,
        field_boosts: Optional[Dict[str, float]] = None,
    ) -> List[Tuple[str, float]]:
        """
        Search the index with TF-IDF scoring.

        Parameters
        ----------
        query : str
            Search query string.
        top_k : int
            Number of top results to return.
        field_boosts : dict, optional
            Boost weights for different fields (title, body, brand, tags).

        Returns
        -------
        list of (doc_id, score) tuples, sorted by descending score.
        """
        if field_boosts is None:
            field_boosts = {"title": 2.0, "body": 1.0, "brand": 1.5, "tags": 1.2}

        tokens = self.tokenize(query)
        if not tokens:
            return []

        scores: Dict[str, float] = defaultdict(float)

        for term in tokens:
            postings = self.index.get(term, [])
            for doc_id, tf in postings:
                tfidf = self._tfidf_score(term, doc_id, tf)
                doc = self.documents.get(doc_id)
                if doc:
                    # Apply field boosts
                    boost = 1.0
                    if term in doc.title.lower():
                        boost = field_boosts.get("title", 1.0)
                    elif term in doc.brand.lower():
                        boost = field_boosts.get("brand", 1.0)
                    elif any(term in t.lower() for t in doc.tags):
                        boost = field_boosts.get("tags", 1.0)
                    scores[doc_id] += tfidf * boost
                else:
                    scores[doc_id] += tfidf

        # Return top-k results
        top_results = heapq.nlargest(top_k, scores.items(), key=lambda x: x[1])
        return top_results

    def suggest(self, prefix: str, max_suggestions: int = 5) -> List[str]:
        """Auto-complete suggestions based on indexed terms."""
        prefix_lower = prefix.lower()
        matching_terms = [
            t for t in self.index.keys()
            if t.startswith(prefix_lower)
        ]
        # Sort by document frequency (popularity)
        matching_terms.sort(key=lambda t: len(self.index[t]), reverse=True)
        return matching_terms[:max_suggestions]


class ProductSearchEngine:
    """
    Enterprise product search engine.

    Features:
    - Full-text search with TF-IDF ranking
    - Price range filtering
    - Category and brand filtering
    - Search suggestions / auto-complete
    - Search history tracking
    - Hot search terms
    """

    def __init__(self) -> None:
        self.index = InvertedIndex()
        self.search_history: List[Tuple[str, datetime]] = []
        self.search_counts: CounterType[str] = Counter()

    def index_product(self, sku: SKU, spu: Optional[SPUCategory] = None) -> None:
        """Add a product to the search index."""
        title = spu.name if spu else sku.name
        body = f"{sku.name} {sku.attribute_display}"
        brand = spu.brand if spu else ""
        category = spu.category_path if spu else ""
        tags = list(sku.attributes.values())

        doc = SearchDocument(
            doc_id=sku.sku_id,
            title=title,
            body=body,
            category=category,
            brand=brand,
            price=sku.price,
            tags=tags,
        )
        self.index.add_document(doc)

    def search(
        self,
        query: str,
        min_price: float = 0,
        max_price: float = float("inf"),
        category: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Search products with optional filters.

        Returns list of (sku_id, relevance_score) tuples.
        """
        # Track search
        self.search_history.append((query, datetime.utcnow()))
        self.search_counts[query] += 1

        # Get index results
        results = self.index.search(query, top_k=top_k * 2)

        # Apply filters
        filtered: List[Tuple[str, float]] = []
        for doc_id, score in results:
            doc = self.index.documents.get(doc_id)
            if doc is None:
                continue
            if doc.price < min_price or doc.price > max_price:
                continue
            if category and doc.category != category:
                continue
            filtered.append((doc_id, score))
            if len(filtered) >= top_k:
                break

        return filtered

    def get_hot_searches(self, top_k: int = 10) -> List[Tuple[str, int]]:
        """Get the most popular search terms."""
        return self.search_counts.most_common(top_k)

    def get_suggestions(self, prefix: str) -> List[str]:
        """Get auto-complete suggestions."""
        return self.index.suggest(prefix)


# ---------------------------------------------------------------------------
# Section 4: Recommendation Engine (推荐引擎)
# ---------------------------------------------------------------------------


class RecommendationEngine:
    """
    Product recommendation engine implementing:
    - Collaborative filtering (user-based and item-based)
    - Content-based filtering
    - Popularity-based recommendations

    Enterprise Example: "Customers who bought X also bought Y"
    and personalized product suggestions based on browsing history.
    """

    def __init__(self) -> None:
        # user_id -> {sku_id: rating}
        self.user_ratings: Dict[str, Dict[str, float]] = defaultdict(dict)
        # sku_id -> set of user_ids who purchased
        self.purchase_history: Dict[str, Set[str]] = defaultdict(set)
        # sku_id -> category
        self.product_categories: Dict[str, str] = {}
        # sku_id -> set of attribute tags
        self.product_tags: Dict[str, Set[str]] = {}

    def record_purchase(self, user_id: str, sku_id: str, rating: float = 5.0) -> None:
        """Record a user purchase with optional rating."""
        self.user_ratings[user_id][sku_id] = rating
        self.purchase_history[sku_id].add(user_id)

    def record_browsing(self, user_id: str, sku_id: str, implicit_rating: float = 2.0) -> None:
        """Record browsing as an implicit signal."""
        if sku_id not in self.user_ratings[user_id]:
            self.user_ratings[user_id][sku_id] = implicit_rating

    def set_product_attributes(
        self, sku_id: str, category: str, tags: Set[str]
    ) -> None:
        """Set product attributes for content-based filtering."""
        self.product_categories[sku_id] = category
        self.product_tags[sku_id] = tags

    def _cosine_similarity(
        self, vec_a: Dict[str, float], vec_b: Dict[str, float]
    ) -> float:
        """Compute cosine similarity between two sparse vectors."""
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0
        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _jaccard_similarity(self, set_a: Set[str], set_b: Set[str]) -> float:
        """Compute Jaccard similarity between two sets."""
        if not set_a and not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def collaborative_filtering_user_based(
        self, user_id: str, top_k_users: int = 5, top_n_items: int = 10
    ) -> List[Tuple[str, float]]:
        """
        User-based collaborative filtering.

        Find users similar to the target user, then recommend items
        those similar users liked but the target user hasn't seen.
        """
        target_ratings = self.user_ratings.get(user_id, {})
        if not target_ratings:
            return []

        # Compute similarity with all other users
        similarities: List[Tuple[str, float]] = []
        for other_id, other_ratings in self.user_ratings.items():
            if other_id == user_id:
                continue
            sim = self._cosine_similarity(target_ratings, other_ratings)
            if sim > 0:
                similarities.append((other_id, sim))

        # Get top-K similar users
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_users = similarities[:top_k_users]

        # Aggregate recommendations from similar users
        scores: Dict[str, float] = defaultdict(float)
        for similar_user, sim in top_users:
            for sku_id, rating in self.user_ratings[similar_user].items():
                if sku_id not in target_ratings:
                    scores[sku_id] += sim * rating

        # Return top-N recommendations
        return heapq.nlargest(top_n_items, scores.items(), key=lambda x: x[1])

    def collaborative_filtering_item_based(
        self, user_id: str, top_n_items: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Item-based collaborative filtering.

        Find items similar to what the user has already purchased,
        based on co-purchase patterns.
        """
        user_items = set(self.user_ratings.get(user_id, {}).keys())
        if not user_items:
            return []

        scores: Dict[str, float] = defaultdict(float)

        for purchased_item in user_items:
            purchased_buyers = self.purchase_history.get(purchased_item, set())
            for candidate_id, candidate_buyers in self.purchase_history.items():
                if candidate_id in user_items:
                    continue
                sim = self._jaccard_similarity(purchased_buyers, candidate_buyers)
                if sim > 0:
                    user_rating = self.user_ratings[user_id].get(purchased_item, 3.0)
                    scores[candidate_id] += sim * user_rating

        return heapq.nlargest(top_n_items, scores.items(), key=lambda x: x[1])

    def content_based(
        self, user_id: str, top_n_items: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Content-based recommendation.

        Recommend items with attributes similar to what the user has liked.
        """
        user_items = self.user_ratings.get(user_id, {})
        if not user_items:
            return []

        # Build user preference profile from liked items
        liked_items = {k for k, v in user_items.items() if v >= 3.0}
        liked_tags: Set[str] = set()
        liked_categories: CounterType[str] = Counter()
        for item_id in liked_items:
            liked_tags |= self.product_tags.get(item_id, set())
            cat = self.product_categories.get(item_id)
            if cat:
                liked_categories[cat] += 1

        # Score all unseen items
        scores: Dict[str, float] = {}
        for sku_id in self.product_tags:
            if sku_id in user_items:
                continue
            item_tags = self.product_tags.get(sku_id, set())
            tag_sim = self._jaccard_similarity(liked_tags, item_tags)

            item_cat = self.product_categories.get(sku_id, "")
            cat_score = liked_categories.get(item_cat, 0) / max(len(liked_categories), 1)

            scores[sku_id] = 0.7 * tag_sim + 0.3 * cat_score

        return heapq.nlargest(top_n_items, scores.items(), key=lambda x: x[1])

    def popularity_based(self, top_n_items: int = 10) -> List[Tuple[str, int]]:
        """Recommend the most popular items overall."""
        return heapq.nlargest(
            top_n_items,
            ((sku_id, len(buyers)) for sku_id, buyers in self.purchase_history.items()),
            key=lambda x: x[1],
        )

    def hybrid_recommend(
        self, user_id: str, top_n_items: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Hybrid recommendation combining collaborative and content-based.

        Weighted combination:
        - 40% user-based collaborative
        - 30% item-based collaborative
        - 30% content-based
        """
        cf_user = dict(self.collaborative_filtering_user_based(user_id, top_n_items=top_n_items * 2))
        cf_item = dict(self.collaborative_filtering_item_based(user_id, top_n_items=top_n_items * 2))
        cb = dict(self.content_based(user_id, top_n_items=top_n_items * 2))

        # Normalize scores
        def normalize(d: Dict[str, float]) -> Dict[str, float]:
            if not d:
                return d
            max_val = max(d.values()) if d else 1
            return {k: v / max_val for k, v in d.items()} if max_val > 0 else d

        cf_user_n = normalize(cf_user)
        cf_item_n = normalize(cf_item)
        cb_n = normalize(cb)

        combined: Dict[str, float] = defaultdict(float)
        all_items = set(cf_user_n) | set(cf_item_n) | set(cb_n)
        for item in all_items:
            combined[item] = (
                0.4 * cf_user_n.get(item, 0)
                + 0.3 * cf_item_n.get(item, 0)
                + 0.3 * cb_n.get(item, 0)
            )

        return heapq.nlargest(top_n_items, combined.items(), key=lambda x: x[1])


# ---------------------------------------------------------------------------
# Section 5: Shopping Cart (购物车系统)
# ---------------------------------------------------------------------------


@dataclass
class CartItem:
    """A single item in the shopping cart."""
    sku_id: str
    sku_name: str
    price: float
    amount: int = 1
    selected: bool = True

    @property
    def subtotal(self) -> float:
        return self.price * self.amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sku_id": self.sku_id,
            "sku_name": self.sku_name,
            "price": self.price,
            "amount": self.amount,
            "selected": self.selected,
            "subtotal": self.subtotal,
        }


class ShoppingCart:
    """
    Enterprise shopping cart system.

    Supports:
    - Add, update, remove items
    - Select/deselect individual items
    - Cart total calculation (selected items only)
    - Serialization for Cookie/Redis storage
    - Cart merging (guest -> authenticated user)

    Storage Strategy:
    - Guest users: Cookie/localStorage (client-side)
    - Authenticated users: Redis (server-side, with DB backup)
    """

    def __init__(self, user_id: Optional[str] = None) -> None:
        self.user_id = user_id
        self.items: Dict[str, CartItem] = {}
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def add_item(
        self, sku_id: str, sku_name: str, price: float, amount: int = 1
    ) -> None:
        """Add an item or increase its quantity."""
        if sku_id in self.items:
            self.items[sku_id].amount += amount
        else:
            self.items[sku_id] = CartItem(
                sku_id=sku_id, sku_name=sku_name, price=price, amount=amount
            )
        self.updated_at = datetime.utcnow()

    def update_amount(self, sku_id: str, amount: int) -> bool:
        """Update the quantity of a cart item."""
        if sku_id in self.items:
            if amount <= 0:
                del self.items[sku_id]
            else:
                self.items[sku_id].amount = amount
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_item(self, sku_id: str) -> bool:
        """Remove an item from the cart."""
        if sku_id in self.items:
            del self.items[sku_id]
            self.updated_at = datetime.utcnow()
            return True
        return False

    def toggle_select(self, sku_id: str) -> bool:
        """Toggle selection state of an item."""
        if sku_id in self.items:
            self.items[sku_id].selected = not self.items[sku_id].selected
            return True
        return False

    def select_all(self, selected: bool = True) -> None:
        """Select or deselect all items."""
        for item in self.items.values():
            item.selected = selected

    def clear(self) -> None:
        """Remove all items."""
        self.items.clear()
        self.updated_at = datetime.utcnow()

    @property
    def selected_items(self) -> List[CartItem]:
        return [item for item in self.items.values() if item.selected]

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.selected_items)

    @property
    def total_items(self) -> int:
        return sum(item.amount for item in self.items.values())

    @property
    def selected_count(self) -> int:
        return sum(item.amount for item in self.selected_items)

    def serialize(self) -> str:
        """Serialize cart to JSON string (for Cookie/Redis storage)."""
        data = {
            "user_id": self.user_id,
            "items": {k: v.to_dict() for k, v in self.items.items()},
            "updated_at": self.updated_at.isoformat(),
        }
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def deserialize(cls, json_str: str) -> "ShoppingCart":
        """Deserialize cart from JSON string."""
        data = json.loads(json_str)
        cart = cls(user_id=data.get("user_id"))
        for sku_id, item_data in data.get("items", {}).items():
            cart.items[sku_id] = CartItem(
                sku_id=item_data["sku_id"],
                sku_name=item_data["sku_name"],
                price=item_data["price"],
                amount=item_data["amount"],
                selected=item_data["selected"],
            )
        return cart

    def merge(self, other: "ShoppingCart") -> None:
        """
        Merge another cart into this one.

        Used when a guest user logs in and their guest cart
        needs to be merged with their persistent cart.
        """
        for sku_id, other_item in other.items.items():
            if sku_id in self.items:
                self.items[sku_id].amount += other_item.amount
            else:
                self.items[sku_id] = CartItem(
                    sku_id=other_item.sku_id,
                    sku_name=other_item.sku_name,
                    price=other_item.price,
                    amount=other_item.amount,
                    selected=other_item.selected,
                )
        self.updated_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# Section 6: Order Processing and Inventory (订单处理与库存管理)
# ---------------------------------------------------------------------------


class OrderStatus(Enum):
    """Order lifecycle states."""
    PENDING = "pending"           # Awaiting payment
    PAID = "paid"                 # Payment confirmed
    PROCESSING = "processing"     # Being prepared
    SHIPPED = "shipped"           # In transit
    DELIVERED = "delivered"       # Received by customer
    COMPLETED = "completed"       # After review period
    CANCELLED = "cancelled"       # Cancelled by user or system
    REFUNDING = "refunding"       # Refund in progress
    REFUNDED = "refunded"         # Refund completed


@dataclass
class OrderItem:
    """An item within an order."""
    sku_id: str
    sku_name: str
    price: float
    quantity: int
    subtotal: float = 0.0

    def __post_init__(self) -> None:
        self.subtotal = self.price * self.quantity


@dataclass
class Order:
    """
    E-commerce order entity.

    Tracks the complete lifecycle from creation through payment,
    fulfillment, and potential refund.
    """
    order_id: str = field(default_factory=lambda: f"ORD-{uuid.uuid4().hex[:12].upper()}")
    user_id: str = ""
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    total_amount: float = 0.0
    shipping_address: str = ""
    payment_method: str = ""
    payment_time: Optional[datetime] = None
    shipping_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    cancel_time: Optional[datetime] = None
    cancel_reason: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.items:
            self.total_amount = sum(item.subtotal for item in self.items)

    def can_cancel(self) -> bool:
        return self.status in (OrderStatus.PENDING, OrderStatus.PAID)

    def can_refund(self) -> bool:
        return self.status in (
            OrderStatus.PAID, OrderStatus.PROCESSING,
            OrderStatus.SHIPPED, OrderStatus.DELIVERED,
        )

    def transition(self, new_status: OrderStatus) -> bool:
        """Attempt to transition to a new status."""
        valid_transitions: Dict[OrderStatus, Set[OrderStatus]] = {
            OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
            OrderStatus.PAID: {OrderStatus.PROCESSING, OrderStatus.CANCELLED, OrderStatus.REFUNDING},
            OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED, OrderStatus.REFUNDING},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.REFUNDING},
            OrderStatus.DELIVERED: {OrderStatus.COMPLETED, OrderStatus.REFUNDING},
            OrderStatus.COMPLETED: set(),
            OrderStatus.CANCELLED: set(),
            OrderStatus.REFUNDING: {OrderStatus.REFUNDED},
            OrderStatus.REFUNDED: set(),
        }
        if new_status in valid_transitions.get(self.status, set()):
            self.status = new_status
            self.updated_at = datetime.utcnow()
            now = datetime.utcnow()
            if new_status == OrderStatus.PAID:
                self.payment_time = now
            elif new_status == OrderStatus.SHIPPED:
                self.shipping_time = now
            elif new_status == OrderStatus.DELIVERED:
                self.delivery_time = now
            elif new_status == OrderStatus.CANCELLED:
                self.cancel_time = now
            return True
        return False


class InventoryManager:
    """
    Inventory management with overselling prevention.

    Implements three strategies to prevent overselling:
    1. Pessimistic locking: SELECT ... FOR UPDATE
    2. Optimistic locking: version check on UPDATE
    3. Atomic decrement: WHERE stock >= quantity

    This class simulates the database-level operations.
    """

    def __init__(self) -> None:
        self.stock: Dict[str, int] = {}
        self.reserved: Dict[str, int] = {}  # Reserved but not yet purchased
        self.lock_version: Dict[str, int] = {}  # For optimistic locking

    def set_stock(self, sku_id: str, quantity: int) -> None:
        """Initialize stock for an SKU."""
        self.stock[sku_id] = quantity
        self.reserved[sku_id] = 0
        self.lock_version[sku_id] = 0

    def get_available(self, sku_id: str) -> int:
        """Get available stock (total - reserved)."""
        total = self.stock.get(sku_id, 0)
        reserved = self.reserved.get(sku_id, 0)
        return max(0, total - reserved)

    def reserve(self, sku_id: str, quantity: int) -> bool:
        """
        Reserve stock (atomic decrement pattern).

        Simulates: UPDATE inventory SET stock = stock - %s
                   WHERE sku_id = %s AND stock >= %s

        Returns True if reservation succeeded, False if insufficient stock.
        """
        available = self.get_available(sku_id)
        if available >= quantity:
            self.reserved[sku_id] = self.reserved.get(sku_id, 0) + quantity
            return True
        return False

    def confirm_reservation(self, sku_id: str, quantity: int) -> bool:
        """Confirm a reservation (convert reserved to purchased)."""
        if self.reserved.get(sku_id, 0) >= quantity:
            self.stock[sku_id] = self.stock.get(sku_id, 0) - quantity
            self.reserved[sku_id] -= quantity
            self.lock_version[sku_id] = self.lock_version.get(sku_id, 0) + 1
            return True
        return False

    def release_reservation(self, sku_id: str, quantity: int) -> None:
        """Release a reservation (e.g., on order timeout)."""
        self.reserved[sku_id] = max(
            0, self.reserved.get(sku_id, 0) - quantity
        )

    def restock(self, sku_id: str, quantity: int) -> None:
        """Add stock back (e.g., returns)."""
        self.stock[sku_id] = self.stock.get(sku_id, 0) + quantity


class OrderProcessor:
    """
    Order processing system.

    Handles:
    - Order creation from cart
    - Inventory reservation and confirmation
    - Payment processing
    - Order status transitions
    - Timeout-based auto-cancellation
    """

    def __init__(self, inventory: InventoryManager) -> None:
        self.inventory = inventory
        self.orders: Dict[str, Order] = {}
        self._payment_timeout_minutes: int = 30

    def create_order(
        self,
        user_id: str,
        cart: ShoppingCart,
        shipping_address: str = "",
    ) -> Optional[Order]:
        """
        Create an order from a shopping cart.

        Steps:
        1. Validate cart items
        2. Reserve inventory
        3. Create order record
        4. Return order for payment processing
        """
        selected = cart.selected_items
        if not selected:
            return None

        # Reserve inventory for all items
        reservations: List[Tuple[str, int]] = []
        for item in selected:
            if self.inventory.reserve(item.sku_id, item.amount):
                reservations.append((item.sku_id, item.amount))
            else:
                # Rollback reservations
                for sku_id, qty in reservations:
                    self.inventory.release_reservation(sku_id, qty)
                return None

        # Create order
        order_items = [
            OrderItem(
                sku_id=item.sku_id,
                sku_name=item.sku_name,
                price=item.price,
                quantity=item.amount,
            )
            for item in selected
        ]

        order = Order(
            user_id=user_id,
            items=order_items,
            shipping_address=shipping_address,
        )
        self.orders[order.order_id] = order
        return order

    def process_payment(self, order_id: str, payment_method: str = "alipay") -> bool:
        """
        Process payment for an order.

        In production, this would integrate with Alipay/WeChat Pay APIs.
        """
        order = self.orders.get(order_id)
        if order is None:
            return False

        if not order.transition(OrderStatus.PAID):
            return False

        order.payment_method = payment_method

        # Confirm inventory reservations
        for item in order.items:
            self.inventory.confirm_reservation(item.sku_id, item.quantity)

        return True

    def cancel_order(self, order_id: str, reason: str = "") -> bool:
        """Cancel an order and release inventory."""
        order = self.orders.get(order_id)
        if order is None:
            return False

        if not order.can_cancel():
            return False

        # Release inventory
        for item in order.items:
            self.inventory.release_reservation(item.sku_id, item.quantity)

        order.cancel_reason = reason
        return order.transition(OrderStatus.CANCELLED)

    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        order = self.orders.get(order_id)
        return order.status if order else None

    def get_user_orders(
        self, user_id: str, status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """Get all orders for a user, optionally filtered by status."""
        orders = [o for o in self.orders.values() if o.user_id == user_id]
        if status:
            orders = [o for o in orders if o.status == status]
        orders.sort(key=lambda o: o.created_at, reverse=True)
        return orders


# ---------------------------------------------------------------------------
# Section 7: Flash Sale System (秒杀系统)
# ---------------------------------------------------------------------------


@dataclass
class FlashSaleItem:
    """A flash sale (seckill) event item."""
    event_id: str
    sku_id: str
    original_price: float
    sale_price: float
    total_stock: int
    remaining_stock: int
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime = field(default_factory=datetime.utcnow)
    max_per_user: int = 1
    is_active: bool = True

    @property
    def discount_pct(self) -> float:
        if self.original_price > 0:
            return round((1 - self.sale_price / self.original_price) * 100, 1)
        return 0.0

    @property
    def is_sold_out(self) -> bool:
        return self.remaining_stock <= 0


class FlashSaleManager:
    """
    Flash sale (seckill) management system.

    Handles high-concurrency scenarios:
    - Redis-based atomic stock decrement (simulated)
    - User purchase limits
    - Request rate limiting
    - Queue-based order processing

    Architecture:
    - Frontend: JS countdown, disable repeated clicks
    - Nginx: Rate limiting, request queuing
    - Application: Redis DECR for atomic stock management
    - Database: Async order persistence via message queue
    """

    def __init__(self) -> None:
        self.events: Dict[str, FlashSaleItem] = {}
        self.user_purchases: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.request_counts: CounterType[str] = Counter()

    def create_event(
        self,
        event_id: str,
        sku_id: str,
        original_price: float,
        sale_price: float,
        stock: int,
        duration_minutes: int = 60,
        max_per_user: int = 1,
    ) -> FlashSaleItem:
        """Create a flash sale event."""
        now = datetime.utcnow()
        event = FlashSaleItem(
            event_id=event_id,
            sku_id=sku_id,
            original_price=original_price,
            sale_price=sale_price,
            total_stock=stock,
            remaining_stock=stock,
            start_time=now,
            end_time=now + timedelta(minutes=duration_minutes),
            max_per_user=max_per_user,
        )
        self.events[event_id] = event
        return event

    def attempt_purchase(
        self, event_id: str, user_id: str
    ) -> Tuple[bool, str]:
        """
        Attempt a flash sale purchase.

        Returns (success, message) tuple.

        Checks performed:
        1. Event exists and is active
        2. Event hasn't ended
        3. User hasn't exceeded purchase limit
        4. Stock available (atomic decrement)

        In production, steps 3-4 would be handled by Redis:
        - WATCH event:{id}:stock
        - MULTI
        - DECR event:{id}:stock
        - SADD event:{id}:users {user_id}
        - EXEC
        """
        event = self.events.get(event_id)
        if event is None:
            return False, "Event not found"

        now = datetime.utcnow()
        if now < event.start_time:
            return False, "Sale hasn't started yet"
        if now > event.end_time:
            return False, "Sale has ended"
        if not event.is_active:
            return False, "Sale is inactive"

        # Rate limiting
        self.request_counts[user_id] += 1
        if self.request_counts[user_id] > 10:
            return False, "Too many requests; please try again later"

        # Check per-user limit
        user_bought = self.user_purchases[user_id][event_id]
        if user_bought >= event.max_per_user:
            return False, f"Purchase limit reached ({event.max_per_user} per user)"

        # Atomic stock decrement (simulated Redis DECR)
        if event.remaining_stock <= 0:
            return False, "Sold out"

        event.remaining_stock -= 1
        self.user_purchases[user_id][event_id] += 1
        return True, "Purchase successful"

    def get_event_stats(self, event_id: str) -> Dict[str, Any]:
        """Get event statistics."""
        event = self.events.get(event_id)
        if event is None:
            return {}
        sold = event.total_stock - event.remaining_stock
        return {
            "event_id": event_id,
            "sku_id": event.sku_id,
            "original_price": event.original_price,
            "sale_price": event.sale_price,
            "discount": f"{event.discount_pct}%",
            "total_stock": event.total_stock,
            "sold": sold,
            "remaining": event.remaining_stock,
            "sell_through_rate": f"{sold / event.total_stock * 100:.1f}%",
            "unique_buyers": len(self.user_purchases),
        }


# ---------------------------------------------------------------------------
# Section 8: Demonstration Functions
# ---------------------------------------------------------------------------


def demonstrate_product_catalog() -> None:
    """Show SPU/SKU product model."""
    print("=" * 70)
    print("PART 1: Product Catalog (SPU/SKU Model)")
    print("=" * 70)

    catalog = ProductCatalog()

    # Create SPU
    iphone_spu = SPUCategory(
        spu_id="SPU-001",
        name="iPhone 15 Pro",
        brand="Apple",
        description="Apple iPhone 15 Pro with A17 Pro chip",
        category_path="Electronics > Phones > Apple",
    )
    catalog.add_spu(iphone_spu)

    # Create SKUs (variants)
    variants = [
        {"name": "iPhone 15 Pro 128GB Natural Titanium", "price": 7999, "attrs": {"color": "Natural Titanium", "storage": "128GB"}},
        {"name": "iPhone 15 Pro 256GB Natural Titanium", "price": 8999, "attrs": {"color": "Natural Titanium", "storage": "256GB"}},
        {"name": "iPhone 15 Pro 128GB Blue Titanium", "price": 7999, "attrs": {"color": "Blue Titanium", "storage": "128GB"}},
        {"name": "iPhone 15 Pro 256GB Blue Titanium", "price": 8999, "attrs": {"color": "Blue Titanium", "storage": "256GB"}},
        {"name": "iPhone 15 Pro 512GB Black Titanium", "price": 10999, "attrs": {"color": "Black Titanium", "storage": "512GB"}},
    ]

    for i, v in enumerate(variants):
        sku = SKU(
            sku_id=f"SKU-{i+1:04d}",
            spu_id="SPU-001",
            name=v["name"],
            price=v["price"],
            original_price=v["price"],
            stock=100 + i * 50,
            attributes=v["attrs"],
        )
        catalog.add_sku(sku)

    print(f"\n  Total SPUs: {catalog.total_products}")
    print(f"  Total SKUs: {catalog.total_skus}")

    # Show SPU and its SKUs
    spu = catalog.get_spu("SPU-001")
    print(f"\n  SPU: {spu.name} by {spu.brand}")
    skus = catalog.get_skus_for_spu("SPU-001")
    for sku in skus:
        print(f"    {sku.sku_id}: {sku.name} | CNY {sku.price} | Stock: {sku.stock}")

    # Filter by attribute
    print(f"\n  Filter by color='Blue Titanium':")
    blue_skus = catalog.filter_by_attribute("color", "Blue Titanium")
    for sku in blue_skus:
        print(f"    {sku.name} -- CNY {sku.price}")


def demonstrate_search_engine() -> None:
    """Show product search engine."""
    print("\n" + "=" * 70)
    print("PART 2: Product Search Engine")
    print("=" * 70)

    engine = ProductSearchEngine()

    # Index some products
    products = [
        ("SKU-001", "Apple iPhone 15 Pro Max 256GB 深空黑色", "Apple", "Electronics > Phones", 9999, ["apple", "iphone", "手机", "5G"]),
        ("SKU-002", "Samsung Galaxy S24 Ultra 512GB 钛灰色", "Samsung", "Electronics > Phones", 10999, ["samsung", "galaxy", "手机", "5G"]),
        ("SKU-003", "华为 Mate 60 Pro 512GB 雅丹黑", "华为", "Electronics > Phones", 6999, ["华为", "mate", "手机", "5G"]),
        ("SKU-004", "小米 14 Ultra 1TB 白色", "小米", "Electronics > Phones", 5999, ["小米", "手机", "摄影"]),
        ("SKU-005", "MacBook Pro 14英寸 M3 Pro 银色", "Apple", "Electronics > Laptops", 14999, ["apple", "macbook", "笔记本", "M3"]),
        ("SKU-006", "联想 ThinkPad X1 Carbon 黑色", "联想", "Electronics > Laptops", 9999, ["联想", "thinkpad", "笔记本", "商务"]),
        ("SKU-007", "AirPods Pro 2 USB-C", "Apple", "Electronics > Audio", 1899, ["apple", "耳机", "降噪"]),
        ("SKU-008", "索尼 WH-1000XM5 黑色", "索尼", "Electronics > Audio", 2499, ["索尼", "耳机", "降噪", "头戴"]),
    ]

    for sku_id, name, brand, cat, price, tags in products:
        doc = SearchDocument(
            doc_id=sku_id, title=name, body=name,
            category=cat, brand=brand, price=price, tags=tags,
        )
        engine.index.add_document(doc)

    print(f"\n  Indexed {engine.index.doc_count} products")

    # Search
    queries = ["苹果手机", "5G手机", "笔记本", "降噪耳机"]
    for query in queries:
        results = engine.search(query, top_k=3)
        print(f"\n  Search: '{query}'")
        for sku_id, score in results:
            doc = engine.index.documents[sku_id]
            print(f"    [{score:.4f}] {doc.title} -- CNY {doc.price}")

    # Hot searches
    print(f"\n  Hot search terms:")
    for term, count in engine.get_hot_searches():
        print(f"    '{term}': {count} searches")


def demonstrate_recommendation() -> None:
    """Show recommendation engine."""
    print("\n" + "=" * 70)
    print("PART 3: Recommendation Engine")
    print("=" * 70)

    engine = RecommendationEngine()

    # Set product attributes
    products = {
        "SKU-001": ("Phones", {"apple", "iphone", "5G", "premium"}),
        "SKU-002": ("Phones", {"samsung", "galaxy", "5G", "premium"}),
        "SKU-003": ("Phones", {"huawei", "5G", "premium"}),
        "SKU-004": ("Phones", {"xiaomi", "5G", "camera"}),
        "SKU-005": ("Laptops", {"apple", "macbook", "pro", "M3"}),
        "SKU-006": ("Laptops", {"lenovo", "thinkpad", "business"}),
        "SKU-007": ("Audio", {"apple", "earbuds", "noise-cancel"}),
        "SKU-008": ("Audio", {"sony", "headphones", "noise-cancel"}),
    }
    for sku_id, (cat, tags) in products.items():
        engine.set_product_attributes(sku_id, cat, tags)

    # Simulate user purchase history
    engine.record_purchase("user-A", "SKU-001", 5.0)
    engine.record_purchase("user-A", "SKU-005", 5.0)
    engine.record_purchase("user-A", "SKU-007", 4.0)

    engine.record_purchase("user-B", "SKU-001", 5.0)
    engine.record_purchase("user-B", "SKU-002", 4.0)
    engine.record_purchase("user-B", "SKU-008", 5.0)

    engine.record_purchase("user-C", "SKU-003", 4.0)
    engine.record_purchase("user-C", "SKU-004", 5.0)
    engine.record_purchase("user-C", "SKU-008", 4.0)

    engine.record_purchase("user-D", "SKU-005", 5.0)
    engine.record_purchase("user-D", "SKU-006", 4.0)
    engine.record_purchase("user-D", "SKU-007", 3.0)

    # User-based collaborative filtering
    print("\n  User-based CF for user-A:")
    cf_results = engine.collaborative_filtering_user_based("user-A")
    for sku_id, score in cf_results:
        print(f"    {sku_id}: score={score:.4f}")

    # Item-based collaborative filtering
    print("\n  Item-based CF for user-A:")
    item_results = engine.collaborative_filtering_item_based("user-A")
    for sku_id, score in item_results:
        print(f"    {sku_id}: score={score:.4f}")

    # Content-based
    print("\n  Content-based for user-A:")
    cb_results = engine.content_based("user-A")
    for sku_id, score in cb_results:
        print(f"    {sku_id}: score={score:.4f}")

    # Hybrid
    print("\n  Hybrid recommendation for user-A:")
    hybrid_results = engine.hybrid_recommend("user-A")
    for sku_id, score in hybrid_results:
        print(f"    {sku_id}: score={score:.4f}")

    # Popularity
    print("\n  Most popular products:")
    popular = engine.popularity_based(5)
    for sku_id, count in popular:
        print(f"    {sku_id}: purchased by {count} users")


def demonstrate_shopping_cart() -> None:
    """Show shopping cart system."""
    print("\n" + "=" * 70)
    print("PART 4: Shopping Cart System")
    print("=" * 70)

    cart = ShoppingCart(user_id="user-001")

    # Add items
    cart.add_item("SKU-001", "iPhone 15 Pro 256GB", 8999, 1)
    cart.add_item("SKU-007", "AirPods Pro 2", 1899, 2)
    cart.add_item("SKU-005", "MacBook Pro 14 M3 Pro", 14999, 1)

    print(f"\n  Cart items: {cart.total_items}")
    print(f"  Cart total: CNY {cart.total:,.2f}")

    for item in cart.selected_items:
        print(f"    {item.sku_name} x{item.amount} = CNY {item.subtotal:,.2f}")

    # Serialize for storage
    serialized = cart.serialize()
    print(f"\n  Serialized cart size: {len(serialized)} bytes")

    # Deserialize
    restored = ShoppingCart.deserialize(serialized)
    print(f"  Restored cart items: {restored.total_items}")

    # Merge carts (guest + authenticated)
    guest_cart = ShoppingCart()
    guest_cart.add_item("SKU-008", "Sony WH-1000XM5", 2499, 1)
    guest_cart.add_item("SKU-007", "AirPods Pro 2", 1899, 1)  # Already in user cart

    print(f"\n  Merging guest cart ({guest_cart.total_items} items)...")
    cart.merge(guest_cart)
    print(f"  Merged cart items: {cart.total_items}")
    for item in cart.selected_items:
        print(f"    {item.sku_name} x{item.amount} = CNY {item.subtotal:,.2f}")


def demonstrate_order_processing() -> None:
    """Show order processing and inventory management."""
    print("\n" + "=" * 70)
    print("PART 5: Order Processing & Inventory Management")
    print("=" * 70)

    # Setup inventory
    inventory = InventoryManager()
    inventory.set_stock("SKU-001", 50)
    inventory.set_stock("SKU-007", 100)
    inventory.set_stock("SKU-005", 30)

    print("\n  Initial inventory:")
    for sku_id in ["SKU-001", "SKU-007", "SKU-005"]:
        print(f"    {sku_id}: available={inventory.get_available(sku_id)}")

    # Create order from cart
    cart = ShoppingCart(user_id="user-001")
    cart.add_item("SKU-001", "iPhone 15 Pro 256GB", 8999, 2)
    cart.add_item("SKU-007", "AirPods Pro 2", 1899, 1)

    processor = OrderProcessor(inventory)
    order = processor.create_order("user-001", cart, "Beijing, China")

    if order:
        print(f"\n  Order created: {order.order_id}")
        print(f"  Status: {order.status.value}")
        print(f"  Total: CNY {order.total_amount:,.2f}")
        for item in order.items:
            print(f"    {item.sku_name} x{item.quantity} = CNY {item.subtotal:,.2f}")

        print(f"\n  Inventory after reservation:")
        for sku_id in ["SKU-001", "SKU-007"]:
            print(f"    {sku_id}: available={inventory.get_available(sku_id)}")

        # Process payment
        if processor.process_payment(order.order_id, "alipay"):
            print(f"\n  Payment processed. Status: {order.status.value}")
            print(f"  Payment time: {order.payment_time}")

            print(f"\n  Inventory after payment:")
            for sku_id in ["SKU-001", "SKU-007"]:
                print(f"    {sku_id}: available={inventory.get_available(sku_id)}")

        # Status transitions
        for new_status in [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.COMPLETED]:
            success = order.transition(new_status)
            if success:
                print(f"  -> Status: {order.status.value}")
    else:
        print("  Failed to create order (insufficient stock).")


def demonstrate_flash_sale() -> None:
    """Show flash sale (seckill) system."""
    print("\n" + "=" * 70)
    print("PART 6: Flash Sale System (秒杀)")
    print("=" * 70)

    manager = FlashSaleManager()

    # Create flash sale event
    event = manager.create_event(
        event_id="FLASH-001",
        sku_id="SKU-001",
        original_price=8999,
        sale_price=5999,
        stock=5,
        duration_minutes=60,
        max_per_user=1,
    )
    print(f"\n  Flash sale: {event.sku_id}")
    print(f"  Price: CNY {event.sale_price} (was {event.original_price}, -{event.discount_pct}%)")
    print(f"  Stock: {event.remaining_stock}")

    # Simulate concurrent purchases
    print(f"\n  Simulating purchases:")
    for i in range(8):
        user_id = f"user-{i+1:03d}"
        success, msg = manager.attempt_purchase("FLASH-001", user_id)
        status = "SUCCESS" if success else "FAILED"
        print(f"    {user_id}: [{status}] {msg}")

    # Show stats
    stats = manager.get_event_stats("FLASH-001")
    print(f"\n  Event stats:")
    for key, val in stats.items():
        print(f"    {key}: {val}")


def demonstrate_ecommerce_architecture() -> None:
    """Show e-commerce platform architecture overview."""
    print("\n" + "=" * 70)
    print("PART 7: E-Commerce Architecture Overview")
    print("=" * 70)

    platforms = [
        EcommercePlatform(
            name="Alibaba (B2B)", model=BusinessModel.B2B,
            features=["wholesale", "trade assurance", "RFQ"],
            supports_full_text_search=True,
        ),
        EcommercePlatform(
            name="Taobao (C2C)", model=BusinessModel.C2C,
            features=["personal shops", "live streaming", "reviews"],
            supports_third_party_login=True, supports_recommendation=True,
        ),
        EcommercePlatform(
            name="JD.com (B2C)", model=BusinessModel.B2C,
            features=["self-operated logistics", "quality guarantee"],
            supports_flash_sale=True, supports_recommendation=True,
        ),
        EcommercePlatform(
            name="Tmall (B2B2C)", model=BusinessModel.B2B2C,
            features=["brand flagship stores", "Tmall Global"],
            supports_flash_sale=True, supports_recommendation=True,
            supports_full_text_search=True,
        ),
        EcommercePlatform(
            name="Meituan (O2O)", model=BusinessModel.O2O,
            features=["food delivery", "hotel booking", "group buying"],
            supports_recommendation=True,
        ),
    ]

    for p in platforms:
        print(f"\n  {p.summary()}")
        print(f"    Features: {', '.join(p.features[:4])}")


# ---------------------------------------------------------------------------
# Main Guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("E-Commerce Website Technical Analysis -- Enterprise Demo")
    print("=" * 70)

    demonstrate_product_catalog()
    demonstrate_search_engine()
    demonstrate_recommendation()
    demonstrate_shopping_cart()
    demonstrate_order_processing()
    demonstrate_flash_sale()
    demonstrate_ecommerce_architecture()

    print("\n" + "=" * 70)
    print("All demonstrations completed successfully.")
    print("=" * 70)
