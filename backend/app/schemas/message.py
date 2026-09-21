from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class CitationOut(BaseModel):
    document_id: Optional[int] = None
    filename: str
    chunk_index: int
    snippet: str
    distance: float


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    conversation_id: int
    sender_id: Optional[int] = None
    citations: Optional[str] = None
    latency_ms: Optional[int] = None


class MessageOut(MessageBase):
    id: int
    conversation_id: int
    tenant_id: int
    sender_id: Optional[int] = None
    citations: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str
    document_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    conversation_id: int
    user_message: MessageOut
    assistant_message: MessageOut
    citations: List[CitationOut] = []
    suggest_escalation: bool = False
    latency_ms: int = 0
