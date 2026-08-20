"""赋分换算服务 - 按等级比例区间将原始分换算为赋分"""
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.exam import ExamSubject
from app.models.score import Score
from app.models.scoring import ScoringScheme


class ScoreConversionService:
    """基于累计百分比 + 等级区间线性插值的赋分换算。

    规则：
    1. 原始分降序排序，对每个唯一分数 x 计算累计百分比 p(x) = 该分数及以上人数 / 总人数 * 100
    2. 按 p 落入唯一等级 Bk（rank_start*100 <= p < rank_end*100，末档含边界）
    3. 段内等比例插值：赋分 = score_end + (score_start - score_end) * (x - 段内下限) / (段内上限 - 段内下限)
    4. 段内只有一个唯一分数时赋分取该段上限 score_start
    5. 同原始分 -> 同 p -> 同等级 -> 同赋分
    """

    def __init__(self, db: Session):
        self.db = db

    def convert_exam_subject(self, exam_subject_id, force: bool = False) -> Dict:
        es = self.db.query(ExamSubject).filter(ExamSubject.id == exam_subject_id).first()
        if not es:
            raise ValueError("考试科目不存在")
        if es.scoring_type != "converted":
            return {"exam_subject_id": str(exam_subject_id), "converted": 0, "total": 0, "message": "该科目未标记为赋分科目，跳过"}
        if not es.scheme_id:
            raise ValueError("未配置赋分方案，请先在考试配置中选择方案")
        scheme = self.db.query(ScoringScheme).filter(ScoringScheme.id == es.scheme_id).first()
        if not scheme or not scheme.brackets:
            raise ValueError("赋分方案不存在或为空")
        brackets = sorted(scheme.brackets, key=lambda b: float(b.get("rank_start", 0)))
        scores = self.db.query(Score).filter(Score.exam_subject_id == exam_subject_id).all()
        if not scores:
            return {"exam_subject_id": str(exam_subject_id), "converted": 0, "total": 0, "message": "暂无成绩数据"}

        total = len(scores)
        raw_values = sorted({s.score_value for s in scores}, reverse=True)

        # 每个唯一分数的累计百分比（该分数及以上人数占比）
        pct: Dict[float, float] = {}
        cumulative = 0
        for x in raw_values:
            cumulative += sum(1 for s in scores if s.score_value == x)
            pct[x] = cumulative / total * 100.0

        # 唯一分数归入等级区间
        bracket_groups: Dict[int, List[float]] = {}
        for x in raw_values:
            p = pct[x]
            for i, b in enumerate(brackets):
                rs = float(b.get("rank_start", 0)) * 100.0
                re = float(b.get("rank_end", 1)) * 100.0
                if p >= rs and (p < re or i == len(brackets) - 1):
                    bracket_groups.setdefault(i, []).append(x)
                    break
            else:
                raise ValueError(f"原始分 {x} 的累计百分比 {p:.2f}% 不在任何等级区间内")

        converted_by_score: Dict[float, int] = {}
        for i, b in enumerate(brackets):
            xs = bracket_groups.get(i, [])
            if not xs:
                continue
            score_start = float(b.get("score_start", 100))
            score_end = float(b.get("score_end", 30))
            if score_end > score_start:
                score_start, score_end = score_end, score_start
            lo, hi = min(xs), max(xs)
            for x in xs:
                if hi == lo:
                    converted = score_start
                else:
                    converted = score_end + (score_start - score_end) * (x - lo) / (hi - lo)
                converted_by_score[x] = int(round(converted))

        updated = 0
        for s in scores:
            if not force and es.conversion_mode == "manual" and s.converted_score is not None:
                continue
            s.converted_score = float(converted_by_score.get(s.score_value))
            s.converted_source = "system"
            updated += 1
        self.db.commit()
        return {"exam_subject_id": str(exam_subject_id), "converted": updated, "total": total}
