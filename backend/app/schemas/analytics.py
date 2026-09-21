from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ActivityPoint(BaseModel):
    date: str
    conversations: int
    messages: int
    tickets: int


class TicketStatusBreakdown(BaseModel):
    open: int
    in_progress: int
    resolved: int
    closed: int


class DocumentStat(BaseModel):
    id: int
    filename: str
    chunk_count: int
    file_size: int
    created_at: str


class AnalyticsDashboardOut(BaseModel):
    total_conversations: int
    total_messages: int
    total_tickets: int
    resolved_tickets: int
    resolution_rate_pct: float
    avg_messages_per_conversation: float
    avg_ai_latency_ms: int
    total_documents: int
    total_document_chunks: int
    ticket_status_breakdown: TicketStatusBreakdown
    activity_trend: List[ActivityPoint]
    top_documents: List[DocumentStat]
