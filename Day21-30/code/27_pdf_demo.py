"""
Day 27 - Python操作PDF文件 (Python PDF Operations)
====================================================

Comprehensive demo covering:
  1. Reading PDF files with PyPDF2 (text extraction, metadata, page info)
  2. Creating PDF files with reportlab (text, shapes, images, tables)
  3. Merging multiple PDFs into one
  4. Adding watermarks to PDF pages
  5. Encrypting / decrypting PDF files
  6. Enterprise examples:
       - Invoice PDF generator
       - Batch PDF merger
       - Watermark adder (text + image)
       - Simple form filler

Dependencies:
    pip install PyPDF2 reportlab

Author: Python-100-Days Course
"""

from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence

# ---------------------------------------------------------------------------
# Third-party imports (with graceful fallback messages)
# ---------------------------------------------------------------------------
try:
    import PyPDF2
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    sys.exit(
        "PyPDF2 is required. Install it with:\n"
        "  pip install PyPDF2"
    )

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, inch, mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    sys.exit(
        "reportlab is required. Install it with:\n"
        "  pip install reportlab"
    )


# ===================================================================
# 1. Reading PDF Files with PyPDF2
# ===================================================================

def extract_text_from_pdf(pdf_path: str | Path) -> list[str]:
    """Extract text from every page of a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A list of strings, one per page.

    Raises:
        FileNotFoundError: If the file does not exist.
        PyPDF2.errors.PdfReadError: If the file is not a valid PDF.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages_text: list[str] = []
    for page in reader.pages:
        text: str = page.extract_text() or ""
        pages_text.append(text)
    return pages_text


def get_pdf_metadata(pdf_path: str | Path) -> dict[str, Any]:
    """Return metadata dictionary from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A dict with keys like 'title', 'author', 'creator', 'pages', etc.
    """
    reader = PdfReader(str(pdf_path))
    info = reader.metadata
    meta: dict[str, Any] = {
        "pages": len(reader.pages),
    }
    if info:
        meta["title"] = info.title
        meta["author"] = info.author
        meta["creator"] = info.creator
        meta["producer"] = info.producer
    return meta


def get_page_info(pdf_path: str | Path) -> list[dict[str, Any]]:
    """Return basic geometry information for each page.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A list of dicts with keys: page_number, width, height, rotation.
    """
    reader = PdfReader(str(pdf_path))
    result: list[dict[str, Any]] = []
    for idx, page in enumerate(reader.pages):
        box = page.mediabox
        result.append({
            "page_number": idx + 1,
            "width": float(box.width),
            "height": float(box.height),
            "rotation": page.get("/Rotate", 0),
        })
    return result


# ===================================================================
# 2. Creating PDF Files with reportlab
# ===================================================================

def create_simple_pdf(output_path: str | Path) -> None:
    """Create a simple PDF with text and basic shapes.

    Args:
        output_path: Where to save the generated PDF.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4  # 595.27 x 841.89 points

    # -- Title --
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#2c3e50"))
    c.drawCentredString(width / 2, height - 80, "Python PDF Demo")

    # -- Subtitle --
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#7f8c8d"))
    c.drawCentredString(width / 2, height - 110, "Created with reportlab")

    # -- Horizontal rule --
    c.setStrokeColor(colors.HexColor("#3498db"))
    c.setLineWidth(2)
    c.line(50, height - 130, width - 50, height - 130)

    # -- Body text --
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    text_lines = [
        "This PDF was generated entirely with Python code.",
        "reportlab provides low-level canvas drawing as well as",
        "high-level platypus layout (paragraphs, tables, images).",
        "",
        "Key features demonstrated here:",
        "  - Drawing text, lines, rectangles, and circles",
        "  - Setting fonts, colors, and line widths",
        "  - Multi-page document creation",
    ]
    y = height - 170
    for line in text_lines:
        c.drawString(60, y, line)
        y -= 20

    # -- Draw some shapes --
    c.setFillColor(colors.HexColor("#e74c3c"))
    c.rect(60, y - 80, 60, 60, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#2ecc71"))
    c.circle(180, y - 50, 30, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#3498db"))
    c.circle(270, y - 50, 30, fill=1, stroke=0)

    # -- Second page --
    c.showPage()
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor("#8e44ad"))
    c.drawCentredString(width / 2, height - 80, "Page 2 - More Content")
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawString(60, height - 120, "This is the second page of the demo PDF.")

    c.save()
    print(f"[create_simple_pdf] Saved to: {output_path}")


def create_table_pdf(output_path: str | Path) -> None:
    """Create a PDF containing a formatted table using platypus.

    Args:
        output_path: Where to save the generated PDF.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story: list[Any] = []

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=20,
    )
    story.append(Paragraph("Quarterly Sales Report", title_style))
    story.append(Spacer(1, 20))

    # Table data
    header = ["Region", "Q1", "Q2", "Q3", "Q4", "Total"]
    rows = [
        ["North", "$12,500", "$14,200", "$13,800", "$16,100", "$56,600"],
        ["South", "$9,800", "$11,300", "$10,500", "$12,400", "$44,000"],
        ["East", "$15,200", "$16,800", "$17,100", "$18,500", "$67,600"],
        ["West", "$11,100", "$12,600", "$11,900", "$13,700", "$49,300"],
    ]
    table_data = [header] + rows

    table = Table(table_data, colWidths=[80, 70, 70, 70, 70, 80])
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 11),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        # Alternating row colors
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ecf0f1")),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#ecf0f1")),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
        # Total column highlight
        ("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (-1, 1), (-1, -1), colors.HexColor("#27ae60")),
    ]))
    story.append(table)

    # Footer note
    story.append(Spacer(1, 30))
    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
    )
    story.append(
        Paragraph(
            f"Report generated on {datetime.now():%Y-%m-%d %H:%M} by Python.",
            note_style,
        )
    )

    doc.build(story)
    print(f"[create_table_pdf] Saved to: {output_path}")


# ===================================================================
# 3. PDF Merging
# ===================================================================

def merge_pdfs(
    input_paths: Sequence[str | Path],
    output_path: str | Path,
) -> None:
    """Merge multiple PDF files into a single output file.

    Args:
        input_paths: Ordered sequence of PDF file paths to merge.
        output_path: Destination path for the merged PDF.

    Raises:
        FileNotFoundError: If any input file does not exist.
    """
    writer = PdfWriter()

    for path in input_paths:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"[merge_pdfs] Merged {len(input_paths)} files -> {output_path}")


def extract_page_range(
    pdf_path: str | Path,
    start: int,
    end: int,
    output_path: str | Path,
) -> None:
    """Extract a range of pages (1-indexed, inclusive) from a PDF.

    Args:
        pdf_path: Source PDF path.
        start: First page number (1-indexed).
        end: Last page number (1-indexed, inclusive).
        output_path: Destination path.
    """
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    total = len(reader.pages)

    # Clamp to valid range
    start = max(1, start)
    end = min(total, end)

    for page_num in range(start - 1, end):
        writer.add_page(reader.pages[page_num])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(
        f"[extract_page_range] Pages {start}-{end} of '{pdf_path}' "
        f"-> {output_path}"
    )


# ===================================================================
# 4. Watermarking
# ===================================================================

def create_text_watermark(
    output_path: str | Path,
    text: str = "CONFIDENTIAL",
    width: float = 595.27,
    height: float = 841.89,
    font_size: int = 60,
    angle: float = 45.0,
    opacity: float = 0.15,
) -> None:
    """Create a single-page PDF containing a diagonal text watermark.

    Args:
        output_path: Where to save the watermark PDF.
        text: The watermark text.
        width: Page width in points (default A4).
        height: Page height in points (default A4).
        font_size: Font size for the watermark text.
        angle: Rotation angle in degrees.
        opacity: Text opacity (0.0 transparent - 1.0 opaque).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=(width, height))
    c.setFont("Helvetica-Bold", font_size)
    c.setFillColorRGB(0.5, 0.5, 0.5, opacity)

    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(angle)
    c.drawCentredString(0, 0, text)
    c.restoreState()

    c.save()
    print(f"[create_text_watermark] Saved to: {output_path}")


