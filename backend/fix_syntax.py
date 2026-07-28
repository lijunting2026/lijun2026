with open('app/api/v1/analysis.py', 'r', encoding="utf-8") as f:
    c = f.read()
c = c.replace('\nreturn {\n        "stats"', '\n    return {\n        "stats"')
old = '    return {\n        "stats": {\n            "grades": grade_count, "classes": class_count, "subjects": subject_count,\n            "students": student_count, "exams": exam_count, "scores": score_count,\n        },\n        "recent_exams": exams_data,\n        "subject_stats": subject_stats,\n    }'
new = '    return {\n        "stats": {\n            "grades": grade_count, "classes": class_count, "subjects": subject_count,\n            "students": student_count, "exams": exam_count, "scores": score_count,\n        },\n        "recent_exams": exams_data,\n        "subject_stats": subject_stats,\n        "trend": {"direction": trend_direction, "description": trend_desc},\n        "risk_students": risk_students,\n        "subject_alerts": subject_alerts,\n        "class_ranking": class_ranking,\n        "exam_type_stats": exam_type_stats,\n    }'
count = c.count(old)
c = c.replace(old, new)
with open('app/api/v1/analysis.py', 'w', encoding="utf-8") as f:
    f.write(c)
import py_compile
py_compile.compile('app/api/v1/analysis.py', doraise=True)
print(f"OK, replaced {count}")