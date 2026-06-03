"""
Day 22 - Object Serialization and Deserialization
===================================================

Serialization converts Python objects into a storable/transmittable format.
Deserialization reverses that process.

Three standard-library approaches are covered:
    1. json   - language-neutral text format (the industry standard for APIs)
    2. pickle - Python-specific binary format (arbitrary object graphs)
    3. shelve - dict-like persistent store built on top of pickle + dbm

C++ comparison note
-------------------
In C++ the de-facto JSON library is **nlohmann/json** (single-header).
Rough equivalence:

    Python                          C++ (nlohmann/json)
    ----------------------------    -----------------------------------
    json.dumps(obj)                 j.dump()              // -> std::string
    json.loads(s)                   json::parse(s)        // -> json object
    json.dump(obj, fp)              std::ofstream os(...); os << j;
    json.load(fp)                   json::parse(std::ifstream(...))

Key differences:
    - Python's json module works with dicts/lists natively.
      nlohmann/json uses its own `json` type; explicit conversion to/from
      user structs is done via `to_json` / `from_json` overloads.
    - Python silently converts int keys to strings (JSON spec).
      nlohmann/json preserves types until serialization.
    - nlohmann/json is header-only, compile-time checked, and faster for
      large payloads; Python's json module is simpler to use at the REPL.

Enterprise context
------------------
REST APIs exchange JSON payloads.  A typical Python web framework
(Django REST, FastAPI, Flask) serializes response dicts into JSON
using the same json module demonstrated here.
"""

from __future__ import annotations

import json
import os
import pickle
import shelve
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_DIR: Path = Path(tempfile.mkdtemp(prefix="day22_"))


def _out(filename: str) -> Path:
    """Return an absolute path under the temp directory."""
    return SAMPLE_DIR / filename


# ---------------------------------------------------------------------------
# 1. JSON - language-neutral, human-readable
# ---------------------------------------------------------------------------

@dataclass
class Car:
    brand: str
    max_speed: int


@dataclass
class Person:
    name: str
    age: int
    friends: list[str] = field(default_factory=list)
    cars: list[Car] = field(default_factory=list)


def demo_json_basics() -> None:
    """Serialize and deserialize with the json module."""
    person = Person(
        name="Luo Hao",
        age=40,
        friends=["Wang Dachui", "Bai Yuanfang"],
        cars=[
            Car("BMW", 240),
            Car("Audi", 280),
            Car("Benz", 280),
        ],
    )

    # Convert dataclass hierarchy to a plain dict, then to a JSON string.
    data: dict[str, Any] = asdict(person)
    json_str: str = json.dumps(data, ensure_ascii=False, indent=2)
    print("=== json.dumps (pretty-printed) ===")
    print(json_str)

    # Write to file with json.dump
    json_path: Path = _out("person.json")
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    print(f"\nWrote JSON to {json_path}")

    # Read back with json.load
    with open(json_path, encoding="utf-8") as fp:
        loaded: dict[str, Any] = json.load(fp)
    print(f"\n=== json.load -> dict ===")
    print(loaded)
    print(f"Type: {type(loaded)}")


def demo_json_custom_encoder() -> None:
    """Custom encoder to handle objects json does not know about natively."""

    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    payload: dict[str, Any] = {
        "event": "API response serialization",
        "timestamp": datetime.now(timezone.utc),
        "status": 200,
        "data": {"items": [1, 2, 3]},
    }

    encoded: str = json.dumps(payload, cls=DateTimeEncoder, indent=2)
    print("\n=== Custom encoder (datetime -> ISO string) ===")
    print(encoded)


def demo_json_roundtrip_types() -> None:
    """Show the JSON <-> Python type mapping."""
    sample: dict[str, Any] = {
        "object": {"key": "value"},      # dict  -> object
        "array": [1, 2, 3],              # list  -> array
        "string": "hello",               # str   -> string
        "number_int": 42,                # int   -> number
        "number_float": 3.14,            # float -> number
        "boolean": True,                 # bool  -> boolean
        "null": None,                    # None  -> null
    }
    s: str = json.dumps(sample, indent=2)
    print("\n=== JSON type round-trip ===")
    print(s)

    back: dict[str, Any] = json.loads(s)
    # Note: tuple would also become an array on dump but loads returns list.
    assert back["array"] == [1, 2, 3]
    assert back["null"] is None
    print("Round-trip assertions passed.")


# ---------------------------------------------------------------------------
# 2. PICKLE - Python-specific binary serialization
# ---------------------------------------------------------------------------

def demo_pickle() -> None:
    """
    Pickle can serialize almost any Python object (functions, classes, etc.)
    but is **not safe** for untrusted data -- never pickle.load from
    an untrusted source.
    """
    data: dict[str, Any] = {
        "scores": [98, 87, 92, 100],
        "meta": {"class": "A", "term": 2},
    }

    pkl_path: Path = _out("data.pkl")

    # Write
    with open(pkl_path, "wb") as fp:
        pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"\n=== pickle.dump -> {pkl_path} ===")
    print(f"File size: {pkl_path.stat().st_size} bytes")

    # Read
    with open(pkl_path, "rb") as fp:
        restored: dict[str, Any] = pickle.load(fp)
    print(f"pickle.load restored: {restored}")
    assert restored == data, "Pickle round-trip failed!"


