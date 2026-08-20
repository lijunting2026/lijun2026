"""再训练练习生成服务 —— 根据薄弱知识点生成分层练习"""
import uuid, random
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.exam_detail import SubjectKnowledgePoint
from app.models.subject import Subject


class PracticeGeneratorService:
    """练习生成服务 —— 基于薄弱知识点生成针对性训练题"""

    PRACTICE_TEMPLATES = {
        "选择题": {
            "基础": [
                "下列关于 {kp} 的说法正确的是：",
                "在 {kp} 中，下列哪个选项是正确的？",
                "以下关于 {kp} 的描述，错误的是：",
            ],
            "提高": [
                "已知关于 {kp} 的条件，下列结论正确的是：",
                "结合 {kp} 的知识，分析以下哪个选项正确：",
                "在 {kp} 的应用中，下列推理正确的是：",
            ],
            "挑战": [
                "综合运用 {kp} 的知识，判断以下结论：",
                "在复杂情境中应用 {kp}，下列分析最合理的是：",
                "以下关于 {kp} 的综合论述，正确的是：",
            ],
        },
        "填空题": {
            "基础": [
                "根据 {kp} 的基本性质，填空：____",
                "在 {kp} 中，已知条件为 ____，则结果为：",
                "计算以下 {kp} 相关问题，填入答案：____",
            ],
            "提高": [
                "已知 {kp} 的条件，推导出 ____",
                "综合运用 {kp}，完成以下推导：____",
                "分析 {kp} 的变式问题，填空：____",
            ],
            "挑战": [
                "在 {kp} 的综合问题中，填入正确推理步骤：____",
                "探索 {kp} 的深层规律，完成证明：____",
            ],
        },
        "解答题": {
            "基础": [
                "请简述 {kp} 的基本概念，并举例说明。",
                "根据 {kp} 的定义，解决以下简单问题。",
                "应用 {kp} 的基本公式，完成下列计算。",
            ],
            "提高": [
                "综合运用 {kp} 的相关知识，解决下列问题，写出详细过程。",
                "分析以下关于 {kp} 的问题，写出解题思路和步骤。",
                "结合 {kp} 与其他相关知识，完成下列证明或计算。",
            ],
            "挑战": [
                "深入探究 {kp} 的综合应用，解决以下复杂问题。",
                "在 {kp} 的背景下，设计解题方案并完整作答。",
                "综合运用多个知识点（包含 {kp}），完成以下综合题。",
            ],
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def generate_practice(
        self,
        student_id: str,
        weak_knowledge_points: List[Dict] = None,
        question_count: int = 10,
        include_types: List[str] = None,
    ) -> Dict[str, Any]:
        """生成针对性练习"""
        if include_types is None:
            include_types = ["选择题", "填空题", "解答题"]

        if not weak_knowledge_points:
            return {
                "student_id": student_id,
                "practice_sheets": [],
                "total_questions": 0,
                "message": "无薄弱知识点，无需生成练习",
            }

        sheets = []
        question_id = 0

        # Sort weak KPs by mastery rate (ascending = weakest first)
        sorted_kps = sorted(weak_knowledge_points, key=lambda x: x.get("mastery_rate", 100))

        # Distribute questions across KPs
        kp_question_count = max(1, question_count // len(sorted_kps))

        for kp_info in sorted_kps[:8]:  # Limit to top 8 weakest KPs
            kp_name = kp_info.get("knowledge_point_name", "")
            if not kp_name:
                continue

            kp_questions = []
            # Generate 3 difficulty levels per KP
            for difficulty in ["基础", "提高", "挑战"]:
                if len(kp_questions) >= kp_question_count:
                    break
                if kp_question_count <= 3:
                    # Few questions per KP, use "提高" primarily
                    target_difficulty = "提高"
                else:
                    target_difficulty = difficulty

                # Pick a question type
                q_types_pool = [t for t in include_types if t in self.PRACTICE_TEMPLATES]
                if not q_types_pool:
                    q_types_pool = ["选择题", "填空题"]

                for q_type in q_types_pool:
                    templates = self.PRACTICE_TEMPLATES.get(q_type, {}).get(target_difficulty, [])
                    if not templates:
                        continue
                    template = random.choice(templates)
                    question_id += 1
                    kp_questions.append({
                        "id": f"p{question_id}",
                        "question_no": question_id,
                        "question_type": q_type,
                        "difficulty": target_difficulty,
                        "content": template.format(kp=kp_name),
                        "knowledge_point": kp_name,
                        "hint": f"本题考察「{kp_name}」，{self._get_difficulty_hint(target_difficulty)}",
                        "estimated_time": self._get_estimated_time(q_type, target_difficulty),
                    })
                    if len(kp_questions) >= kp_question_count:
                        break

            if kp_questions:
                sheets.append({
                    "knowledge_point": kp_name,
                    "mastery_rate": kp_info.get("mastery_rate", 0),
                    "questions": kp_questions,
                })

        # Flatten for total count
        total = sum(len(s["questions"]) for s in sheets)

        return {
            "student_id": student_id,
            "practice_sheets": sheets,
            "total_questions": total,
            "message": f"已针对 {len(sheets)} 个薄弱知识点生成 {total} 道练习题",
        }

    def generate_from_student_analysis(self, student_kp_data: Dict, question_count: int = 10) -> Dict[str, Any]:
        """从学生知识点分析结果生成练习"""
        weaknesses = student_kp_data.get("weaknesses", [])
        if not weaknesses:
            return {
                "practice_sheets": [],
                "total_questions": 0,
                "message": "暂无薄弱知识点，请继续保持！",
            }

        kp_list = [
            {
                "knowledge_point_id": w.get("knowledge_point_id", ""),
                "knowledge_point_name": w.get("knowledge_point_name", ""),
                "mastery_rate": w.get("mastery_rate", 0),
            }
            for w in weaknesses
        ]

        return self.generate_practice("", kp_list, question_count)

    def _get_difficulty_hint(self, difficulty: str) -> str:
        hints = {
            "基础": "建议先回顾基本概念和公式",
            "提高": "需要灵活运用知识，注意分析题目条件",
            "挑战": "综合性强，建议分步骤分析，注意知识点之间的联系",
        }
        return hints.get(difficulty, "")

    def _get_estimated_time(self, q_type: str, difficulty: str) -> str:
        times = {
            "选择题": {"基础": "1分钟", "提高": "2分钟", "挑战": "3分钟"},
            "填空题": {"基础": "1分钟", "提高": "2分钟", "挑战": "3分钟"},
            "解答题": {"基础": "5分钟", "提高": "8分钟", "挑战": "12分钟"},
        }
        return times.get(q_type, {}).get(difficulty, "3分钟")
