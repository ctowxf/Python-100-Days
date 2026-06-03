"""
Day 23 - Python CSV File Reading and Writing
=============================================
Demonstrates the csv module, DictReader/DictWriter, and pandas for CSV.

C++ Comparison:
    In C++, parsing CSV requires manual string splitting with std::getline,
    std::stringstream, or custom tokenizers. Python's csv module handles
    quoting, escaping, dialects, and edge cases (embedded commas, newlines
    inside fields) automatically -- work that would take 100+ lines of C++.

    C++ approach (manual parsing):
        std::string line;
        while (std::getline(file, line)) {
            std::stringstream ss(line);
            std::string cell;
            while (std::getline(ss, cell, ',')) {
                // handle quotes, escapes, etc. manually
            }
        }

    Python approach:
        import csv
        with open('data.csv') as f:
            for row in csv.reader(f):
                print(row)  # already a list of strings
"""

from __future__ import annotations

import csv
import io
import random
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# pandas is optional; enterprise scripts often require it
try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# ---------------------------------------------------------------------------
# Helper: default output directory
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path(__file__).resolve().parent / "csv_output"


def ensure_output_dir() -> Path:
    """Create the output directory if it does not exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


# ===================================================================
# Part 1 -- Basic csv.writer / csv.reader
# ===================================================================

def demo_writer_basic(path: Path) -> None:
    """Write student scores to a CSV file using csv.writer.

    Mirrors the example from the tutorial: five students, three subjects.
    """
    names = ["关羽", "张飞", "赵云", "马超", "黄忠"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["姓名", "语文", "数学", "英语"])
        for name in names:
            scores = [random.randint(50, 100) for _ in range(3)]
            writer.writerow([name, *scores])
    print(f"[writer] wrote {len(names)} rows -> {path}")


def demo_reader_basic(path: Path) -> list[list[str]]:
    """Read the CSV file back using csv.reader and print each row."""
    rows: list[list[str]] = []
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            rows.append(row)
            print(f"  line {reader.line_num}: {row}")
    return rows


# ===================================================================
# Part 2 -- Custom dialect (pipe-delimited, all fields quoted)
# ===================================================================

def demo_writer_pipe_delimited(path: Path) -> None:
    """Write with pipe delimiter and QUOTE_ALL (as shown in the tutorial)."""
    names = ["关羽", "张飞", "赵云", "马超", "黄忠"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="|", quoting=csv.QUOTE_ALL)
        writer.writerow(["姓名", "语文", "数学", "英语"])
        for name in names:
            scores = [random.randint(50, 100) for _ in range(3)]
            writer.writerow([name, *scores])
    print(f"[writer|pipe] wrote rows -> {path}")


# ===================================================================
# Part 3 -- DictReader / DictWriter
# ===================================================================

@dataclass
class Employee:
    """Simple data class representing an employee record."""
    emp_id: int
    name: str
    department: str
    salary: float
    hire_date: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "emp_id": self.emp_id,
            "name": self.name,
            "department": self.department,
            "salary": self.salary,
            "hire_date": self.hire_date,
        }


def generate_sample_employees(n: int = 10) -> list[Employee]:
    """Generate *n* random Employee records for demonstration."""
    departments = ["Engineering", "Marketing", "Sales", "Finance", "HR"]
    base_date = datetime(2020, 1, 1)
    employees: list[Employee] = []
    for i in range(1, n + 1):
        employees.append(
            Employee(
                emp_id=1000 + i,
                name=f"Employee_{i:03d}",
                department=random.choice(departments),
                salary=round(random.uniform(50_000, 150_000), 2),
                hire_date=(base_date + timedelta(days=random.randint(0, 1500))).strftime("%Y-%m-%d"),
            )
        )
    return employees


def demo_dictwriter(path: Path, employees: list[Employee]) -> None:
    """Write Employee records using csv.DictWriter."""
    fieldnames = ["emp_id", "name", "department", "salary", "hire_date"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for emp in employees:
            writer.writerow(emp.to_dict())
    print(f"[DictWriter] wrote {len(employees)} employees -> {path}")


def demo_dictreader(path: Path) -> list[dict[str, str]]:
    """Read Employee CSV using csv.DictReader (column access by name)."""
    rows: list[dict[str, str]] = []
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    print(f"[DictReader] read {len(rows)} rows; fields = {reader.fieldnames}")
    return rows


# ===================================================================
# Part 4 -- Enterprise Example: Sales Report Generator
# ===================================================================

@dataclass
class SaleRecord:
    """A single sales transaction."""
    date: str
    region: str
    product: str
    quantity: int
    unit_price: float

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


def generate_sales_data(n: int = 50) -> list[SaleRecord]:
    """Produce synthetic sales data for demonstration."""
    regions = ["North", "South", "East", "West"]
    products = ["Widget-A", "Widget-B", "Gadget-X", "Gadget-Y", "Module-Z"]
    base_date = datetime(2025, 1, 1)
    records: list[SaleRecord] = []
    for _ in range(n):
        records.append(
            SaleRecord(
                date=(base_date + timedelta(days=random.randint(0, 364))).strftime("%Y-%m-%d"),
                region=random.choice(regions),
                product=random.choice(products),
                quantity=random.randint(1, 200),
                unit_price=round(random.uniform(10, 500), 2),
            )
        )
    return records


def write_sales_report(path: Path, records: list[SaleRecord]) -> None:
    """Write a sales CSV report with an extra 'total' column."""
    fieldnames = ["date", "region", "product", "quantity", "unit_price", "total"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow({**rec.__dict__, "total": f"{rec.total:.2f}"})
    print(f"[SalesReport] {len(records)} transactions -> {path}")


def summarize_sales_csv(path: Path) -> dict[str, float]:
    """Read the sales CSV and produce per-region revenue totals."""
    region_totals: dict[str, float] = {}
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            region = row["region"]
            region_totals[region] = region_totals.get(region, 0.0) + float(row["total"])
    return region_totals


# ===================================================================
# Part 5 -- Enterprise Example: Data Import / Export Pipeline
# ===================================================================

def export_to_csv(path: Path, data: list[dict[str, Any]], fieldnames: list[str]) -> int:
    """Generic CSV export utility used in ETL pipelines.

    Returns the number of rows written.
    """
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
    return len(data)


def import_from_csv(path: Path) -> list[dict[str, str]]:
    """Generic CSV import utility; returns list of row dicts."""
    with open(path, "r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ===================================================================
# Part 6 -- Enterprise Example: Log File Analysis
# ===================================================================

@dataclass
class LogEntry:
    """Represents one line from a CSV-formatted access log."""
    timestamp: str
    level: str
    source: str
    message: str

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> LogEntry:
        return cls(
            timestamp=d.get("timestamp", ""),
            level=d.get("level", "INFO"),
            source=d.get("source", "unknown"),
            message=d.get("message", ""),
        )


def generate_sample_log(path: Path, n: int = 30) -> None:
    """Create a sample CSV access log for analysis."""
    levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    sources = ["auth", "api", "db", "cache", "scheduler"]
    messages = [
        "Request processed successfully",
        "Timeout waiting for response",
        "Authentication failed for user",
        "Database connection pool exhausted",
        "Cache miss -- fetching from origin",
        "Rate limit exceeded",
        "Health check passed",
    ]
    base = datetime(2025, 6, 1, 8, 0, 0)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "level", "source", "message"])
        for i in range(n):
            ts = (base + timedelta(minutes=i * random.randint(1, 15))).strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([
                ts,
                random.choices(levels, weights=[50, 20, 15, 15])[0],
                random.choice(sources),
                random.choice(messages),
            ])
    print(f"[LogGenerator] {n} log entries -> {path}")


def analyze_log(path: Path) -> dict[str, dict[str, int]]:
    """Analyze a CSV log file: count entries per level and per source."""
    by_level: dict[str, int] = {}
    by_source: dict[str, int] = {}
    with open(path, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            level = row.get("level", "UNKNOWN")
            source = row.get("source", "unknown")
            by_level[level] = by_level.get(level, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
    return {"by_level": by_level, "by_source": by_source}


# ===================================================================
# Part 7 -- pandas Integration (if available)
# ===================================================================

def demo_pandas_csv(sales_path: Path, employee_path: Path) -> None:
    """Demonstrate pandas read_csv / to_csv for richer data analysis.

    pandas.read_csv returns a DataFrame -- far more powerful than csv.reader
    for filtering, grouping, aggregation, and visualization.
    """
    if not HAS_PANDAS:
        print("[pandas] skipped (pandas not installed)")
        return

    print("\n--- pandas: Sales Analysis ---")
    df_sales: pd.DataFrame = pd.read_csv(sales_path)
    print(f"  Shape: {df_sales.shape}")
    print(f"  Columns: {list(df_sales.columns)}")
    print(f"  Revenue by region:\n{df_sales.groupby('region')['total'].sum().to_string()}")

    # Export a filtered subset
    high_value = df_sales[df_sales["total"] > 5000]
    hv_path = OUTPUT_DIR / "high_value_sales.csv"
    high_value.to_csv(hv_path, index=False)
    print(f"  High-value transactions exported -> {hv_path}  ({len(high_value)} rows)")

    print("\n--- pandas: Employee Analysis ---")
    df_emp: pd.DataFrame = pd.read_csv(employee_path)
    print(f"  Shape: {df_emp.shape}")
    avg_salary = df_emp.groupby("department")["salary"].mean().round(2)
    print(f"  Avg salary by department:\n{avg_salary.to_string()}")


# ===================================================================
# Part 8 -- csv module vs C++ (detailed comparison comment block)
# ===================================================================

CPP_COMPARISON = """
==========================================================================
Python csv module  vs  Manual C++ CSV Parsing
==========================================================================

