from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, Any

from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.db.session import SessionLocal
from app.crud import user as crud_user
from app.crud import tenant as crud_tenant
from app.crud import refresh_token as crud_rt
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.api.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = crud_user.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Resolve or create tenant
    company_name = user_in.company_name or user_in.email.split("@")[0].capitalize() + " Support"
    tenant = crud_tenant.create_tenant(db, name=company_name)

    hashed = get_password_hash(user_in.password)
    user = crud_user.create_user(
        db,
        email=user_in.email,
        hashed_password=hashed,
        tenant_id=tenant.id,
        full_name=user_in.full_name,
        role="admin",
    )
    return user


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, user_in.email)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token, access_exp = create_access_token(user.id, user.tenant_id)
    refresh_token, refresh_exp, jti = create_refresh_token(user.id, user.tenant_id)

    crud_rt.create_refresh_token(
        db,
        jti=jti,
        user_id=user.id,
        expires_at=datetime.fromtimestamp(refresh_exp, tz=timezone.utc),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/refresh", response_model=Token)
def refresh(body: Dict[str, str], db: Session = Depends(get_db)):
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

    crud_rt.revoke_refresh_token(db, jti=jti)
    user_id = int(payload.get("sub"))
    user = crud_user.get_user(db, user_id=user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User unavailable")

    access_token, access_exp = create_access_token(user.id, user.tenant_id)
    refresh_token, refresh_exp, new_jti = create_refresh_token(user.id, user.tenant_id)

    crud_rt.create_refresh_token(
        db,
        jti=new_jti,
        user_id=user.id,
        expires_at=datetime.fromtimestamp(refresh_exp, tz=timezone.utc),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(body: Dict[str, str], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rtoken = body.get("refresh_token")
    if rtoken:
        payload = decode_token(rtoken)
        if payload and payload.get("jti"):
            crud_rt.revoke_refresh_token(db, jti=payload.get("jti"))
    return {"status": "success", "message": "Logged out successfully"}
