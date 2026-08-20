import re
from typing import Dict

def validate_password_strength(password: str) -> Dict:
    """
    Validate password strength.
    Returns: { valid: bool, message: str, strength: str }
    """
    checks = {
        "length": len(password) >= 8,
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "lowercase": bool(re.search(r"[a-z]", password)),
        "digit": bool(re.search(r"[0-9]", password)),
        "special": bool(re.search(r"[^a-zA-Z0-9\s]", password)),
    }

    failed = [k for k, v in checks.items() if not v]

    if len(failed) >= 3:
        strength = "weak"
    elif len(failed) >= 1:
        strength = "medium"
    else:
        strength = "strong"

    if not checks["length"]:
        return {"valid": False, "message": "密码至少8位", "strength": strength}

    hints = []
    if not checks["uppercase"]:
        hints.append("包含大写字母")
    if not checks["lowercase"]:
        hints.append("包含小写字母")
    if not checks["digit"]:
        hints.append("包含数字")
    if not checks["special"]:
        hints.append("包含特殊字符")

    if hints:
        return {
            "valid": False,
            "message": "密码需要" + "、".join(hints),
            "strength": strength,
        }

    return {"valid": True, "message": "密码强度合格", "strength": strength}


def get_password_strength_text(strength: str) -> str:
    mapping = {"weak": "弱", "medium": "中", "strong": "强"}
    return mapping.get(strength, "未知")


def get_password_strength_color(strength: str) -> str:
    mapping = {"weak": "#F56C6C", "medium": "#E6A23C", "strong": "#67C23A"}
    return mapping.get(strength, "#909399")
