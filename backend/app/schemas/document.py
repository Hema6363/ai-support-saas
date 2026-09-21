from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_type: str
    file_size: int


class DocumentCreate(DocumentBase):
    file_path: str


class DocumentOut(DocumentBase):
    id: int
    tenant_id: int
    owner_id: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentReindexResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    chunk_count: int
    message: str
