"""
Day 25 - Python读写Excel文件 (Part 2): Advanced openpyxl

Covers: openpyxl read/write, cell styles, formulas, charts (Bar, Line, Pie),
        merged cells, conditional formatting, freeze panes, and an enterprise
        dashboard export example.
"""

from __future__ import annotations

import datetime
import random
from pathlib import Path
from typing import Any, Sequence

import openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    NamedStyle,
    PatternFill,
    Side,
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

# ---------------------------------------------------------------------------
# 1. Reading an existing Excel file
# ---------------------------------------------------------------------------


def read_workbook(path: str | Path) -> None:
    """Load an existing workbook and print summary information."""
    wb: Workbook = load_workbook(path)
    print(f"Sheet names : {wb.sheetnames}")

    sheet: Worksheet = wb.worksheets[0]
    print(f"Dimensions  : {sheet.dimensions}")
    print(f"Rows x Cols : {sheet.max_row} x {sheet.max_column}")

    # Access a single cell two ways
    print(f"Cell C3 (cell method) : {sheet.cell(3, 3).value}")
    print(f"Cell C3 (bracket)     : {sheet['C3'].value}")

    # Iterate rows and format values
    for row in sheet.iter_rows(min_row=2, max_row=min(sheet.max_row, 10)):
        cells: list[str] = []
        for cell in row:
            val: Any = cell.value
            if isinstance(val, datetime.datetime):
                cells.append(val.strftime("%Y-%m-%d"))
            elif isinstance(val, (int, float)):
                cells.append(f"{val:>10.2f}")
            else:
                cells.append(str(val) if val is not None else "")
        print("\t".join(cells))


# ---------------------------------------------------------------------------
# 2. Writing an Excel file with data, styles and formulas
# ---------------------------------------------------------------------------


HEADER_STYLE: dict[str, Any] = {
    "font": Font(size=12, bold=True, color="FFFFFF", name="Arial"),
    "fill": PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid"),
    "alignment": Alignment(horizontal="center", vertical="center"),
    "border": Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    ),
}

DATA_STYLE: dict[str, Any] = {
    "font": Font(size=11, name="Arial"),
    "alignment": Alignment(horizontal="center", vertical="center"),
    "border": Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    ),
}


def _apply_style(cell: openpyxl.cell.cell.Cell, style: dict[str, Any]) -> None:
    """Apply a style dict to a cell."""
    for attr, value in style.items():
        setattr(cell, attr, value)


def write_scores_workbook(output: str | Path = "scores.xlsx") -> Path:
    """Create a sample scores workbook with formulas and styling."""
    wb = Workbook()
    sheet: Worksheet = wb.active
    sheet.title = "期末成绩"

    headers: tuple[str, ...] = ("姓名", "语文", "数学", "英语", "平均分")
    for col_idx, title in enumerate(headers, start=1):
        cell = sheet.cell(1, col_idx, title)
        _apply_style(cell, HEADER_STYLE)

    names: tuple[str, ...] = ("关羽", "张飞", "赵云", "马超", "黄忠")
    for row_idx, name in enumerate(names, start=2):
        sheet.cell(row_idx, 1, name)
        _apply_style(sheet.cell(row_idx, 1), DATA_STYLE)
        for col_idx in range(2, 5):
            score = random.randint(60, 100)
            sheet.cell(row_idx, col_idx, score)
            _apply_style(sheet.cell(row_idx, col_idx), DATA_STYLE)
        # Formula for average
        formula = f"=AVERAGE(B{row_idx}:D{row_idx})"
        avg_cell = sheet.cell(row_idx, 5, formula)
        avg_cell.font = Font(size=11, italic=True, color="4169E1")
        avg_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Adjust dimensions
    sheet.row_dimensions[1].height = 28
    for col_idx in range(1, 6):
        sheet.column_dimensions[get_column_letter(col_idx)].width = 14

    # Freeze the header row
    sheet.freeze_panes = "A2"

    out_path = Path(output)
    wb.save(out_path)
    print(f"[write_scores_workbook] Saved -> {out_path.resolve()}")
    return out_path


# ---------------------------------------------------------------------------
# 3. Chart helpers
# ---------------------------------------------------------------------------


def add_bar_chart(
    sheet: Worksheet,
    title: str,
    data_ref: Reference,
    cat_ref: Reference,
    anchor: str = "A10",
) -> None:
    """Insert a clustered column bar chart into *sheet*."""
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = title
    chart.y_axis.title = "数值"
    chart.x_axis.title = "分类"
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cat_ref)
    chart.shape = 4
    chart.width = 18
    chart.height = 12
    sheet.add_chart(chart, anchor)


def add_line_chart(
    sheet: Worksheet,
    title: str,
    data_ref: Reference,
    cat_ref: Reference,
    anchor: str = "A28",
) -> None:
    """Insert a line chart into *sheet*."""
    chart = LineChart()
    chart.style = 10
    chart.title = title
    chart.y_axis.title = "数值"
    chart.x_axis.title = "分类"
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cat_ref)
    chart.width = 18
    chart.height = 12
    sheet.add_chart(chart, anchor)


