from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils import parse_uuid
from app.core.database import get_db
from app.models.scoring import ScoringScheme
from app.schemas.scoring import (
    ScoringSchemeCreate,
    ScoringSchemeUpdate,
    ScoringSchemeResponse,
)

router = APIRouter(prefix="/scoring-schemes", tags=["赋分方案"])


def _get_scheme(db: Session, scheme_id: str) -> ScoringScheme:
    scheme = db.query(ScoringScheme).filter(ScoringScheme.id == parse_uuid(scheme_id)).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="赋分方案不存在")
    return scheme


@router.get("/", response_model=List[ScoringSchemeResponse])
def list_schemes(preset_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(ScoringScheme)
    if preset_only:
        q = q.filter(ScoringScheme.is_preset == True)  # noqa: E712
    return q.order_by(ScoringScheme.sort_order, ScoringScheme.name).all()


@router.get("/presets", response_model=List[ScoringSchemeResponse])
def list_presets(db: Session = Depends(get_db)):
    return (
        db.query(ScoringScheme)
        .filter(ScoringScheme.is_preset == True)  # noqa: E712
        .order_by(ScoringScheme.sort_order, ScoringScheme.name)
        .all()
    )


@router.post("/", response_model=ScoringSchemeResponse)
def create_scheme(data: ScoringSchemeCreate, db: Session = Depends(get_db)):
    scheme = ScoringScheme(
        name=data.name,
        description=data.description,
        brackets=[b.model_dump() for b in data.brackets],
        is_preset=False,
        sort_order=data.sort_order,
    )
    db.add(scheme)
    db.commit()
    db.refresh(scheme)
    return scheme


@router.put("/{scheme_id}", response_model=ScoringSchemeResponse)
def update_scheme(scheme_id: str, data: ScoringSchemeUpdate, db: Session = Depends(get_db)):
    scheme = _get_scheme(db, scheme_id)
    if data.name is not None:
        scheme.name = data.name
    if data.description is not None:
        scheme.description = data.description
    if data.brackets is not None:
        scheme.brackets = [b.model_dump() for b in data.brackets]
    if data.sort_order is not None:
        scheme.sort_order = data.sort_order
    db.commit()
    db.refresh(scheme)
    return scheme


@router.delete("/{scheme_id}")
def delete_scheme(scheme_id: str, db: Session = Depends(get_db)):
    scheme = _get_scheme(db, scheme_id)
    if scheme.is_preset:
        raise HTTPException(status_code=400, detail="内置方案不可删除")
    db.delete(scheme)
    db.commit()
    return {"message": "已删除"}