def add_watermark(
    pdf_path: str | Path,
    watermark_path: str | Path,
    output_path: str | Path,
) -> None:
    """Overlay a watermark PDF onto every page of a source PDF.

    Args:
        pdf_path: The original PDF.
        watermark_path: A single-page PDF used as the watermark.
        output_path: Destination for the watermarked PDF.
    """
    reader = PdfReader(str(pdf_path))
    wm_reader = PdfReader(str(watermark_path))
    wm_page = wm_reader.pages[0]
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(wm_page)
        writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(
        f"[add_watermark] Watermarked {len(reader.pages)} pages "
        f"-> {output_path}"
    )


def add_watermark_even_odd(
    pdf_path: str | Path,
    watermark_odd_path: str | Path,
    watermark_even_path: str | Path,
    output_path: str | Path,
) -> None:
    """Apply different watermarks to odd and even pages.

    Args:
        pdf_path: The original PDF.
        watermark_odd_path: Watermark PDF for odd-numbered pages.
        watermark_even_path: Watermark PDF for even-numbered pages.
        output_path: Destination for the watermarked PDF.
    """
    reader = PdfReader(str(pdf_path))
    wm_odd = PdfReader(str(watermark_odd_path)).pages[0]
    wm_even = PdfReader(str(watermark_even_path)).pages[0]
    writer = PdfWriter()

    for idx, page in enumerate(reader.pages):
        if idx % 2 == 0:  # 0-indexed: page 1 is index 0 -> odd
            page.merge_page(wm_odd)
        else:
            page.merge_page(wm_even)
        writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"[add_watermark_even_odd] Saved to: {output_path}")


