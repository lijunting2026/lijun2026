import io
from typing import Dict, Any, List, Optional
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage

from reportlab.pdfbase.ttfonts import TTFont
import os as _os
_CJK_REGISTERED = False
_CJK_FONT_CANDIDATES = [
    ('C:/Windows/Fonts/simsun.ttc', True),
    ('C:/Windows/Fonts/msyh.ttc', True),
    ('C:/Windows/Fonts/simhei.ttf', True),
    ('/System/Library/Fonts/PingFang.ttc', False),
]
for _path, _is_win in _CJK_FONT_CANDIDATES:
    if _os.path.exists(_path):
        try:
            pdfmetrics.registerFont(TTFont("CJK-Font", _path))
            _CJK_REGISTERED = True
            break
        except:
            continue


class PdfGenerator:
    def __init__(self, db):
        self.db = db

    def _get_cjk_style(self, name, parent, **kw):
        """Create a paragraph style with CJK font support"""
        from reportlab.lib.styles import ParagraphStyle
        try:
            style = ParagraphStyle(name, parent=parent, **kw)
            style.fontName = "CJK-Font"
        except:
            style = ParagraphStyle(name, parent=parent, **kw)
        return style

    def _add_chart_to_pdf(self, elements, chart_buf, width=460, height=260):
        """Add a chart image to PDF elements list"""
        import sys as _sys
        if chart_buf:
            buf_data = chart_buf.getvalue()
            print(f"DEBUG: chart buf size: {len(buf_data)}", file=_sys.stderr)
            if len(buf_data) > 500:
                chart_buf.seek(0)
                try:
                    elements.append(RLImage(chart_buf, width=width, height=height))
                    elements.append(Spacer(1, 8))
                except Exception as e:
                    print(f"DEBUG: chart add error: {e}", file=_sys.stderr)

    def generate_class_pdf(self, class_id: str) -> io.BytesIO:
        from app.services.analytics.student_tracking import ClassAnalysisService
        service = ClassAnalysisService(self.db)
        data = service.get_class_overview(class_id)
        if not data:
            return None

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = self._get_cjk_style('CustomTitle', styles['Title'], fontSize=18, spaceAfter=12)
        heading_style = self._get_cjk_style('CustomHeading', styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6)
        normal = self._get_cjk_style('CJKNormal', styles['Normal'])

        elements = []
        elements.append(Paragraph(f"{data.get('class_name', '')} 班级分析报告", title_style))
        elements.append(Paragraph(f"年级: {data.get('grade_name', '-')}    学生人数: {data.get('student_count', 0)}    考试次数: {data.get('exam_count', 0)}", normal))
        elements.append(Spacer(1, 12))

        # Subject stats table
        elements.append(Paragraph("各科统计", heading_style))
        subject_stats = data.get("subject_stats", [])
        if subject_stats:
            t_data = [[s.get("subject_name", ""), str(s.get("avg_score", "")), str(s.get("max_score", "")), str(s.get("min_score", "")), str(s.get("count", ""))] for s in subject_stats]
            t = Table([["科目", "平均分", "最高分", "最低分", "样本数"]] + t_data, colWidths=[80, 70, 70, 70, 60])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#409EFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'CJK-Font'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 8))

        # Subject bar chart
        if subject_stats:
            try:
                labels = [s.get("subject_name", "") for s in subject_stats]
                scores = [s.get("avg_score", 0) for s in subject_stats]
                chart_buf = draw_bar_chart(scores, labels, title="各科平均分", ylabel="平均分", width=520, height=320)
                if chart_buf and len(chart_buf.getvalue()) > 500:
                    from reportlab.platypus import Image as RLImage
                    chart_buf.seek(0)
                    elements.append(PageBreak())
                    elements.append(Paragraph("各科平均分柱状图", heading_style))
                    elements.append(RLImage(chart_buf, width=460, height=280))
                    elements.append(Spacer(1, 12))
            except:
                pass

        elements.append(Paragraph("考试成绩趋势", heading_style))
        exam_summary = data.get("exam_summary", [])
        if exam_summary:
            t_data = [[e.get("exam_name", ""), e.get("exam_date", ""), f"{e.get('avg_rate', '')}%"] for e in exam_summary]
            t = Table([["考试名称", "考试日期", "平均得分率(%)"]] + t_data, colWidths=[160, 80, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#409EFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'CJK-Font'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 8))

        # Exam trend line chart
        if exam_summary:
            try:
                rates = [e.get("avg_rate", 0) or 0 for e in exam_summary]
                exam_names = [e.get("exam_name", "")[:8] for e in exam_summary]
                if rates:
                    chart_buf = draw_line_chart([{"name": "得分率", "data": rates}], exam_names, title="考试成绩趋势", width=520, height=300)
                    if chart_buf and len(chart_buf.getvalue()) > 500:
                        from reportlab.platypus import Image as RLImage
                        chart_buf.seek(0)
                        elements.append(PageBreak())
                        elements.append(Paragraph("考试成绩趋势图", heading_style))
                        elements.append(RLImage(chart_buf, width=460, height=260))
                        elements.append(Spacer(1, 12))
            except:
                pass

        elements.append(Paragraph("学生成绩一览", heading_style))
        student_list = data.get("student_list", [])
        if student_list:
            t_data = [[s.get("student_no", ""), s.get("student_name", ""), f"{s.get('avg_rate', '')}%" if s.get('avg_rate') is not None else "-"] for s in student_list[:30]]
            t = Table([["学号", "姓名", "得分率(%)"]] + t_data, colWidths=[110, 90, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#409EFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'CJK-Font'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
            ]))
            elements.append(t)
            if len(student_list) > 30:
                elements.append(Paragraph(f"...共 {len(student_list)} 名学生，仅展示前30名", normal))

        doc.build(elements)
        buf.seek(0)
        return buf

    # ==================== STUDENT ANALYSIS ====================

    def generate_student_pdf(self, student_id: str) -> io.BytesIO:
        service = StudentTrackingService(self.db)
        data = service.get_student_scores(student_id)
        if not data:
            return None

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = self._get_cjk_style('CustomTitle', styles['Title'], fontSize=18, spaceAfter=12)
        heading_style = self._get_cjk_style('CustomHeading', styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6)
        normal = self._get_cjk_style('CJKNormal', styles['Normal'])
        bold = self._get_cjk_style('BoldNormal', styles['Normal'], fontSize=10, spaceAfter=4)

        elements = []
        elements.append(Paragraph(f"{data.get('student_name', '')} 学情跟踪报告", title_style))
        elements.append(Paragraph(f"学号: {data.get('student_no', '-')}    班级: {data.get('class_name', '-')}    年级: {data.get('grade_name', '-')}", normal))
        elements.append(Paragraph(f"考试次数: {data.get('exam_count', 0)}    总体趋势: {data.get('overall_trend', '暂无数据')}", normal))
        elements.append(Spacer(1, 12))

        # Strengths & Weaknesses
        elements.append(Paragraph("优势与薄弱科目", heading_style))
        strengths = data.get("strengths", [])
        weaknesses = data.get("weaknesses", [])
        if strengths:
            s_text = "; ".join([f"{s.get('subject_name', '')}(平均{s.get('avg_rate', '')}%/最新{s.get('latest_rate', '')}%)" for s in strengths])
            elements.append(Paragraph(f"<b>优势科目:</b> {s_text}", bold))
        if weaknesses:
            w_text = "; ".join([f"{s.get('subject_name', '')}(平均{s.get('avg_rate', '')}%/最新{s.get('latest_rate', '')}%)" for s in weaknesses])
            elements.append(Paragraph(f"<b>薄弱科目:</b> {w_text}", bold))

        # Trend chart
        elements.append(Paragraph("各科成绩趋势", heading_style))
        exams = data.get("exams", [])
        trends = data.get("trends", [])
        if exams and trends:
            exam_names = [e.get("exam_name", "")[:6] for e in exams]
            series_list = []
            for t in trends:
                scores = [(s.get("rate", 0) or 0) for s in (t.get("scores") or [])]
                if scores:
                    series_list.append({"name": t.get("subject_name", ""), "data": scores})
            # Trend chart
        elements.append(Paragraph("各科成绩趋势", heading_style))
        exams = data.get("exams", [])
        trends = data.get("trends", [])
        if exams and trends:
            try:
                exam_names = [e.get("exam_name", "")[:6] for e in exams]
                series_list = []
                for t in trends:
                    scores = [(s.get("rate", 0) or 0) for s in (t.get("scores") or [])]
                    if scores:
                        series_list.append({"name": t.get("subject_name", ""), "data": scores})
                if series_list:
                    chart = draw_line_chart(series_list, exam_names, title="各科成绩趋势", ylabel="得分率(%)", width=520, height=320)
                    if chart and len(chart.getvalue()) > 500:
                        from reportlab.platypus import Image as RLImage
                        chart.seek(0)
                        elements.append(PageBreak())
                        elements.append(Paragraph("各科成绩趋势图", heading_style))
                        elements.append(RLImage(chart, width=460, height=280))
                        elements.append(Spacer(1, 12))
            except:
                pass

        # Exam history
        elements.append(Paragraph("历次成绩", heading_style))
        if exams:
            t_data = []
            for e in exams:
                row = [e.get("exam_name", ""), e.get("exam_date", ""), f"{e.get('avg_rate', '')}%" if e.get('avg_rate') else "-"]
                for s in (e.get("subjects") or []):
                    row.append(f"{s.get('subject_name', '')}:{s.get('score', '-')}")
                t_data.append(row)
            max_cols = max(len(r) for r in t_data) if t_data else 3
            headers = ["考试", "日期", "综合得分率"]
            if t_data:
                extra = max_cols - 3
                for i in range(extra):
                    headers.append("科目" + str(i+1))
            t = Table([headers] + t_data, colWidths=[100, 60, 70] + [50] * (max_cols - 3))
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#409EFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'CJK-Font'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))
            elements.append(t)

        doc.build(elements)
        buf.seek(0)
        return buf

    # ==================== WORD ====================

    def generate_pdf(self, exam_id: str) -> io.BytesIO:
        data = self.get_analysis_data(exam_id)
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)

        styles = getSampleStyleSheet()
        title_style = self._get_cjk_style('CustomTitle', styles['Title'], fontSize=18, spaceAfter=20)
        heading_style = self._get_cjk_style('CustomHeading', styles['Heading2'], fontSize=14, spaceBefore=12, spaceAfter=6)
        normal = self._get_cjk_style('CJKNormal', styles['Normal'])

        elements = []
        elements.append(Paragraph(data.get("exam_name", "考试分析报告"), title_style))
        elements.append(Paragraph(f"考试日期: {data.get('exam_date', '-')}", normal))
        elements.append(Paragraph(f"参考人数: {data.get('total_students', 0)}", normal))
        elements.append(Spacer(1, 12))

        # Grade stats
        elements.append(Paragraph("年级总体统计", heading_style))
        grade_stats = data.get("grade_stats", [])
        if grade_stats:
            headers = ["科目", "平均分", "得分率%", "最高分", "最低分", "及格率%", "优秀率%", "标准差"]
            rows = [[
                gs.get("subject_name", ""),
                str(gs.get("avg_score", "")),
                str(gs.get("avg_score_rate", "")),
                str(gs.get("max_score", "")),
                str(gs.get("min_score", "")),
                str(gs.get("pass_rate", "")),
                str(gs.get("excellent_rate", "")),
                str(gs.get("std_dev", ""))
            ] for gs in grade_stats]
            t = Table([headers] + rows, colWidths=[46, 38, 38, 34, 34, 38, 38, 34])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#409EFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'CJK-Font'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('LEADING', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f7fa')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(t)
            elements.append(PageBreak())

        # Class stats
        elements.append(Paragraph("各班统计", heading_style))
        for cs in data.get("class_stats", []):
            elements.append(Paragraph(f"{cs.get('class_name', '')} (人数: {cs.get('student_count', 0)})", heading_style))
            stats_list = cs.get("stats", [])
            if stats_list:
                h = ["科目", "平均分", "得分率%", "及格率%"]
                r = [[s.get("subject_name", ""), str(s.get("avg_score", "")), str(s.get("avg_score_rate", "")), str(s.get("pass_rate", ""))] for s in stats_list]
                t = Table([h] + r, colWidths=[80, 55, 55, 55])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#409EFF')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, -1), 'CJK-Font'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 8))

        doc.build(elements)
        buf.seek(0)
        return buf

    # ==================== PPT ====================

