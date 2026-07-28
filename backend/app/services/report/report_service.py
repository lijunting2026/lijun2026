import io
from typing import Dict, Any, List, Optional
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

from app.services.analytics.analysis_service import AnalysisService
from app.services.analytics.student_tracking import StudentTrackingService, ClassAnalysisService
from app.services.report.chart_generator import draw_bar_chart, draw_line_chart, draw_radar_chart, draw_table_image
from app.services.report.pdf_generator import PdfGenerator
from app.services.report.ppt_generator import PptGenerator

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage

from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGB
from pptx.enum.text import PP_ALIGN

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os as _os
_CJK_REGISTERED = False
_CJK_FONT_CANDIDATES = [
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..", "fonts", "SimSun.ttf"),
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..", "fonts", "simsun.ttc"),
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..", "fonts", "msyh.ttf"),
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..", "fonts", "msyhbd.ttf"),
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]

class ReportService:
    def __init__(self, db):
        self.db = db
        self.pdf_gen = PdfGenerator(db)
        self.ppt_gen = PptGenerator(db)
    
    def get_analysis_data(self, exam_id: str) -> Dict[str, Any]:
        return self.analysis_service.get_exam_analysis(exam_id)


    # ==================== CLASS ANALYSIS ====================

    def _add_chart_to_docx(self, doc, chart_buf, width_inches=5.5):
        """Add a chart image to a Word document"""
        if chart_buf and chart_buf.getbuffer().nbytes > 1000:
            doc.add_picture(chart_buf, width=Inches(width_inches))
            doc.add_paragraph("")

    def generate_class_word(self, class_id: str) -> io.BytesIO:
        from app.services.analytics.student_tracking import ClassAnalysisService
        service = ClassAnalysisService(self.db)
        data = service.get_class_overview(class_id)
        if not data:
            return None

        doc = Document()
        style = doc.styles['Normal']
        font = style.font
        font.name = 'SimSun'
        font.size = Pt(11)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

        # Title
        title = doc.add_heading(f"{data.get('class_name', '')} 班级分析报告", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(f"年级: {data.get('grade_name', '-')}    学生人数: {data.get('student_count', 0)}    考试次数: {data.get('exam_count', 0)}")
        doc.add_paragraph("")

        # Overview table
        doc.add_heading("各科统计", level=1)
        subject_stats = data.get("subject_stats", [])
        if subject_stats:
            table = doc.add_table(rows=1, cols=5)
            table.style = 'Light Grid Accent 1'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            hdr = table.rows[0].cells
            for i, h in enumerate(["科目", "平均分", "最高分", "最低分", "样本数"]):
                hdr[i].text = h
            for ss in subject_stats:
                row = table.add_row().cells
                row[0].text = ss.get("subject_name", "")
                row[1].text = str(ss.get("avg_score", ""))
                row[2].text = str(ss.get("max_score", ""))
                row[3].text = str(ss.get("min_score", ""))
                row[4].text = str(ss.get("count", ""))

        # Bar chart - subject averages
        if subject_stats:
            labels = [s.get("subject_name", "") for s in subject_stats]
            scores = [s.get("avg_score", 0) for s in subject_stats]
            chart = draw_bar_chart(scores, labels, title="各科平均分", ylabel="平均分")
            self._add_chart_to_docx(doc, chart)

        # Exam trend
        doc.add_heading("考试成绩趋势", level=1)
        exam_summary = data.get("exam_summary", [])
        if exam_summary:
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Light Grid Accent 1'
            for i, h in enumerate(["考试名称", "考试日期", "平均得分率(%)"]):
                table.rows[0].cells[i].text = h
            for es in exam_summary:
                row = table.add_row().cells
                row[0].text = es.get("exam_name", "")
                row[1].text = es.get("exam_date", "")
                row[2].text = f"{es.get('avg_rate', '')}%"

            # Line chart
            exam_names = [e.get("exam_name", "")[:8] for e in exam_summary]
            rates = [e.get("avg_rate", 0) or 0 for e in exam_summary]
            if rates:
                chart = draw_line_chart([{"name": "得分率", "data": rates}], exam_names, title="考试成绩趋势", ylabel="得分率(%)")
                self._add_chart_to_docx(doc, chart)

        # Student list
        doc.add_heading("学生成绩一览", level=1)
        student_list = data.get("student_list", [])
        if student_list:
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Light Grid Accent 1'
            for i, h in enumerate(["学号", "姓名", "综合得分率(%)"]):
                table.rows[0].cells[i].text = h
            for sl in student_list:
                row = table.add_row().cells
                row[0].text = sl.get("student_no", "")
                row[1].text = sl.get("student_name", "")
                row[2].text = f"{sl.get('avg_rate', '')}%" if sl.get('avg_rate') is not None else "-"

        # Risk students
        risk = data.get("risk_students", [])
        if risk:
            doc.add_heading("需关注学生", level=1)
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Light Grid Accent 1'
            for i, h in enumerate(["学号", "姓名", "综合得分率(%)"]):
                table.rows[0].cells[i].text = h
            for r in risk:
                row = table.add_row().cells
                row[0].text = r.get("student_no", "")
                row[1].text = r.get("student_name", "")
                row[2].text = f"{r.get('avg_rate', '')}%"

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf

    def generate_student_word(self, student_id: str) -> io.BytesIO:
        service = StudentTrackingService(self.db)
        data = service.get_student_scores(student_id)
        if not data:
            return None

        doc = Document()
        style = doc.styles['Normal']
        font = style.font
        font.name = 'SimSun'
        font.size = Pt(11)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

        # Title
        title = doc.add_heading(f"{data.get('student_name', '')} 学情跟踪报告", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(f"学号: {data.get('student_no', '-')}    班级: {data.get('class_name', '-')}    年级: {data.get('grade_name', '-')}")
        doc.add_paragraph(f"考试次数: {data.get('exam_count', 0)}    总体趋势: {data.get('overall_trend', '暂无数据')}")
        doc.add_paragraph("")

        # Strengths & Weaknesses
        doc.add_heading("优势与薄弱科目", level=1)
        strengths = data.get("strengths", [])
        weaknesses = data.get("weaknesses", [])
        if strengths or weaknesses:
            doc.add_paragraph(f"优势科目 ({len(strengths)}): " + ", ".join([f"{s.get('subject_name', '')}({s.get('avg_rate', '')}%)" for s in strengths]))
            doc.add_paragraph(f"薄弱科目 ({len(weaknesses)}): " + ", ".join([f"{s.get('subject_name', '')}({s.get('avg_rate', '')}%)" for s in weaknesses]))
            doc.add_paragraph("")

        # Trend chart
        doc.add_heading("各科成绩趋势", level=1)
        exams = data.get("exams", [])
        trends = data.get("trends", [])
        if exams and trends:
            exam_names = [e.get("exam_name", "")[:6] for e in exams]
            series_list = []
            for t in trends:
                scores = [(s.get("rate", 0) or 0) for s in (t.get("scores") or [])]
                if scores:
                    series_list.append({"name": t.get("subject_name", ""), "data": scores})
            if series_list and exam_names:
                chart = draw_line_chart(series_list, exam_names, title="各科成绩趋势", ylabel="得分率(%)", width=640, height=360)
                self._add_chart_to_docx(doc, chart)

        # Exam history table
        doc.add_heading("历次成绩", level=1)
        if exams:
            table = doc.add_table(rows=1, cols=3 + max((len(e.get("subjects", [])) for e in exams), default=0))
            table.style = 'Light Grid Accent 1'
            hdr = table.rows[0].cells
            hdr[0].text = "考试"
            hdr[1].text = "日期"
            hdr[2].text = "综合得分率"
            col = 3
            for e in exams:
                for s in (e.get("subjects") or []):
                    if col < len(hdr):
                        hdr[col].text = s.get("subject_name", "")
                    col += 1
                break  # Only need first exam's subjects for headers
            for e in exams:
                row = table.add_row().cells
                row[0].text = e.get("exam_name", "")
                row[1].text = e.get("exam_date", "")
                row[2].text = f"{e.get('avg_rate', '')}%"
                ci = 3
                for s in (e.get("subjects") or []):
                    if ci < len(row):
                        row[ci].text = str(s.get("score", "-"))
                        ci += 1

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf

    def generate_word(self, exam_id: str) -> io.BytesIO:
        from app.services.report.word_generator import generate_exam_word
        return generate_exam_word(exam_id, self.db, self.analysis_service)


    def generate_pdf(self, exam_id: str) -> io.BytesIO:
        return self.pdf_gen.generate_pdf(exam_id)

    def generate_class_pdf(self, class_id: str) -> io.BytesIO:
        return self.pdf_gen.generate_class_pdf(class_id)

    def generate_student_pdf(self, student_id: str) -> io.BytesIO:
        return self.pdf_gen.generate_student_pdf(student_id)

    def generate_ppt(self, exam_id: str) -> io.BytesIO:
        return self.ppt_gen.generate_ppt(exam_id)