# ===================================================================
# 5. Encryption / Decryption
# ===================================================================

def encrypt_pdf(
    pdf_path: str | Path,
    output_path: str | Path,
    password: str,
) -> None:
    """Encrypt a PDF file with a user password.

    Args:
        pdf_path: Source PDF path.
        output_path: Destination for the encrypted PDF.
        password: The encryption password.
    """
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"[encrypt_pdf] Encrypted -> {output_path}")


def decrypt_pdf(
    pdf_path: str | Path,
    output_path: str | Path,
    password: str,
) -> bool:
    """Decrypt a password-protected PDF.

    Args:
        pdf_path: Encrypted PDF path.
        output_path: Destination for the decrypted PDF.
        password: The decryption password.

    Returns:
        True if decryption succeeded, False if the password was wrong.
    """
    reader = PdfReader(str(pdf_path))

    if reader.is_encrypted:
        if not reader.decrypt(password):
            print("[decrypt_pdf] Wrong password.")
            return False

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"[decrypt_pdf] Decrypted -> {output_path}")
    return True


# ===================================================================
# 6. Enterprise Example: Invoice Generator
# ===================================================================

@dataclass
class InvoiceItem:
    """A single line item on an invoice."""
    description: str
    quantity: int
    unit_price: float

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Invoice:
    """Represents a complete invoice."""
    invoice_number: str
    date: str
    customer_name: str
    customer_address: str
    items: list[InvoiceItem] = field(default_factory=list)
    tax_rate: float = 0.0  # e.g. 0.10 for 10%

    @property
    def subtotal(self) -> float:
        return sum(item.total for item in self.items)

    @property
    def tax(self) -> float:
        return self.subtotal * self.tax_rate

    @property
    def grand_total(self) -> float:
        return self.subtotal + self.tax


