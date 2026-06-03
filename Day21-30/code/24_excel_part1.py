"""
Day 24 - Python读写Excel文件 (Part 1): openpyxl Basics
=======================================================

This module demonstrates comprehensive Excel file operations using the openpyxl
library, covering:

  1. openpyxl fundamentals: workbook, worksheet, and cell manipulation
  2. Reading and writing data with type safety
  3. Applying formulas for automated calculations
  4. Styling cells with fonts, borders, fills, and alignment
  5. C++ comparison: Python openpyxl vs C++ libxlsxwriter
  6. Enterprise-grade examples:
      - Employee report generator
      - Inventory tracker
      - Financial summary generator

Requirements:
    pip install openpyxl

Reference:
    Day 24 material from "Python-100-Days" by Jackfrued
    https://github.com/jackfrued/Python-100-Days
"""

from __future__ import annotations

import datetime
import random
import string
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from openpyxl import Workbook, load_workbook
from openpyxl.cell import Cell
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    NamedStyle,
    PatternFill,
    Side,
    numbers,
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet


# ---------------------------------------------------------------------------
# Section 1: openpyxl Basics - Workbook, Sheet, and Cell Operations
# ---------------------------------------------------------------------------

def demonstrate_workbook_basics() -> None:
    """
    Demonstrate fundamental openpyxl operations:
    - Creating a workbook
    - Accessing and renaming worksheets
    - Reading / writing individual cells
    - Iterating over rows and columns
    """
    print("=" * 70)
    print("Section 1: openpyxl Basics - Workbook, Sheet, Cell Operations")
    print("=" * 70)

    # --- Create a new workbook ---
    wb: Workbook = Workbook()
    print(f"[INFO] Created workbook with default sheet: '{wb.sheetnames}'")

    # --- Access the active (default) worksheet ---
    ws: Worksheet = wb.active
    ws.title = "StudentScores"
    print(f"[INFO] Renamed active sheet to: '{ws.title}'")

    # --- Create additional worksheets ---
    ws_summary: Worksheet = wb.create_sheet(title="Summary")
    ws_raw: Worksheet = wb.create_sheet(title="RawData", index=0)
    print(f"[INFO] All sheets: {wb.sheetnames}")

    # --- Write data to cells (three equivalent styles) ---
    ws_raw["A1"] = "Experiment"
    ws_raw.cell(row=1, column=2, value="Date")
    ws_raw.cell(row=1, column=3, value="Value")

    # --- Iterate to populate sample data ---
    experiments: List[Tuple[str, str, float]] = [
        ("Trial-A", "2026-01-15", 45.3),
        ("Trial-B", "2026-02-20", 67.8),
        ("Trial-C", "2026-03-10", 52.1),
    ]
    for row_idx, (name, date_str, val) in enumerate(experiments, start=2):
        ws_raw.cell(row=row_idx, column=1, value=name)
        ws_raw.cell(row=row_idx, column=2, value=date_str)
        ws_raw.cell(row=row_idx, column=3, value=val)

    # --- Reading cells back ---
    print(f"[DATA] A1 (string):   {ws_raw['A1'].value!r}")
    print(f"[DATA] C2 (numeric):  {ws_raw.cell(row=2, column=3).value!r}")

    # --- Iterating over a range of rows ---
    print("[DATA] RawData contents:")
    for row in ws_raw.iter_rows(
        min_row=1, max_row=ws_raw.max_row, max_col=3, values_only=True
    ):
        print(f"       {row}")

    # --- Append rows efficiently ---
    ws.append(["Trial-D", "2026-04-05", 73.9])
    ws.append(["Trial-E", "2026-05-18", 81.2])

    # Save for later use by other demos
    demo_path = Path("demo_workbook_basics.xlsx")
    wb.save(demo_path)
    print(f"[INFO] Saved demo workbook to: {demo_path.resolve()}\n")


# ---------------------------------------------------------------------------
# Section 2: Formulas and Calculations
# ---------------------------------------------------------------------------

