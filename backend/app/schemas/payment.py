from pydantic import BaseModel
from typing import List, Optional


class PlanFeature(BaseModel):
    name: str
    included: bool


class SubscriptionPlanOut(BaseModel):
    id: str
    name: str
    price_monthly: int
    currency: str
    max_documents: int
    max_queries_per_month: int
    features: List[str]


class CheckoutSessionRequest(BaseModel):
    plan_id: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
    mode: str


class SubscriptionStatusOut(BaseModel):
    tenant_id: int
    plan: str
    status: str
    documents_used: int
    documents_limit: int
    queries_used: int
    queries_limit: int
    is_active: bool
