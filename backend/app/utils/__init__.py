import uuid
from fastapi import HTTPException, status


def parse_uuid(value: str, name: str = "ID") -> uuid.UUID:
    """Validate and convert a string to UUID, raising a 400 error on failure."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的{name}格式",
        )
