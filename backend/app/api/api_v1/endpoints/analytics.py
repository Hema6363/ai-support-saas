from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.ticket import Ticket
from app.models.document import Document
from app.schemas.analytics import (
    AnalyticsDashboardOut,
    TicketStatusBreakdown,
    ActivityPoint,
    DocumentStat,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboardOut)
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = current_user.tenant_id

    # 1. Total counts
    total_convs = db.query(func.count(Conversation.id)).filter(Conversation.tenant_id == tid).scalar() or 0
    total_msgs = db.query(func.count(Message.id)).filter(Message.tenant_id == tid).scalar() or 0
    total_tickets = db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tid).scalar() or 0
    resolved_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.tenant_id == tid, Ticket.status.in_(["resolved", "closed"]))
        .scalar()
        or 0
    )

    resolution_rate = round((resolved_tickets / total_tickets * 100), 1) if total_tickets > 0 else 100.0
    avg_msgs = round(total_msgs / total_convs, 1) if total_convs > 0 else 0.0

    # 2. AI Latency
    avg_latency = (
        db.query(func.avg(Message.latency_ms))
        .filter(Message.tenant_id == tid, Message.role == "assistant", Message.latency_ms.isnot(None))
        .scalar()
    )
    avg_ai_latency_ms = int(avg_latency) if avg_latency else 450

    # 3. Documents
    docs = db.query(Document).filter(Document.tenant_id == tid).all()
    total_docs = len(docs)
    total_chunks = sum(d.chunk_count for d in docs)

    # 4. Ticket status breakdown
    open_count = db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tid, Ticket.status == "open").scalar() or 0
    in_prog_count = db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tid, Ticket.status == "in_progress").scalar() or 0
    res_count = db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tid, Ticket.status == "resolved").scalar() or 0
    closed_count = db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tid, Ticket.status == "closed").scalar() or 0

    breakdown = TicketStatusBreakdown(
        open=open_count,
        in_progress=in_prog_count,
        resolved=res_count,
        closed=closed_count,
    )

    # 5. Activity trend (last 7 days)
    activity_trend: List[ActivityPoint] = []
    now = datetime.now(timezone.utc)
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        date_str = day_start.strftime("%b %d")

        c_count = (
            db.query(func.count(Conversation.id))
            .filter(Conversation.tenant_id == tid, Conversation.created_at >= day_start, Conversation.created_at < day_end)
            .scalar()
            or 0
        )
        m_count = (
            db.query(func.count(Message.id))
            .filter(Message.tenant_id == tid, Message.created_at >= day_start, Message.created_at < day_end)
            .scalar()
            or 0
        )
        t_count = (
            db.query(func.count(Ticket.id))
            .filter(Ticket.tenant_id == tid, Ticket.created_at >= day_start, Ticket.created_at < day_end)
            .scalar()
            or 0
        )

        activity_trend.append(ActivityPoint(
            date=date_str,
            conversations=c_count,
            messages=m_count,
            tickets=t_count,
        ))

    # 6. Top documents
    top_docs = [
        DocumentStat(
            id=d.id,
            filename=d.original_filename,
            chunk_count=d.chunk_count,
            file_size=d.file_size,
            created_at=d.created_at.strftime("%Y-%m-%d %H:%M") if d.created_at else "",
        )
        for d in docs[:10]
    ]

    return AnalyticsDashboardOut(
        total_conversations=total_convs,
        total_messages=total_msgs,
        total_tickets=total_tickets,
        resolved_tickets=resolved_tickets,
        resolution_rate_pct=resolution_rate,
        avg_messages_per_conversation=avg_msgs,
        avg_ai_latency_ms=avg_ai_latency_ms,
        total_documents=total_docs,
        total_document_chunks=total_chunks,
        ticket_status_breakdown=breakdown,
        activity_trend=activity_trend,
        top_documents=top_docs,
    )
