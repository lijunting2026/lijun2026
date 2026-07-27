from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.report.report_service import ReportService

router = APIRouter(prefix="/report", tags=["报告导出"])


def get_service(db: Session) -> ReportService:
    return ReportService(db)


@router.get("/word/{exam_id}")
def export_word(exam_id: str, db: Session = Depends(get_db)):
    try:
        service = get_service(db)
        buf = service.generate_word(exam_id)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=analysis_report.docx"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf/{exam_id}")
def export_pdf(exam_id: str, db: Session = Depends(get_db)):
    try:
        service = get_service(db)
        buf = service.generate_pdf(exam_id)
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=analysis_report.pdf"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ppt/{exam_id}")
def export_ppt(exam_id: str, db: Session = Depends(get_db)):
    try:
        service = get_service(db)
        buf = service.generate_ppt(exam_id)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f"attachment; filename=analysis_report.pptx"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/excel/{exam_id}")
def export_excel(exam_id: str, db: Session = Depends(get_db)):
    from app.services.analytics.analysis_service import AnalysisService
    import io, openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from fastapi.responses import StreamingResponse
    import urllib.parse
    
    service = AnalysisService(db)
    data = service.get_exam_analysis(exam_id)
    if not data:
        raise HTTPException(status_code=404, detail="考试不存在")
    
    wb = openpyxl.Workbook()
    
    # Sheet 1: 年级统计
    ws = wb.active
    ws.title = "年级统计"
    hf = Font(bold=True, color="FFFFFF", size=11)
    hfill = PatternFill(start_color="409EFF", end_color="409EFF", fill_type="solid")
    ha = Alignment(horizontal="center", vertical="center")
    tb = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
    
    headers = ["科目", "平均分", "得分率", "最高分", "最低分", "及格率", "优秀率", "标准差"]
    ws.append(["考试名称", data.get("exam_name", "")])
    ws.append(["考试日期", data.get("exam_date", "")])
    ws.append(["参考人数", data.get("total_students", 0)])
    ws.append([])
    ws.append(headers)
    for ci in range(1, len(headers)+1):
        c = ws.cell(row=5, column=ci)
        c.font, c.fill, c.alignment, c.border = hf, hfill, ha, tb
    
    for gs in data.get("grade_stats", []):
        ws.append([gs.get("subject_name", ""), gs.get("avg_score", ""), f"{gs.get('avg_score_rate', '')}%", gs.get("max_score", ""), gs.get("min_score", ""), f"{gs.get('pass_rate', '')}%", f"{gs.get('excellent_rate', '')}%", gs.get("std_dev", "")])
    
    ws.column_dimensions["A"].width = 14
    for c in "BCDEFGH":
        ws.column_dimensions[c].width = 12
    
    # Sheet 2: 班级统计
    ws2 = wb.create_sheet("班级统计")
    class_stats = data.get("class_stats", [])
    if class_stats:
        all_subj = list(set(s.get("subject_name", "") for cs in class_stats for s in cs.get("stats", [])))
        h2 = ["班级", "人数"] + all_subj
        ws2.append(h2)
        for ci in range(1, len(h2)+1):
            c = ws2.cell(row=1, column=ci)
            c.font, c.fill, c.alignment, c.border = hf, hfill, ha, tb
        for cs in class_stats:
            row_data = [cs.get("class_name", ""), cs.get("student_count", 0)]
            smap = {s.get("subject_name", ""): s.get("avg_score", "") for s in cs.get("stats", [])}
            for subj in all_subj:
                row_data.append(smap.get(subj, ""))
            ws2.append(row_data)
    
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={urllib.parse.quote(data.get('exam_name', 'report') + '_分析报表.xlsx')}"},
    )