Feature                  | Python csv module                     | C++ (manual / third-party)
-------------------------|---------------------------------------|------------------------------------
Built-in                 | Yes (stdlib)                          | No -- need <fstream> + custom code
Quoting / escaping       | Automatic (RFC 4180 compliant)        | Manual implementation required
Dialect support          | Yes (excel, excel-tab, unix, custom)  | Must hand-code per delimiter
Embedded newlines        | Handled automatically                 | Complex state machine needed
Unicode / encoding       | Native (UTF-8, etc.)                  | Requires codec libraries
DictReader / DictWriter  | Built-in column-name mapping          | Manual struct mapping
Performance (small file) | Adequate                              | Slightly faster
Performance (big file)   | Good with pandas (C backend)          | Good with hand-optimized loops
Lines of code (basic)    | ~10 lines                             | ~80-120 lines

Python csv module abstracts away the tedious details of CSV parsing so
developers can focus on business logic rather than delimiter/quote handling.
==========================================================================
"""

# ===================================================================
# Main Entry Point
# ===================================================================

def main() -> None:
    """Run all demonstrations."""
    out = ensure_output_dir()
    print(f"Output directory: {out}\n")

    # --- Part 1: basic writer / reader ---
    print("=" * 60)
    print("Part 1: Basic csv.writer / csv.reader")
    print("=" * 60)
    scores_path = out / "scores.csv"
    demo_writer_basic(scores_path)
    print()
    demo_reader_basic(scores_path)

    # --- Part 2: pipe-delimited variant ---
    print("\n" + "=" * 60)
    print("Part 2: Pipe-delimited CSV (custom dialect)")
    print("=" * 60)
    pipe_path = out / "scores_pipe.csv"
    demo_writer_pipe_delimited(pipe_path)
    with open(pipe_path, "r", encoding="utf-8") as f:
        print(f"  Content preview:\n{f.read()}")

    # --- Part 3: DictWriter / DictReader ---
    print("=" * 60)
    print("Part 3: DictWriter / DictReader")
    print("=" * 60)
    emp_path = out / "employees.csv"
    employees = generate_sample_employees(8)
    demo_dictwriter(emp_path, employees)
    rows = demo_dictreader(emp_path)
    for r in rows[:3]:
        print(f"  {r}")
    if len(rows) > 3:
        print(f"  ... ({len(rows) - 3} more)")

    # --- Part 4: Sales report generator ---
    print("\n" + "=" * 60)
    print("Part 4: Enterprise -- Sales Report Generator")
    print("=" * 60)
    sales_path = out / "sales_report.csv"
    sales = generate_sales_data(40)
    write_sales_report(sales_path, sales)
    totals = summarize_sales_csv(sales_path)
    print("  Revenue by region:")
    for region, rev in sorted(totals.items()):
        print(f"    {region:>10s}: ${rev:,.2f}")

    # --- Part 5: Import / Export pipeline ---
    print("\n" + "=" * 60)
    print("Part 5: Enterprise -- Data Import / Export Pipeline")
    print("=" * 60)
    export_path = out / "export_employees.csv"
    n = export_to_csv(export_path, [e.to_dict() for e in employees], list(employees[0].to_dict().keys()))
    print(f"  Exported {n} records -> {export_path}")
    imported = import_from_csv(export_path)
    print(f"  Imported {len(imported)} records back")

    # --- Part 6: Log analysis ---
    print("\n" + "=" * 60)
    print("Part 6: Enterprise -- CSV Log Analysis")
    print("=" * 60)
    log_path = out / "access_log.csv"
    generate_sample_log(log_path, 25)
    analysis = analyze_log(log_path)
    print("  Entries by level:")
    for lvl, cnt in sorted(analysis["by_level"].items()):
        print(f"    {lvl:>8s}: {cnt}")
    print("  Entries by source:")
    for src, cnt in sorted(analysis["by_source"].items()):
        print(f"    {src:>10s}: {cnt}")

    # --- Part 7: pandas integration ---
    print("\n" + "=" * 60)
    print("Part 7: pandas CSV Integration")
    print("=" * 60)
    demo_pandas_csv(sales_path, emp_path)

    # --- Part 8: C++ comparison ---
    print(CPP_COMPARISON)

    print("Done. CSV files saved in:", out)


if __name__ == "__main__":
    main()