def add_pie_chart(
    sheet: Worksheet,
    title: str,
    data_ref: Reference,
    cat_ref: Reference,
    anchor: str = "A46",
) -> None:
    """Insert a pie chart with percentage labels into *sheet*."""
    chart = PieChart()
    chart.title = title
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cat_ref)
    chart.dataLabels = DataLabelList()
    chart.dataLabels.showPercent = True
    chart.dataLabels.showCatName = True
    chart.width = 16
    chart.height = 12
    sheet.add_chart(chart, anchor)


# ---------------------------------------------------------------------------
# 4. Enterprise Dashboard Export
# ---------------------------------------------------------------------------


# Simulated quarterly department performance data
_DASHBOARD_DATA: dict[str, list[tuple[str, int, int, int]]] = {
    "Q1": [
        ("销售部", 120, 95, 80),
        ("技术部", 80, 88, 92),
        ("市场部", 60, 70, 65),
        ("运营部", 45, 50, 55),
    ],
    "Q2": [
        ("销售部", 135, 100, 85),
        ("技术部", 90, 95, 97),
        ("市场部", 75, 80, 72),
        ("运营部", 55, 60, 62),
    ],
}


def export_dashboard(
    output: str | Path = "enterprise_dashboard.xlsx",
) -> Path:
    """
    Build an enterprise dashboard workbook that demonstrates:
    - Multiple styled sheets (one per quarter)
    - Merged header cells
    - Bar, Line, and Pie charts per sheet
    - Conditional-style highlights via NamedStyle
    - Freeze panes and column auto-width
    """
    wb = Workbook()
    # Remove default sheet – we will create our own
    wb.remove(wb.active)

    header_style = NamedStyle(name="dashboard_header")
    header_style.font = Font(size=13, bold=True, color="FFFFFF")
    header_style.fill = PatternFill("solid", fgColor="2F5496")
    header_style.alignment = Alignment(horizontal="center", vertical="center")
    header_style.border = Border(
        left=Side("thin"),
        right=Side("thin"),
        top=Side("thin"),
        bottom=Side("thin"),
    )

    data_border = Border(
        left=Side("thin"),
        right=Side("thin"),
        top=Side("thin"),
        bottom=Side("thin"),
    )

    for quarter, rows in _DASHBOARD_DATA.items():
        sheet: Worksheet = wb.create_sheet(title=f"{quarter} 绩效")

        # -- Title row (merged) --
        sheet.merge_cells("A1:F1")
        title_cell = sheet["A1"]
        title_cell.value = f"{quarter} 部门绩效看板"
        title_cell.font = Font(size=16, bold=True, color="2F5496")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        sheet.row_dimensions[1].height = 36

        # -- Column headers --
        col_headers: tuple[str, ...] = (
            "部门",
            "营收(万)",
            "利润(万)",
            "满意度(%)",
        )
        for col_idx, hdr in enumerate(col_headers, start=1):
            cell = sheet.cell(3, col_idx, hdr)
            if "dashboard_header" not in wb.named_styles:
                wb.add_named_style(header_style)
            cell.style = header_style

        # -- Data rows --
        for row_offset, (dept, revenue, profit, satisfaction) in enumerate(rows):
            r = 4 + row_offset
            values: tuple[Any, ...] = (dept, revenue, profit, satisfaction)
            for c, val in enumerate(values, start=1):
                cell = sheet.cell(r, c, val)
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = data_border
                # Highlight high satisfaction
                if c == 4 and isinstance(val, (int, float)) and val >= 90:
                    cell.font = Font(bold=True, color="008000")

        # -- Column widths --
        for col_idx in range(1, 5):
            sheet.column_dimensions[get_column_letter(col_idx)].width = 16

        sheet.freeze_panes = "A4"

        # -- Charts --
        last_data_row = 3 + len(rows)
        data_ref = Reference(
            sheet, min_col=2, min_row=3, max_col=4, max_row=last_data_row
        )
        cat_ref = Reference(
            sheet, min_col=1, min_row=4, max_row=last_data_row
        )

        add_bar_chart(sheet, f"{quarter} 部门营收对比", data_ref, cat_ref, anchor="A10")
        add_line_chart(sheet, f"{quarter} 趋势图", data_ref, cat_ref, anchor="A28")

        # Pie chart – single-series (profit only)
        profit_ref = Reference(
            sheet, min_col=3, min_row=3, max_col=3, max_row=last_data_row
        )
        add_pie_chart(sheet, f"{quarter} 利润占比", profit_ref, cat_ref, anchor="A46")

    out_path = Path(output)
    wb.save(out_path)
    print(f"[export_dashboard] Saved -> {out_path.resolve()}")
    return out_path


# ---------------------------------------------------------------------------
# 5. Quick demo combining everything
# ---------------------------------------------------------------------------


def demo_full_workflow() -> None:
    """End-to-end: write scores, read them back, then export a dashboard."""
    print("=" * 60)
    print("Step 1 - Write a styled scores workbook")
    print("=" * 60)
    scores_path = write_scores_workbook("demo_scores.xlsx")

    print()
    print("=" * 60)
    print("Step 2 - Read the workbook back")
    print("=" * 60)
    read_workbook(scores_path)

    print()
    print("=" * 60)
    print("Step 3 - Export enterprise dashboard")
    print("=" * 60)
    export_dashboard("demo_dashboard.xlsx")

    print()
    print("All done. Check the generated .xlsx files.")


# ---------------------------------------------------------------------------
# __main__ guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_full_workflow()
