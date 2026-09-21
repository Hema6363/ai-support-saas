from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketOut, TicketEscalateRequest
from app.crud import ticket as crud_ticket
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg
from app.services.integrations_service import integrations_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=List[TicketOut])
def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_ticket.list_tickets(
        db,
        tenant_id=current_user.tenant_id,
        status=status,
        priority=priority,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = crud_ticket.create_ticket(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        priority=body.priority or "medium",
        conversation_id=body.conversation_id,
    )

    # Trigger notification integration
    await integrations_service.notify_ticket_escalated(
        ticket_id=ticket.id,
        tenant_id=current_user.tenant_id,
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
    )

    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = crud_ticket.get_ticket(db, ticket_id=ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    body: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = crud_ticket.get_ticket(db, ticket_id=ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    updated = crud_ticket.update_ticket(
        db=db,
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        is_resolved=body.is_resolved,
    )
    return updated


@router.post("/escalate-from-conversation", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def escalate_conversation(
    req: TicketEscalateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = crud_conv.get_conversation(
        db, conversation_id=req.conversation_id, tenant_id=current_user.tenant_id
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get conversation transcript summary
    messages = crud_msg.list_messages(
        db, conversation_id=conv.id, tenant_id=current_user.tenant_id, limit=20
    )
    transcript_snippets = []
    for m in messages:
        sender_label = "User" if m.role == "user" else "AI Assistant"
        transcript_snippets.append(f"{sender_label}: {m.content}")

    transcript_text = "\n".join(transcript_snippets)
    title = req.title or f"Escalated Support: {conv.title}"
    description = f"Auto-escalated from AI Conversation #{conv.id} ('{conv.title}').\n\nTranscript History:\n{transcript_text}"

    ticket = crud_ticket.create_ticket(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        title=title,
        description=description,
        priority=req.priority or "high",
        status="open",
        conversation_id=conv.id,
    )

    await integrations_service.notify_ticket_escalated(
        ticket_id=ticket.id,
        tenant_id=current_user.tenant_id,
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
    )

    return ticket
