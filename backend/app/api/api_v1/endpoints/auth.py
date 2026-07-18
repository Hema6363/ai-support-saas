from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict

from backend.app.schemas.user import UserCreate, UserOut, Token
from backend.app.db.session import SessionLocal
from backend.app.crud import user as crud_user
from backend.app.crud import refresh_token as crud_rt
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.app.api.deps import get_current_user, get_db

router = APIRouter()


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = crud_user.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user_in.password)
    user = crud_user.create_user(db, email=user_in.email, hashed_password=hashed)
    return user


@router.post("/auth/login", response_model=Token)
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, user_in.email)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token, access_exp = create_access_token(user.id)
    refresh_token, refresh_exp, jti = create_refresh_token(user.id)

    # store refresh token
    crud_rt.create_refresh_token(db, jti=jti, user_id=user.id, expires_at=datetime.fromtimestamp(refresh_exp))

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/auth/refresh", response_model=Token)
def refresh(body: Dict[str, str], db: Session = Depends(get_db)):
    # body should be {"refresh_token": "..."}
    rtoken = body.get("refresh_token") if isinstance(body, dict) else None
    if not rtoken:
        raise HTTPException(status_code=400, detail="refresh_token required")
    payload = decode_token(rtoken)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    jti = payload.get("jti")
    stored = crud_rt.get_refresh_token(db, jti=jti)
    if not stored or stored.revoked:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    # rotate
    crud_rt.revoke_refresh_token(db, jti=jti)
    user_id = payload.get("sub")
    access_token, access_exp = create_access_token(user_id)
    refresh_token, refresh_exp, new_jti = create_refresh_token(user_id)
    crud_rt.create_refresh_token(db, jti=new_jti, user_id=user_id, expires_at=datetime.fromtimestamp(refresh_exp))

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/auth/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
