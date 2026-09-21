from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.message import MessageOut


class ConversationBase(BaseModel):
    title: str = "New Conversation"
    document_id: Optional[int] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = None


class ConversationOut(ConversationBase):
    id: int
    tenant_id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationOut):
    messages: List[MessageOut] = []
