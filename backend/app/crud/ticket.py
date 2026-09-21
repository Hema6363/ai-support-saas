from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.ticket import Ticket


def get_ticket(db: Session, ticket_id: int, tenant_id: int) -> Optional[Ticket]:
    return (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.tenant_id == tenant_id)
        .first()
    )


def list_tickets(
    db: Session,
    tenant_id: int,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Ticket]:
    query = db.query(Ticket).filter(Ticket.tenant_id == tenant_id)
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    return query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()


def create_ticket(
    db: Session,
    tenant_id: int,
    user_id: int,
    title: str,
    description: str,
    priority: str = "medium",
    status: str = "open",
    conversation_id: Optional[int] = None,
) -> Ticket:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        tenant_id=tenant_id,
        user_id=user_id,
        title=title,
        description=description,
        priority=priority,
        status=status,
        conversation_id=conversation_id,
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(
    db: Session,
    ticket_id: int,
    tenant_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    is_resolved: Optional[bool] = None,
) -> Optional[Ticket]:
    ticket = get_ticket(db, ticket_id, tenant_id)
    if ticket:
        if title is not None:
            ticket.title = title
        if description is not None:
            ticket.description = description
        if status is not None:
            ticket.status = status
            if status in ["resolved", "closed"]:
                ticket.is_resolved = True
            elif status in ["open", "in_progress"]:
                ticket.is_resolved = False
        if priority is not None:
            ticket.priority = priority
        if is_resolved is not None:
            ticket.is_resolved = is_resolved
            if is_resolved and ticket.status not in ["resolved", "closed"]:
                ticket.status = "resolved"

        ticket.updated_at = datetime.now(timezone.utc)
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    return ticket
