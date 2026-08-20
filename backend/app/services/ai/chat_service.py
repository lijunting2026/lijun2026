import uuid, json, math, os as os_module
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import httpx

from app.models.score import Score
from app.models.student import Student
from app.models.exam import Exam, ExamSubject
from app.models.subject import Subject
from app.models.school import ClassInfo
from app.core.config import settings
from app.services.analytics.analysis_service import AnalysisService
from app.services.analytics.student_tracking import StudentTrackingService


class AIChatService:
    def __init__(self, db: Session):
        self.db = db
        self.analysis_svc = AnalysisService(db)
        self.student_svc = StudentTrackingService(db)

    def chat(self, message: str, context_type: str = "general", context_id: str = None, history: list = None) -> Dict[str, Any]:
        context_data = {}

        # Collect context based on type
        if context_type == "exam" and context_id:
            context_data = self.analysis_svc.get_exam_analysis(context_id)
        elif context_type == "student" and context_id:
            context_data = self.student_svc.get_student_scores(context_id)
            advice = self.student_svc.generate_advice(context_id)
            if advice:
                context_data["advice"] = advice
        elif context_type == "report" and context_id:
            context_data = self.analysis_svc.get_exam_analysis(context_id)

        # Try LLM first if configured
        if settings.LLM_ENABLED and settings.LLM_API_KEY:
            try:
                response = self._call_llm(message, context_type, context_data)
                if response:
                    return {"response": response, "context_type": context_type, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            except Exception as e:
                print(f"LLM call failed, falling back to rule-based: {e}")

        # Fallback to rule-based response
        response = self._generate_response(message, context_type, context_data)
        return {"response": response, "context_type": context_type, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def _build_messages(self, system_prompt: str, message: str, history: list = None) -> list:
        """Build message list with history for multi-turn conversation"""
        msgs = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history:
                role = "assistant" if h.role == "assistant" else "user"
                msgs.append({"role": role, "content": h.content})
        msgs.append({"role": "user", "content": message})
        return msgs

    def _call_llm(self, message: str, context_type: str, data: Dict, history: list = None) -> Optional[str]:
        # Build system prompt from context
        system_prompt = "你是一个专业的考试成绩分析AI助手，擅长数据分析、学情诊断和学习建议。请基于提供的上下文数据，用中文回答用户的问题。回答要专业、简洁、有洞察力。"

        if context_type == "exam" and data:
            exam_name = data.get("exam_name", "未知")
            total_students = data.get("total_students", 0)
            grade_stats = data.get("grade_stats", [])
            system_prompt += f"\n\n当前正在分析考试：{exam_name}，参考人数：{total_students}"
            if grade_stats:
                stats_summary = "; ".join([f"{g['subject_name']}: 平均分{g['avg_score']}, 得分率{g['avg_score_rate']}%, 及格率{g['pass_rate']}%, 优秀率{g['excellent_rate']}%" for g in grade_stats[:6]])
                system_prompt += f"\n各科统计：{stats_summary}"

        elif context_type == "student" and data:
            student_name = data.get("student_name", "未知")
            exam_count = data.get("exam_count", 0)
            overall_trend = data.get("overall_trend", "未知")
            strengths = data.get("strengths", [])
            weaknesses = data.get("weaknesses", [])
            system_prompt += f"\n\n当前查看学生：{student_name}，考试次数：{exam_count}，总体趋势：{overall_trend}"
            if strengths:
                system_prompt += f"\n优势科目：{', '.join([s['subject_name'] for s in strengths])}"
            if weaknesses:
                system_prompt += f"\n薄弱科目：{', '.join([s['subject_name'] for s in weaknesses])}"

        elif context_type == "general":
            system_prompt += "\n\n当前为通用对话模式，用户可以咨询考试分析、学情跟踪、报告生成等功能。"

        # Call OpenAI-compatible API
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    f"{settings.LLM_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                )
                if resp.status_code == 200:
                    result = resp.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"LLM API error: {resp.status_code} {resp.text[:200]}")
                    return None
        except Exception as e:
            print(f"LLM request failed: {e}")
            return None

    def _generate_response(self, message: str, context_type: str, data: Dict) -> str:
        msg_lower = message.lower()

        # PPT optimization
        if context_type == "report" and any(k in msg_lower for k in ["ppt", "版式", "优化", "布局", "设计"]):
            return self._ppt_suggestion(data)

        # Student deep analysis
        if context_type == "student" and any(k in msg_lower for k in ["分析", "指导", "建议", "怎么", "如何", "改进"]):
            return self._student_analysis(data, message)

        # Exam deep analysis
        if context_type == "exam" and any(k in msg_lower for k in ["分析", "解读", "怎么看", "说明", "趋势", "对比"]):
            return self._exam_analysis(data, message)

        # Default by context
        if context_type == "exam":
            return self._exam_analysis(data, message)
        elif context_type == "student":
            return self._student_analysis(data, message)
        else:
            return self._general_chat(data, message)

    def _ppt_suggestion(self, data: Dict) -> str:
        lines = []
        lines.append("💡 **PPT 优化建议**\n")
        exam_name = data.get("exam_name", "考试")
        grade_stats = data.get("grade_stats", [])
        class_stats = data.get("class_stats", [])
        lines.append(f"### 1. 封面设计")
        lines.append(f'- 标题：**{exam_name}质量分析报告**')
        lines.append(f'- 副标题：包含考试日期、参考人数等关键信息')
        lines.append(f'- 推荐使用学校主题色作为背景，居中排版\n')
        lines.append(f"### 2. 内容结构优化")
        lines.append(f'- **Slide 1**：封面 + 核心数据摘要')
        lines.append(f'- **Slide 2**：年级总体统计表 + 各科平均分柱状图')
        lines.append(f'- **Slide 3**：各科得分率雷达图 + 及格率/优秀率对比')
        lines.append(f'- **Slide 4-5**：各班统计（每班一页或两班一页）')
        lines.append(f'- **Slide 6**：分数段分布图')
        lines.append(f'- **Slide 7**：总结与建议\n')
        lines.append(f"### 3. 可视化建议")
        lines.append(f'- 柱状图使用渐变色，前3名用亮色标注')
        lines.append(f'- 雷达图展示各科均衡程度，一目了然')
        lines.append(f'- 折线图展示历次考试趋势（需多场考试数据）')
        lines.append(f'- 表格使用斑马纹，标题行深蓝底白字\n')
        if grade_stats:
            best = max(grade_stats, key=lambda x: x.get("avg_score", 0))
            worst = min(grade_stats, key=lambda x: x.get("avg_score", 0))
            lines.append(f"### 4. 关键数据点")
            lines.append(f'- 最高平均分科目：{best.get("subject_name", "")}（{best.get("avg_score", "")}分）')
            lines.append(f'- 最低平均分科目：{worst.get("subject_name", "")}（{worst.get("avg_score", "")}分）')
        return "\n".join(lines)

    def _student_analysis(self, data: Dict, message: str) -> str:
        if not data:
            return "⚠️ 未找到该学生的数据，请确认学生信息是否正确。"
        lines = []
        student_name = data.get("student_name", "")
        lines.append(f"📎 **{student_name} 学情分析**\n")
        lines.append(f"**基本信息**")
        lines.append(f'- 班级：{data.get("class_name", "-")} / {data.get("grade_name", "-")}')
        lines.append(f'- 考试次数：{data.get("exam_count", 0)}')
        lines.append(f'- 总体趋势：{data.get("overall_trend", "-")}')
        lines.append("")
        strengths = data.get("strengths", [])
        weaknesses = data.get("weaknesses", [])
        if strengths:
            lines.append("**💪 优势科目**")
            for s in strengths:
                lines.append(f'- {s["subject_name"]}：平均得分率{s["avg_rate"]}%，最新{s["latest_rate"]}%')
            lines.append("")
        if weaknesses:
            lines.append("**⚠️ 薄弱科目**")
            for s in weaknesses:
                lines.append(f'- {s["subject_name"]}：平均得分率{s["avg_rate"]}%，最新{s["latest_rate"]}%')
            lines.append("")
        advice = data.get("advice")
        if advice:
            items = advice.get("advice_items", [])
            if items:
                lines.append("**💡 学习建议**")
                for item in items[:5]:
                    emoji = "🔴" if item.get("priority") == "high" else "🟡" if item.get("priority") == "medium" else "🟢"
                    lines.append(f'{emoji} **{item.get("category", "")}**：{item.get("content", "")}')
        return "\n".join(lines)

    def _exam_analysis(self, data: Dict, message: str) -> str:
        if not data:
            return "⚠️ 未找到该考试的数据，请确认考试信息是否正确。"
        lines = []
        exam_name = data.get("exam_name", "")
        lines.append(f"📊 **{exam_name} 深度分析**\n")
        lines.append(f"**考试概况**")
        lines.append(f'- 考试日期：{data.get("exam_date", "-")}')
        lines.append(f'- 参考人数：{data.get("total_students", 0)}')
        lines.append(f'- {len(data.get("grade_stats", []))} 个科目，{len(data.get("class_stats", []))} 个班级')
        lines.append("")
        grade_stats = data.get("grade_stats", [])
        if grade_stats:
            lines.append("**各科表现**")
            for gs in grade_stats:
                name = gs.get("subject_name", "")
                avg = gs.get("avg_score", 0)
                rate = gs.get("avg_score_rate", 0)
                passed = gs.get("pass_rate", 0)
                excellent = gs.get("excellent_rate", 0)
                max_s = gs.get("max_score", 0)
                min_s = gs.get("min_score", 0)
                if rate >= 75:
                    emoji = "🟢"
                elif rate >= 60:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                lines.append(f'{emoji} **{name}**：均分{avg}（得分率 {rate}%），及格 {passed}% / 优秀 {excellent}%，最高{max_s} / 最低{min_s}')
            lines.append("")
        class_stats = data.get("class_stats", [])
        if class_stats and len(class_stats) > 1:
            lines.append("**班级对比**")
            for cs in class_stats:
                stats = cs.get("stats", [])
                if stats:
                    avg_rates = [s.get("avg_score_rate", 0) for s in stats]
                    class_avg = sum(avg_rates) / len(avg_rates) if avg_rates else 0
                    lines.append(f'- {cs.get("class_name", "")}：综合得分率 {class_avg:.1f}%')
            lines.append("")
        if grade_stats:
            best = max(grade_stats, key=lambda x: x.get("avg_score_rate", 0))
            worst = min(grade_stats, key=lambda x: x.get("avg_score_rate", 0))
            lines.append("**📕 关键发现**")
            lines.append(f'1. 优势科目：**{best.get("subject_name", "")}**（得分率 {best.get("avg_score_rate", "")}%）')
            lines.append(f'2. 待提升科目：**{worst.get("subject_name", "")}**（得分率 {worst.get("avg_score_rate", "")}%）')
            if worst.get("pass_rate", 100) < 60:
                lines.append(f'3. ⚠️ {worst.get("subject_name", "")} 及格率仅 {worst.get("pass_rate", "")}%，需要重点关注')
            if class_stats and len(class_stats) > 1:
                cs_sorted = sorted(class_stats, key=lambda c: sum(s.get("avg_score_rate", 0) for s in c.get("stats", [])) / max(len(c.get("stats", [])), 1), reverse=True)
                lines.append(f'4. 最佳班级：**{cs_sorted[0].get("class_name", "")}**')
                lines.append(f'5. 需关注班级：**{cs_sorted[-1].get("class_name", "")}**')
        return "\n".join(lines)

    def _general_chat(self, data: Dict, message: str) -> str:
        return ("你好！我是AI分析助手。我可以帮你：\n\n"
                "📊 **考试分析** - 选择一场考试，我可以帮你深入解读成绩数据\n"
                "📈 **学情跟踪** - 选择一名学生，我可以给出个性化学习建议\n"
                "📫 **报告优化** - 在考试分析页，我可以帮你优化PPT内容和版式\n\n"
                "请先在左侧选择一个分析场景（考试分析/学情跟踪），然后告诉我你的需求！")
