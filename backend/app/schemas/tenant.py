from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class TenantBase(BaseModel):
    name: str
    plan: Optional[str] = "starter"


class TenantCreate(TenantBase):
    slug: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None


class TenantOut(TenantBase):
    id: int
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