def demonstrate_formulas() -> None:
    """
    Demonstrate writing Excel formulas into cells using openpyxl.
    Formulas are written as strings prefixed with '=' and Excel evaluates
    them when the file is opened in a spreadsheet application.
    """
    print("=" * 70)
    print("Section 2: Formulas and Calculations")
    print("=" * 70)

    wb: Workbook = Workbook()
    ws: Worksheet = wb.active
    ws.title = "FormulaDemo"

    # --- Header row ---
    headers: List[str] = ["Product", "Q1", "Q2", "Q3", "Q4", "Total", "Average"]
    for col, header in enumerate(headers, start=1):
        ws.cell(row=1, column=col, value=header)

    # --- Data rows ---
    products: List[Tuple[str, int, int, int, int]] = [
        ("Widget-A", 120, 135, 142, 158),
        ("Widget-B", 98, 105, 110, 120),
        ("Widget-C", 200, 210, 195, 225),
    ]
    for row_idx, (name, q1, q2, q3, q4) in enumerate(products, start=2):
        ws.cell(row=row_idx, column=1, value=name)
        ws.cell(row=row_idx, column=2, value=q1)
        ws.cell(row=row_idx, column=3, value=q2)
        ws.cell(row=row_idx, column=4, value=q3)
        ws.cell(row=row_idx, column=5, value=q4)
        # SUM formula for annual total
        ws.cell(row=row_idx, column=6, value=f"=SUM(B{row_idx}:E{row_idx})")
        # AVERAGE formula
        ws.cell(row=row_idx, column=7, value=f"=AVERAGE(B{row_idx}:E{row_idx})")

    # --- Grand total row ---
    total_row: int = len(products) + 2
    ws.cell(row=total_row, column=1, value="Grand Total")
    for col in range(2, 7):  # B through F
        col_letter: str = get_column_letter(col)
        ws.cell(
            row=total_row,
            column=col,
            value=f"=SUM({col_letter}2:{col_letter}{total_row - 1})",
        )

    # --- COUNT and MAX formulas ---
    stats_row: int = total_row + 1
    ws.cell(row=stats_row, column=1, value="Product Count")
    ws.cell(row=stats_row, column=2, value=f"=COUNTA(A2:A{total_row - 1})")
    ws.cell(row=stats_row + 1, column=1, value="Max Q1 Sales")
    ws.cell(row=stats_row + 1, column=2, value=f"=MAX(B2:B{total_row - 1})")
    ws.cell(row=stats_row + 2, column=1, value="Min Q1 Sales")
    ws.cell(row=stats_row + 2, column=2, value=f"=MIN(B2:B{total_row - 1})")

    # --- VLOOKUP example (looking up Widget-A Q3 sales) ---
    ws.cell(row=stats_row + 3, column=1, value="Lookup: Widget-A Q3")
    ws.cell(
        row=stats_row + 3,
        column=2,
        value='=VLOOKUP("Widget-A",A2:E4,4,FALSE)',
    )

    print("[INFO] Wrote formulas: SUM, AVERAGE, COUNTA, MAX, MIN, VLOOKUP")
    print("[TIP]  Formulas are evaluated when opened in Excel/LibreOffice.\n")

    demo_path = Path("demo_formulas.xlsx")
    wb.save(demo_path)
    print(f"[INFO] Saved formula demo to: {demo_path.resolve()}\n")


# ---------------------------------------------------------------------------
# Section 3: Styling Cells
# ---------------------------------------------------------------------------

def _create_header_style() -> NamedStyle:
    """Create a reusable NamedStyle for table headers."""
    style = NamedStyle(name="header_style")
    style.font = Font(name="Arial", size=12, bold=True, color="FFFFFF")
    style.fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    style.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    style.border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    return style


def _create_data_style() -> NamedStyle:
    """Create a reusable NamedStyle for data cells."""
    style = NamedStyle(name="data_style")
    style.font = Font(name="Arial", size=10)
    style.alignment = Alignment(horizontal="center", vertical="center")
    style.border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    return style


