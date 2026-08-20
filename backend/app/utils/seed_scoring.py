"""赋分方案种子数据（内置预设，幂等：仅空库时填充）"""
from app.core.database import SessionLocal
from app.models.scoring import ScoringScheme


def seed_scoring_schemes():
    """内置赋分方案：库为空时填充，不覆盖用户自定义方案"""
    db = SessionLocal()
    try:
        if db.query(ScoringScheme).count() > 0:
            print("赋分方案库已有数据，跳过预设填充")
            return

        presets = [
            {
                "name": "新高考3分一段（15/35/35/13/2）",
                "description": "湖南/湖北/广东/福建/江苏等新高考省份常用规则：A 15%→100-86，B 35%→85-71，C 35%→70-56，D 13%→55-41，E 2%→40-30",
                "brackets": [
                    {"rank_start": 0.0, "rank_end": 0.15, "score_start": 100, "score_end": 86},
                    {"rank_start": 0.15, "rank_end": 0.50, "score_start": 85, "score_end": 71},
                    {"rank_start": 0.50, "rank_end": 0.85, "score_start": 70, "score_end": 56},
                    {"rank_start": 0.85, "rank_end": 0.98, "score_start": 55, "score_end": 41},
                    {"rank_start": 0.98, "rank_end": 1.0, "score_start": 40, "score_end": 30},
                ],
                "is_preset": True,
                "sort_order": 1,
            },
            {
                "name": "浙江1分一段（21级，每级3分）",
                "description": "浙江省等级赋分：21个等级、赋分100~40每级差3分，等级内同分同赋分。各级人数比例按均分预设，实际比例请以浙江省官方文件为准并可在方案中调整",
                "brackets": [
                    {"rank_start": i / 21, "rank_end": (i + 1) / 21, "score_start": 100 - 3 * i, "score_end": 100 - 3 * i}
                    for i in range(21)
                ],
                "is_preset": True,
                "sort_order": 2,
            },
            {
                "name": "山东5等8级（3/7/16/24/24/16/7/3）",
                "description": "山东省等级赋分：8个等级、赋分21~100（A 3%→91-100，B+ 7%→81-90，B 16%→71-80，C+ 24%→61-70，C 24%→51-60，D+ 16%→41-50，D 7%→31-40，E 3%→21-30），实施时以官方文件核对",
                "brackets": [
                    {"rank_start": 0.0, "rank_end": 0.03, "score_start": 100, "score_end": 91},
                    {"rank_start": 0.03, "rank_end": 0.10, "score_start": 90, "score_end": 81},
                    {"rank_start": 0.10, "rank_end": 0.26, "score_start": 80, "score_end": 71},
                    {"rank_start": 0.26, "rank_end": 0.50, "score_start": 70, "score_end": 61},
                    {"rank_start": 0.50, "rank_end": 0.74, "score_start": 60, "score_end": 51},
                    {"rank_start": 0.74, "rank_end": 0.90, "score_start": 50, "score_end": 41},
                    {"rank_start": 0.90, "rank_end": 0.97, "score_start": 40, "score_end": 31},
                    {"rank_start": 0.97, "rank_end": 1.0, "score_start": 30, "score_end": 21},
                ],
                "is_preset": True,
                "sort_order": 3,
            },
        ]

        for item in presets:
            db.add(ScoringScheme(**item))
        db.commit()
        print(f"赋分方案预设已填充：{len(presets)} 套")
    finally:
        db.close()


if __name__ == "__main__":
    seed_scoring_schemes()
