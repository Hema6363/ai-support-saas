from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.message import Message
from app.models.conversation import Conversation


def list_messages(
    db: Session, conversation_id: int, tenant_id: int, limit: int = 100
) -> List[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.tenant_id == tenant_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .all()
    )


def create_message(
    db: Session,
    tenant_id: int,
    conversation_id: int,
    role: str,
    content: str,
    sender_id: Optional[int] = None,
    citations: Optional[str] = None,
    latency_ms: Optional[int] = None,
) -> Message:
    now = datetime.now(timezone.utc)
    msg = Message(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        sender_id=sender_id,
        citations=citations,
        latency_ms=latency_ms,
        created_at=now,
    )
    db.add(msg)

    # Touch parent conversation's updated_at so it sorts to top
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.tenant_id == tenant_id)
        .first()
    )
    if conv:
        conv.updated_at = now
        db.add(conv)

    db.commit()
    db.refresh(msg)
    return msg
