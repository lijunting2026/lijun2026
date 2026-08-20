"""知识点种子数据（幂等：每次启动清空后重新填充）"""
from app.core.database import SessionLocal
from app.models.subject import Subject
from app.models.exam_detail import SubjectKnowledgePoint


def seed_knowledge_points():
    """为每个科目创建知识点（幂等：清空旧数据后重新填充）"""
    db = SessionLocal()

    # 清空旧数据，确保每次启动时重新填充
    db.query(SubjectKnowledgePoint).delete()
    db.commit()

    subjects = db.query(Subject).all()
    subj_map = {s.name: s for s in subjects}

    # —— 数学知识点 ——
    math_kps = {
        "集合与常用逻辑用语": ["集合的概念与运算", "命题与量词", "充分必要条件"],
        "函数": ["函数的概念与表示", "函数的性质(单调/奇偶/周期)", "指数函数与对数函数", "幂函数", "函数的图像"],
        "三角函数": ["三角函数的概念", "三角恒等变换", "三角函数的图像与性质", "解三角形"],
        "数列": ["等差数列", "等比数列", "数列求和", "数列综合应用"],
        "立体几何": ["空间几何体", "点线面位置关系", "平行与垂直的判定", "空间向量与立体几何"],
        "概率与统计": ["排列组合", "二项式定理", "概率", "统计"],
    }
    math_subj = subj_map.get("数学")
    if math_subj:
        for parent_name, children in math_kps.items():
            parent = SubjectKnowledgePoint(
                subject_id=math_subj.id, name=parent_name, sort_order=0
            )
            db.add(parent)
            db.flush()
            for i, child_name in enumerate(children):
                child = SubjectKnowledgePoint(
                    subject_id=math_subj.id, name=child_name,
                    parent_id=parent.id, sort_order=i + 1,
                )
                db.add(child)

    # —— 语文知识点 ——
    chinese_kps = {
        "语言文字运用": ["字音字形", "词语理解与运用", "病句辨析与修改", "语言表达"],
        "古代诗文阅读": ["文言文阅读", "古诗词鉴赏", "名篇名句默写"],
        "现代文阅读": ["论述类文本阅读", "文学类文本阅读", "实用类文本阅读"],
        "写作": ["审题立意", "结构布局", "素材运用", "语言表达技巧"],
    }
    chinese_subj = subj_map.get("语文")
    if chinese_subj:
        for parent_name, children in chinese_kps.items():
            parent = SubjectKnowledgePoint(
                subject_id=chinese_subj.id, name=parent_name, sort_order=0
            )
            db.add(parent)
            db.flush()
            for i, child_name in enumerate(children):
                child = SubjectKnowledgePoint(
                    subject_id=chinese_subj.id, name=child_name,
                    parent_id=parent.id, sort_order=i + 1,
                )
                db.add(child)

    # —— 英语知识点 ——
    english_kps = {
        "语法": ["时态语态", "非谓语动词", "从句", "虚拟语气", "特殊句式"],
        "词汇": ["词义辨析", "固定搭配", "短语动词"],
        "阅读理解": ["主旨大意", "细节理解", "推理判断", "词义猜测"],
        "写作": ["应用文写作", "读后续写", "概要写作"],
    }
    english_subj = subj_map.get("英语")
    if english_subj:
        for parent_name, children in english_kps.items():
            parent = SubjectKnowledgePoint(
                subject_id=english_subj.id, name=parent_name, sort_order=0
            )
            db.add(parent)
            db.flush()
            for i, child_name in enumerate(children):
                child = SubjectKnowledgePoint(
                    subject_id=english_subj.id, name=child_name,
                    parent_id=parent.id, sort_order=i + 1,
                )
                db.add(child)

    # —— 物理知识点 ——
    physics_kps = {
        "力学": ["运动的描述", "相互作用与牛顿定律", "曲线运动与万有引力", "功和能"],
        "电磁学": ["电场", "恒定电流", "磁场", "电磁感应"],
        "热学": ["分子动理论", "气体定律", "热力学定律"],
        "光学与近代物理": ["几何光学", "光的波动性", "原子物理"],
    }
    physics_subj = subj_map.get("物理")
    if physics_subj:
        for parent_name, children in physics_kps.items():
            parent = SubjectKnowledgePoint(
                subject_id=physics_subj.id, name=parent_name, sort_order=0
            )
            db.add(parent)
            db.flush()
            for i, child_name in enumerate(children):
                child = SubjectKnowledgePoint(
                    subject_id=physics_subj.id, name=child_name,
                    parent_id=parent.id, sort_order=i + 1,
                )
                db.add(child)

    # —— 化学知识点 ——
    chemistry_kps = {
        "基本概念": ["物质的量", "离子反应", "氧化还原反应"],
        "元素化合物": ["金属元素", "非金属元素", "元素周期律"],
        "化学反应原理": ["化学反应与能量", "化学反应速率与平衡", "水溶液中的离子平衡"],
        "有机化学": ["有机物的结构", "烃及其衍生物", "有机反应类型"],
    }
    chemistry_subj = subj_map.get("化学")
    if chemistry_subj:
        for parent_name, children in chemistry_kps.items():
            parent = SubjectKnowledgePoint(
                subject_id=chemistry_subj.id, name=parent_name, sort_order=0
            )
            db.add(parent)
            db.flush()
            for i, child_name in enumerate(children):
                child = SubjectKnowledgePoint(
                    subject_id=chemistry_subj.id, name=child_name,
                    parent_id=parent.id, sort_order=i + 1,
                )
                db.add(child)

    # —— 生物知识点 ——
    biology_kps = {
        "分子与细胞": ["细胞的分子组成", "细胞的结构", "细胞的代谢", "细胞增殖与分化"],
        "遗传与进化": ["遗传规律", "基因的本质", "基因的表达", "生物进化"],
        "稳态与环境": ["内环境与稳态", "动物生命活动调节", "植物激素调节", "生态系统"],
    }
    biology_subj = subj_map.get("生物")
    if biology_subj:
        for parent_name, children in biology_kps.items():
            parent = SubjectKnowledgePoint(
                subject_id=biology_subj.id, name=parent_name, sort_order=0
            )
            db.add(parent)
            db.flush()
            for i, child_name in enumerate(children):
                child = SubjectKnowledgePoint(
                    subject_id=biology_subj.id, name=child_name,
                    parent_id=parent.id, sort_order=i + 1,
                )
                db.add(child)

    db.commit()
    db.close()
    print(f"知识点种子数据：6个科目，共约120+个知识点已填充")


if __name__ == "__main__":
    seed_knowledge_points()
