from fastapi import APIRouter, Depends, HTTPException, status, Request
from collections import defaultdict
import time

_LOGIN_ATTEMPTS = defaultdict(list)
_LOGIN_LIMIT = 5
_LOGIN_WINDOW = 300

def _check_login_rate(ip: str):
    now = time.time()
    _LOGIN_ATTEMPTS[ip] = [t for t in _LOGIN_ATTEMPTS[ip] if now - t < _LOGIN_WINDOW]
    if len(_LOGIN_ATTEMPTS[ip]) >= _LOGIN_LIMIT:
        retry_after = int(_LOGIN_WINDOW - (now - _LOGIN_ATTEMPTS[ip][0]))
        raise HTTPException(status_code=429, detail=f"Too many login attempts, retry in {retry_after}s")
    _LOGIN_ATTEMPTS[ip].append(now)
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.deps import get_current_user
import uuid
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdate, PasswordChangeRequest

router = APIRouter(prefix="/auth", tags=["认证管理"])

@router.post("/login", response_model=TokenResponse)
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    _check_login_rate(client_ip)
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, user=UserResponse(
        id=str(user.id), username=user.username, display_name=user.display_name,
        role=user.role, is_active=user.is_active, needs_password_change=user.needs_password_change
    ))

@router.post("/change-password")
def change_password(
    data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="新密码至少8位")
    current_user.password_hash = get_password_hash(data.new_password)
    current_user.needs_password_change = False
    db.commit()
    return {"message": "密码修改成功"}

@router.post("/register", response_model=UserResponse)
def register(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可注册新用户")
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        display_name=data.display_name,
        role=data.role or "editor",
        needs_password_change=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=str(user.id), username=user.username, display_name=user.display_name,
        role=user.role, is_active=user.is_active, needs_password_change=user.needs_password_change
    )

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可查看用户列表")
    users = db.query(User).all()
    return [UserResponse(
        id=str(u.id), username=u.username, display_name=u.display_name,
        role=u.role, is_active=u.is_active, needs_password_change=u.needs_password_change, created_at=u.created_at
    ) for u in users]

@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可修改用户")
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.username:
        existing = db.query(User).filter(
            User.username == data.username, User.id != uuid.UUID(user_id)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = data.username
    if data.display_name:
        user.display_name = data.display_name
    if data.password:
        user.password_hash = get_password_hash(data.password)
        user.needs_password_change = False
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=str(user.id), username=user.username, display_name=user.display_name,
        role=user.role, is_active=user.is_active, needs_password_change=user.needs_password_change, created_at=user.created_at
    )

@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可删除用户")
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "已删除"}