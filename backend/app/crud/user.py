from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    hashed_password: str,
    tenant_id: int,
    full_name: Optional[str] = None,
    role: str = "admin",
) -> User:
    try:
        user = User(
            email=email,
            hashed_password=hashed_password,
            tenant_id=tenant_id,
            full_name=full_name,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise