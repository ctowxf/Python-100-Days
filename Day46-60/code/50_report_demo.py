"""
50_report_demo.py - Django制作报表 (Report Generation in Django)
===============================================================

本模块演示Django项目中的报表生成技术,包括:
- Excel报表导出(openpyxl/xlwt)
- PDF报表生成(reportlab)
- 数据可视化图表(matplotlib)
- JSON数据接口供前端ECharts渲染
- 企业级销售仪表盘和月度报表生成器

企业级应用场景:
- 销售数据日报/周报/月报自动生成
- 财务报表PDF导出(含图表)
- 大屏数据可视化后端API
- 定时报表任务(Celery + Django)

依赖安装:
    pip install django openpyxl xlwt reportlab matplotlib
"""

from __future__ import annotations

import io
import os
import sys
import json
import datetime
from decimal import Decimal
from typing import Any, Optional, List, Dict, Tuple, Union
from urllib.parse import quote

# ============================================================================
# Django环境配置
# ============================================================================

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
        USE_TZ=True,
        TIME_ZONE='Asia/Shanghai',
        ROOT_URLCONF=__name__,
    )
    django.setup()

from django.db import models, connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Max, Min, F, Q
from django.db.models.functions import TruncMonth, TruncDay, TruncYear


# ============================================================================
# 第一部分: 数据模型定义
# ============================================================================

