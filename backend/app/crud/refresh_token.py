from sqlalchemy.orm import Session
from backend.app.models.refresh_token import RefreshToken
from datetime import datetime


def create_refresh_token(db: Session, jti: str, user_id: int, expires_at: datetime):
    rt = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def revoke_refresh_token(db: Session, jti: str):
    rt = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if rt:
        rt.revoked = True
        db.add(rt)
        db.commit()
        db.refresh(rt)
    return rt


def get_refresh_token(db: Session, jti: str):
    return db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
