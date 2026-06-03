"""
Python 操作 Word 和 PowerPoint 文件
===================================

覆盖内容:
  - python-docx: 创建/读取/模板替换 Word 文档
  - python-pptx: 创建/编辑 PowerPoint 演示文稿
  - 企业场景: 自动化报告生成（综合 Word + PPT）

依赖安装:
  pip install python-docx python-pptx
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from docx.document import Document as Doc
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PptxRGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches as PptxInches
from pptx.util import Pt as PptxPt

# ---------------------------------------------------------------------------
# 输出目录
# ---------------------------------------------------------------------------
OUTPUT_DIR: Path = Path(__file__).resolve().parent / "output" / "day26"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ===================================================================
# Part 1 -- python-docx: Word 文档基础操作
# ===================================================================


def create_simple_word_document() -> Path:
    """创建一个包含标题、段落、列表、表格的简单 Word 文档。"""
    doc: Doc = Document()

    # --- 大标题 ---
    doc.add_heading("Python 自动化办公演示", level=0)

    # --- 正文段落 (带内联格式) ---
    p = doc.add_paragraph("Python 是一门非常流行的编程语言，它")
    run = p.add_run("简单")
    run.bold = True
    run.font.size = Pt(18)
    p.add_run("而且")
    run = p.add_run("优雅")
    run.font.size = Pt(18)
    run.underline = True
    p.add_run("。")

    # --- 各级标题 + 列表 ---
    doc.add_heading("一、无序列表示例", level=1)
    for item in ["数据分析", "Web 开发", "自动化运维"]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("二、有序列表示例", level=1)
    for item in ["安装 Python", "编写脚本", "执行并验证"]:
        doc.add_paragraph(item, style="List Number")

    # --- 表格 ---
    doc.add_heading("三、员工信息表", level=1)
    headers: list[str] = ["姓名", "部门", "职位", "入职日期"]
    rows_data: list[tuple[str, str, str, str]] = [
        ("张三", "研发部", "高级工程师", "2020-03-15"),
        ("李四", "产品部", "产品经理", "2019-07-01"),
        ("王五", "测试部", "测试主管", "2021-01-10"),
    ]

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 表头
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.text = header
        for run in cell.paragraphs[0].runs:
            run.bold = True
    # 数据行
    for row_data in rows_data:
        cells = table.add_row().cells
        for idx, value in enumerate(row_data):
            cells[idx].text = value

    # --- 分页 + 附注 ---
    doc.add_page_break()
    doc.add_heading("附录", level=1)
    doc.add_paragraph(
        "本文档由 Python 程序自动生成，演示 python-docx 的基本用法。",
        style="Intense Quote",
    )

    out_path: Path = OUTPUT_DIR / "simple_word_demo.docx"
    doc.save(str(out_path))
    print(f"[Word] 简单文档已保存 -> {out_path}")
    return out_path


def read_word_paragraphs(docx_path: str | Path) -> list[str]:
    """读取 Word 文档的所有段落文本并返回。"""
    doc: Doc = Document(str(docx_path))
    paragraphs: list[str] = []
    for idx, para in enumerate(doc.paragraphs):
        text: str = para.text.strip()
        if text:
            paragraphs.append(text)
            print(f"  段落 {idx}: {text[:60]}...")
    return paragraphs


def apply_custom_heading_style(doc: Doc) -> None:
    """为文档创建自定义标题样式 (如企业 VI 配色)。"""
    style = doc.styles.add_style("CompanyHeading", WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = doc.styles["Heading 1"]
    font = style.font
    font.size = Pt(22)
    font.bold = True
    font.color.rgb = RGBColor(0x00, 0x51, 0x8A)  # 企业蓝


def create_styled_document() -> Path:
    """演示自定义样式的文档创建。"""
    doc: Doc = Document()
    apply_custom_heading_style(doc)

    doc.add_paragraph("公司内部报告", style="CompanyHeading")
    doc.add_paragraph("本报告使用自定义的企业 VI 样式生成。")
    doc.add_paragraph(f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    out_path: Path = OUTPUT_DIR / "styled_word_demo.docx"
    doc.save(str(out_path))
    print(f"[Word] 自定义样式文档已保存 -> {out_path}")
    return out_path


# ===================================================================
# Part 2 -- python-docx: 模板替换（批量生成离职证明）
# ===================================================================


@dataclass
class EmployeeRecord:
    """员工离职信息数据类。"""

    name: str
    id_number: str
    start_date: str
    end_date: str
    department: str
    position: str
    company: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "id": self.id_number,
            "sdate": self.start_date,
            "edate": self.end_date,
            "department": self.department,
            "position": self.position,
            "company": self.company,
        }


def create_resignation_template(template_path: str | Path) -> None:
    """从零创建一个带占位符的离职证明模板文件。

    这样即使没有现成模板文件，程序也能自给自足。
    """
    doc: Doc = Document()

    # 标题
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.add_run("离 职 证 明")
    run.bold = True
    run.font.size = Pt(22)

    # 正文 (占位符使用 {key} 格式)
    body_text = (
        "    兹证明 {name}，身份证号码：{id}，"
        "于 {sdate} 至 {edate} 在我单位 {department} 部门"
        "担任 {position} 职务，在职期间无不良表现。"
        "因个人原因，于 {edate} 起终止解除劳动合同。"
        "现已结清财务相关费用，办理完解除劳动关系相关手续，"
        "双方不存在任何劳动争议。"
    )
    doc.add_paragraph(body_text)

    doc.add_paragraph("")
    doc.add_paragraph("特此证明！")
    doc.add_paragraph("")

    sign_para = doc.add_paragraph()
    sign_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    sign_para.add_run("公司名称（盖章）: {company}")

    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    date_para.add_run(datetime.now().strftime("%Y 年 %m 月 %d 日"))

    doc.save(str(template_path))
    print(f"[Word] 离职证明模板已创建 -> {template_path}")


def generate_resignation_letters(
    template_path: str | Path,
    employees: list[EmployeeRecord],
) -> list[Path]:
    """基于模板批量生成离职证明 Word 文档。

    关键技巧: 不能直接替换 paragraph.text，否则会丢失样式。
    必须遍历 paragraph.runs 逐个替换 run.text 中的占位符。
    """
    generated: list[Path] = []
    for emp in employees:
        doc: Doc = Document(str(template_path))
        emp_dict: dict[str, str] = emp.to_dict()

        for para in doc.paragraphs:
            if "{" not in para.text:
                continue
            for run in para.runs:
                if "{" not in run.text:
                    continue
                # 查找占位符并替换
                start: int = run.text.find("{")
                end: int = run.text.find("}")
                if start == -1 or end == -1:
                    continue
                key: str = run.text[start + 1 : end]
                placeholder: str = run.text[start : end + 1]
                if key in emp_dict:
                    run.text = run.text.replace(placeholder, emp_dict[key])

        out_path: Path = OUTPUT_DIR / f"{emp.name}_离职证明.docx"
        doc.save(str(out_path))
        generated.append(out_path)
        print(f"[Word] 离职证明已生成 -> {out_path}")

    return generated


# ===================================================================
# Part 3 -- python-pptx: PowerPoint 基础操作
# ===================================================================


def create_simple_presentation() -> Path:
    """创建一个包含标题页和项目符号页的简单 PowerPoint。"""
    pres: Presentation = Presentation()

    # ---- 第 1 页: 标题页 ----
    title_layout = pres.slide_layouts[0]  # Title Slide
    slide = pres.slides.add_slide(title_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Python 自动化办公"
    subtitle.text = "用代码提升工作效率  |  2026 年度"

    # ---- 第 2 页: 目录 ----
    bullet_layout = pres.slide_layouts[1]  # Title and Content
    slide = pres.slides.add_slide(bullet_layout)
    slide.shapes.title.text = "目录"
    tf = slide.placeholders[1].text_frame
    tf.text = "python-docx 操作 Word"
    for item in [
        "python-pptx 操作 PowerPoint",
        "模板替换与批量生成",
        "企业自动化报告实战",
    ]:
        p = tf.add_paragraph()
        p.text = item
        p.level = 0

    # ---- 第 3 页: 分层大纲 ----
    slide = pres.slides.add_slide(bullet_layout)
    slide.shapes.title.text = "python-docx 核心能力"
    tf = slide.placeholders[1].text_frame
    tf.text = "文档创建与编辑"
    sub_items: list[tuple[str, int]] = [
        ("标题、段落、列表", 1),
        ("表格与图片", 1),
        ("样式与格式控制", 1),
        ("模板占位符替换", 1),
        ("批量生成文档", 2),
    ]
    for text, level in sub_items:
        p = tf.add_paragraph()
        p.text = text
        p.level = level

    out_path: Path = OUTPUT_DIR / "simple_pptx_demo.pptx"
    pres.save(str(out_path))
    print(f"[PPT] 简单演示文稿已保存 -> {out_path}")
    return out_path


# ===================================================================
# Part 4 -- 企业场景: 自动化季度报告生成
# ===================================================================


@dataclass
class DepartmentMetrics:
    """部门季度绩效指标。"""

    name: str
    headcount: int
    revenue: float  # 万元
    cost: float  # 万元
    satisfaction: float  # 百分比 0-100

    @property
    def profit(self) -> float:
        return self.revenue - self.cost

    @property
    def profit_margin(self) -> float:
        return (self.profit / self.revenue * 100) if self.revenue else 0.0


@dataclass
class QuarterlyReportData:
    """季度报告数据容器。"""

    quarter: str  # e.g. "2026-Q1"
    company_name: str
    departments: list[DepartmentMetrics] = field(default_factory=list)
    summary_notes: str = ""

    @property
    def total_revenue(self) -> float:
        return sum(d.revenue for d in self.departments)

    @property
    def total_cost(self) -> float:
        return sum(d.cost for d in self.departments)

    @property
    def total_profit(self) -> float:
        return self.total_revenue - self.total_cost

    @property
    def total_headcount(self) -> int:
        return sum(d.headcount for d in self.departments)

    @property
    def avg_satisfaction(self) -> float:
        if not self.departments:
            return 0.0
        return sum(d.satisfaction for d in self.departments) / len(
            self.departments
        )


def generate_quarterly_word_report(data: QuarterlyReportData) -> Path:
    """根据季度数据自动生成 Word 报告。

    包含: 封面、总览表格、各部门明细、管理层总结。
    """
    doc: Doc = Document()

    # ---- 封面 ----
    doc.add_heading(f"{data.company_name}", level=0)
    doc.add_heading(f"{data.quarter} 季度经营报告", level=1)
    gen_info = doc.add_paragraph()
    gen_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    gen_info.add_run(f"\n\n生成日期: {datetime.now().strftime('%Y-%m-%d')}")
    doc.add_page_break()

    # ---- 一、总览 ----
    doc.add_heading("一、季度总览", level=1)
    summary_table = doc.add_table(rows=5, cols=2)
    summary_table.style = "Light Grid Accent 1"
    summary_items: list[tuple[str, str]] = [
        ("报告季度", data.quarter),
        ("总营收（万元）", f"{data.total_revenue:,.2f}"),
        ("总成本（万元）", f"{data.total_cost:,.2f}"),
        ("净利润（万元）", f"{data.total_profit:,.2f}"),
        ("员工总数", str(data.total_headcount)),
    ]
    for row_idx, (label, value) in enumerate(summary_items):
        summary_table.rows[row_idx].cells[0].text = label
        summary_table.rows[row_idx].cells[1].text = value

    # ---- 二、部门明细表 ----
    doc.add_heading("二、各部门绩效明细", level=1)
    dept_headers = ["部门", "人数", "营收", "成本", "利润", "利润率", "满意度"]
    dept_table = doc.add_table(rows=1, cols=len(dept_headers))
    dept_table.style = "Medium Shading 1 Accent 1"
    # 表头
    for i, h in enumerate(dept_headers):
        cell = dept_table.rows[0].cells[i]
        cell.text = h
        for run in cell.paragraphs[0].runs:
            run.bold = True
    # 数据行
    for dept in data.departments:
        cells = dept_table.add_row().cells
        cells[0].text = dept.name
        cells[1].text = str(dept.headcount)
        cells[2].text = f"{dept.revenue:,.2f}"
        cells[3].text = f"{dept.cost:,.2f}"
        cells[4].text = f"{dept.profit:,.2f}"
        cells[5].text = f"{dept.profit_margin:.1f}%"
        cells[6].text = f"{dept.satisfaction:.1f}%"

    # ---- 三、利润分析 ----
    doc.add_heading("三、利润分析", level=1)
    max_dept = max(data.departments, key=lambda d: d.profit_margin)
    min_dept = min(data.departments, key=lambda d: d.profit_margin)
    doc.add_paragraph(
        f"利润率最高的部门为「{max_dept.name}」"
        f"（{max_dept.profit_margin:.1f}%），"
        f"最低的为「{min_dept.name}」（{min_dept.profit_margin:.1f}%）。"
    )
    doc.add_paragraph(
        f"全公司平均员工满意度为 {data.avg_satisfaction:.1f}%。"
    )

    # ---- 四、管理层备注 ----
    if data.summary_notes:
        doc.add_heading("四、管理层备注", level=1)
        doc.add_paragraph(data.summary_notes, style="Intense Quote")

    out_path: Path = OUTPUT_DIR / f"{data.quarter}_经营报告.docx"
    doc.save(str(out_path))
    print(f"[Word] 季度报告已保存 -> {out_path}")
    return out_path


def generate_quarterly_pptx_report(data: QuarterlyReportData) -> Path:
    """根据季度数据自动生成 PowerPoint 汇报演示文稿。"""
    pres: Presentation = Presentation()

    # ---- 封面 ----
    slide = pres.slides.add_slide(pres.slide_layouts[0])
    slide.shapes.title.text = f"{data.company_name}"
    slide.placeholders[1].text = (
        f"{data.quarter} 季度经营报告\n"
        f"{datetime.now().strftime('%Y-%m-%d')}"
    )

    # ---- 总览页 ----
    bullet_layout = pres.slide_layouts[1]
    slide = pres.slides.add_slide(bullet_layout)
    slide.shapes.title.text = "季度总览"
    tf = slide.placeholders[1].text_frame
    tf.text = f"总营收: {data.total_revenue:,.2f} 万元"
    overview_items: list[str] = [
        f"总成本: {data.total_cost:,.2f} 万元",
        f"净利润: {data.total_profit:,.2f} 万元",
        f"员工总数: {data.total_headcount} 人",
        f"平均满意度: {data.avg_satisfaction:.1f}%",
    ]
    for item in overview_items:
        p = tf.add_paragraph()
        p.text = item
        p.level = 0

    # ---- 部门对比页 (用表格展示) ----
    slide = pres.slides.add_slide(pres.slide_layouts[5])  # Title Only
    slide.shapes.title.text = "各部门绩效对比"

    cols_count = 5
    rows_count = len(data.departments) + 1
    left = PptxInches(0.5)
    top = PptxInches(1.5)
    width = PptxInches(9.0)
    height = PptxInches(0.4 * rows_count)

    table_shape = slide.shapes.add_table(
        rows_count, cols_count, left, top, width, height
    )
    table = table_shape.table

    headers: list[str] = ["部门", "营收(万)", "成本(万)", "利润率", "满意度"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = PptxRGBColor(0x00, 0x51, 0x8A)
        for paragraph in cell.text_frame.paragraphs:
            paragraph.font.color.rgb = PptxRGBColor(0xFF, 0xFF, 0xFF)
            paragraph.font.bold = True
            paragraph.font.size = PptxPt(12)

    for row_idx, dept in enumerate(data.departments, start=1):
        values: list[str] = [
            dept.name,
            f"{dept.revenue:,.2f}",
            f"{dept.cost:,.2f}",
            f"{dept.profit_margin:.1f}%",
            f"{dept.satisfaction:.1f}%",
        ]
        for col_idx, val in enumerate(values):
            cell = table.cell(row_idx, col_idx)
            cell.text = val
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = PptxPt(11)

    # ---- 结论页 ----
    slide = pres.slides.add_slide(bullet_layout)
    slide.shapes.title.text = "结论与展望"
    tf = slide.placeholders[1].text_frame
    max_dept = max(data.departments, key=lambda d: d.profit_margin)
    tf.text = f"表现最佳部门: {max_dept.name}（利润率 {max_dept.profit_margin:.1f}%）"
    if data.summary_notes:
        p = tf.add_paragraph()
        p.text = data.summary_notes
        p.level = 1

    out_path: Path = OUTPUT_DIR / f"{data.quarter}_经营报告.pptx"
    pres.save(str(out_path))
    print(f"[PPT] 季度报告已保存 -> {out_path}")
    return out_path


# ===================================================================
# Part 5 -- 读取已有 Word 文档
# ===================================================================


def inspect_word_document(docx_path: str | Path) -> None:
    """打印 Word 文档的段落、表格等结构信息，便于调试。"""
    doc: Doc = Document(str(docx_path))
    print(f"\n--- 文档结构分析: {docx_path} ---")
    print(f"段落数量: {len(doc.paragraphs)}")
    print(f"表格数量: {len(doc.tables)}")
    print(f"节数量:   {len(doc.sections)}")
    print("\n段落列表:")
    for i, para in enumerate(doc.paragraphs):
        style_name: str = para.style.name if para.style else "None"
        text_preview: str = para.text[:50] if para.text else "(空)"
        print(f"  [{i}] style={style_name:20s} | {text_preview}")
    for t_idx, table in enumerate(doc.tables):
        print(f"\n表格 {t_idx}: {len(table.rows)} 行 x {len(table.columns)} 列")
        for r_idx, row in enumerate(table.rows):
            cells_text = [cell.text for cell in row.cells]
            print(f"  行 {r_idx}: {cells_text}")


# ===================================================================
# main
# ===================================================================


def build_sample_report_data() -> QuarterlyReportData:
    """构造一份示例季度数据。"""
    departments: list[DepartmentMetrics] = [
        DepartmentMetrics("产品研发", 45, 850.0, 520.0, 88.5),
        DepartmentMetrics("市场营销", 20, 620.0, 410.0, 79.2),
        DepartmentMetrics("客户成功", 15, 380.0, 260.0, 91.0),
        DepartmentMetrics("行政人事", 10, 0.0, 150.0, 82.3),
    ]
    return QuarterlyReportData(
        quarter="2026-Q1",
        company_name="风车车科技有限公司",
        departments=departments,
        summary_notes=(
            "本季度整体业绩稳中有升，产品研发部继续保持高利润率。"
            "下季度重点: 拓展市场营销渠道，提升行政效率。"
        ),
    )


def main() -> None:
    """主函数: 依次演示所有功能。"""
    separator: str = "=" * 60

    # ------ Part 1: Word 基础 ------
    print(f"\n{separator}")
    print("Part 1: 创建简单 Word 文档")
    print(separator)
    word_path: Path = create_simple_word_document()

    print(f"\n{separator}")
    print("Part 1b: 自定义样式文档")
    print(separator)
    create_styled_document()

    print(f"\n{separator}")
    print("Part 1c: 读取刚才生成的文档")
    print(separator)
    read_word_paragraphs(word_path)

    print(f"\n{separator}")
    print("Part 1d: 文档结构深度分析")
    print(separator)
    inspect_word_document(word_path)

    # ------ Part 2: 模板替换 ------
    print(f"\n{separator}")
    print("Part 2: 离职证明模板替换（批量生成）")
    print(separator)
    template_path: Path = OUTPUT_DIR / "离职证明模板.docx"
    create_resignation_template(template_path)

    employees: list[EmployeeRecord] = [
        EmployeeRecord(
            name="骆昊",
            id_number="100200198011280001",
            start_date="2008年3月1日",
            end_date="2012年2月29日",
            department="产品研发",
            position="架构师",
            company="成都华为技术有限公司",
        ),
        EmployeeRecord(
            name="王大锤",
            id_number="510210199012125566",
            start_date="2019年1月1日",
            end_date="2021年4月30日",
            department="产品研发",
            position="Python开发工程师",
            company="成都谷道科技有限公司",
        ),
        EmployeeRecord(
            name="李元芳",
            id_number="2102101995103221599",
            start_date="2020年5月10日",
            end_date="2021年3月5日",
            department="产品研发",
            position="Java开发工程师",
            company="同城企业管理集团有限公司",
        ),
    ]
    generate_resignation_letters(template_path, employees)

    # ------ Part 3: PowerPoint 基础 ------
    print(f"\n{separator}")
    print("Part 3: 创建简单 PowerPoint")
    print(separator)
    create_simple_presentation()

    # ------ Part 4: 企业自动化报告 ------
    print(f"\n{separator}")
    print("Part 4: 企业季度自动化报告 (Word + PPT)")
    print(separator)
    report_data: QuarterlyReportData = build_sample_report_data()
    generate_quarterly_word_report(report_data)
    generate_quarterly_pptx_report(report_data)

    print(f"\n{separator}")
    print("全部完成! 所有文件已保存到:")
    print(f"  {OUTPUT_DIR}")
    print(separator)


if __name__ == "__main__":
    main()