class SalesRecord(models.Model):
    """
    销售记录模型 - 用于报表数据源

    字段说明:
    - product_name: 商品名称
    - category: 商品类别
    - region: 销售区域
    - salesperson: 销售人员
    - quantity: 销售数量
    - unit_price: 单价(DecimalField,精确到分)
    - total_amount: 总金额
    - sale_date: 销售日期
    """
    product_name: models.CharField = models.CharField(max_length=200, verbose_name='商品名称')
    category: models.CharField = models.CharField(
        max_length=50,
        verbose_name='商品类别',
        choices=[
            ('electronics', '电子产品'),
            ('clothing', '服装鞋帽'),
            ('food', '食品饮料'),
            ('home', '家居用品'),
            ('sports', '运动户外'),
        ],
    )
    region: models.CharField = models.CharField(
        max_length=50,
        verbose_name='销售区域',
        choices=[
            ('north', '华北区'),
            ('east', '华东区'),
            ('south', '华南区'),
            ('west', '西部区'),
            ('central', '华中区'),
        ],
    )
    salesperson: models.CharField = models.CharField(max_length=50, verbose_name='销售人员')
    quantity: models.PositiveIntegerField = models.IntegerField(verbose_name='销售数量')
    unit_price: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='单价(元)',
    )
    total_amount: models.DecimalField = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='总金额(元)',
    )
    cost: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='成本(元)',
    )
    sale_date: models.DateField = models.DateField(verbose_name='销售日期', db_index=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        db_table = 'report_sales_record'
        verbose_name = '销售记录'
        verbose_name_plural = '销售记录列表'
        ordering = ['-sale_date']
        indexes = [
            models.Index(fields=['category', 'sale_date'], name='idx_sale_cat_date'),
            models.Index(fields=['region', 'sale_date'], name='idx_sale_region_date'),
            models.Index(fields=['salesperson', 'sale_date'], name='idx_sale_person_date'),
        ]

    def __str__(self) -> str:
        return f'{self.product_name} - ¥{self.total_amount} ({self.sale_date})'

    @property
    def profit(self) -> Decimal:
        """毛利润"""
        return self.total_amount - self.cost

    @property
    def profit_rate(self) -> Optional[Decimal]:
        """毛利率"""
        if self.total_amount > 0:
            return ((self.total_amount - self.cost) / self.total_amount * 100).quantize(Decimal('0.01'))
        return None


# ============================================================================
# 第二部分: 报表数据服务层
# ============================================================================

class ReportDataService:
    """
    报表数据服务 - 封装所有报表数据查询逻辑

    遵循单一职责原则: 数据查询与报表格式化分离
    """

    @staticmethod
    def get_monthly_sales_summary(year: int) -> List[Dict[str, Any]]:
        """
        获取月度销售汇总

        返回: [{"month": "2024-01", "total_sales": 123456.78, "order_count": 100, ...}, ...]
        """
        results = (
            SalesRecord.objects
            .filter(sale_date__year=year)
            .annotate(month=TruncMonth('sale_date'))
            .values('month')
            .annotate(
                total_sales=Sum('total_amount'),
                total_cost=Sum('cost'),
                order_count=Count('id'),
                total_quantity=Sum('quantity'),
                avg_order_amount=Avg('total_amount'),
            )
            .order_by('month')
        )

        report_data = []
        for row in results:
            total_sales = row['total_sales'] or Decimal('0')
            total_cost = row['total_cost'] or Decimal('0')
            profit = total_sales - total_cost
            profit_rate = (profit / total_sales * 100).quantize(Decimal('0.01')) if total_sales > 0 else Decimal('0')

            report_data.append({
                'month': row['month'].strftime('%Y-%m'),
                'total_sales': float(total_sales),
                'total_cost': float(total_cost),
                'profit': float(profit),
                'profit_rate': float(profit_rate),
                'order_count': row['order_count'],
                'total_quantity': row['total_quantity'],
                'avg_order_amount': float(row['avg_order_amount'] or 0),
            })

        return report_data

    @staticmethod
    def get_category_sales(year: int, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取按商品类别的销售统计"""
        qs = SalesRecord.objects.filter(sale_date__year=year)
        if month:
            qs = qs.filter(sale_date__month=month)

        results = (
            qs.values('category')
            .annotate(
                total_sales=Sum('total_amount'),
                total_quantity=Sum('quantity'),
                order_count=Count('id'),
            )
            .order_by('-total_sales')
        )

        category_map = dict(SalesRecord._meta.get_field('category').choices)
        return [
            {
                'category': row['category'],
                'category_name': category_map.get(row['category'], row['category']),
                'total_sales': float(row['total_sales'] or 0),
                'total_quantity': row['total_quantity'] or 0,
                'order_count': row['order_count'],
            }
            for row in results
        ]

    @staticmethod
    def get_region_sales(year: int, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取按区域的销售统计"""
        qs = SalesRecord.objects.filter(sale_date__year=year)
        if month:
            qs = qs.filter(sale_date__month=month)

        results = (
            qs.values('region')
            .annotate(
                total_sales=Sum('total_amount'),
                order_count=Count('id'),
            )
            .order_by('-total_sales')
        )

        region_map = dict(SalesRecord._meta.get_field('region').choices)
        return [
            {
                'region': row['region'],
                'region_name': region_map.get(row['region'], row['region']),
                'total_sales': float(row['total_sales'] or 0),
                'order_count': row['order_count'],
            }
            for row in results
        ]

    @staticmethod
    def get_salesperson_ranking(year: int, month: Optional[int] = None, top_n: int = 10) -> List[Dict[str, Any]]:
        """获取销售人员业绩排名"""
        qs = SalesRecord.objects.filter(sale_date__year=year)
        if month:
            qs = qs.filter(sale_date__month=month)

        results = (
            qs.values('salesperson')
            .annotate(
                total_sales=Sum('total_amount'),
                total_profit=Sum(F('total_amount') - F('cost')),
                order_count=Count('id'),
                total_quantity=Sum('quantity'),
            )
            .order_by('-total_sales')[:top_n]
        )

        return [
            {
                'rank': idx + 1,
                'salesperson': row['salesperson'],
                'total_sales': float(row['total_sales'] or 0),
                'total_profit': float(row['total_profit'] or 0),
                'order_count': row['order_count'],
                'total_quantity': row['total_quantity'] or 0,
            }
            for idx, row in enumerate(results)
        ]

    @staticmethod
    def get_daily_trend(year: int, month: int) -> List[Dict[str, Any]]:
        """获取日销售趋势"""
        results = (
            SalesRecord.objects
            .filter(sale_date__year=year, sale_date__month=month)
            .annotate(day=TruncDay('sale_date'))
            .values('day')
            .annotate(
                total_sales=Sum('total_amount'),
                order_count=Count('id'),
            )
            .order_by('day')
        )

        return [
            {
                'date': row['day'].strftime('%m-%d'),
                'total_sales': float(row['total_sales'] or 0),
                'order_count': row['order_count'],
            }
            for row in results
        ]

    @staticmethod
    def get_top_products(year: int, month: Optional[int] = None, top_n: int = 10) -> List[Dict[str, Any]]:
        """获取热销商品Top N"""
        qs = SalesRecord.objects.filter(sale_date__year=year)
        if month:
            qs = qs.filter(sale_date__month=month)

        results = (
            qs.values('product_name', 'category')
            .annotate(
                total_sales=Sum('total_amount'),
                total_quantity=Sum('quantity'),
            )
            .order_by('-total_sales')[:top_n]
        )

        category_map = dict(SalesRecord._meta.get_field('category').choices)
        return [
            {
                'rank': idx + 1,
                'product_name': row['product_name'],
                'category': category_map.get(row['category'], row['category']),
                'total_sales': float(row['total_sales'] or 0),
                'total_quantity': row['total_quantity'] or 0,
            }
            for idx, row in enumerate(results)
        ]


# ============================================================================
# 第三部分: Excel报表导出
# ============================================================================

class ExcelReportGenerator:
    """
    Excel报表生成器

    使用openpyxl生成.xlsx格式的Excel报表
    支持: 多工作表、单元格样式、公式、图表
    """

    @staticmethod
    def export_monthly_report(year: int, month: int) -> io.BytesIO:
        """
        生成月度销售报表Excel

        包含4个工作表:
        1. 销售总览(Dashboard)
        2. 明细数据
        3. 分类统计
        4. 销售人员排名
        """
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, numbers
            from openpyxl.chart import BarChart, PieChart, LineChart, Reference
            from openpyxl.utils import get_column_letter
        except ImportError:
            return ExcelReportGenerator._export_with_xlwt(year, month)

        wb = Workbook()
        header_font = Font(name='Arial', bold=True, size=12, color='FFFFFF')
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center')
        data_font = Font(name='Arial', size=10)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin'),
        )

        # ---- 工作表1: 销售总览 ----
        ws_dashboard = wb.active
        ws_dashboard.title = '销售总览'

        summary = ReportDataService.get_monthly_sales_summary(year)
        month_data = next((m for m in summary if m['month'] == f'{year}-{month:02d}'), None)

        if month_data:
            ws_dashboard['A1'] = f'{year}年{month}月 销售报表'
            ws_dashboard['A1'].font = Font(name='Arial', bold=True, size=16, color='1F4E79')
            ws_dashboard.merge_cells('A1:F1')

            dashboard_data = [
                ['指标', '数值'],
                ['销售总额', f"¥{month_data['total_sales']:,.2f}"],
                ['成本总额', f"¥{month_data['total_cost']:,.2f}"],
                ['毛利润', f"¥{month_data['profit']:,.2f}"],
                ['毛利率', f"{month_data['profit_rate']}%"],
                ['订单数', month_data['order_count']],
                ['平均客单价', f"¥{month_data['avg_order_amount']:,.2f}"],
            ]

            for row_idx, row_data in enumerate(dashboard_data, start=3):
                for col_idx, value in enumerate(row_data, start=1):
                    cell = ws_dashboard.cell(row=row_idx, column=col_idx, value=value)
                    cell.font = data_font
                    cell.border = border
                    if row_idx == 3:
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = header_alignment

            ws_dashboard.column_dimensions['A'].width = 20
            ws_dashboard.column_dimensions['B'].width = 25

        # ---- 工作表2: 明细数据 ----
        ws_detail = wb.create_sheet('明细数据')
        detail_headers = ['日期', '商品', '类别', '区域', '销售人员', '数量', '单价', '金额', '成本', '利润']
        for col_idx, header in enumerate(detail_headers, start=1):
            cell = ws_detail.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border

        records = SalesRecord.objects.filter(
            sale_date__year=year, sale_date__month=month,
        ).order_by('sale_date')

        category_map = dict(SalesRecord._meta.get_field('category').choices)
        region_map = dict(SalesRecord._meta.get_field('region').choices)

        for row_idx, record in enumerate(records, start=2):
            row_data = [
                record.sale_date.strftime('%Y-%m-%d'),
                record.product_name,
                category_map.get(record.category, record.category),
                region_map.get(record.region, record.region),
                record.salesperson,
                record.quantity,
                float(record.unit_price),
                float(record.total_amount),
                float(record.cost),
                float(record.profit),
            ]
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws_detail.cell(row=row_idx, column=col_idx, value=value)
                cell.font = data_font
                cell.border = border
                if col_idx >= 6:
                    cell.alignment = Alignment(horizontal='right')
                    if col_idx >= 7:
                        cell.number_format = '#,##0.00'

        col_widths = [12, 25, 12, 10, 12, 8, 12, 15, 12, 12]
        for i, width in enumerate(col_widths, start=1):
            ws_detail.column_dimensions[get_column_letter(i)].width = width

        # ---- 工作表3: 分类统计(含饼图) ----
        ws_category = wb.create_sheet('分类统计')
        cat_data = ReportDataService.get_category_sales(year, month)

        cat_headers = ['类别', '销售金额', '销售数量', '订单数']
        for col_idx, header in enumerate(cat_headers, start=1):
            cell = ws_category.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        for row_idx, item in enumerate(cat_data, start=2):
            ws_category.cell(row=row_idx, column=1, value=item['category_name'])
            ws_category.cell(row=row_idx, column=2, value=item['total_sales'])
            ws_category.cell(row=row_idx, column=3, value=item['total_quantity'])
            ws_category.cell(row=row_idx, column=4, value=item['order_count'])

        if len(cat_data) > 0:
            pie = PieChart()
            pie.title = '各类别销售占比'
            pie.style = 10
            labels = Reference(ws_category, min_col=1, min_row=2, max_row=len(cat_data) + 1)
            data_ref = Reference(ws_category, min_col=2, min_row=1, max_row=len(cat_data) + 1)
            pie.add_data(data_ref, titles_from_data=True)
            pie.set_categories(labels)
            ws_category.add_chart(pie, 'F2')

        ws_category.column_dimensions['A'].width = 15
        ws_category.column_dimensions['B'].width = 15

        # ---- 工作表4: 销售人员排名 ----
        ws_ranking = wb.create_sheet('销售排名')
        rank_data = ReportDataService.get_salesperson_ranking(year, month)

        rank_headers = ['排名', '销售人员', '销售金额', '毛利润', '订单数', '销量']
        for col_idx, header in enumerate(rank_headers, start=1):
            cell = ws_ranking.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        for row_idx, item in enumerate(rank_data, start=2):
            ws_ranking.cell(row=row_idx, column=1, value=item['rank'])
            ws_ranking.cell(row=row_idx, column=2, value=item['salesperson'])
            ws_ranking.cell(row=row_idx, column=3, value=item['total_sales'])
            ws_ranking.cell(row=row_idx, column=4, value=item['total_profit'])
            ws_ranking.cell(row=row_idx, column=5, value=item['order_count'])
            ws_ranking.cell(row=row_idx, column=6, value=item['total_quantity'])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _export_with_xlwt(year: int, month: int) -> io.BytesIO:
        """使用xlwt降级方案(生成.xls格式)"""
        import xlwt

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('销售明细')

        header_style = xlwt.easyxf(
            'font: bold on, height 240, name Arial;'
            'align: horiz center, vert centre;'
            'pattern: pattern solid, fore_colour 0x4472C4;'
            'font: colour white;'
        )

        headers = ['日期', '商品', '类别', '区域', '销售人员', '数量', '单价', '金额', '成本']
        for col_idx, header in enumerate(headers):
            ws.write(0, col_idx, header, header_style)

        records = SalesRecord.objects.filter(
            sale_date__year=year, sale_date__month=month,
        ).order_by('sale_date')

        data_style = xlwt.easyxf('font: name Arial, height 200;')
        money_style = xlwt.easyxf('font: name Arial, height 200;', num_format_str='#,##0.00')

        category_map = dict(SalesRecord._meta.get_field('category').choices)
        region_map = dict(SalesRecord._meta.get_field('region').choices)

        for row_idx, record in enumerate(records, start=1):
            ws.write(row_idx, 0, record.sale_date.strftime('%Y-%m-%d'), data_style)
            ws.write(row_idx, 1, record.product_name, data_style)
            ws.write(row_idx, 2, category_map.get(record.category, record.category), data_style)
            ws.write(row_idx, 3, region_map.get(record.region, record.region), data_style)
            ws.write(row_idx, 4, record.salesperson, data_style)
            ws.write(row_idx, 5, record.quantity, data_style)
            ws.write(row_idx, 6, float(record.unit_price), money_style)
            ws.write(row_idx, 7, float(record.total_amount), money_style)
            ws.write(row_idx, 8, float(record.cost), money_style)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer


# ============================================================================
# 第四部分: PDF报表生成
# ============================================================================

class PDFReportGenerator:
    """
    PDF报表生成器

    使用reportlab生成PDF格式的报表
    支持: 中文字体、表格、图表、页眉页脚
    """

    @staticmethod
    def export_monthly_report(year: int, month: int) -> io.BytesIO:
        """生成月度销售报表PDF"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, mm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph,
            Spacer, Image, PageBreak,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()

        # 尝试注册中文字体
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simhei.ttf',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            ]
            chinese_font = 'Helvetica'
            for fp in font_paths:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont('ChineseFont', fp))
                    chinese_font = 'ChineseFont'
                    break
        except Exception:
            chinese_font = 'Helvetica'

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=chinese_font,
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontName=chinese_font,
            fontSize=14,
            alignment=TA_LEFT,
            spaceBefore=15,
            spaceAfter=10,
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=chinese_font,
            fontSize=10,
        )

        elements: List[Any] = []

        # ---- 报表标题 ----
        elements.append(Paragraph(f'{year}年{month}月 销售报表', title_style))
        elements.append(Spacer(1, 10 * mm))

        # ---- 汇总数据 ----
        summary = ReportDataService.get_monthly_sales_summary(year)
        month_data = next((m for m in summary if m['month'] == f'{year}-{month:02d}'), None)

        if month_data:
            elements.append(Paragraph('一、销售总览', subtitle_style))

            summary_table_data = [
                ['指标', '数值'],
                ['销售总额', f"¥{month_data['total_sales']:,.2f}"],
                ['成本总额', f"¥{month_data['total_cost']:,.2f}"],
                ['毛利润', f"¥{month_data['profit']:,.2f}"],
                ['毛利率', f"{month_data['profit_rate']}%"],
                ['订单数', str(month_data['order_count'])],
                ['平均客单价', f"¥{month_data['avg_order_amount']:,.2f}"],
            ]

            summary_table = Table(summary_table_data, colWidths=[150, 200])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 10 * mm))

        # ---- 分类统计表格 ----
        elements.append(Paragraph('二、分类销售统计', subtitle_style))
        cat_data = ReportDataService.get_category_sales(year, month)

        cat_table_data = [['类别', '销售金额(元)', '销售数量', '订单数']]
        for item in cat_data:
            cat_table_data.append([
                item['category_name'],
                f"{item['total_sales']:,.2f}",
                str(item['total_quantity']),
                str(item['order_count']),
            ])

        cat_table = Table(cat_table_data, colWidths=[120, 150, 100, 100])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 10 * mm))

        # ---- 销售排名表格 ----
        elements.append(Paragraph('三、销售人员排名(Top 10)', subtitle_style))
        rank_data = ReportDataService.get_salesperson_ranking(year, month, top_n=10)

        rank_table_data = [['排名', '销售人员', '销售金额(元)', '毛利润(元)', '订单数']]
        for item in rank_data:
            rank_table_data.append([
                str(item['rank']),
                item['salesperson'],
                f"{item['total_sales']:,.2f}",
                f"{item['total_profit']:,.2f}",
                str(item['order_count']),
            ])

        rank_table = Table(rank_table_data, colWidths=[60, 120, 150, 150, 80])
        rank_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(rank_table)

        # ---- 图表 ----
        elements.append(PageBreak())
        elements.append(Paragraph('四、销售趋势图', subtitle_style))

        try:
            chart_image = PDFReportGenerator._generate_trend_chart(year, month)
            if chart_image:
                elements.append(Image(chart_image, width=400 * mm, height=150 * mm))
        except Exception as e:
            elements.append(Paragraph(f'图表生成失败: {e}', normal_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _generate_trend_chart(year: int, month: int) -> Optional[io.BytesIO]:
        """使用matplotlib生成销售趋势图"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            return None

        daily_data = ReportDataService.get_daily_trend(year, month)
        if not daily_data:
            return None

        dates = [d['date'] for d in daily_data]
        sales = [d['total_sales'] for d in daily_data]
        orders = [d['order_count'] for d in daily_data]

        fig, ax1 = plt.subplots(figsize=(16, 6))

        color = '#4472C4'
        ax1.bar(dates, sales, color=color, alpha=0.7, label='销售额')
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('销售额(元)', color=color, fontsize=12)
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.tick_params(axis='x', rotation=45)

        ax2 = ax1.twinx()
        color2 = '#ED7D31'
        ax2.plot(dates, orders, color=color2, marker='o', linewidth=2, label='订单数')
        ax2.set_ylabel('订单数', color=color2, fontsize=12)
        ax2.tick_params(axis='y', labelcolor=color2)

        plt.title(f'{year}年{month}月 每日销售趋势', fontsize=14)
        fig.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf


# ============================================================================
# 第五部分: Matplotlib图表生成(独立使用)
# ============================================================================

class ChartGenerator:
    """
    Matplotlib图表生成器

    生成各种统计图表,可嵌入Web页面或导出为图片
    """

    @staticmethod
    def generate_category_pie_chart(year: int, month: Optional[int] = None) -> io.BytesIO:
        """生成类别销售占比饼图"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        cat_data = ReportDataService.get_category_sales(year, month)
        if not cat_data:
            raise ValueError('无数据可生成图表')

        labels = [d['category_name'] for d in cat_data]
        sizes = [d['total_sales'] for d in cat_data]
        colors_list = ['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5']

        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            colors=colors_list[:len(labels)],
            startangle=90, pctdistance=0.85,
        )
        for text in texts:
            text.set_fontsize(11)
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_color('white')

        period = f'{year}年' if not month else f'{year}年{month}月'
        ax.set_title(f'{period} 各类别销售占比', fontsize=14, fontweight='bold')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    @staticmethod
    def generate_region_bar_chart(year: int, month: Optional[int] = None) -> io.BytesIO:
        """生成区域销售柱状图"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        region_data = ReportDataService.get_region_sales(year, month)
        if not region_data:
            raise ValueError('无数据可生成图表')

        regions = [d['region_name'] for d in region_data]
        sales = [d['total_sales'] for d in region_data]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(regions, sales, color=['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5'])

        for bar, sale in zip(bars, sales):
            ax.text(
                bar.get_x() + bar.get_width() / 2., bar.get_height(),
                f'¥{sale:,.0f}',
                ha='center', va='bottom', fontsize=10,
            )

        ax.set_ylabel('销售金额(元)', fontsize=12)
        ax.set_title('各区域销售对比', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    @staticmethod
    def generate_salesperson_barh_chart(year: int, month: Optional[int] = None) -> io.BytesIO:
        """生成销售人员排名横向柱状图"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        rank_data = ReportDataService.get_salesperson_ranking(year, month, top_n=10)
        if not rank_data:
            raise ValueError('无数据可生成图表')

        names = [d['salesperson'] for d in reversed(rank_data)]
        sales = [d['total_sales'] for d in reversed(rank_data)]
        profits = [d['total_profit'] for d in reversed(rank_data)]

        fig, ax = plt.subplots(figsize=(10, 6))
        y_pos = range(len(names))

        ax.barh(y_pos, sales, height=0.4, label='销售额', color='#4472C4')
        ax.barh([y + 0.4 for y in y_pos], profits, height=0.4, label='毛利润', color='#ED7D31')

        ax.set_yticks([y + 0.2 for y in y_pos])
        ax.set_yticklabels(names, fontsize=10)
        ax.set_xlabel('金额(元)', fontsize=12)
        ax.set_title('销售人员业绩排名', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='x', alpha=0.3)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf


# ============================================================================
# 第六部分: Django视图函数(报表导出接口)
# ============================================================================

def export_excel(request: HttpRequest, year: int, month: int) -> HttpResponse:
    """
    导出Excel报表视图

    URL: /reports/excel/<year>/<month>/
    """
    buffer = ExcelReportGenerator.export_monthly_report(year, month)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename = quote(f'销售报表_{year}年{month}月.xlsx')
    response['Content-Disposition'] = f'attachment; filename*=utf-8\'\'{filename}'
    return response


def export_pdf(request: HttpRequest, year: int, month: int) -> HttpResponse:
    """
    导出PDF报表视图

    URL: /reports/pdf/<year>/<month>/
    """
    buffer = PDFReportGenerator.export_monthly_report(year, month)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = quote(f'销售报表_{year}年{month}月.pdf')
    response['Content-Disposition'] = f'attachment; filename*=utf-8\'\'{filename}'
    return response


def get_sales_dashboard_data(request: HttpRequest) -> JsonResponse:
    """
    销售仪表盘数据接口(供前端ECharts渲染)

    URL: /api/dashboard/?year=2024&month=1
    """
    year = int(request.GET.get('year', datetime.date.today().year))
    month = request.GET.get('month')
    month_int = int(month) if month else None

    data = {
        'summary': ReportDataService.get_monthly_sales_summary(year),
        'category_sales': ReportDataService.get_category_sales(year, month_int),
        'region_sales': ReportDataService.get_region_sales(year, month_int),
        'top_products': ReportDataService.get_top_products(year, month_int),
        'salesperson_ranking': ReportDataService.get_salesperson_ranking(year, month_int),
    }

    if month_int:
        data['daily_trend'] = ReportDataService.get_daily_trend(year, month_int)

    return JsonResponse(data, json_dumps_params={'ensure_ascii': False})


def get_chart_image(request: HttpRequest, chart_type: str) -> HttpResponse:
    """
    图表图片接口

    URL: /reports/chart/<chart_type>/?year=2024&month=1
    chart_type: pie | bar | ranking
    """
    year = int(request.GET.get('year', datetime.date.today().year))
    month = request.GET.get('month')
    month_int = int(month) if month else None

    chart_generators = {
        'pie': ChartGenerator.generate_category_pie_chart,
        'bar': ChartGenerator.generate_region_bar_chart,
        'ranking': ChartGenerator.generate_salesperson_barh_chart,
    }

    generator = chart_generators.get(chart_type)
    if not generator:
        return JsonResponse({'error': f'不支持的图表类型: {chart_type}'}, status=400)

    try:
        buffer = generator(year, month_int)
        return HttpResponse(buffer.getvalue(), content_type='image/png')
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=404)


# ============================================================================
# 第七部分: URL配置
# ============================================================================

from django.urls import path

urlpatterns = [
    path('reports/excel/<int:year>/<int:month>/', export_excel, name='export_excel'),
    path('reports/pdf/<int:year>/<int:month>/', export_pdf, name='export_pdf'),
    path('api/dashboard/', get_sales_dashboard_data, name='dashboard_api'),
    path('reports/chart/<str:chart_type>/', get_chart_image, name='chart_image'),
]


# ============================================================================
# 第八部分: 示例数据填充
# ============================================================================

def populate_sample_data() -> None:
    """填充示例销售数据"""
    import random

    products = [
        ('iPhone 15 Pro', 'electronics', Decimal('9999'), Decimal('6500')),
        ('iPhone 15', 'electronics', Decimal('5999'), Decimal('3800')),
        ('Huawei Mate 60', 'electronics', Decimal('6999'), Decimal('4200')),
        ('MacBook Pro 14"', 'electronics', Decimal('14999'), Decimal('9800')),
        ('运动鞋 Air Max', 'clothing', Decimal('899'), Decimal('350')),
        ('羽绒服', 'clothing', Decimal('1299'), Decimal('500')),
        ('有机牛奶(箱)', 'food', Decimal('89'), Decimal('45')),
        ('进口坚果礼盒', 'food', Decimal('168'), Decimal('80')),
        ('智能台灯', 'home', Decimal('299'), Decimal('120')),
        ('乳胶枕头', 'home', Decimal('399'), Decimal('150')),
        ('瑜伽垫', 'sports', Decimal('159'), Decimal('60')),
        ('跑步机', 'sports', Decimal('3999'), Decimal('1800')),
    ]

    regions = ['north', 'east', 'south', 'west', 'central']
    salespersons = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十']

    records = []
    now = datetime.date.today()

    for months_ago in range(6):
        month_date = now - datetime.timedelta(days=months_ago * 30)
        year = month_date.year
        month = month_date.month

        num_records = random.randint(50, 100)
        for _ in range(num_records):
            prod_name, category, price, cost = random.choice(products)
            qty = random.randint(1, 5)
            sale_date = datetime.date(year, month, random.randint(1, min(28, 31)))

            records.append(SalesRecord(
                product_name=prod_name,
                category=category,
                region=random.choice(regions),
                salesperson=random.choice(salespersons),
                quantity=qty,
                unit_price=price,
                total_amount=price * qty,
                cost=cost * qty,
                sale_date=sale_date,
            ))

    SalesRecord.objects.bulk_create(records, batch_size=500)
    print(f'  已创建 {len(records)} 条销售记录')


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    """主函数: 创建表、填充数据、演示报表生成"""
    print('=' * 70)
    print('  Django制作报表 - 企业级报表系统实战演示')
    print('  (Report Generation - Enterprise Report System Demo)')
    print('=' * 70)

    # 1. 创建数据库表
    print('\n[Step 1] 创建数据库表...')
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(SalesRecord)
        print(f'  [OK] 创建表: {SalesRecord._meta.db_table}')

    # 2. 填充示例数据
    print('\n[Step 2] 填充示例销售数据...')
    populate_sample_data()

    # 3. 数据查询演示
    print('\n[Step 3] 报表数据查询演示...')
    now = datetime.date.today()
    year = now.year
    month = now.month

    print(f'\n--- {year}年月度销售汇总 ---')
    summary = ReportDataService.get_monthly_sales_summary(year)
    for m in summary:
        print(f"  {m['month']}: 销售额 ¥{m['total_sales']:,.2f}, "
              f"利润 ¥{m['profit']:,.2f}, 订单 {m['order_count']}笔")

    print(f'\n--- {year}年{month}月 分类统计 ---')
    cat_data = ReportDataService.get_category_sales(year, month)
    for item in cat_data:
        print(f"  {item['category_name']}: ¥{item['total_sales']:,.2f} ({item['order_count']}笔)")

    print(f'\n--- {year}年{month}月 销售排名 ---')
    rank_data = ReportDataService.get_salesperson_ranking(year, month)
    for item in rank_data:
        print(f"  #{item['rank']} {item['salesperson']}: ¥{item['total_sales']:,.2f}")

    # 4. Excel导出演示
    print('\n[Step 4] Excel报表导出演示...')
    try:
        excel_buffer = ExcelReportGenerator.export_monthly_report(year, month)
        print(f'  [OK] Excel报表生成成功, 大小: {len(excel_buffer.getvalue())} bytes')
        output_path = f'sales_report_{year}_{month:02d}.xlsx'
        with open(output_path, 'wb') as f:
            f.write(excel_buffer.getvalue())
        print(f'  [OK] 已保存到: {output_path}')
    except Exception as e:
        print(f'  [ERROR] Excel导出失败: {e}')

    # 5. PDF导出演示
    print('\n[Step 5] PDF报表导出演示...')
    try:
        pdf_buffer = PDFReportGenerator.export_monthly_report(year, month)
        print(f'  [OK] PDF报表生成成功, 大小: {len(pdf_buffer.getvalue())} bytes')
        output_path = f'sales_report_{year}_{month:02d}.pdf'
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print(f'  [OK] 已保存到: {output_path}')
    except Exception as e:
        print(f'  [ERROR] PDF导出失败: {e}')

    # 6. 图表生成演示
    print('\n[Step 6] Matplotlib图表生成演示...')
    try:
        pie_chart = ChartGenerator.generate_category_pie_chart(year, month)
        print(f'  [OK] 饼图生成成功, 大小: {len(pie_chart.getvalue())} bytes')
    except Exception as e:
        print(f'  [WARN] 饼图生成: {e}')

    # 7. Django视图函数演示
    print('\n[Step 7] Django视图函数演示...')
    print('  可用API端点:')
    print(f'    GET /reports/excel/{year}/{month}/     - 导出Excel报表')
    print(f'    GET /reports/pdf/{year}/{month}/       - 导出PDF报表')
    print(f'    GET /api/dashboard/?year={year}&month={month}  - 仪表盘数据(JSON)')
    print(f'    GET /reports/chart/pie/?year={year}&month={month}  - 饼图图片')
    print(f'    GET /reports/chart/bar/?year={year}    - 柱状图图片')
    print(f'    GET /reports/chart/ranking/?year={year}&month={month}  - 排名图图片')

    print('\n' + '=' * 70)
    print('  所有演示执行完毕!')
    print('=' * 70)


if __name__ == '__main__':
    main()