def demo_pickle_complex_objects() -> None:
    """Pickle handles sets, tuples, nested structures, and custom objects."""
    complex_obj: dict[str, Any] = {
        "set": {1, 2, 3},
        "tuple": (4, 5, 6),
        "nested": {"a": {"b": {"c": [7, 8, 9]}}},
    }

    pkl_path: Path = _out("complex.pkl")
    with open(pkl_path, "wb") as fp:
        pickle.dump(complex_obj, fp)

    with open(pkl_path, "rb") as fp:
        loaded: dict[str, Any] = pickle.load(fp)

    assert loaded["set"] == {1, 2, 3}
    assert isinstance(loaded["set"], set)
    assert loaded["tuple"] == (4, 5, 6)
    print("\n=== pickle complex objects ===")
    print(f"Loaded: {loaded}")
    print("Types preserved: set, tuple, nested dict")


# ---------------------------------------------------------------------------
# 3. SHELVE - dict-like persistent key/value store
# ---------------------------------------------------------------------------

def demo_shelve() -> None:
    """
    shelve is a persistent dictionary.  Keys must be strings; values are
    pickled automatically.  Think of it as a lightweight embedded database.
    """
    shelf_path: str = str(_out("cache"))  # shelve appends its own extension

    # Write several entries
    with shelve.open(shelf_path) as db:
        db["user:1"] = {"name": "Alice", "role": "admin"}
        db["user:2"] = {"name": "Bob", "role": "viewer"}
        db["config"] = {"debug": False, "version": 2}
        print(f"\n=== shelve write: {len(db)} entries ===")

    # Read back
    with shelve.open(shelf_path) as db:
        print("Keys:", list(db.keys()))
        print("user:1 ->", db["user:1"])
        print("config ->", db["config"])

        # Update
        db["config"] = {"debug": True, "version": 3}
        print("Updated config ->", db["config"])


# ---------------------------------------------------------------------------
# 4. Enterprise pattern: API response serialization
# ---------------------------------------------------------------------------

@dataclass
class APIResponse:
    """
    A generic API envelope used by many enterprise REST APIs.
    Serializes cleanly to JSON for HTTP responses.
    """
    success: bool
    code: int
    message: str
    data: dict[str, Any] | list[Any] | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self, **kwargs: Any) -> str:
        """Serialize to a JSON string (ready for an HTTP response body)."""
        return json.dumps(asdict(self), ensure_ascii=False, **kwargs)

    @classmethod
    def from_json(cls, raw: str) -> APIResponse:
        """Deserialize from a JSON string."""
        d: dict[str, Any] = json.loads(raw)
        return cls(**d)


def demo_api_response_serialization() -> None:
    """Simulate constructing and serializing an API response."""
    # Successful response
    ok_resp = APIResponse(
        success=True,
        code=200,
        message="Fetched 3 records",
        data={"items": [{"id": 1, "name": "Widget"}, {"id": 2, "name": "Gadget"}]},
    )
    json_payload: str = ok_resp.to_json(indent=2)
    print("\n=== API response (success) ===")
    print(json_payload)

    # Simulate client-side deserialization
    parsed: APIResponse = APIResponse.from_json(json_payload)
    print(f"\nDeserialized: success={parsed.success}, code={parsed.code}, "
          f"items={len(parsed.data['items']) if parsed.data else 0}")

    # Error response
    err_resp = APIResponse(success=False, code=404, message="Resource not found")
    print("\n=== API response (error) ===")
    print(err_resp.to_json(indent=2))


# ---------------------------------------------------------------------------
# 5. Comparison table printed at runtime
# ---------------------------------------------------------------------------

def print_comparison_table() -> None:
    """Side-by-side comparison of json vs pickle vs shelve."""
    print("\n" + "=" * 72)
    print(f"{'Feature':<28} {'json':<16} {'pickle':<16} {'shelve':<16}")
    print("-" * 72)
    rows: list[tuple[str, str, str, str]] = [
        ("Format", "Text (JSON)", "Binary", "Binary (dbm)"),
        ("Human-readable", "Yes", "No", "No"),
        ("Cross-language", "Yes", "No (Python)", "No (Python)"),
        ("Supported types", "dict/list/str/int/float/bool/None",
         "Almost any", "Almost any (str keys)"),
        ("Security", "Safe", "UNTRUSTED RISK", "UNTRUSTED RISK"),
        ("Use case", "APIs, config", "Caching, deepcopy", "Simple DB"),
        ("C++ equivalent", "nlohmann/json", "Boost.Serialization", "N/A"),
    ]
    for feature, j, p, s in rows:
        print(f"{feature:<28} {j:<16} {p:<16} {s:<16}")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Working directory for demo files:", SAMPLE_DIR)
    print()

    # --- JSON ---
    demo_json_basics()
    demo_json_custom_encoder()
    demo_json_roundtrip_types()

    # --- Pickle ---
    demo_pickle()
    demo_pickle_complex_objects()

    # --- Shelve ---
    demo_shelve()

    # --- Enterprise API response ---
    demo_api_response_serialization()

    # --- Comparison ---
    print_comparison_table()

    print(f"\nDemo files written to: {SAMPLE_DIR}")
