"""
Day 12 - Common Data Structures: Sets (set / frozenset)

Covers:
  - Creating sets and frozensets
  - Set comprehension
  - Membership testing, iteration, binary operations
  - Comparison operators (subset / superset / equality)
  - Mutable set methods (add, discard, remove, pop, clear, isdisjoint)
  - frozenset as hashable element inside another set

C++ Comparison (Python set vs C++ std::unordered_set):
  ---------------------------------------------------------------
  | Feature                    | Python set       | C++ unordered_set  |
  |----------------------------|------------------|--------------------|
  | Underlying structure       | Hash table        | Hash table          |
  | Element type restriction   | hashable only     | user-defined hasher |
  | Duplicate handling         | auto-dedup        | auto-dedup          |
  | Ordering guarantee         | none              | none                |
  | Membership test (avg)      | O(1)              | O(1)                |
  | Mutability                 | set = mutable     | mutable             |
  | Immutable variant          | frozenset         | N/A (use const &)   |
  | Set algebra                | &, |, -, ^        | custom algorithms   |
  | Element must be hashable   | yes (hash())      | yes (std::hash)     |
  ---------------------------------------------------------------
  Key difference: Python's frozenset is hashable itself and can be
  stored inside another set/dict key.  In C++ you would need a custom
  hash wrapper to achieve the same.

Enterprise Use Cases:
  1. Permission Deduplication - merge role-based permission sets
     without duplicates when assigning multiple roles to a user.
  2. Tag Management - compute common/unique tags across resources
     for analytics dashboards and access-control overlap reports.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# 1. Creating sets
# ---------------------------------------------------------------------------

def demo_create_sets() -> None:
    """Demonstrate the various ways to create a set."""
    # Literal syntax (note: {} with at least one element, otherwise it's a dict)
    set1: set[int] = {1, 2, 3, 3, 3, 2}
    print(f"set1 (literal, duplicates removed): {set1}")

    set2: set[str] = {"banana", "pitaya", "apple", "apple", "banana", "grape"}
    print(f"set2 (literal, strings): {set2}")

    # set() constructor from iterable
    set3: set[str] = set("hello")
    print(f"set3 (from string 'hello'): {set3}")

    set4: set[int] = set([1, 2, 2, 3, 3, 3, 2, 1])
    print(f"set4 (from list): {set4}")

    # Empty set must use set(), NOT {}
    empty: set[int] = set()
    print(f"empty set: {empty}  (type: {type(empty)})")


# ---------------------------------------------------------------------------
# 2. Set comprehension
# ---------------------------------------------------------------------------

def demo_set_comprehension() -> None:
    """Set comprehension mirrors list comprehension but produces a set."""
    # Multiples of 3 or 7 in range [1, 20)
    multiples: set[int] = {n for n in range(1, 20) if n % 3 == 0 or n % 7 == 0}
    print(f"Multiples of 3 or 7 in [1,20): {multiples}")

    # Unique word lengths from a sentence
    sentence: str = "the quick brown fox jumps over the lazy dog"
    lengths: set[int] = {len(word) for word in sentence.split()}
    print(f"Unique word lengths: {lengths}")


# ---------------------------------------------------------------------------
# 3. Membership testing & iteration
# ---------------------------------------------------------------------------

def demo_membership_and_iteration() -> None:
    """in / not in checks and for-in loop over a set."""
    languages: set[str] = {"Python", "C++", "Java", "Kotlin", "Swift"}

    print(f"'Python' in languages: {'Python' in languages}")
    print(f"'Ruby' in languages:   {'Ruby' in languages}")

    print("Iterating (order is implementation-dependent):")
    for lang in languages:
        print(f"  {lang}")


# ---------------------------------------------------------------------------
# 4. Binary operations: intersection, union, difference, symmetric difference
# ---------------------------------------------------------------------------

def demo_binary_operations() -> None:
    """All four set algebra operations via operators and methods."""
    set1: set[int] = {1, 2, 3, 4, 5, 6, 7}
    set2: set[int] = {2, 4, 6, 8, 10}

    # Intersection
    print(f"set1 & set2  = {set1 & set2}")
    print(f"set1.intersection(set2) = {set1.intersection(set2)}")

    # Union
    print(f"set1 | set2  = {set1 | set2}")
    print(f"set1.union(set2) = {set1.union(set2)}")

    # Difference
    print(f"set1 - set2  = {set1 - set2}")
    print(f"set1.difference(set2) = {set1.difference(set2)}")

    # Symmetric difference
    print(f"set1 ^ set2  = {set1 ^ set2}")
    print(f"set1.symmetric_difference(set2) = {set1.symmetric_difference(set2)}")

    # Compound assignment
    s: set[int] = {1, 3, 5, 7}
    s |= {2, 4, 6}
    print(f"After |= : {s}")   # {1, 2, 3, 4, 5, 6, 7}

    s &= {3, 6, 9}
    print(f"After &= : {s}")   # {3, 6}

    s -= {3}
    print(f"After -= : {s}")   # {6}


# ---------------------------------------------------------------------------
# 5. Comparison operators & subset / superset
# ---------------------------------------------------------------------------

def demo_comparisons() -> None:
    """Subset, superset, and equality checks."""
    set1: set[int] = {1, 3, 5}
    set2: set[int] = {1, 2, 3, 4, 5}
    set3: set[int] = {5, 4, 3, 2, 1}

    print(f"set1 < set2  (strict subset):  {set1 < set2}")   # True
    print(f"set1 <= set2 (subset):          {set1 <= set2}")  # True
    print(f"set2 < set3  (strict subset):   {set2 < set3}")   # False
    print(f"set2 <= set3 (subset):          {set2 <= set3}")  # True
    print(f"set2 > set1  (strict superset): {set2 > set1}")   # True
    print(f"set2 == set3 (equal):           {set2 == set3}")  # True

    # Method equivalents
    print(f"set1.issubset(set2):   {set1.issubset(set2)}")
    print(f"set2.issuperset(set1): {set2.issuperset(set1)}")


# ---------------------------------------------------------------------------
# 6. Mutable set methods: add, discard, remove, pop, clear, isdisjoint
# ---------------------------------------------------------------------------

def demo_set_methods() -> None:
    """CRUD-like operations on a mutable set."""
    s: set[int] = {1, 10, 100}

    # Add
    s.add(1000)
    s.add(10000)
    print(f"After add: {s}")

    # discard() - safe removal, no error if absent
    s.discard(10)
    print(f"After discard(10): {s}")

    # remove() - raises KeyError if absent; guard with membership check
    if 100 in s:
        s.remove(100)
    print(f"After remove(100): {s}")

    # pop() - removes and returns an arbitrary element
    popped: int = s.pop()
    print(f"popped: {popped}, remaining: {s}")

    # isdisjoint - check for zero overlap
    a: set[str] = {"Java", "Python", "C++", "Kotlin"}
    b: set[str] = {"Kotlin", "Swift", "Java", "Dart"}
    c: set[str] = {"HTML", "CSS", "JavaScript"}
    print(f"a.isdisjoint(b): {a.isdisjoint(b)}")  # False
    print(f"a.isdisjoint(c): {a.isdisjoint(c)}")  # True

    # clear
    s.clear()
    print(f"After clear: {s}")  # set()


# ---------------------------------------------------------------------------
# 7. frozenset - immutable, hashable set
# ---------------------------------------------------------------------------

def demo_frozenset() -> None:
    """frozenset supports all read-only set operations and is hashable."""
    fs1: frozenset[int] = frozenset({1, 3, 5, 7})
    fs2: frozenset[int] = frozenset(range(1, 6))

    print(f"fs1: {fs1}")
    print(f"fs2: {fs2}")
    print(f"fs1 & fs2 = {fs1 & fs2}")       # frozenset({1, 3, 5})
    print(f"fs1 | fs2 = {fs1 | fs2}")       # frozenset({1, 2, 3, 4, 5, 7})
    print(f"fs1 - fs2 = {fs1 - fs2}")       # frozenset({7})
    print(f"fs1 < fs2 = {fs1 < fs2}")       # False

    # frozenset is hashable -> can live inside another set
    set_of_frozensets: set[frozenset[int]] = {fs1, fs2}
    print(f"set of frozensets: {set_of_frozensets}")

    # frozenset can be a dict key too
    metadata: dict[frozenset[str], str] = {
        frozenset({"read", "write"}): "editor",
        frozenset({"read"}): "viewer",
    }
    print(f"metadata keys are frozensets: {metadata}")


# ---------------------------------------------------------------------------
# 8. Enterprise scenario: Permission Deduplication
# ---------------------------------------------------------------------------

def merge_permissions(*role_permission_sets: set[str]) -> set[str]:
    """
    Merge permission sets from multiple roles into one deduplicated set.

    In enterprise RBAC (Role-Based Access Control) systems, a user may be
    assigned several roles.  Each role carries its own set of permissions.
    Duplicates across roles are automatically eliminated by the set union.

    Args:
        *role_permission_sets: Variable number of permission sets, one per role.

    Returns:
        A single set containing all unique permissions.

    Example:
        >>> merge_permissions(
        ...     {"read:docs", "write:docs"},
        ...     {"read:docs", "admin:users"},
        ... )
        {'read:docs', 'write:docs', 'admin:users'}
    """
    merged: set[str] = set()
    for perm_set in role_permission_sets:
        merged |= perm_set
    return merged


def demo_permission_dedup() -> None:
    """Simulate deduplicating permissions across multiple roles."""
    role_admin: set[str] = {"read:docs", "write:docs", "delete:docs", "admin:users"}
    role_editor: set[str] = {"read:docs", "write:docs"}
    role_viewer: set[str] = {"read:docs"}

    user_roles: set[str] = role_admin | role_editor | role_viewer
    print(f"All permissions (union): {user_roles}")

    # Which permissions does admin have that viewer does not?
    admin_only: set[str] = role_admin - role_viewer
    print(f"Admin-only permissions: {admin_only}")

    # Which permissions are shared by all three roles?
    shared: set[str] = role_admin & role_editor & role_viewer
    print(f"Permissions common to all roles: {shared}")

    # Using the helper for N roles
    merged: set[str] = merge_permissions(role_admin, role_editor, role_viewer)
    print(f"Merged via helper: {merged}")


# ---------------------------------------------------------------------------
# 9. Enterprise scenario: Tag Management
# ---------------------------------------------------------------------------

def common_tags(*resource_tag_sets: set[str]) -> set[str]:
    """Return tags that appear in every given resource."""
    if not resource_tag_sets:
        return set()
    result: set[str] = resource_tag_sets[0]
    for tags in resource_tag_sets[1:]:
        result &= tags
    return result


def unique_tags(resource: str, all_resources: dict[str, set[str]]) -> set[str]:
    """Return tags that belong ONLY to the specified resource."""
    others: set[str] = set()
    for name, tags in all_resources.items():
        if name != resource:
            others |= tags
    return all_resources[resource] - others


def demo_tag_management() -> None:
    """Simulate tag-based resource classification and overlap analysis."""
    servers: dict[str, set[str]] = {
        "web-prod-01":    {"env:prod", "tier:web",   "region:us-east", "team:platform"},
        "web-prod-02":    {"env:prod", "tier:web",   "region:us-west", "team:platform"},
        "api-prod-01":    {"env:prod", "tier:api",   "region:us-east", "team:backend"},
        "db-staging-01":  {"env:staging", "tier:db",  "region:us-east", "team:data"},
    }

    print("--- All tags across resources ---")
    all_tags: set[str] = set()
    for tags in servers.values():
        all_tags |= tags
    print(f"  {all_tags}")

    print("\n--- Tags common to ALL resources ---")
    shared: set[str] = common_tags(*servers.values())
    print(f"  {shared or '(none)'}")

    print("\n--- Unique tags per resource ---")
    for name in servers:
        uniq: set[str] = unique_tags(name, servers)
        print(f"  {name}: {uniq or '(none)'}")

    print("\n--- Which resources share 'env:prod'? ---")
    prod_resources: set[str] = {name for name, tags in servers.items() if "env:prod" in tags}
    print(f"  {prod_resources}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sections: list[tuple[str, object]] = [
        ("1. Creating Sets", demo_create_sets),
        ("2. Set Comprehension", demo_set_comprehension),
        ("3. Membership & Iteration", demo_membership_and_iteration),
        ("4. Binary Operations", demo_binary_operations),
        ("5. Comparisons (subset / superset)", demo_comparisons),
        ("6. Set Methods", demo_set_methods),
        ("7. frozenset", demo_frozenset),
        ("8. Enterprise: Permission Dedup", demo_permission_dedup),
        ("9. Enterprise: Tag Management", demo_tag_management),
    ]

    for title, func in sections:
        print(f"\n{'=' * 60}")
        print(f" {title}")
        print(f"{'=' * 60}")
        func()