def generate_invoice_pdf(invoice: Invoice, output_path: str | Path) -> None:
    """Generate a professional-looking invoice PDF.

    Args:
        invoice: An Invoice dataclass with all details.
        output_path: Where to save the invoice PDF.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story: list[Any] = []

    # -- Header --
    header_style = ParagraphStyle(
        "InvoiceHeader",
        parent=styles["Title"],
        fontSize=28,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=5,
    )
    story.append(Paragraph("INVOICE", header_style))
    story.append(Spacer(1, 10))

    # -- Invoice info --
    info_style = ParagraphStyle(
        "Info",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
    )
    info_html = (
        f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
        f"<b>Date:</b> {invoice.date}<br/>"
        f"<b>Customer:</b> {invoice.customer_name}<br/>"
        f"<b>Address:</b> {invoice.customer_address}"
    )
    story.append(Paragraph(info_html, info_style))
    story.append(Spacer(1, 20))

    # -- Line items table --
    header_row = ["#", "Description", "Qty", "Unit Price", "Total"]
    data_rows: list[list[Any]] = []
    for i, item in enumerate(invoice.items, 1):
        data_rows.append([
            str(i),
            item.description,
            str(item.quantity),
            f"${item.unit_price:,.2f}",
            f"${item.total:,.2f}",
        ])

    # Subtotal, Tax, Grand Total rows
    data_rows.append(["", "", "", "Subtotal", f"${invoice.subtotal:,.2f}"])
    if invoice.tax_rate > 0:
        pct = f"{invoice.tax_rate * 100:.0f}%"
        data_rows.append(["", "", "", f"Tax ({pct})", f"${invoice.tax:,.2f}"])
    data_rows.append(["", "", "", "TOTAL", f"${invoice.grand_total:,.2f}"])

    table_data = [header_row] + data_rows
    table = Table(table_data, colWidths=[30, 230, 50, 90, 90])
    table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        # Data
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        # Alternating rows
        *[
            ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#ecf0f1"))
            for i in range(2, len(table_data), 2)
        ],
        # Grid
        ("GRID", (0, 0), (-1, len(invoice.items)), 0.5, colors.grey),
        # Summary rows - no left grid
        ("LINEABOVE", (3, len(invoice.items) + 1), (-1, len(invoice.items) + 1),
         1, colors.HexColor("#2c3e50")),
        # TOTAL row
        ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (3, -1), (-1, -1), 12),
        ("TEXTCOLOR", (3, -1), (-1, -1), colors.HexColor("#27ae60")),
        ("LINEABOVE", (3, -1), (-1, -1), 1.5, colors.HexColor("#2c3e50")),
    ]))
    story.append(table)

    # -- Footer --
    story.append(Spacer(1, 40))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    story.append(
        Paragraph("Thank you for your business!", footer_style)
    )

    doc.build(story)
    print(f"[generate_invoice_pdf] Invoice '{invoice.invoice_number}' -> {output_path}")


# ===================================================================
# 7. Enterprise Example: Batch PDF Merger
# ===================================================================

@dataclass
class MergeJob:
    """Describes a batch PDF merge operation."""
    input_dir: str | Path
    output_path: str | Path
    pattern: str = "*.pdf"
    sort_by_name: bool = True


def batch_merge(job: MergeJob) -> None:
    """Merge all PDFs matching a glob pattern in a directory.

    Args:
        job: A MergeJob describing the merge parameters.
    """
    input_dir = Path(job.input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    pdf_files = sorted(input_dir.glob(job.pattern))
    if not pdf_files:
        print(f"[batch_merge] No files matching '{job.pattern}' in {input_dir}")
        return

    # Remove the output file from inputs if it lives in the same directory
    output_abs = Path(job.output_path).resolve()
    pdf_files = [f for f in pdf_files if f.resolve() != output_abs]

    if not pdf_files:
        print("[batch_merge] No input files remaining after excluding output.")
        return

    merge_pdfs(pdf_files, job.output_path)
    print(f"[batch_merge] Job complete. {len(pdf_files)} files merged.")


# ===================================================================
# 8. Enterprise Example: Watermark Adder
# ===================================================================

@dataclass
class WatermarkJob:
    """Configuration for a watermarking operation."""
    pdf_path: str | Path
    output_path: str | Path
    watermark_text: str = "CONFIDENTIAL"
    font_size: int = 60
    angle: float = 45.0
    opacity: float = 0.15


def apply_text_watermark(job: WatermarkJob) -> None:
    """Create a text watermark and apply it to a PDF.

    This is a convenience function that combines watermark creation
    and application in a single step.

    Args:
        job: A WatermarkJob with all watermark parameters.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        wm_path = tmp.name

    try:
        # Determine page size from the source PDF
        reader = PdfReader(str(job.pdf_path))
        first_page = reader.pages[0]
        box = first_page.mediabox
        page_w = float(box.width)
        page_h = float(box.height)

        create_text_watermark(
            wm_path,
            text=job.watermark_text,
            width=page_w,
            height=page_h,
            font_size=job.font_size,
            angle=job.angle,
            opacity=job.opacity,
        )
        add_watermark(job.pdf_path, wm_path, job.output_path)
    finally:
        os.unlink(wm_path)