def demonstrate_styling() -> None:
    """
    Demonstrate cell styling: fonts, fills, borders, alignment,
    column widths, and row heights.
    """
    print("=" * 70)
    print("Section 3: Styling Cells")
    print("=" * 70)

    wb: Workbook = Workbook()
    ws: Worksheet = wb.active
    ws.title = "StyledReport"

    header_style = _create_header_style()
    data_style = _create_data_style()

    headers: List[str] = ["Name", "Department", "Score", "Grade"]
    col_widths: List[int] = [20, 18, 12, 12]

    # --- Write headers with style ---
    for col, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell: Cell = ws.cell(row=1, column=col, value=header)
        cell.style = header_style
        ws.column_dimensions[get_column_letter(col)].width = width

    # --- Set row height for header ---
    ws.row_dimensions[1].height = 30

    # --- Alternating row colors ---
    light_fill = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
    records: List[Tuple[str, str, int, str]] = [
        ("Alice", "Engineering", 92, "A"),
        ("Bob", "Marketing", 78, "B"),
        ("Charlie", "Engineering", 85, "A"),
        ("Diana", "Sales", 67, "C"),
        ("Eve", "Engineering", 95, "A"),
    ]

    for row_idx, (name, dept, score, grade) in enumerate(records, start=2):
        for col_idx, value in enumerate([name, dept, score, grade], start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.style = data_style
            if row_idx % 2 == 0:
                cell.fill = light_fill

    # --- Conditional formatting: highlight scores >= 90 ---
    red_font = Font(name="Arial", size=10, bold=True, color="CC0000")
    for row_idx in range(2, len(records) + 2):
        score_cell = ws.cell(row=row_idx, column=3)
        if score_cell.value is not None and score_cell.value >= 90:
            score_cell.font = red_font

    print("[INFO] Applied header style, alternating row fills, and conditional formatting.\n")

    demo_path = Path("demo_styling.xlsx")
    wb.save(demo_path)
    print(f"[INFO] Saved styled report to: {demo_path.resolve()}\n")


# ---------------------------------------------------------------------------
# Section 4: C++ Comparison — Python openpyxl vs C++ libxlsxwriter
# ---------------------------------------------------------------------------

def print_cpp_comparison() -> None:
    """
    Print a detailed comparison between Python openpyxl and C++ libxlsxwriter.

    C++ libxlsxwriter (https://github.com/jmcnamara/libxlsxwriter):
      - A C library for creating Excel .xlsx files.
      - Write-only: cannot read or modify existing files.
      - Very fast and memory-efficient for large datasets.
      - Requires manual memory management (C-style) or RAII wrappers in C++.
      - No formula evaluation engine; formulas are stored as text for Excel.

    Python openpyxl:
      - Pure Python, read/write support for .xlsx files.
      - Rich API for formulas, charts, styles, data validation, pivot tables.
      - Slower than C++ for very large files but much faster to develop with.
      - Automatic memory management via Python's garbage collector.
      - Extensive community and documentation.
    """
    print("=" * 70)
    print("Section 4: Python openpyxl vs C++ libxlsxwriter")
    print("=" * 70)

    comparison_rows: List[Tuple[str, str, str]] = [
        ("Aspect", "Python openpyxl", "C++ libxlsxwriter"),
        ("-" * 22, "-" * 22, "-" * 22),
        ("Language", "Python", "C / C++"),
        ("Read Support", "Yes (full .xlsx)", "No (write-only)"),
        ("Write Support", "Yes", "Yes (.xlsx only)"),
        ("Performance", "Moderate", "Very High"),
        ("Memory Usage", "Higher (object overhead)", "Low (manual mgmt)"),
        ("Ease of Use", "Very High", "Moderate"),
        ("Formula Support", "Write formulas as strings", "Write formulas as strings"),
        ("Formula Eval", "No (deferred to Excel)", "No (deferred to Excel)"),
        ("Charts", "Built-in (Bar, Pie, Line, ...)", "Built-in (extensive)"),
        ("Styling", "Rich (fonts, fills, borders)", "Rich (formats, fills, borders)"),
        ("Large Files", "Feasible with read_only/write_only modes", "Excellent (streaming)"),
        ("Dependencies", "Pure Python (+ et_xmlfile)", "None (single C lib)"),
        ("Typical Use", "Automation, data pipelines, reports", "High-perf data export, embedded"),
    ]

    for row in comparison_rows:
        print(f"  {row[0]:<22} | {row[1]:<22} | {row[2]:<22}")

    print()
    print("  Key takeaway:")
    print("  - Choose openpyxl for rapid prototyping, read-modify-write workflows,")
    print("    and Python-centric automation pipelines.")
    print("  - Choose libxlsxwriter when you need maximum write performance in C/C++")
    print("    and do not need to read existing Excel files.")
    print()


# ---------------------------------------------------------------------------
# Section 5: Enterprise Example — Employee Report Generator
# ---------------------------------------------------------------------------

@dataclass
class Employee:
    """Represents an employee record."""
    emp_id: str
    name: str
    department: str
    position: str
    hire_date: datetime.date
    salary: float
    performance_score: float  # 0-100


def generate_employee_report(
    employees: Sequence[Employee],
    output_path: Union[str, Path] = "employee_report.xlsx",
) -> Path:
    """
    Generate a formatted employee report Excel workbook.

    Sheets created:
      - 'Employee Roster': full employee listing
      - 'Department Summary': aggregated department statistics

    Args:
        employees: Sequence of Employee dataclass instances.
        output_path: Destination file path.

    Returns:
        The resolved Path of the saved file.
    """
    output_path = Path(output_path)

    wb: Workbook = Workbook()
    header_style = _create_header_style()
    data_style = _create_data_style()
    currency_fmt = '#,##0.00 "CNY"'
    date_fmt = "YYYY-MM-DD"

    # ---- Sheet 1: Employee Roster ----
    ws_roster: Worksheet = wb.active
    ws_roster.title = "Employee Roster"

    roster_headers: List[str] = [
        "ID", "Name", "Department", "Position",
        "Hire Date", "Salary (CNY)", "Performance",
    ]
    roster_widths: List[int] = [10, 16, 16, 18, 14, 16, 14]

    for col, (hdr, w) in enumerate(zip(roster_headers, roster_widths), start=1):
        cell = ws_roster.cell(row=1, column=col, value=hdr)
        cell.style = header_style
        ws_roster.column_dimensions[get_column_letter(col)].width = w
    ws_roster.row_dimensions[1].height = 28

    for row_idx, emp in enumerate(employees, start=2):
        values: List[Any] = [
            emp.emp_id, emp.name, emp.department, emp.position,
            emp.hire_date, emp.salary, emp.performance_score,
        ]
        for col_idx, val in enumerate(values, start=1):
            cell = ws_roster.cell(row=row_idx, column=col_idx, value=val)
            cell.style = data_style
            if col_idx == 5:
                cell.number_format = date_fmt
            elif col_idx == 6:
                cell.number_format = currency_fmt

    # Add summary formulas at the bottom
    last_data_row: int = len(employees) + 1
    summary_row: int = last_data_row + 2
    ws_roster.cell(row=summary_row, column=4, value="Total Salary:").font = Font(bold=True)
    ws_roster.cell(
        row=summary_row, column=5,
        value=f"=SUM(F2:F{last_data_row})",
    ).number_format = currency_fmt
    ws_roster.cell(row=summary_row + 1, column=4, value="Avg Performance:").font = Font(bold=True)
    ws_roster.cell(
        row=summary_row + 1, column=5,
        value=f"=AVERAGE(G2:G{last_data_row})",
    ).number_format = "0.00"

    # Freeze the header row
    ws_roster.freeze_panes = "A2"

    # ---- Sheet 2: Department Summary ----
    ws_dept: Worksheet = wb.create_sheet(title="Department Summary")

    dept_headers: List[str] = [
        "Department", "Headcount", "Total Salary",
        "Avg Salary", "Avg Performance",
    ]
    for col, hdr in enumerate(dept_headers, start=1):
        cell = ws_dept.cell(row=1, column=col, value=hdr)
        cell.style = header_style
        ws_dept.column_dimensions[get_column_letter(col)].width = 18
    ws_dept.row_dimensions[1].height = 28

    # Aggregate data by department
    dept_data: Dict[str, List[Employee]] = {}
    for emp in employees:
        dept_data.setdefault(emp.department, []).append(emp)

    for row_idx, (dept, emps) in enumerate(sorted(dept_data.items()), start=2):
        headcount: int = len(emps)
        total_sal: float = sum(e.salary for e in emps)
        avg_sal: float = total_sal / headcount if headcount else 0.0
        avg_perf: float = (
            statistics.mean(e.performance_score for e in emps) if emps else 0.0
        )
        row_values: List[Any] = [dept, headcount, total_sal, avg_sal, avg_perf]
        for col_idx, val in enumerate(row_values, start=1):
            cell = ws_dept.cell(row=row_idx, column=col_idx, value=val)
            cell.style = data_style
            if col_idx in (3, 4):
                cell.number_format = currency_fmt
            elif col_idx == 5:
                cell.number_format = "0.00"

    wb.save(output_path)
    print(f"[INFO] Employee report saved to: {output_path.resolve()}")
    return output_path


# ---------------------------------------------------------------------------
# Section 6: Enterprise Example — Inventory Tracker
# ---------------------------------------------------------------------------

@dataclass
class InventoryItem:
    """Represents an inventory line item."""
    sku: str
    product_name: str
    category: str
    quantity_on_hand: int
    unit_cost: float
    reorder_level: int
    supplier: str


def generate_inventory_tracker(
    items: Sequence[InventoryItem],
    output_path: Union[str, Path] = "inventory_tracker.xlsx",
) -> Path:
    """
    Generate an inventory tracking workbook with stock status indicators.

    Sheets created:
      - 'Inventory': full item listing with total value formulas
      - 'Reorder Alerts': items below their reorder level
    """
    output_path = Path(output_path)
    wb: Workbook = Workbook()
    header_style = _create_header_style()
    data_style = _create_data_style()
    currency_fmt = '#,##0.00 "CNY"'

    # ---- Sheet 1: Inventory ----
    ws_inv: Worksheet = wb.active
    ws_inv.title = "Inventory"

    inv_headers: List[str] = [
        "SKU", "Product", "Category", "Qty On Hand",
        "Unit Cost", "Total Value", "Reorder Level", "Status", "Supplier",
    ]
    inv_widths: List[int] = [10, 22, 14, 14, 14, 16, 14, 12, 18]
    for col, (hdr, w) in enumerate(zip(inv_headers, inv_widths), start=1):
        cell = ws_inv.cell(row=1, column=col, value=hdr)
        cell.style = header_style
        ws_inv.column_dimensions[get_column_letter(col)].width = w
    ws_inv.row_dimensions[1].height = 28

    # Conditional fill colors for status
    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for row_idx, item in enumerate(items, start=2):
        ws_inv.cell(row=row_idx, column=1, value=item.sku).style = data_style
        ws_inv.cell(row=row_idx, column=2, value=item.product_name).style = data_style
        ws_inv.cell(row=row_idx, column=3, value=item.category).style = data_style
        ws_inv.cell(row=row_idx, column=4, value=item.quantity_on_hand).style = data_style

        cost_cell = ws_inv.cell(row=row_idx, column=5, value=item.unit_cost)
        cost_cell.style = data_style
        cost_cell.number_format = currency_fmt

        # Total Value = Qty * Unit Cost (formula)
        total_cell = ws_inv.cell(
            row=row_idx, column=6,
            value=f"=D{row_idx}*E{row_idx}",
        )
        total_cell.style = data_style
        total_cell.number_format = currency_fmt

        ws_inv.cell(row=row_idx, column=7, value=item.reorder_level).style = data_style

        # Status logic
        qty = item.quantity_on_hand
        reorder = item.reorder_level
        if qty <= 0:
            status = "OUT OF STOCK"
            status_fill = red_fill
        elif qty <= reorder:
            status = "LOW STOCK"
            status_fill = yellow_fill
        else:
            status = "IN STOCK"
            status_fill = green_fill

        status_cell = ws_inv.cell(row=row_idx, column=8, value=status)
        status_cell.style = data_style
        status_cell.fill = status_fill

        ws_inv.cell(row=row_idx, column=9, value=item.supplier).style = data_style

    # Summary formulas
    last_row: int = len(items) + 1
    sum_row: int = last_row + 2
    ws_inv.cell(row=sum_row, column=2, value="Total Inventory Value:").font = Font(bold=True)
    ws_inv.cell(
        row=sum_row, column=6,
        value=f"=SUM(F2:F{last_row})",
    ).number_format = currency_fmt
    ws_inv.cell(row=sum_row + 1, column=2, value="Total Items:").font = Font(bold=True)
    ws_inv.cell(row=sum_row + 1, column=6, value=f"=SUM(D2:D{last_row})")
    ws_inv.cell(row=sum_row + 2, column=2, value="Items Needing Reorder:").font = Font(bold=True)
    ws_inv.cell(
        row=sum_row + 2, column=6,
        value=f'=COUNTIF(H2:H{last_row},"LOW STOCK")+COUNTIF(H2:H{last_row},"OUT OF STOCK")',
    )

    ws_inv.freeze_panes = "A2"

    # ---- Sheet 2: Reorder Alerts ----
    ws_alert: Worksheet = wb.create_sheet(title="Reorder Alerts")
    alert_headers: List[str] = ["SKU", "Product", "Qty On Hand", "Reorder Level", "Deficit"]
    for col, hdr in enumerate(alert_headers, start=1):
        cell = ws_alert.cell(row=1, column=col, value=hdr)
        cell.style = header_style
        ws_alert.column_dimensions[get_column_letter(col)].width = 16
    ws_alert.row_dimensions[1].height = 28

    alert_row: int = 2
    for item in items:
        if item.quantity_on_hand <= item.reorder_level:
            ws_alert.cell(row=alert_row, column=1, value=item.sku).style = data_style
            ws_alert.cell(row=alert_row, column=2, value=item.product_name).style = data_style
            ws_alert.cell(row=alert_row, column=3, value=item.quantity_on_hand).style = data_style
            ws_alert.cell(row=alert_row, column=4, value=item.reorder_level).style = data_style
            deficit_cell = ws_alert.cell(
                row=alert_row, column=5,
                value=f"=D{alert_row}-C{alert_row}",
            )
            deficit_cell.style = data_style
            deficit_cell.fill = red_fill
            alert_row += 1

    wb.save(output_path)
    print(f"[INFO] Inventory tracker saved to: {output_path.resolve()}")
    return output_path


# ---------------------------------------------------------------------------
# Section 7: Enterprise Example — Financial Summary
# ---------------------------------------------------------------------------

@dataclass
class MonthlyFinancials:
    """Financial data for a single month."""
    month: str
    revenue: float
    cost_of_goods: float
    operating_expenses: float
    other_income: float = 0.0
    tax_rate: float = 0.25


def generate_financial_summary(
    data: Sequence[MonthlyFinancials],
    output_path: Union[str, Path] = "financial_summary.xlsx",
) -> Path:
    """
    Generate a financial summary workbook with derived metrics and charts.

    Sheets created:
      - 'P&L Statement': income statement with formulas
      - 'Chart Data': auto-generated bar chart of revenue vs net profit
    """
    output_path = Path(output_path)
    wb: Workbook = Workbook()
    header_style = _create_header_style()
    data_style = _create_data_style()
    currency_fmt = '#,##0.00'
    pct_fmt = '0.00%'

    # ---- Sheet 1: P&L Statement ----
    ws_pl: Worksheet = wb.active
    ws_pl.title = "P&L Statement"

    pl_headers: List[str] = [
        "Month", "Revenue", "COGS", "Gross Profit",
        "Gross Margin", "OpEx", "Other Income",
        "EBIT", "Tax", "Net Profit", "Net Margin",
    ]
    pl_widths: List[int] = [12, 16, 16, 16, 14, 16, 14, 16, 14, 16, 14]
    for col, (hdr, w) in enumerate(zip(pl_headers, pl_widths), start=1):
        cell = ws_pl.cell(row=1, column=col, value=hdr)
        cell.style = header_style
        ws_pl.column_dimensions[get_column_letter(col)].width = w
    ws_pl.row_dimensions[1].height = 28

    for row_idx, fin in enumerate(data, start=2):
        r: str = str(row_idx)

        ws_pl.cell(row=row_idx, column=1, value=fin.month).style = data_style
        ws_pl.cell(row=row_idx, column=2, value=fin.revenue).style = data_style
        ws_pl.cell(row=row_idx, column=2).number_format = currency_fmt
        ws_pl.cell(row=row_idx, column=3, value=fin.cost_of_goods).style = data_style
        ws_pl.cell(row=row_idx, column=3).number_format = currency_fmt

        # Gross Profit = Revenue - COGS
        ws_pl.cell(row=row_idx, column=4, value=f"=B{r}-C{r}").number_format = currency_fmt
        # Gross Margin = Gross Profit / Revenue
        ws_pl.cell(row=row_idx, column=5, value=f"=D{r}/B{r}").number_format = pct_fmt

        ws_pl.cell(row=row_idx, column=6, value=fin.operating_expenses).style = data_style
        ws_pl.cell(row=row_idx, column=6).number_format = currency_fmt
        ws_pl.cell(row=row_idx, column=7, value=fin.other_income).style = data_style
        ws_pl.cell(row=row_idx, column=7).number_format = currency_fmt

        # EBIT = Gross Profit - OpEx + Other Income
        ws_pl.cell(row=row_idx, column=8, value=f"=D{r}-F{r}+G{r}").number_format = currency_fmt
        # Tax = EBIT * tax_rate (if positive)
        ws_pl.cell(
            row=row_idx, column=9,
            value=f'=MAX(H{r},0)*{fin.tax_rate}',
        ).number_format = currency_fmt
        # Net Profit = EBIT - Tax
        ws_pl.cell(row=row_idx, column=10, value=f"=H{r}-I{r}").number_format = currency_fmt
        # Net Margin = Net Profit / Revenue
        ws_pl.cell(row=row_idx, column=11, value=f"=J{r}/B{r}").number_format = pct_fmt

    # Annual totals row
    total_row: int = len(data) + 2
    ws_pl.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True)
    for col in [2, 3, 4, 6, 7, 8, 9, 10]:
        letter = get_column_letter(col)
        ws_pl.cell(
            row=total_row, column=col,
            value=f"=SUM({letter}2:{letter}{total_row - 1})",
        ).number_format = currency_fmt
    # Average margins
    ws_pl.cell(
        row=total_row, column=5,
        value=f"=AVERAGE(E2:E{total_row - 1})",
    ).number_format = pct_fmt
    ws_pl.cell(
        row=total_row, column=11,
        value=f"=AVERAGE(K2:K{total_row - 1})",
    ).number_format = pct_fmt

    ws_pl.freeze_panes = "B2"

    # ---- Sheet 2: Revenue Chart ----
    ws_chart: Worksheet = wb.create_sheet(title="Chart Data")

    # Copy month, revenue, net profit for charting
    ws_chart.cell(row=1, column=1, value="Month")
    ws_chart.cell(row=1, column=2, value="Revenue")
    ws_chart.cell(row=1, column=3, value="Net Profit")
    for row_idx, fin in enumerate(data, start=2):
        ws_chart.cell(row=row_idx, column=1, value=fin.month)
        ws_chart.cell(row=row_idx, column=2, value=fin.revenue)
        ws_chart.cell(row=row_idx, column=3, value=f"='P&L Statement'!J{row_idx}")

    chart = BarChart()
    chart.type = "col"
    chart.title = "Monthly Revenue vs Net Profit"
    chart.y_axis.title = "Amount (CNY)"
    chart.x_axis.title = "Month"
    chart.style = 10
    chart.width = 24
    chart.height = 14

    categories = Reference(ws_chart, min_col=1, min_row=2, max_row=len(data) + 1)
    revenue_data = Reference(ws_chart, min_col=2, min_row=1, max_row=len(data) + 1)
    profit_data = Reference(ws_chart, min_col=3, min_row=1, max_row=len(data) + 1)
    chart.add_data(revenue_data, titles_from_data=True)
    chart.add_data(profit_data, titles_from_data=True)
    chart.set_categories(categories)
    ws_chart.add_chart(chart, "E2")

    wb.save(output_path)
    print(f"[INFO] Financial summary saved to: {output_path.resolve()}")
    return output_path


