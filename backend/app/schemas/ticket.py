from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class TicketBase(BaseModel):
    title: str
    description: str
    priority: Optional[str] = "medium"


class TicketCreate(TicketBase):
    conversation_id: Optional[int] = None


class TicketEscalateRequest(BaseModel):
    conversation_id: int
    title: Optional[str] = None
    priority: Optional[str] = "high"


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    is_resolved: Optional[bool] = None


class TicketOut(TicketBase):
    id: int
    tenant_id: int
    user_id: int
    conversation_id: Optional[int] = None
    status: str
    is_resolved: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