def batch_watermark(
    pdf_paths: Sequence[str | Path],
    output_dir: str | Path,
    watermark_text: str = "CONFIDENTIAL",
) -> None:
    """Apply the same text watermark to multiple PDFs.

    Args:
        pdf_paths: List of PDF files to watermark.
        output_dir: Directory to store watermarked copies.
        watermark_text: Text to use as watermark.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdf_paths:
        pdf_path = Path(pdf_path)
        out = output_dir / f"{pdf_path.stem}_watermarked{pdf_path.suffix}"
        job = WatermarkJob(
            pdf_path=pdf_path,
            output_path=out,
            watermark_text=watermark_text,
        )
        apply_text_watermark(job)

    print(f"[batch_watermark] Processed {len(pdf_paths)} files -> {output_dir}")


# ===================================================================
# 9. Enterprise Example: Simple Form Filler
# ===================================================================

def fill_form_overlay(
    pdf_path: str | Path,
    output_path: str | Path,
    fields: dict[str, tuple[float, float]],
    values: dict[str, str],
    font_size: int = 12,
    page_index: int = 0,
) -> None:
    """Overlay text values at specified coordinates on a PDF page.

    This is a simple approach to form filling: it creates a transparent
    overlay PDF with the field values drawn at the given (x, y) positions,
    then merges it on top of the target page.

    Args:
        pdf_path: Path to the existing PDF (e.g., a blank form).
        output_path: Destination for the filled PDF.
        fields: Mapping of field_name -> (x, y) position in points.
        values: Mapping of field_name -> text value to fill.
        font_size: Font size for field values.
        page_index: Which page of the PDF to fill (0-indexed).
    """
    reader = PdfReader(str(pdf_path))
    target_page = reader.pages[page_index]
    box = target_page.mediabox
    page_w = float(box.width)
    page_h = float(box.height)

    # Create overlay with field values
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        overlay_path = tmp.name

    try:
        c = canvas.Canvas(overlay_path, pagesize=(page_w, page_h))
        c.setFont("Helvetica", font_size)
        c.setFillColor(colors.black)

        for field_name, value in values.items():
            if field_name in fields:
                x, y = fields[field_name]
                c.drawString(x, y, value)

        c.save()

        # Merge overlay onto the target page
        overlay_reader = PdfReader(overlay_path)
        overlay_page = overlay_reader.pages[0]

        writer = PdfWriter()
        for idx, page in enumerate(reader.pages):
            if idx == page_index:
                page.merge_page(overlay_page)
            writer.add_page(page)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)

    finally:
        os.unlink(overlay_path)

    print(f"[fill_form_overlay] Filled form -> {output_path}")


def create_blank_form(
    output_path: str | Path,
    title: str = "Sample Form",
    field_labels: Optional[list[str]] = None,
) -> dict[str, tuple[float, float]]:
    """Create a simple blank form PDF and return field positions.

    This helper generates a form with labeled lines for writing,
    useful for demonstrating the form filler.

    Args:
        output_path: Where to save the blank form.
        title: Form title.
        field_labels: List of field names/labels.

    Returns:
        A dict mapping field_name -> (x, y) where values should be placed.
    """
    if field_labels is None:
        field_labels = ["Name", "Date", "Amount", "Signature"]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 60, title)

    # Fields
    c.setFont("Helvetica", 12)
    y_start = height - 130
    line_spacing = 60
    label_x = 70
    field_x = 200
    line_end_x = width - 70
    field_positions: dict[str, tuple[float, float]] = {}

    for i, label in enumerate(field_labels):
        y = y_start - i * line_spacing
        # Draw label
        c.drawString(label_x, y, f"{label}:")
        # Draw underline for the field
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.line(field_x, y - 2, line_end_x, y - 2)
        # Record position (value will be drawn slightly above the line)
        field_positions[label] = (field_x + 5, y)

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.grey)
    c.drawCentredString(
        width / 2, 40,
        f"Form created {datetime.now():%Y-%m-%d} - Python-100-Days Demo",
    )

    c.save()
    print(f"[create_blank_form] Saved to: {output_path}")
    return field_positions


# ===================================================================
# 10. Demo Runner
# ===================================================================

def run_full_demo(output_dir: str | Path) -> None:
    """Run all demos in a temporary directory.

    Args:
        output_dir: Directory to store all generated files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("  Python PDF Operations - Full Demo")
    print("=" * 60)

    # --- 1. Create a simple PDF ---
    print("\n--- 1. Creating a simple PDF ---")
    simple_path = output_dir / "01_simple.pdf"
    create_simple_pdf(simple_path)

    # --- 2. Create a table PDF ---
    print("\n--- 2. Creating a table PDF ---")
    table_path = output_dir / "02_table.pdf"
    create_table_pdf(table_path)

    # --- 3. Read metadata and text ---
    print("\n--- 3. Reading PDF metadata and text ---")
    meta = get_pdf_metadata(simple_path)
    print(f"    Metadata: {meta}")
    page_info = get_page_info(simple_path)
    print(f"    Page info: {page_info}")
    text_pages = extract_text_from_pdf(simple_path)
    for i, text in enumerate(text_pages, 1):
        preview = text[:80].replace("\n", " ") if text else "(empty)"
        print(f"    Page {i}: {preview}...")

    # --- 4. Merge PDFs ---
    print("\n--- 4. Merging PDFs ---")
    merged_path = output_dir / "04_merged.pdf"
    merge_pdfs([simple_path, table_path], merged_path)

    # --- 5. Extract page range ---
    print("\n--- 5. Extracting page range (pages 1-2 from merged) ---")
    extract_path = output_dir / "05_extracted.pdf"
    extract_page_range(merged_path, 1, 2, extract_path)

    # --- 6. Encrypt and decrypt ---
    print("\n--- 6. Encrypting and decrypting PDF ---")
    encrypted_path = output_dir / "06_encrypted.pdf"
    encrypt_pdf(simple_path, encrypted_path, password="secret123")
    decrypted_path = output_dir / "06_decrypted.pdf"
    decrypt_pdf(encrypted_path, decrypted_path, password="secret123")

    # --- 7. Text watermark ---
    print("\n--- 7. Adding text watermark ---")
    watermarked_path = output_dir / "07_watermarked.pdf"
    apply_text_watermark(WatermarkJob(
        pdf_path=simple_path,
        output_path=watermarked_path,
        watermark_text="DRAFT",
        font_size=50,
        opacity=0.12,
    ))

    # --- 8. Invoice generator ---
    print("\n--- 8. Generating invoice ---")
    invoice = Invoice(
        invoice_number="INV-2026-0042",
        date="2026-06-02",
        customer_name="Acme Corporation",
        customer_address="123 Business Ave, Suite 100, Tech City",
        items=[
            InvoiceItem("Web Development Services", 1, 5000.00),
            InvoiceItem("Cloud Hosting (12 months)", 12, 99.99),
            InvoiceItem("SSL Certificate", 1, 149.99),
            InvoiceItem("Domain Registration", 2, 14.99),
        ],
        tax_rate=0.10,
    )
    invoice_path = output_dir / "08_invoice.pdf"
    generate_invoice_pdf(invoice, invoice_path)

    # --- 9. Form filler ---
    print("\n--- 9. Creating and filling a form ---")
    blank_form_path = output_dir / "09_blank_form.pdf"
    field_positions = create_blank_form(
        blank_form_path,
        title="Expense Report",
        field_labels=["Name", "Department", "Date", "Amount", "Description"],
    )
    filled_form_path = output_dir / "09_filled_form.pdf"
    fill_form_overlay(
        blank_form_path,
        filled_form_path,
        fields=field_positions,
        values={
            "Name": "Jane Smith",
            "Department": "Engineering",
            "Date": "2026-06-02",
            "Amount": "$2,450.00",
            "Description": "Conference travel expenses",
        },
    )

    # --- 10. Batch watermark ---
    print("\n--- 10. Batch watermarking ---")
    wm_output_dir = output_dir / "10_batch_watermarked"
    batch_watermark(
        [simple_path, table_path],
        wm_output_dir,
        watermark_text="INTERNAL",
    )

    # --- Summary ---
    print("\n" + "=" * 60)
    print("  All demos completed successfully!")
    print(f"  Output directory: {output_dir}")
    print("=" * 60)

    # List generated files
    all_files = sorted(output_dir.rglob("*.pdf"))
    print(f"\n  Generated {len(all_files)} PDF file(s):")
    for f in all_files:
        size_kb = f.stat().st_size / 1024
        print(f"    - {f.relative_to(output_dir)}  ({size_kb:.1f} KB)")


# ===================================================================
# Main Guard
# ===================================================================

if __name__ == "__main__":
    # Use a temp directory for the demo so nothing pollutes the repo
    demo_dir = Path(tempfile.mkdtemp(prefix="pdf_demo_"))
    print(f"Demo output directory: {demo_dir}\n")

    try:
        run_full_demo(demo_dir)
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise

    print(f"\nDemo files are in: {demo_dir}")
    print("You can inspect or delete them as needed.")