# ---------------------------------------------------------------------------
# Section 8: Utility — Reading an Existing Excel File
# ---------------------------------------------------------------------------

def read_excel_file(file_path: Union[str, Path]) -> List[List[Any]]:
    """
    Read all data from the first sheet of an Excel file.

    Args:
        file_path: Path to the .xlsx file.

    Returns:
        A list of rows, where each row is a list of cell values.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    wb = load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active

    rows: List[List[Any]] = []
    for row in ws.iter_rows(values_only=True):
        rows.append(list(row))

    wb.close()
    return rows


# ---------------------------------------------------------------------------
# Section 9: Data Generators (for demo purposes)
# ---------------------------------------------------------------------------

def _generate_sample_employees(count: int = 20) -> List[Employee]:
    """Generate synthetic employee records for demonstration."""
    departments = ["Engineering", "Marketing", "Sales", "Finance", "HR"]
    positions = ["Junior", "Senior", "Lead", "Manager", "Director"]
    surnames = ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou"]
    given_names = ["Wei", "Fang", "Ming", "Ling", "Jie", "Xin", "Yu", "Hua", "Jun", "Ping"]

    employees: List[Employee] = []
    for i in range(count):
        name = f"{random.choice(surnames)} {random.choice(given_names)}"
        dept = random.choice(departments)
        pos = random.choice(positions)
        hire_date = datetime.date(
            random.randint(2018, 2025),
            random.randint(1, 12),
            random.randint(1, 28),
        )
        salary = round(random.uniform(8000, 45000), 2)
        perf = round(random.uniform(50, 100), 1)
        emp_id = f"EMP{i + 1:04d}"
        employees.append(Employee(emp_id, name, dept, pos, hire_date, salary, perf))
    return employees


def _generate_sample_inventory(count: int = 15) -> List[InventoryItem]:
    """Generate synthetic inventory records for demonstration."""
    categories = ["Electronics", "Stationery", "Furniture", "Cleaning", "Food"]
    suppliers = ["Supplier-A", "Supplier-B", "Supplier-C", "Supplier-D"]

    items: List[InventoryItem] = []
    for i in range(count):
        sku = f"SKU{i + 1:04d}"
        product = f"Product-{random.choice(string.ascii_uppercase)}{random.randint(100, 999)}"
        cat = random.choice(categories)
        qty = random.randint(0, 500)
        cost = round(random.uniform(5, 500), 2)
        reorder = random.randint(10, 80)
        supplier = random.choice(suppliers)
        items.append(InventoryItem(sku, product, cat, qty, cost, reorder, supplier))
    return items


def _generate_sample_financials() -> List[MonthlyFinancials]:
    """Generate 12 months of synthetic financial data."""
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    records: List[MonthlyFinancials] = []
    base_revenue = 500_000.0
    for month in months:
        revenue = base_revenue * random.uniform(0.85, 1.25)
        cogs = revenue * random.uniform(0.35, 0.50)
        opex = revenue * random.uniform(0.15, 0.25)
        other = revenue * random.uniform(0.0, 0.05)
        records.append(MonthlyFinancials(month, round(revenue, 2), round(cogs, 2),
                                         round(opex, 2), round(other, 2)))
    return records


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations and generate enterprise report files."""
    print()
    print("#" * 70)
    print("#  Day 24: Python读写Excel文件 (Part 1) — openpyxl Comprehensive Demo")
    print("#" * 70)
    print()

    # Set random seed for reproducibility
    random.seed(42)

    # 1. Workbook basics
    demonstrate_workbook_basics()

    # 2. Formulas
    demonstrate_formulas()

    # 3. Styling
    demonstrate_styling()

    # 4. C++ comparison
    print_cpp_comparison()

    # 5. Enterprise: Employee Report
    print("=" * 70)
    print("Section 5: Enterprise Example — Employee Report Generator")
    print("=" * 70)
    employees = _generate_sample_employees(20)
    generate_employee_report(employees, "enterprise_employee_report.xlsx")
    # Demonstrate reading it back
    rows = read_excel_file("enterprise_employee_report.xlsx")
    print(f"[VERIFY] Employee report has {len(rows)} rows (including header).")
    print(f"[VERIFY] First data row: {rows[1] if len(rows) > 1 else 'N/A'}")
    print()

    # 6. Enterprise: Inventory Tracker
    print("=" * 70)
    print("Section 6: Enterprise Example — Inventory Tracker")
    print("=" * 70)
    inventory = _generate_sample_inventory(15)
    generate_inventory_tracker(inventory, "enterprise_inventory_tracker.xlsx")
    rows = read_excel_file("enterprise_inventory_tracker.xlsx")
    print(f"[VERIFY] Inventory tracker has {len(rows)} rows (including header).")
    print()

    # 7. Enterprise: Financial Summary
    print("=" * 70)
    print("Section 7: Enterprise Example — Financial Summary")
    print("=" * 70)
    financials = _generate_sample_financials()
    generate_financial_summary(financials, "enterprise_financial_summary.xlsx")
    rows = read_excel_file("enterprise_financial_summary.xlsx")
    print(f"[VERIFY] Financial summary has {len(rows)} rows (including header).")
    print()

    # Cleanup info
    print("=" * 70)
    print("All demo files generated successfully:")
    print("  - demo_workbook_basics.xlsx")
    print("  - demo_formulas.xlsx")
    print("  - demo_styling.xlsx")
    print("  - enterprise_employee_report.xlsx")
    print("  - enterprise_inventory_tracker.xlsx")
    print("  - enterprise_financial_summary.xlsx")
    print("=" * 70)
    print("\nOpen these files in Excel or LibreOffice to see formulas and charts rendered.")


if __name__ == "__main__":
    main()
