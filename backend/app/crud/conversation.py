from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.conversation import Conversation


def get_conversation(
    db: Session, conversation_id: int, tenant_id: int
) -> Optional[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.tenant_id == tenant_id)
        .first()
    )


def list_conversations(
    db: Session, tenant_id: int, user_id: Optional[int] = None, skip: int = 0, limit: int = 50
) -> List[Conversation]:
    query = db.query(Conversation).filter(Conversation.tenant_id == tenant_id)
    if user_id:
        query = query.filter(Conversation.user_id == user_id)
    return query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()


def create_conversation(
    db: Session,
    tenant_id: int,
    user_id: int,
    title: str = "New Conversation",
    document_id: Optional[int] = None,
) -> Conversation:
    now = datetime.now(timezone.utc)
    conv = Conversation(
        tenant_id=tenant_id,
        user_id=user_id,
        title=title,
        document_id=document_id,
        created_at=now,
        updated_at=now,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def update_conversation_title(
    db: Session, conversation_id: int, tenant_id: int, title: str
) -> Optional[Conversation]:
    conv = get_conversation(db, conversation_id, tenant_id)
    if conv:
        conv.title = title
        conv.updated_at = datetime.now(timezone.utc)
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def delete_conversation(db: Session, conversation_id: int, tenant_id: int) -> bool:
    conv = get_conversation(db, conversation_id, tenant_id)
    if conv:
        db.delete(conv)
        db.commit()
        return True
    return False
